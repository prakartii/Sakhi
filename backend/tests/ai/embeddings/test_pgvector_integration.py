"""Integration test proving app.ai.embeddings.retrieve() ranks results
*inside Postgres* via pgvector's `<=>` operator, not by fetching every row
and sorting in Python. This is the test that backs the "shared business
memory" retrieval claim — everything else in app.ai.embeddings is unit
tests against mocks/pure functions; this one hits a real database.

Requires a real Postgres with the `vector` extension available, pointed to
by TEST_DATABASE_URL — e.g. a throwaway container:

    docker run --rm -d -e POSTGRES_PASSWORD=test -e POSTGRES_DB=sakhi_test \
        -p 55432:5432 pgvector/pgvector:pg16
    TEST_DATABASE_URL=postgresql://postgres:test@localhost:55432/sakhi_test pytest ...

Skipped entirely when TEST_DATABASE_URL isn't set, so the rest of the suite
runs with no external dependency. WARNING: this test creates, truncates,
and drops `business_memory` / `memory_embeddings` tables in whatever
database TEST_DATABASE_URL points to — always point it at a disposable
test database, never at a real one.

These two tests are deliberately plain `def`, not `async def` +
pytest-asyncio: on Windows, psycopg's async mode needs a selector-based
event loop, which asyncio's default Windows policy (ProactorEventLoop)
doesn't provide. The fix is `asyncio.run(coro, loop_factory=...)` (Python
3.12+), scoped to exactly this call via `_run()` below — never
`asyncio.set_event_loop_policy()`, which would change the process-wide
default and leak into every other test's event loop (pytest imports all
test modules before running any of them, so even a module-level policy
change here would affect unrelated tests, not just this file).
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from collections.abc import Coroutine
from typing import Any, TypeVar

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.embeddings.retrieve import retrieve
from app.ai.embeddings.schemas import RetrievedMemory

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL not set — point it at a Postgres+pgvector instance to run this test",
)

EMBEDDING_DIM = 1536
_PRICE_TOPIC = 0
_SUPPLIER_TOPIC = 1
_ORDER_TOPIC = 2

_T = TypeVar("_T")


def _run(coro: Coroutine[Any, Any, _T]) -> _T:
    if sys.platform == "win32":
        return asyncio.run(coro, loop_factory=asyncio.SelectorEventLoop)
    return asyncio.run(coro)


def _vector(weights: dict[int, float]) -> list[float]:
    """A mostly-zero 1536-dim vector with a couple of components set —
    real embeddings are dense, but this keeps expected cosine similarity
    fully predictable so the test's assertions aren't guessing."""
    values = [0.0] * EMBEDDING_DIM
    for index, weight in weights.items():
        values[index] = weight
    return values


class _FixedVectorProvider(EmbeddingProvider):
    """Returns pre-set vectors instead of calling a real embedding API —
    the test controls semantic similarity directly rather than depending
    on what a live model would happen to produce for a given string."""

    def __init__(self, vectors_by_text: dict[str, list[float]]) -> None:
        self._vectors_by_text = vectors_by_text

    @property
    def model_name(self) -> str:
        return "fixed-vector-test-provider"

    @property
    def dimensions(self) -> int:
        return EMBEDDING_DIM

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectors_by_text[t] for t in texts]


def _sqlalchemy_url(raw: str) -> str:
    if raw.startswith("postgresql+"):
        return raw
    if raw.startswith("postgres://"):
        return "postgresql+psycopg://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw[len("postgresql://") :]
    return raw


async def _setup_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("create extension if not exists vector"))
        await conn.execute(text("create extension if not exists pgcrypto"))
        await conn.execute(
            text(
                """
                create table if not exists business_memory (
                    id uuid primary key default gen_random_uuid(),
                    business_profile_id uuid,
                    title varchar(200),
                    content text not null
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                create table if not exists memory_embeddings (
                    id uuid primary key default gen_random_uuid(),
                    business_memory_id uuid not null
                        references business_memory(id) on delete cascade,
                    chunk_index integer not null default 0,
                    chunk_text text not null,
                    embedding vector(1536),
                    embedding_model varchar(100)
                )
                """
            )
        )
        # Guarantee a clean slate even if a previous run crashed before teardown.
        await conn.execute(text("truncate table memory_embeddings, business_memory cascade"))


async def _teardown_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("drop table if exists memory_embeddings"))
        await conn.execute(text("drop table if exists business_memory"))
    await engine.dispose()


async def _insert_memory(
    session: AsyncSession,
    *,
    content: str,
    embedding: list[float],
    title: str | None = None,
) -> str:
    memory_id = str(uuid.uuid4())
    await session.execute(
        text("insert into business_memory (id, title, content) values (:id, :title, :content)"),
        {"id": memory_id, "title": title, "content": content},
    )
    await session.execute(
        text(
            """
            insert into memory_embeddings
                (business_memory_id, chunk_index, chunk_text, embedding, embedding_model)
            values
                (:business_memory_id, 0, :chunk_text, cast(:embedding as vector), 'test')
            """
        ),
        {
            "business_memory_id": memory_id,
            "chunk_text": content,
            "embedding": "[" + ",".join(repr(v) for v in embedding) + "]",
        },
    )
    return memory_id


async def _ranking_scenario() -> tuple[list[RetrievedMemory], str, str]:
    assert TEST_DATABASE_URL is not None  # guaranteed by pytestmark's skipif
    engine = create_async_engine(_sqlalchemy_url(TEST_DATABASE_URL))
    try:
        await _setup_schema(engine)
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with session_factory() as session:
            price_change_id = await _insert_memory(
                session,
                title="Price change",
                content="Raised dupatta price from Rs 640 to Rs 820 because cloth got more expensive.",
                embedding=_vector({_PRICE_TOPIC: 0.95, _ORDER_TOPIC: 0.05}),
            )
            cost_increase_id = await _insert_memory(
                session,
                title="Cost increase",
                content="Cotton base cloth cost went up Rs 28 per metre.",
                embedding=_vector({_PRICE_TOPIC: 0.85, _SUPPLIER_TOPIC: 0.15}),
            )
            await _insert_memory(
                session,
                title="Supplier delay",
                content="Indigo dye lot from Bagru delayed 9 days, orders slipped to July.",
                embedding=_vector({_SUPPLIER_TOPIC: 1.0}),
            )
            await _insert_memory(
                session,
                title="Bulk order",
                content="Bengaluru boutique ordered 40 dupattas for Rs 32,800.",
                embedding=_vector({_ORDER_TOPIC: 1.0}),
            )
            await session.commit()

            query = "Why did I raise my prices?"
            provider = _FixedVectorProvider({query: _vector({_PRICE_TOPIC: 1.0})})
            results = await retrieve(session, query, k=2, provider=provider)

        return results, price_change_id, cost_increase_id
    finally:
        await _teardown_schema(engine)


def test_retrieve_ranks_by_cosine_similarity_computed_in_postgres() -> None:
    results, price_change_id, cost_increase_id = _run(_ranking_scenario())

    assert len(results) == 2
    # Both pricing-related chunks outrank the supplier-delay and bulk-order
    # ones, in the right relative order — proving Postgres did the ranking,
    # not that "the first row happened to be right."
    assert results[0].business_memory_id == price_change_id
    assert results[1].business_memory_id == cost_increase_id
    assert results[0].similarity > results[1].similarity
    assert "dupatta price" in results[0].content


async def _k_scenario() -> list[RetrievedMemory]:
    assert TEST_DATABASE_URL is not None  # guaranteed by pytestmark's skipif
    engine = create_async_engine(_sqlalchemy_url(TEST_DATABASE_URL))
    try:
        await _setup_schema(engine)
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with session_factory() as session:
            for i in range(4):
                await _insert_memory(
                    session,
                    content=f"Memory number {i}",
                    embedding=_vector({_PRICE_TOPIC: 1.0 - i * 0.1}),
                )
            await session.commit()

            query = "price"
            provider = _FixedVectorProvider({query: _vector({_PRICE_TOPIC: 1.0})})
            return await retrieve(session, query, k=1, provider=provider)
    finally:
        await _teardown_schema(engine)


def test_retrieve_respects_k() -> None:
    results = _run(_k_scenario())

    assert len(results) == 1
    assert results[0].content == "Memory number 0"
