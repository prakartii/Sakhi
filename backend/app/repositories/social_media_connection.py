"""Data-access layer for social_media_connections.

Builds entirely on BaseRepository for create/get_by_id/get_all/update/
delete/exists — the additions are list_by_business_profile (a thin,
readable wrapper around get_all()'s generic filtering),
get_by_business_profile_and_platform (used by
SocialMediaConnectionService.connect to decide reconnect-in-place vs.
create — the table's unique(business_profile_id, platform) constraint means
there is at most one row to find), and search().
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SocialConnectionStatus, SocialMediaPlatform
from app.models.social_media_connection import SocialMediaConnection
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("account_name", "account_id", "profile_url")


class SocialMediaConnectionRepository(BaseRepository[SocialMediaConnection]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SocialMediaConnection)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        platform: SocialMediaPlatform | None = None,
        connection_status: SocialConnectionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SocialMediaConnection], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if platform is not None:
            filters["platform"] = platform
        if connection_status is not None:
            filters["connection_status"] = connection_status
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def get_by_business_profile_and_platform(
        self, business_profile_id: uuid.UUID, platform: SocialMediaPlatform
    ) -> SocialMediaConnection | None:
        items, _total = await self.get_all(
            filters={
                "business_profile_id": business_profile_id,
                "platform": platform,
            },
            limit=1,
        )
        return items[0] if items else None

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SocialMediaConnection], int]:
        """Substring search over account_name/account_id/profile_url,
        optionally narrowed to one business's connections."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
