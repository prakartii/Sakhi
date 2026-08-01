"""Data-access layer for business_memory (structured long-term AI memory)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_memory import BusinessMemory
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("title", "content")


class BusinessMemoryRepository(BaseRepository[BusinessMemory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BusinessMemory)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        is_archived: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BusinessMemory], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if is_archived is not None:
            filters["is_archived"] = is_archived
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BusinessMemory], int]:
        """Substring search over title/content, optionally narrowed to one
        business's memory."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
