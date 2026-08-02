"""Brand Assets CRUD endpoints.

Storage only: brand_name, tagline, brand_story, mission, vision, colors,
typography, logo/favicon links, brand voice, packaging notes — with one
exception: POST /{brand_asset_id}/generate-logo, which calls
app.ai.image.generate_image (kind="logo") to produce an AI-recommended
logo image and saves its URL. Every other endpoint in this module stays
storage-only, reading and writing branding data a caller provides.

No authentication yet: business_profile_id is supplied explicitly by the
caller (request body on create, required query param on list) instead of
being derived from a session — the same deliberate, temporary gap already
documented on the Business Profile endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.image import generate_image
from app.ai.providers.base import AIProviderError
from app.api.deps import get_db_session
from app.models.enums import BrandAssetStatus
from app.schemas.brand_asset import (
    BrandAssetCreate,
    BrandAssetListResponse,
    BrandAssetRead,
    BrandAssetUpdate,
)
from app.services.brand_asset import (
    BrandAssetNotFoundError,
    BrandAssetService,
    InvalidReferenceError,
)

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> BrandAssetService:
    return BrandAssetService(db)


@router.post(
    "",
    response_model=BrandAssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a brand asset",
    responses={
        422: {
            "description": "Validation failed, or business_profile_id does not exist"
        },
    },
)
async def create_brand_asset(
    payload: BrandAssetCreate,
    service: BrandAssetService = Depends(get_service),
) -> BrandAssetRead:
    """Create a brand identity record for a business. `status` defaults to
    `draft`; a business may have multiple brand_assets rows (drafts,
    successive rebrands) — nothing here enforces only one `active` row."""
    try:
        return await service.create(payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "",
    response_model=BrandAssetListResponse,
    summary="List a business's brand assets",
)
async def list_brand_assets(
    business_profile_id: uuid.UUID = Query(
        ...,
        description="Owning business id (temporary — replaced by session-derived "
        "scoping once auth exists).",
    ),
    status_filter: BrandAssetStatus | None = Query(
        None, alias="status", description="Filter by lifecycle status."
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BrandAssetService = Depends(get_service),
) -> BrandAssetListResponse:
    """List brand assets owned by a given business, newest first."""
    items, total = await service.list(
        business_profile_id, status=status_filter, limit=limit, offset=offset
    )
    return BrandAssetListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{brand_asset_id}",
    response_model=BrandAssetRead,
    summary="Get a brand asset by id",
    responses={404: {"description": "Brand asset not found"}},
)
async def get_brand_asset(
    brand_asset_id: uuid.UUID,
    service: BrandAssetService = Depends(get_service),
) -> BrandAssetRead:
    try:
        return await service.get(brand_asset_id)
    except BrandAssetNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Brand asset not found."
        ) from exc


@router.patch(
    "/{brand_asset_id}",
    response_model=BrandAssetRead,
    summary="Partially update a brand asset",
    responses={
        404: {"description": "Brand asset not found"},
        422: {"description": "Validation failed"},
    },
)
async def update_brand_asset(
    brand_asset_id: uuid.UUID,
    payload: BrandAssetUpdate,
    service: BrandAssetService = Depends(get_service),
) -> BrandAssetRead:
    """Update only the fields present in the request body; omitted fields
    are left unchanged."""
    try:
        return await service.update(brand_asset_id, payload)
    except BrandAssetNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Brand asset not found."
        ) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.post(
    "/{brand_asset_id}/generate-logo",
    response_model=BrandAssetRead,
    summary="AI-recommend a logo for this brand and save it",
    responses={
        404: {"description": "Brand asset not found"},
        503: {"description": "Image provider unavailable"},
    },
)
async def generate_logo(
    brand_asset_id: uuid.UUID,
    service: BrandAssetService = Depends(get_service),
) -> BrandAssetRead:
    """Generates one logo concept (app.ai.image, kind="logo" — a flat
    vector mark, no text, per that kind's style hint) from this brand's own
    name/tagline/voice/palette, and saves it as logo_url. Calling this
    again replaces the previous logo_url with a fresh concept; nothing
    here keeps a history of past attempts."""
    try:
        brand_asset = await service.get(brand_asset_id)
    except BrandAssetNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand asset not found.") from exc

    prompt = (
        f"A logo mark for '{brand_asset.brand_name}'"
        + (f", tagline '{brand_asset.tagline}'" if brand_asset.tagline else "")
        + f". Brand personality: {brand_asset.brand_voice or 'warm and approachable'}."
        + (f" Primary color: {brand_asset.primary_color}." if brand_asset.primary_color else "")
    )
    try:
        image = await generate_image(prompt, "logo", "square")
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return await service.update(
        brand_asset_id, BrandAssetUpdate(brand_name=brand_asset.brand_name, logo_url=image.url)
    )


@router.delete(
    "/{brand_asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a brand asset",
    responses={404: {"description": "Brand asset not found"}},
)
async def delete_brand_asset(
    brand_asset_id: uuid.UUID,
    service: BrandAssetService = Depends(get_service),
) -> None:
    """Sets status to 'archived' rather than deleting the row — see
    BrandAssetService.delete for why."""
    try:
        await service.delete(brand_asset_id)
    except BrandAssetNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Brand asset not found."
        ) from exc
