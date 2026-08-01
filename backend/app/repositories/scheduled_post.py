"""Data-access layer for scheduled_posts.

Builds on BaseRepository for create/get_by_id/update/delete/exists — the
additions are list_by_business_profile (the general listing, optionally
narrowed to one status), list_queue ("Get Queue": items still pending —
queued or actively publishing), and list_history ("Publishing History":
items with a resolved outcome — published, failed, or cancelled — newest
activity first). Both list_queue/list_history use BaseRepository's existing
support for list-valued filters (rendered as an IN(...) clause by
_build_conditions) rather than a bespoke query — no new query-building
needed for a status-set filter.

No search() here: unlike every other module in this codebase, Scheduled
Posts was never asked for a Search operation, and its only free-text
columns (published_url, error_log) are populated by a future publishing
component this module doesn't call — adding a search method with no caller
would be unused code, not architectural consistency.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PublishingStatus
from app.models.scheduled_post import ScheduledPost
from app.repositories.base import BaseRepository

_QUEUE_STATUSES = (PublishingStatus.QUEUED, PublishingStatus.PUBLISHING)
_HISTORY_STATUSES = (
    PublishingStatus.PUBLISHED,
    PublishingStatus.FAILED,
    PublishingStatus.CANCELLED,
)


class ScheduledPostRepository(BaseRepository[ScheduledPost]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ScheduledPost)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        publishing_status: PublishingStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ScheduledPost], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if publishing_status is not None:
            filters["publishing_status"] = publishing_status
        return await self.get_all(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=ScheduledPost.scheduled_time,
        )

    async def list_queue(
        self,
        business_profile_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ScheduledPost], int]:
        """Pending work: queued or actively publishing, soonest first."""
        return await self.get_all(
            filters={
                "business_profile_id": business_profile_id,
                "publishing_status": list(_QUEUE_STATUSES),
            },
            limit=limit,
            offset=offset,
            order_by=ScheduledPost.scheduled_time,
        )

    async def list_history(
        self,
        business_profile_id: uuid.UUID,
        *,
        publishing_status: PublishingStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ScheduledPost], int]:
        """Resolved outcomes — published, failed, or cancelled by default,
        or narrowed to one specific status — most recently updated first."""
        statuses = (
            [publishing_status]
            if publishing_status is not None
            else list(_HISTORY_STATUSES)
        )
        return await self.get_all(
            filters={
                "business_profile_id": business_profile_id,
                "publishing_status": statuses,
            },
            limit=limit,
            offset=offset,
            order_by=ScheduledPost.updated_at.desc(),
        )
