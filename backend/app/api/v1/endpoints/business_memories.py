"""Business Memory endpoints: read-only listing for the Memory page, plus
two AI-powered views — search() (semantic retrieval via app.ai.embeddings,
pgvector) and insights() (a narrated "Why" over the business's own memory
stats via app.ai.explanations). Rows here are written by the voice
pipeline (app.services.voice), never by a client — see
app/schemas/business_memory.py's docstring — so this module still only
exposes GET, no create/update/delete.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.retrieve import retrieve
from app.ai.explanations import ExplanationRequest, explain
from app.ai.providers.base import AIProviderError
from app.api.deps import get_business_memory_repository, get_db_session
from app.models.business_memory import BusinessMemory
from app.repositories.business_memory import BusinessMemoryRepository
from app.schemas.business_memory import (
    BusinessMemoryListResponse,
    MemoryInsightsResponse,
    MemorySearchResponse,
    MemorySearchResultOut,
)

router = APIRouter()

# Enough to cover a demo-scale business's whole memory history for the
# insights facts computation without an unbounded query.
_INSIGHTS_FACTS_LIMIT = 200


@router.get(
    "",
    response_model=BusinessMemoryListResponse,
    summary="List a business's memories, newest first",
)
async def list_business_memories(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    is_archived: bool | None = Query(None, description="Filter by archived status."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repository: BusinessMemoryRepository = Depends(get_business_memory_repository),
) -> BusinessMemoryListResponse:
    items, total = await repository.list_by_business_profile(
        business_profile_id, is_archived=is_archived, limit=limit, offset=offset
    )
    return BusinessMemoryListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/search",
    response_model=MemorySearchResponse,
    summary="Semantic search over a business's memories (pgvector, via app.ai.embeddings)",
    responses={503: {"description": "Embedding provider unavailable"}},
)
async def search_business_memories(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    query: str = Query(..., min_length=1, max_length=500),
    k: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db_session),
) -> MemorySearchResponse:
    """Ranks memories by cosine similarity to `query`, computed in Postgres
    via pgvector (see app.ai.embeddings.retrieve) — not a substring match."""
    try:
        results = await retrieve(db, query, k=k, business_profile_id=str(business_profile_id))
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return MemorySearchResponse(
        query=query,
        results=[
            MemorySearchResultOut(
                business_memory_id=uuid.UUID(r.business_memory_id),
                title=r.title,
                content=r.content,
                similarity=r.similarity,
            )
            for r in results
        ],
    )


@router.get(
    "/insights",
    response_model=MemoryInsightsResponse,
    summary="A narrated 'Why' over a business's memory stats (app.ai.explanations)",
    responses={503: {"description": "AI provider unavailable"}},
)
async def business_memory_insights(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    repository: BusinessMemoryRepository = Depends(get_business_memory_repository),
) -> MemoryInsightsResponse:
    memories, total = await repository.list_by_business_profile(
        business_profile_id, is_archived=False, limit=_INSIGHTS_FACTS_LIMIT
    )
    facts, top_type, avg_importance = _build_memory_facts(memories)

    try:
        explanation = await explain(
            ExplanationRequest(subject="What your Business Memory says", facts=facts)
        )
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return MemoryInsightsResponse(
        why=explanation.why,
        basis=explanation.basis,
        total=total,
        top_type=top_type,
        avg_importance=avg_importance,
    )


def _build_memory_facts(
    memories: list[BusinessMemory],
) -> tuple[list[str], str | None, float | None]:
    """Deterministic aggregation — no LLM — the facts app.ai.explanations
    is allowed to narrate from. `memories` must already be newest-first
    (BusinessMemoryRepository.list_by_business_profile's default order)."""
    if not memories:
        return (["No memories have been recorded yet."], None, None)

    type_counts: dict[str, int] = {}
    importance_sum = 0
    high_importance = 0
    for memory in memories:
        type_counts[memory.memory_type.value] = type_counts.get(memory.memory_type.value, 0) + 1
        importance_sum += memory.importance_score
        if memory.importance_score >= 4:
            high_importance += 1

    top_type, top_count = max(type_counts.items(), key=lambda kv: kv[1])
    avg_importance = round(importance_sum / len(memories), 1)
    latest = memories[0]

    facts = [
        f"{len(memories)} memories recorded in total.",
        f"Most common type: {top_type} ({top_count} of {len(memories)} memories).",
        f"Average importance score: {avg_importance} out of 5.",
        f"{high_importance} memories are marked high importance (4 or 5 out of 5).",
        f"Most recent memory: {latest.title or latest.content[:120]}.",
    ]
    return facts, top_type, avg_importance
