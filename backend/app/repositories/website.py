"""Data-access layer for websites.

Builds entirely on BaseRepository for create/get_by_id/get_all/update/
delete/exists — the only additions are list_by_business_profile (a thin,
readable wrapper around get_all()'s generic filtering), archive (a
mechanical column-set operation the service uses instead of delete() — see
that service for why), and search().
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WebsiteStatus
from app.models.website import Website
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = (
    "website_name",
    "seo_title",
    "seo_description",
    "template",
    "custom_domain",
)


class WebsiteRepository(BaseRepository[Website]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Website)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        status: WebsiteStatus | None = None,
        published: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Website], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if status is not None:
            filters["status"] = status
        if published is not None:
            filters["published"] = published
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def archive(self, website: Website) -> Website:
        website.status = WebsiteStatus.ARCHIVED
        await self.session.flush()
        return website

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Website], int]:
        """Substring search over website_name/seo_title/seo_description/
        template/custom_domain, optionally narrowed to one business's
        websites."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
