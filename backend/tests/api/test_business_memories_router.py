"""Endpoint-level tests for the Business Memory read/search/insights API.

BusinessMemoryRepository is replaced via dependency_overrides with an
in-memory fake; app.ai.embeddings.retrieve.retrieve and
app.ai.explanations.explain are monkeypatched on the endpoint module so no
real pgvector query or AI provider call happens — same isolation pattern
as tests/api/test_schemes_router.py.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.ai.embeddings.schemas import RetrievedMemory
from app.ai.explanations import Explanation
from app.api.deps import get_business_memory_repository, get_db_session
from app.api.v1.endpoints import business_memories as endpoint_module
from app.main import app
from app.models.business_memory import BusinessMemory
from app.models.enums import MemorySource, MemoryType

BASE_URL = "/api/v1/business-memories"


class _FakeMemoryRepo:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, BusinessMemory] = {}

    async def list_by_business_profile(
        self, business_profile_id, *, is_archived=None, limit=20, offset=0
    ):
        items = [m for m in self.store.values() if m.business_profile_id == business_profile_id]
        if is_archived is not None:
            items = [m for m in items if m.is_archived == is_archived]
        return items[offset : offset + limit], len(items)


async def _fake_retrieve(session, query, *, k=5, business_profile_id=None, provider=None):
    return [
        RetrievedMemory(
            business_memory_id=str(uuid.uuid4()),
            title="Supplier delay",
            content="Bagru dyer missed the festival order by four days.",
            chunk_index=0,
            chunk_text="Bagru dyer missed the festival order by four days.",
            similarity=0.87,
        )
    ]


async def _fake_explain(request):
    return Explanation(why=f"Why: {request.subject}", basis="Based on your recorded memories.")


@pytest.fixture
async def fakes(monkeypatch) -> AsyncGenerator[_FakeMemoryRepo, None]:
    repo = _FakeMemoryRepo()
    monkeypatch.setattr(endpoint_module, "retrieve", _fake_retrieve)
    monkeypatch.setattr(endpoint_module, "explain", _fake_explain)
    app.dependency_overrides[get_business_memory_repository] = lambda: repo
    app.dependency_overrides[get_db_session] = lambda: None
    try:
        yield repo
    finally:
        app.dependency_overrides.pop(get_business_memory_repository, None)
        app.dependency_overrides.pop(get_db_session, None)


def _make_memory(business_profile_id, **overrides) -> BusinessMemory:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        business_profile_id=business_profile_id,
        source_voice_log_id=None,
        memory_type=MemoryType.CHALLENGE,
        title="Supplier delay",
        content="Bagru dyer missed the festival order by four days.",
        source=MemorySource.VOICE,
        importance_score=4,
        is_archived=False,
        occurred_at=now,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return BusinessMemory(**defaults)


async def test_list_requires_business_profile_id(client, fakes):
    response = await client.get(BASE_URL)
    assert response.status_code == 422


async def test_list_returns_only_that_business_profiles_memories(client, fakes):
    repo = fakes
    profile_id = uuid.uuid4()
    other_profile_id = uuid.uuid4()
    memory = _make_memory(profile_id)
    repo.store[memory.id] = memory
    other = _make_memory(other_profile_id)
    repo.store[other.id] = other

    response = await client.get(BASE_URL, params={"business_profile_id": str(profile_id)})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Supplier delay"


async def test_search_returns_ranked_results(client, fakes):
    profile_id = uuid.uuid4()

    response = await client.get(
        BASE_URL + "/search",
        params={"business_profile_id": str(profile_id), "query": "supplier delay"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "supplier delay"
    assert len(body["results"]) == 1
    assert body["results"][0]["similarity"] == 0.87


async def test_search_requires_non_empty_query(client, fakes):
    response = await client.get(
        BASE_URL + "/search",
        params={"business_profile_id": str(uuid.uuid4()), "query": ""},
    )
    assert response.status_code == 422


async def test_insights_returns_narrated_stats(client, fakes):
    repo = fakes
    profile_id = uuid.uuid4()
    repo.store[uuid.uuid4()] = _make_memory(profile_id, importance_score=5)
    repo.store[uuid.uuid4()] = _make_memory(profile_id, importance_score=3)

    response = await client.get(BASE_URL + "/insights", params={"business_profile_id": str(profile_id)})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["top_type"] == "challenge"
    assert body["avg_importance"] == 4.0
    assert body["why"]
    assert body["basis"]


async def test_insights_handles_no_memories_gracefully(client, fakes):
    response = await client.get(
        BASE_URL + "/insights", params={"business_profile_id": str(uuid.uuid4())}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["top_type"] is None
    assert body["avg_importance"] is None
