"""Data-access layer for content_calendar_items.

Builds on BaseRepository for create/get_by_id/update/delete/exists — the
additions are list_by_business_profile (platform/status filters via the
generic equality dict; this is "List Calendar"), list_by_date_range (a
column-range comparison the generic filter dict can't express — backs both
Monthly and Weekly Calendar, which differ only in what start/end the
service computes), and search() (title/caption/call_to_action; hashtags is
a Postgres array column, not comparable via .ilike(), so it's excluded from
free-text search — same reasoning as any other array/JSON column in this
codebase).
"""

import uuid
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_calendar_item import ContentCalendarItem
from app.models.enums import ContentStatus, SocialMediaPlatform
from app.repositories.base import BaseRepository, RepositoryError

_SEARCH_FIELDS = ("title", "caption", "call_to_action")


class ContentCalendarItemRepository(BaseRepository[ContentCalendarItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ContentCalendarItem)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        platform: SocialMediaPlatform | None = None,
        status: ContentStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ContentCalendarItem], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if platform is not None:
            filters["platform"] = platform
        if status is not None:
            filters["status"] = status
        return await self.get_all(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=ContentCalendarItem.scheduled_datetime,
        )

    async def list_by_date_range(
        self,
        business_profile_id: uuid.UUID,
        *,
        start: datetime,
        end: datetime,
        platform: SocialMediaPlatform | None = None,
        status: ContentStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ContentCalendarItem], int]:
        """Items with business_profile_id matching and scheduled_datetime
        in [start, end) — the shared query behind Monthly and Weekly
        Calendar. Items with no scheduled_datetime never match a range, by
        design: an unscheduled draft has no calendar date to appear on."""
        self._validate_pagination(limit, offset)
        conditions = [
            ContentCalendarItem.business_profile_id == business_profile_id,
            ContentCalendarItem.scheduled_datetime >= start,
            ContentCalendarItem.scheduled_datetime < end,
        ]
        if platform is not None:
            conditions.append(ContentCalendarItem.platform == platform)
        if status is not None:
            conditions.append(ContentCalendarItem.status == status)
        return await self._list_by_condition(
            and_(*conditions), limit=limit, offset=offset
        )

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ContentCalendarItem], int]:
        """Substring search over title/caption/call_to_action, optionally
        narrowed to one business's content."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )

    async def _list_by_condition(
        self, condition, *, limit: int, offset: int
    ) -> tuple[list[ContentCalendarItem], int]:
        count_stmt = (
            select(func.count()).select_from(ContentCalendarItem).where(condition)
        )
        list_stmt = (
            select(ContentCalendarItem)
            .where(condition)
            .order_by(ContentCalendarItem.scheduled_datetime.asc())
            .limit(limit)
            .offset(offset)
        )
        try:
            total = (await self.session.execute(count_stmt)).scalar_one()
            rows = (await self.session.execute(list_stmt)).scalars().all()
        except SQLAlchemyError as exc:
            raise RepositoryError(
                "Failed to list content calendar items by date range"
            ) from exc
        return list(rows), total
