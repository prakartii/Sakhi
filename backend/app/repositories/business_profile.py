"""Data-access layer for business_profiles.

Builds entirely on BaseRepository for create/get_by_id/get_all/update/
delete/exists — the only additions are list_by_user (a thin, readable
wrapper around get_all()'s generic filtering that
app.services.business_profile already depends on), archive (a mechanical
column-set operation the service uses instead of delete() when it wants a
soft delete — see that service for why), and search().
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_profile import BusinessProfile
from app.models.enums import BusinessStatus
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = (
    "business_name",
    "business_category",
    "industry",
    "city",
    "state",
    "owner_name",
    "business_description",
)


class BusinessProfileRepository(BaseRepository[BusinessProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BusinessProfile)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        status: BusinessStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BusinessProfile], int]:
        filters: dict[str, object] = {"user_id": user_id}
        if status is not None:
            filters["status"] = status
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def archive(self, business_profile: BusinessProfile) -> BusinessProfile:
        # is_primary must also clear here: uq_business_profiles_primary_per_user
        # is a partial unique index on (user_id) WHERE is_primary — leaving it
        # true on an archived row would keep blocking that user from ever
        # onboarding a replacement primary business, which defeats the point
        # of archiving one in the first place.
        business_profile.status = BusinessStatus.ARCHIVED
        business_profile.is_primary = False
        await self.session.flush()
        return business_profile

    async def search(
        self,
        query: str,
        *,
        user_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BusinessProfile], int]:
        """Substring search over business_name/business_category/industry/
        city/state/owner_name/business_description, optionally narrowed to
        one user's businesses."""
        filters = {"user_id": user_id} if user_id is not None else None
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
