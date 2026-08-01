"""Data-access layer for government_schemes (the global scheme catalog).

Unlike most other repositories in this package, this one has no
business_profile_id to scope by — government_schemes is reference data
shared across every business, not owned by one.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.government_scheme import GovernmentScheme
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("scheme_name", "description", "issuing_authority", "category")


class GovernmentSchemeRepository(BaseRepository[GovernmentScheme]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GovernmentScheme)

    async def list_active(
        self, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[GovernmentScheme], int]:
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
    ) -> tuple[list[GovernmentScheme], int]:
        """Substring search over scheme_name/description/issuing_authority/
        category, active schemes only unless active_only=False."""
        filters = {"is_active": True} if active_only else None
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
