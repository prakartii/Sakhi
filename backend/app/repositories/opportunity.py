"""Data-access layer for opportunities (the global opportunity catalog).

Unlike most other repositories in this package, this one has no
business_profile_id to scope by — opportunities is reference data shared
across every business, not owned by one.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("title", "description", "source_name", "category")


class OpportunityRepository(BaseRepository[Opportunity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Opportunity)

    async def list_active(
        self, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[Opportunity], int]:
        return await self.get_all(
            filters={"is_active": True}, limit=limit, offset=offset
        )

    async def search(
        self,
        query: str,
        *,
        active_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Opportunity], int]:
        """Substring search over title/description/source_name/category,
        active opportunities only unless active_only=False."""
        filters = {"is_active": True} if active_only else None
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
