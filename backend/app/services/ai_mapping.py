"""Maps this app's ORM rows onto app.ai's own Pydantic input types.

app.ai.business.models.BusinessProfile (and BrandKit) are the AI layer's
input contract, deliberately separate from app.models.business_profile.
BusinessProfile (the storage shape) — see the integration plan's AI module
audit. Every service that calls into app.ai needs this same translation, so
it lives here once instead of being copy-pasted per caller.
"""

from __future__ import annotations

from app.ai.brand.models import Bios, BrandKit, PaletteColor, Typography, VoiceGuide
from app.ai.business.models import BusinessProfile as AIBusinessProfile
from app.models.brand_asset import BrandAsset
from app.models.business_profile import BusinessProfile


def to_ai_business_profile(profile: BusinessProfile) -> AIBusinessProfile:
    return AIBusinessProfile(
        id=str(profile.id),
        name=profile.business_name,
        business_type=profile.business_category or "general",
        target_audience=profile.target_audience or "general customers",
        location=profile.city or profile.country,
        goals=[],
        has_website=bool(profile.website_url),
        has_instagram=bool(profile.instagram_url),
        has_logo=bool(profile.logo_url),
        brand_voice=None,
    )


def to_ai_brand_kit(brand: BrandAsset) -> BrandKit:
    """Best-effort reconstruction of a BrandKit from a stored BrandAsset row.

    brand_assets only persists a subset of what BrandKit carries (no
    structured palette roles, bios, or logo prompt — see the integration
    plan's risk notes), so fields the schema has no column for are filled
    with the closest reasonable default rather than invented content.
    """
    heading, _, body = (brand.typography or "").partition(" / ")
    palette = []
    if brand.primary_color:
        palette.append(PaletteColor(name="Primary", hex=brand.primary_color, role="primary"))
    if brand.secondary_color:
        palette.append(PaletteColor(name="Secondary", hex=brand.secondary_color, role="accent"))
    if not palette:
        palette.append(PaletteColor(name="Primary", hex="#8F2F56", role="primary"))

    return BrandKit(
        name_suggestions=[brand.brand_name],
        tagline=brand.tagline or "",
        mission=brand.mission or "",
        brand_story=brand.brand_story or "",
        voice=VoiceGuide(tone=brand.brand_voice or "warm", keywords=[]),
        palette=palette,
        typography=Typography(heading=heading or "Poppins", body=body or "Inter"),
        bios=Bios(instagram="", linkedin=""),
        packaging_ideas=[p.strip() for p in (brand.packaging_notes or "").split(";") if p.strip()],
        logo_prompt=f"A logo for {brand.brand_name}, {brand.brand_voice or 'warm'} in tone.",
    )
