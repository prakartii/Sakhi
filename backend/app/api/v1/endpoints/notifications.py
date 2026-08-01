"""Notification CRUD + read-state endpoints.

user_id is derived from the caller's verified Supabase session
(get_current_app_user) for create/list/mark-all-read — a client can never
read or write another user's notifications through this router.

Covers System Notifications, Business Alerts, Finance Alerts, and Inventory
Alerts via the existing `notification_type` values (system, cashflow_alert,
inventory_alert, plus scheme_match/opportunity_match/mentor_match/reminder
for broader business-growth alerts). There is no dedicated "marketing_alert"
value in the existing notification_type_enum — adding one is a migration
change, which is out of scope here; callers needing a marketing-specific
category should use `system` until that value exists.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_app_user, get_db_session
from app.models.enums import NotificationType
from app.models.user import User
from app.schemas.notification import (
    MarkAllReadResponse,
    NotificationCreate,
    NotificationListResponse,
    NotificationRead,
    NotificationStatus,
)
from app.services.notification import (
    InvalidReferenceError,
    NotificationNotFoundError,
    NotificationService,
)

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> NotificationService:
    return NotificationService(db)


@router.post(
    "",
    response_model=NotificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a notification",
    responses={
        422: {
            "description": "Validation failed, or user_id/business_profile_id "
            "does not exist"
        },
    },
)
async def create_notification(
    payload: NotificationCreate,
    current_user: User = Depends(get_current_app_user),
    service: NotificationService = Depends(get_service),
) -> NotificationRead:
    """Create a notification for the authenticated user — system
    notification, business alert, finance alert, or inventory alert,
    selected via `notification_type`. Always created on the in-app channel."""
    payload.user_id = current_user.id
    try:
        return await service.create(payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List a user's notifications",
)
async def list_notifications(
    business_profile_id: uuid.UUID | None = Query(
        None, description="Filter to notifications about one business."
    ),
    notification_type: NotificationType | None = Query(
        None, description="Filter by notification type."
    ),
    status_filter: NotificationStatus | None = Query(
        None, alias="status", description="Filter by read state."
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_app_user),
    service: NotificationService = Depends(get_service),
) -> NotificationListResponse:
    """List the authenticated user's notifications, most recent first."""
    items, total = await service.list(
        current_user.id,
        business_profile_id=business_profile_id,
        notification_type=notification_type,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return NotificationListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


# Registered before "/{notification_id}" — a POST-vs-GET/DELETE method split
# means there's no literal-vs-parametrized collision today, but keeping
# literal single-segment routes ahead of parametrized ones is the
# established defensive convention in this codebase (see the Inventory
# router's low-stock/out-of-stock endpoints).
@router.post(
    "/mark-all-read",
    response_model=MarkAllReadResponse,
    summary="Mark all of a user's notifications as read",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_app_user),
    service: NotificationService = Depends(get_service),
) -> MarkAllReadResponse:
    updated_count = await service.mark_all_read(current_user.id)
    return MarkAllReadResponse(updated_count=updated_count)


@router.get(
    "/{notification_id}",
    response_model=NotificationRead,
    summary="Get a notification by id",
    responses={404: {"description": "Notification not found"}},
)
async def get_notification(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_service),
) -> NotificationRead:
    try:
        return await service.get(notification_id)
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Notification not found."
        ) from exc


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark a single notification as read",
    responses={404: {"description": "Notification not found"}},
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_service),
) -> NotificationRead:
    """Idempotent: marking an already-read notification read again is a
    no-op that returns the existing row unchanged."""
    try:
        return await service.mark_read(notification_id)
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Notification not found."
        ) from exc


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification",
    responses={404: {"description": "Notification not found"}},
)
async def delete_notification(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_service),
) -> None:
    try:
        await service.delete(notification_id)
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Notification not found."
        ) from exc
