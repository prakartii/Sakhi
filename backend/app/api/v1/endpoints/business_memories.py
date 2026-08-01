"""Business Memory endpoints: read-only listing for the Memory page.

Rows here are written by the voice pipeline (app.services.voice), never by
a client — see app/schemas/business_memory.py's docstring — so this module
only exposes GET, not create/update/delete.

No authentication yet: business_profile_id is supplied explicitly by the
caller (required query param on list) instead of being derived from a
session — the same deliberate, temporary gap already documented on every
other business-profile-scoped module in this project (inventory,
transactions, brand-assets, ...).
"""

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_business_memory_repository
from app.repositories.business_memory import BusinessMemoryRepository
from app.schemas.business_memory import BusinessMemoryListResponse

router = APIRouter()


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
