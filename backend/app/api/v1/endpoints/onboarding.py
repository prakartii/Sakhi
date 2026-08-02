"""POST /onboarding — the Business Setup wizard's single "Create my
business" call.

Thin wrapper, not a new pipeline: parses the wizard's free-text story with
app.ai.business.onboarding.parse_onboarding, generates a brand kit with
app.ai.brand.generator.generate_brand, then persists both through the
already-existing BusinessProfileService and BrandAssetService — the same
create() paths the business-profiles and brand-assets routers use directly.
No new storage logic; this endpoint only maps AI output onto those two
services' existing Create schemas.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.brand.generator import generate_brand
from app.ai.business.onboarding import parse_onboarding
from app.ai.providers import AIProviderError
from app.api.deps import get_current_app_user, get_db_session
from app.models.user import User
from app.schemas.brand_asset import BrandAssetCreate
from app.schemas.business_profile import BusinessProfileCreate
from app.schemas.onboarding import (
    BiosOut,
    OnboardingRequest,
    OnboardingResponse,
    PaletteColorOut,
)
from app.services.brand_asset import BrandAssetService
from app.services.brand_asset import InvalidReferenceError as BrandInvalidReferenceError
from app.services.business_profile import (
    BusinessProfileConflictError,
    BusinessProfileService,
)
from app.services.business_profile import InvalidReferenceError as ProfileInvalidReferenceError

router = APIRouter()


@router.post(
    "",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Parse a business story into a business profile + brand kit",
    responses={
        409: {"description": "User already has a primary business profile"},
        422: {"description": "text was empty, or the AI provider's output failed validation"},
        503: {"description": "AI provider unavailable"},
    },
)
async def create_from_story(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db_session),
) -> OnboardingResponse:
    try:
        ai_profile = await parse_onboarding(payload.text)
        brand_kit = await generate_brand(ai_profile)
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    profile_service = BusinessProfileService(db)
    products_summary = "; ".join(p.name for p in ai_profile.products) or None
    try:
        profile = await profile_service.create(
            BusinessProfileCreate(
                user_id=current_user.id,
                business_name=ai_profile.name,
                business_category=ai_profile.business_type or None,
                target_audience=ai_profile.target_audience or None,
                products_or_services=products_summary,
                business_description=payload.text,
                city=ai_profile.location or None,
            )
        )
    except BusinessProfileConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except ProfileInvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    palette_hex = [c.hex for c in brand_kit.palette]
    brand_service = BrandAssetService(db)
    try:
        brand_asset = await brand_service.create(
            BrandAssetCreate(
                business_profile_id=profile.id,
                brand_name=ai_profile.name,
                tagline=brand_kit.tagline,
                brand_story=brand_kit.brand_story,
                mission=brand_kit.mission,
                primary_color=palette_hex[0] if len(palette_hex) > 0 else None,
                secondary_color=palette_hex[1] if len(palette_hex) > 1 else None,
                typography=f"{brand_kit.typography.heading} / {brand_kit.typography.body}",
                brand_voice=brand_kit.voice.tone,
                packaging_notes="; ".join(brand_kit.packaging_ideas) or None,
            )
        )
    except BrandInvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return OnboardingResponse(
        business_profile=profile,
        brand_asset=brand_asset,
        name_suggestions=brand_kit.name_suggestions,
        palette=[
            PaletteColorOut(name=c.name, hex=c.hex, role=c.role) for c in brand_kit.palette
        ],
        bios=BiosOut(instagram=brand_kit.bios.instagram, linkedin=brand_kit.bios.linkedin),
        packaging_ideas=brand_kit.packaging_ideas,
        logo_prompt=brand_kit.logo_prompt,
    )
