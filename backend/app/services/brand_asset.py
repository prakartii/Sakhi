"""Business logic for Brand Assets.

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions
directly. Format/shape validation (hex color, URL scheme, non-blank
brand_name) lives in the Pydantic schemas at the API boundary, matching
Business Profile's established pattern; the one genuinely interpretive
rule here — deciding that an invalid business_profile_id reference is a
client error, not a server error — is what actually lives in this
service, via _translate_integrity_error below.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_asset import BrandAsset
from app.models.enums import BrandAssetStatus
from app.repositories.brand_asset import BrandAssetRepository
from app.schemas.brand_asset import BrandAssetCreate, BrandAssetUpdate


class BrandAssetNotFoundError(Exception):
    """No brand_assets row exists for the given id."""


class InvalidReferenceError(Exception):
    """The referenced business_profile_id does not exist."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "brand_assets_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


class BrandAssetService:
    def __init__(
        self,
        session: AsyncSession,
        repository: BrandAssetRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or BrandAssetRepository(session)

    async def create(self, payload: BrandAssetCreate) -> BrandAsset:
        brand_asset = BrandAsset(**payload.model_dump())
        try:
            await self._repo.create(brand_asset)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return brand_asset

    async def get(self, brand_asset_id: uuid.UUID) -> BrandAsset:
        brand_asset = await self._repo.get_by_id(brand_asset_id)
        if brand_asset is None:
            raise BrandAssetNotFoundError(str(brand_asset_id))
        return brand_asset

    async def list(
        self,
        business_profile_id: uuid.UUID,
        *,
        status: BrandAssetStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BrandAsset], int]:
        return await self._repo.list_by_business_profile(
            business_profile_id, status=status, limit=limit, offset=offset
        )

    async def update(
        self, brand_asset_id: uuid.UUID, payload: BrandAssetUpdate
    ) -> BrandAsset:
        """PATCH: applies only the fields the caller actually supplied."""
        brand_asset = await self.get(brand_asset_id)
        data = payload.model_dump(exclude_unset=True)
        try:
            await self._repo.update(brand_asset, data)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return brand_asset

    async def delete(self, brand_asset_id: uuid.UUID) -> None:
        """Archives rather than hard-deletes. Unlike business_profiles,
        brand_assets is a leaf table — nothing else cascades off it, so a
        real DELETE would be safe at the database level. It's still the
        wrong default here: brand_story/mission/vision are exactly the
        kind of writing a founder can spend real time on, status already
        has an 'archived' value for this purpose, and there's no undo on a
        REST DELETE. Losing a draft by accident is worse than keeping an
        archived row around.
        """
        brand_asset = await self.get(brand_asset_id)
        await self._repo.archive(brand_asset)
        await self._session.commit()
