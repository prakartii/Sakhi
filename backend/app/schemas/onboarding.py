"""Request/response schemas for POST /onboarding — the thin wrapper that
turns the Business Setup wizard's free-text story into a real business
profile and brand kit by calling app.ai.business.onboarding and
app.ai.brand.generator, then persisting through the existing
BusinessProfileService / BrandAssetService (no new storage logic here)."""

from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.brand_asset import BrandAssetRead
from app.schemas.business_profile import BusinessProfileRead


class OnboardingRequest(BaseModel):
    text: Annotated[
        str,
        Field(
            min_length=1,
            max_length=8000,
            description="Free-text business description — the wizard's story "
            "step plus products/customers/goals folded in as prose, or a "
            "voice transcript.",
        ),
    ]


class PaletteColorOut(BaseModel):
    name: str
    hex: str
    role: str


class BiosOut(BaseModel):
    instagram: str
    linkedin: str


class OnboardingResponse(BaseModel):
    business_profile: BusinessProfileRead
    brand_asset: BrandAssetRead
    # Generated fields BrandAsset has no column for, returned so the wizard
    # can still show them without a second AI call.
    name_suggestions: list[str]
    palette: list[PaletteColorOut]
    bios: BiosOut
    packaging_ideas: list[str]
    logo_prompt: str
