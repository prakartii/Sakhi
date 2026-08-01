"""Data-access layer for brand_assets.

Builds entirely on BaseRepository for create/get_by_id/get_all/update/
delete/exists — the only additions are list_by_business_profile (a thin,
readable wrapper around get_all()'s generic filtering), archive (a
mechanical column-set operation the service uses instead of delete() — see
that service for why), and search().
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_asset import BrandAsset
from app.models.enums import BrandAssetStatus
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("brand_name", "tagline", "brand_story")


class BrandAssetRepository(BaseRepository[BrandAsset]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BrandAsset)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        status: BrandAssetStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BrandAsset], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if status is not None:
            filters["status"] = status
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def archive(self, brand_asset: BrandAsset) -> BrandAsset:
        brand_asset.status = BrandAssetStatus.ARCHIVED
        await self.session.flush()
        return brand_asset

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BrandAsset], int]:
        """Substring search over brand_name/tagline/brand_story, optionally
        narrowed to one business's brand assets."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
