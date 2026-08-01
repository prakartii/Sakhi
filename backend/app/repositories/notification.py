"""Data-access layer for notifications (the generic notification outbox)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("title", "body")


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Notification)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        is_read: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        filters: dict[str, object] = {"user_id": user_id}
        if is_read is not None:
            filters["is_read"] = is_read
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def search(
        self,
        query: str,
        *,
        user_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        """Substring search over title/body, optionally narrowed to one
        user's notifications."""
        filters = {"user_id": user_id} if user_id is not None else None
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
