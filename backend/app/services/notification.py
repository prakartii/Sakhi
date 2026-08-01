"""Business logic for the Notification module.

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions
directly, matching every other service in this codebase.

This module only builds on NotificationRepository/BaseRepository's existing
public methods (get_all/get_by_id/create/update/delete) — no repository or
model changes, per this task's constraints. Listing and "mark all read" are
implemented here with the repository's generic filter dict rather than by
adding new repository query methods.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationChannel, NotificationType
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationCreate, NotificationStatus

# BaseRepository._validate_pagination caps limit at 200 — reused as the page
# size for mark_all_read's internal sweep so it stays within that ceiling.
_MARK_ALL_READ_PAGE_SIZE = 200


class NotificationNotFoundError(Exception):
    """No notifications row exists for the given id."""


class InvalidReferenceError(Exception):
    """A referenced user_id or business_profile_id does not exist."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "notifications_user_id_fkey" in message:
        return InvalidReferenceError("user_id does not reference an existing user.")
    if "notifications_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
        repository: NotificationRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or NotificationRepository(session)

    async def create(self, payload: NotificationCreate) -> Notification:
        # channel is always in_app — see app/schemas/notification.py's
        # module docstring for why it's never taken from the caller. is_read
        # is set explicitly rather than left to the column's server_default
        # so a freshly created notification is filterable/correct
        # immediately, without depending on a flush/RETURNING round trip to
        # populate it.
        notification = Notification(
            **payload.model_dump(),
            channel=NotificationChannel.IN_APP,
            is_read=False,
        )
        try:
            await self._repo.create(notification)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return notification

    async def get(self, notification_id: uuid.UUID) -> Notification:
        notification = await self._repo.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFoundError(str(notification_id))
        return notification

    async def list(
        self,
        user_id: uuid.UUID,
        *,
        business_profile_id: uuid.UUID | None = None,
        notification_type: NotificationType | None = None,
        status: NotificationStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        filters: dict[str, object] = {"user_id": user_id}
        if business_profile_id is not None:
            filters["business_profile_id"] = business_profile_id
        if notification_type is not None:
            filters["notification_type"] = notification_type
        if status is not None:
            filters["is_read"] = status == "read"
        return await self._repo.get_all(filters=filters, limit=limit, offset=offset)

    async def mark_read(self, notification_id: uuid.UUID) -> Notification:
        notification = await self.get(notification_id)
        if not notification.is_read:
            await self._repo.update(
                notification,
                {"is_read": True, "read_at": datetime.now(timezone.utc)},
            )
            await self._session.commit()
        return notification

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Marks every unread notification for a user as read, returning how
        many were updated.

        Sweeps in pages rather than issuing one bulk UPDATE, so this stays
        within the repository's existing get_all/update surface instead of
        adding a new repository method. Each update() flushes (but doesn't
        commit), so the next page's is_read=False query — same session, same
        still-open transaction — no longer sees the rows just marked read,
        and the loop terminates once a page comes back empty. One commit at
        the end keeps the whole sweep a single unit of work. Fine for a
        per-user notification inbox; a table-wide bulk UPDATE would be
        worth adding as a repository method if this ever needs to scale
        past that.
        """
        updated = 0
        while True:
            unread, _total = await self._repo.get_all(
                filters={"user_id": user_id, "is_read": False},
                limit=_MARK_ALL_READ_PAGE_SIZE,
                offset=0,
            )
            if not unread:
                break
            now = datetime.now(timezone.utc)
            for notification in unread:
                await self._repo.update(notification, {"is_read": True, "read_at": now})
            updated += len(unread)
        await self._session.commit()
        return updated

    async def delete(self, notification_id: uuid.UUID) -> None:
        notification = await self.get(notification_id)
        await self._repo.delete(notification)
        await self._session.commit()
