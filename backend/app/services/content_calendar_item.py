"""Business logic for the Content Calendar module.

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions
directly. Format/shape validation lives in the Pydantic schemas at the API
boundary; the one genuinely interpretive rule here is
_validate_social_connection: whether a given social_connection_id actually
belongs to the same business and platform isn't something a foreign key
alone can express (the FK only proves the row exists, not that it's the
*right* row for this business/platform), so it's checked here against
SocialMediaConnectionRepository before every create/update.

No AI generation and no publishing happen anywhere in this module — it
only stores and retrieves calendar rows a caller already decided on.

Uses `from __future__ import annotations` for the same reason as
WebsiteService/InventoryService/NotificationService: this class has a
method literally named `list`, which would otherwise shadow the `list`
builtin for any later method's own `list[...]` return annotation once the
class body finishes executing — and monthly_calendar/weekly_calendar/search
all come after `list` and all return `list[...]`.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_calendar_item import ContentCalendarItem
from app.models.enums import ContentStatus, SocialMediaPlatform
from app.repositories.content_calendar_item import ContentCalendarItemRepository
from app.repositories.social_media_connection import SocialMediaConnectionRepository
from app.schemas.content_calendar_item import (
    ContentCalendarItemCreate,
    ContentCalendarItemUpdate,
)


class ContentCalendarItemNotFoundError(Exception):
    """No content_calendar_items row exists for the given id."""


class InvalidReferenceError(Exception):
    """The referenced business_profile_id does not exist."""


class InvalidSocialConnectionError(Exception):
    """social_connection_id doesn't exist, doesn't belong to the same
    business, or doesn't match the content item's platform."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "content_calendar_items_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    if "content_calendar_items_social_connection_id_fkey" in message:
        return InvalidSocialConnectionError(
            "social_connection_id does not reference an existing social media "
            "connection."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


class ContentCalendarItemService:
    def __init__(
        self,
        session: AsyncSession,
        repository: ContentCalendarItemRepository | None = None,
        connection_repository: SocialMediaConnectionRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or ContentCalendarItemRepository(session)
        self._connection_repo = (
            connection_repository or SocialMediaConnectionRepository(session)
        )

    async def _validate_social_connection(
        self,
        business_profile_id: uuid.UUID,
        social_connection_id: uuid.UUID | None,
        platform: SocialMediaPlatform,
    ) -> None:
        if social_connection_id is None:
            return
        connection = await self._connection_repo.get_by_id(social_connection_id)
        if connection is None:
            raise InvalidSocialConnectionError(
                "social_connection_id does not reference an existing social "
                "media connection."
            )
        if connection.business_profile_id != business_profile_id:
            raise InvalidSocialConnectionError(
                "social_connection_id does not belong to the same "
                "business_profile_id."
            )
        if connection.platform != platform:
            raise InvalidSocialConnectionError(
                "social_connection_id's platform does not match this content "
                "item's platform."
            )

    async def create(self, payload: ContentCalendarItemCreate) -> ContentCalendarItem:
        await self._validate_social_connection(
            payload.business_profile_id, payload.social_connection_id, payload.platform
        )
        item = ContentCalendarItem(**payload.model_dump())
        try:
            await self._repo.create(item)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return item

    async def get(self, item_id: uuid.UUID) -> ContentCalendarItem:
        item = await self._repo.get_by_id(item_id)
        if item is None:
            raise ContentCalendarItemNotFoundError(str(item_id))
        return item

    async def list(
        self,
        business_profile_id: uuid.UUID,
        *,
        platform: SocialMediaPlatform | None = None,
        status: ContentStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ContentCalendarItem], int]:
        return await self._repo.list_by_business_profile(
            business_profile_id,
            platform=platform,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def monthly_calendar(
        self,
        business_profile_id: uuid.UUID,
        *,
        year: int,
        month: int,
        platform: SocialMediaPlatform | None = None,
        status: ContentStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ContentCalendarItem], int]:
        """Items scheduled anywhere in the given calendar month, in the
        UTC day boundaries of that month (matching how scheduled_datetime
        is stored — timestamptz)."""
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )
        return await self._repo.list_by_date_range(
            business_profile_id,
            start=start,
            end=end,
            platform=platform,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def weekly_calendar(
        self,
        business_profile_id: uuid.UUID,
        *,
        week_start: date,
        platform: SocialMediaPlatform | None = None,
        status: ContentStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ContentCalendarItem], int]:
        """Items scheduled in the 7 days starting at week_start (inclusive)
        up to but not including week_start + 7 days. Which day a "week"
        starts on is the caller's choice (a calendar UI already knows its
        own week convention) — this just takes whatever date it's given as
        day one.
        """
        start = datetime.combine(week_start, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=7)
        return await self._repo.list_by_date_range(
            business_profile_id,
            start=start,
            end=end,
            platform=platform,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ContentCalendarItem], int]:
        return await self._repo.search(
            query, business_profile_id=business_profile_id, limit=limit, offset=offset
        )

    async def update(
        self, item_id: uuid.UUID, payload: ContentCalendarItemUpdate
    ) -> ContentCalendarItem:
        """PATCH: applies only the fields the caller actually supplied. The
        social-connection check runs against the resulting merged state
        (existing value for anything the caller didn't touch), not the raw
        payload — matching TransactionService.update's approach to the same
        problem for is_recurring/recurring_frequency.
        """
        item = await self.get(item_id)
        data = payload.model_dump(exclude_unset=True)
        social_connection_id = data.get(
            "social_connection_id", item.social_connection_id
        )
        platform = data.get("platform", item.platform)
        await self._validate_social_connection(
            item.business_profile_id, social_connection_id, platform
        )
        try:
            await self._repo.update(item, data)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return item

    async def delete(self, item_id: uuid.UUID) -> None:
        """Hard delete. Unlike Brand Assets/Website, `status` here (draft/
        scheduled/published/failed/cancelled) describes publishing
        lifecycle, not record lifecycle — 'cancelled' already covers "don't
        publish this" without losing the row, so a caller that explicitly
        asks to delete a row means it, the same reasoning
        TransactionService.delete documents for its own hard delete.
        """
        item = await self.get(item_id)
        await self._repo.delete(item)
        await self._session.commit()
