"""Data-access layer for website_versions.

Builds entirely on BaseRepository for create/get_by_id/get_all/exists/
count — versions are append-only, so update()/delete() are inherited but
deliberately never called by WebsiteService (see that service). The
additions here are list_by_website (newest-first, matching
idx_website_versions_website), get_latest (used to show "current" state
without a separate endpoint), and search() over change_notes/website_name.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.website_version import WebsiteVersion
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("website_name", "change_notes")


class WebsiteVersionRepository(BaseRepository[WebsiteVersion]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WebsiteVersion)

    async def list_by_website(
        self,
        website_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[WebsiteVersion], int]:
        return await self.get_all(
            filters={"website_id": website_id},
            limit=limit,
            offset=offset,
            order_by=WebsiteVersion.version_number.desc(),
        )

    async def get_by_website_and_version(
        self, website_id: uuid.UUID, version_number: int
    ) -> WebsiteVersion | None:
        items, _total = await self.get_all(
            filters={"website_id": website_id, "version_number": version_number},
            limit=1,
        )
        return items[0] if items else None

    async def get_latest(self, website_id: uuid.UUID) -> WebsiteVersion | None:
        items, _total = await self.get_all(
            filters={"website_id": website_id},
            limit=1,
            order_by=WebsiteVersion.version_number.desc(),
        )
        return items[0] if items else None

    async def search(
        self,
        query: str,
        *,
        website_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[WebsiteVersion], int]:
        """Substring search over website_name/change_notes, optionally
        narrowed to one website's history."""
        filters = {"website_id": website_id} if website_id is not None else None
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
