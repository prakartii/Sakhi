"""Content Calendar CRUD + calendar-view endpoints.

Storage only: title, content_type, platform, caption, hashtags,
image_prompt, call_to_action, scheduling, and lifecycle status. Nothing
here calls an AI provider and nothing here publishes to a platform — this
module reads and writes calendar data a caller (human or, later, a
separate AI captioning service) provides.

No authentication yet: business_profile_id is supplied explicitly by the
caller (request body on create, required query param on list/search/
monthly/weekly) instead of being derived from a session — the same
deliberate, temporary gap already documented on every other module's
endpoints.

Route order below matters: "/search", "/monthly", and "/weekly" are
literal single-segment GET paths and must be registered before the
parametrized "/{item_id}" GET at the same depth, or FastAPI would try to
parse "search"/"monthly"/"weekly" as a UUID path param — the same hazard
class already documented on the Inventory router's low-stock/out-of-stock
endpoints.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.enums import ContentStatus, SocialMediaPlatform
from app.schemas.content_calendar_item import (
    ContentCalendarItemCreate,
    ContentCalendarItemListResponse,
    ContentCalendarItemRead,
    ContentCalendarItemUpdate,
)
from app.services.content_calendar_item import (
    ContentCalendarItemNotFoundError,
    ContentCalendarItemService,
    InvalidReferenceError,
    InvalidSocialConnectionError,
)

router = APIRouter()


def get_service(
    db: AsyncSession = Depends(get_db_session),
) -> ContentCalendarItemService:
    return ContentCalendarItemService(db)


@router.post(
    "",
    response_model=ContentCalendarItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a content calendar item",
    responses={
        422: {
            "description": "Validation failed, business_profile_id does not "
            "exist, or social_connection_id is invalid for this business/"
            "platform"
        },
    },
)
async def create_content(
    payload: ContentCalendarItemCreate,
    service: ContentCalendarItemService = Depends(get_service),
) -> ContentCalendarItemRead:
    """Plan a piece of content. `status` defaults to `draft`; nothing here
    generates a caption/image or publishes anything."""
    try:
        return await service.create(payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except InvalidSocialConnectionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "",
    response_model=ContentCalendarItemListResponse,
    summary="List a business's content calendar",
)
async def list_calendar(
    business_profile_id: uuid.UUID = Query(
        ...,
        description="Owning business id (temporary — replaced by session-derived "
        "scoping once auth exists).",
    ),
    platform: SocialMediaPlatform | None = Query(
        None, description="Filter by platform."
    ),
    status_filter: ContentStatus | None = Query(
        None, alias="status", description="Filter by lifecycle status."
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ContentCalendarItemService = Depends(get_service),
) -> ContentCalendarItemListResponse:
    """List a business's planned content, soonest scheduled first."""
    items, total = await service.list(
        business_profile_id,
        platform=platform,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return ContentCalendarItemListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/search",
    response_model=ContentCalendarItemListResponse,
    summary="Search a business's content calendar",
)
async def search_content(
    q: str = Query(
        ...,
        min_length=1,
        description="Substring to match against " "title/caption/call_to_action.",
    ),
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ContentCalendarItemService = Depends(get_service),
) -> ContentCalendarItemListResponse:
    items, total = await service.search(
        q, business_profile_id=business_profile_id, limit=limit, offset=offset
    )
    return ContentCalendarItemListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/monthly",
    response_model=ContentCalendarItemListResponse,
    summary="Monthly calendar view",
)
async def monthly_calendar(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    platform: SocialMediaPlatform | None = Query(
        None, description="Filter by platform."
    ),
    status_filter: ContentStatus | None = Query(
        None, alias="status", description="Filter by lifecycle status."
    ),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ContentCalendarItemService = Depends(get_service),
) -> ContentCalendarItemListResponse:
    """Items scheduled anywhere within the given calendar month (UTC)."""
    items, total = await service.monthly_calendar(
        business_profile_id,
        year=year,
        month=month,
        platform=platform,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return ContentCalendarItemListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/weekly",
    response_model=ContentCalendarItemListResponse,
    summary="Weekly calendar view",
)
async def weekly_calendar(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    week_start: date = Query(
        ..., description="First day of the 7-day window (inclusive, UTC)."
    ),
    platform: SocialMediaPlatform | None = Query(
        None, description="Filter by platform."
    ),
    status_filter: ContentStatus | None = Query(
        None, alias="status", description="Filter by lifecycle status."
    ),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ContentCalendarItemService = Depends(get_service),
) -> ContentCalendarItemListResponse:
    """Items scheduled in the 7 days starting at week_start."""
    items, total = await service.weekly_calendar(
        business_profile_id,
        week_start=week_start,
        platform=platform,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return ContentCalendarItemListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/{item_id}",
    response_model=ContentCalendarItemRead,
    summary="Get a content calendar item by id",
    responses={404: {"description": "Content calendar item not found"}},
)
async def get_content(
    item_id: uuid.UUID,
    service: ContentCalendarItemService = Depends(get_service),
) -> ContentCalendarItemRead:
    try:
        return await service.get(item_id)
    except ContentCalendarItemNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Content calendar item not found."
        ) from exc


@router.patch(
    "/{item_id}",
    response_model=ContentCalendarItemRead,
    summary="Partially update a content calendar item",
    responses={
        404: {"description": "Content calendar item not found"},
        422: {
            "description": "Validation failed, or social_connection_id is "
            "invalid for this business/platform"
        },
    },
)
async def update_content(
    item_id: uuid.UUID,
    payload: ContentCalendarItemUpdate,
    service: ContentCalendarItemService = Depends(get_service),
) -> ContentCalendarItemRead:
    """Update only the fields present in the request body; omitted fields
    are left unchanged."""
    try:
        return await service.update(item_id, payload)
    except ContentCalendarItemNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Content calendar item not found."
        ) from exc
    except InvalidSocialConnectionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a content calendar item",
    responses={404: {"description": "Content calendar item not found"}},
)
async def delete_content(
    item_id: uuid.UUID,
    service: ContentCalendarItemService = Depends(get_service),
) -> None:
    """Permanently deletes the row — see ContentCalendarItemService.delete
    for why this module hard-deletes rather than archiving."""
    try:
        await service.delete(item_id)
    except ContentCalendarItemNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Content calendar item not found."
        ) from exc
