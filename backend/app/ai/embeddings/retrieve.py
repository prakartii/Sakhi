"""Runs pgvector similarity search in Postgres — the production ANN
retrieval path for Business Memory RAG. Ranking happens in the database
via the `<=>` cosine-distance operator against memory_embeddings.embedding
(see migration 19's ivfflat index), never by fetching every row and
sorting in Python. app.ai.embeddings.similarity's top_k_similar() is for a
different, smaller-scale use — re-ranking an already-fetched candidate set
(e.g. in tests, or a shortlist pulled some other way).

This is the one place app.ai touches the database directly, and only via a
caller-supplied AsyncSession — it doesn't own connection/session lifecycle,
matching how app.repositories takes a session rather than opening its own.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.factory import get_embedding_provider
from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.embeddings.schemas import RetrievedMemory

# 1 - cosine_distance = cosine_similarity; pgvector's `<=>` operator *is*
# cosine distance under vector_cosine_ops (the ivfflat index's opclass —
# see migration 19), so ORDER BY embedding <=> :query lets Postgres use
# that index instead of a full scan.
_SEARCH_SQL = text(
    """
    select
        bm.id as business_memory_id,
        bm.title as title,
        bm.content as content,
        me.chunk_index as chunk_index,
        me.chunk_text as chunk_text,
        1 - (me.embedding <=> cast(:query_embedding as vector)) as similarity
    from memory_embeddings me
    join business_memory bm on bm.id = me.business_memory_id
    where me.embedding is not null
      and (
          cast(:business_profile_id as uuid) is null
          or bm.business_profile_id = cast(:business_profile_id as uuid)
      )
    order by me.embedding <=> cast(:query_embedding as vector)
    limit :k
    """
)


async def retrieve(
    session: AsyncSession,
    query: str,
    *,
    k: int = 5,
    business_profile_id: str | None = None,
    provider: EmbeddingProvider | None = None,
) -> list[RetrievedMemory]:
    """Embed `query` and return the top-`k` business_memory chunks ranked
    by cosine similarity to it, computed inside Postgres.

    `business_profile_id`, if given, scopes results to one business —
    callers should always pass it in production; it's optional only so
    this can be exercised without a business_profiles row in tests.
    """
    embedder = provider or get_embedding_provider()
    [query_vector] = await embedder.embed([query])

    result = await session.execute(
        _SEARCH_SQL,
        {
            "query_embedding": _to_pgvector_literal(query_vector),
            "business_profile_id": business_profile_id,
            "k": k,
        },
    )
    rows = result.mappings().all()

    return [
        RetrievedMemory(
            business_memory_id=str(row["business_memory_id"]),
            title=row["title"],
            content=row["content"],
            chunk_index=row["chunk_index"],
            chunk_text=row["chunk_text"],
            similarity=float(row["similarity"]),
        )
        for row in rows
    ]


def _to_pgvector_literal(vector: list[float]) -> str:
    """pgvector's text input format is '[v1,v2,...]'; the SQL casts this
    string to `vector` rather than depending on the pgvector Python
    adapter being registered on the connection."""
    return "[" + ",".join(repr(v) for v in vector) + "]"
