"""Scheduled Posts endpoints — the publishing queue/history for Content
Calendar items.

Storage only: nothing here calls a platform API and nothing here publishes
anything. "Update Status" records the outcome of a publish attempt made by
some future component; this router only persists what it reports.

No authentication yet: business_profile_id is supplied explicitly by the
caller (request body on schedule, required query param on queue/history)
instead of being derived from a session — the same deliberate, temporary
gap already documented on every other module's endpoints.

Route order below matters: "/queue" and "/history" are literal
single-segment GET paths and must be registered before the parametrized
"/{scheduled_post_id}" GET at the same depth, or FastAPI would try to
parse "queue"/"history" as a UUID path param — the same hazard class
already documented on the Inventory and Content Calendar routers.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.enums import PublishingStatus
from app.schemas.scheduled_post import (
    ScheduledPostCreate,
    ScheduledPostListResponse,
    ScheduledPostRead,
    UpdateStatusRequest,
)
from app.services.scheduled_post import (
    InvalidContentCalendarReferenceError,
    InvalidReferenceError,
    InvalidScheduleError,
    InvalidSocialConnectionError,
    InvalidStatusTransitionError,
    ScheduledPostNotFoundError,
    ScheduledPostService,
)

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> ScheduledPostService:
    return ScheduledPostService(db)


@router.post(
    "",
    response_model=ScheduledPostRead,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a post",
    responses={
        422: {
            "description": "Validation failed, scheduled_time is not in the "
            "future, content_calendar_id/business_profile_id does not exist, "
            "or social_connection_id is invalid, wrong platform, or not "
            "connected"
        },
    },
)
async def schedule_post(
    payload: ScheduledPostCreate,
    service: ScheduledPostService = Depends(get_service),
) -> ScheduledPostRead:
    """Queue a content_calendar_items row to publish through a connected
    social account at a given time. `publishing_status` starts `queued`."""
    try:
        return await service.schedule_post(payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except InvalidContentCalendarReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except InvalidSocialConnectionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except InvalidScheduleError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "/queue",
    response_model=ScheduledPostListResponse,
    summary="Get the publishing queue",
)
async def get_queue(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ScheduledPostService = Depends(get_service),
) -> ScheduledPostListResponse:
    """Pending work: queued or actively publishing, soonest scheduled
    first."""
    items, total = await service.get_queue(
        business_profile_id, limit=limit, offset=offset
    )
    return ScheduledPostListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/history",
    response_model=ScheduledPostListResponse,
    summary="Get publishing history",
)
async def publishing_history(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    status_filter: PublishingStatus | None = Query(
        None,
        alias="status",
        description="Narrow to one outcome status. Defaults to all resolved "
        "outcomes (published/failed/cancelled).",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ScheduledPostService = Depends(get_service),
) -> ScheduledPostListResponse:
    """Resolved outcomes, most recently updated first."""
    items, total = await service.publishing_history(
        business_profile_id, publishing_status=status_filter, limit=limit, offset=offset
    )
    return ScheduledPostListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/{scheduled_post_id}",
    response_model=ScheduledPostRead,
    summary="Get a scheduled post by id",
    responses={404: {"description": "Scheduled post not found"}},
)
async def get_scheduled_post(
    scheduled_post_id: uuid.UUID,
    service: ScheduledPostService = Depends(get_service),
) -> ScheduledPostRead:
    try:
        return await service.get(scheduled_post_id)
    except ScheduledPostNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Scheduled post not found."
        ) from exc


@router.post(
    "/{scheduled_post_id}/cancel",
    response_model=ScheduledPostRead,
    summary="Cancel a scheduled post",
    responses={
        404: {"description": "Scheduled post not found"},
        422: {"description": "Post has already been published"},
    },
)
async def cancel_schedule(
    scheduled_post_id: uuid.UUID,
    service: ScheduledPostService = Depends(get_service),
) -> ScheduledPostRead:
    """Sets publishing_status to `cancelled`. Idempotent if already
    cancelled; rejected if the post has already published."""
    try:
        return await service.cancel_schedule(scheduled_post_id)
    except ScheduledPostNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Scheduled post not found."
        ) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.post(
    "/{scheduled_post_id}/retry",
    response_model=ScheduledPostRead,
    summary="Retry a failed post",
    responses={
        404: {"description": "Scheduled post not found"},
        422: {"description": "Post is not currently in a failed state"},
    },
)
async def retry_failed_post(
    scheduled_post_id: uuid.UUID,
    service: ScheduledPostService = Depends(get_service),
) -> ScheduledPostRead:
    """Requeues a failed post (`publishing_status` back to `queued`) and
    increments retry_count. Only valid from `failed`."""
    try:
        return await service.retry_failed_post(scheduled_post_id)
    except ScheduledPostNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Scheduled post not found."
        ) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.patch(
    "/{scheduled_post_id}/status",
    response_model=ScheduledPostRead,
    summary="Record the outcome of a publish attempt",
    responses={
        404: {"description": "Scheduled post not found"},
        422: {"description": "Post is already published or cancelled"},
    },
)
async def update_status(
    scheduled_post_id: uuid.UUID,
    payload: UpdateStatusRequest,
    service: ScheduledPostService = Depends(get_service),
) -> ScheduledPostRead:
    """Persists an outcome reported by whatever component actually
    attempted to publish — does not call a platform API itself. Replaces
    published_url/provider_response/error_log with exactly what's in this
    report; not a partial patch. Sets published_at automatically when
    publishing_status is `published`."""
    try:
        return await service.update_status(scheduled_post_id, payload)
    except ScheduledPostNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Scheduled post not found."
        ) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
