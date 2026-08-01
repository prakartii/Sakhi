"""POST /content-calendar/generate — Content AI's "Generate calendar"
action. Thin wrapper: calls app.ai.content.generator.generate_calendar()
(rule-based scheduling + one LLM call for copy) and persists every slot
through the existing ContentCalendarItemService.create() — the same path
POST /content-calendar uses directly. No new storage logic.
"""

from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.content.generator import generate_calendar
from app.ai.providers.base import AIProviderError
from app.ai.providers.groq_provider import GroqProvider
from app.api.deps import get_current_app_user, get_db_session
from app.core.config import settings
from app.models.enums import BrandAssetStatus, ContentStatus, ContentType, SocialMediaPlatform
from app.models.user import User
from app.repositories.brand_asset import BrandAssetRepository
from app.repositories.business_profile import BusinessProfileRepository
from app.schemas.content_calendar_item import ContentCalendarItemCreate
from app.schemas.content_generation import (
    ContentCalendarGenerateRequest,
    ContentCalendarGenerateResponse,
)
from app.services.ai_mapping import to_ai_brand_kit, to_ai_business_profile
from app.services.content_calendar_item import ContentCalendarItemService

router = APIRouter()

_VALID_PLATFORMS = {p.value for p in SocialMediaPlatform}


@lru_cache
def _get_calendar_provider() -> GroqProvider:
    """A month's worth of slot copy (caption + hashtags + image_prompt +
    cta, sometimes reel_script/carousel_slides too) routinely exceeds the
    app-wide AI_MAX_TOKENS=1024 default sized for single-object responses
    — Groq was silently truncating its JSON array before every slot got
    copy, which generate_calendar()'s own count check then (correctly)
    rejected. A provider instance with a larger budget, passed in via the
    existing `provider=` parameter, fixes this without changing
    generator.py itself. Built lazily (not at import time) so a missing
    GROQ_API_KEY surfaces as a 503 on this endpoint, not an app crash.
    """
    return GroqProvider(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        default_temperature=settings.AI_TEMPERATURE,
        default_max_tokens=4096,
    )


@router.post(
    "/generate",
    response_model=ContentCalendarGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a month of content calendar items (captions, hashtags, CTAs)",
    responses={
        404: {"description": "Business profile not found or not owned by the caller"},
        422: {"description": "No brand kit exists yet for this business — run onboarding first"},
        503: {"description": "AI provider unavailable"},
    },
)
async def generate_content_calendar(
    payload: ContentCalendarGenerateRequest,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContentCalendarGenerateResponse:
    profiles = BusinessProfileRepository(db)
    profile = await profiles.get_by_id(payload.business_profile_id)
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business profile not found.")

    brand_assets = BrandAssetRepository(db)
    brands, _ = await brand_assets.list_by_business_profile(
        profile.id, status=BrandAssetStatus.DRAFT, limit=1
    )
    if not brands:
        brands, _ = await brand_assets.list_by_business_profile(profile.id, limit=1)
    if not brands:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No brand kit exists for this business yet — complete onboarding first.",
        )

    platforms = [p for p in payload.platforms if p in _VALID_PLATFORMS] or ["instagram"]

    # generate_calendar() validates that the model returned copy for every
    # scheduled slot and raises if the count doesn't match — a real
    # occasional Groq under-generation on larger batches, not a bug in the
    # generator itself. One retry resolves it in practice; still surfaced
    # as 503 (the standard "try again" signal) if it fails twice.
    posts = None
    last_error: AIProviderError | None = None
    for _attempt in range(2):
        try:
            posts = await generate_calendar(
                to_ai_business_profile(profile),
                to_ai_brand_kit(brands[0]),
                payload.month,
                platforms,
                posts_per_week=payload.posts_per_week,
                provider=_get_calendar_provider(),
            )
            break
        except AIProviderError as exc:
            last_error = exc
    if posts is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(last_error)) from last_error

    service = ContentCalendarItemService(db)
    created = []
    for post in posts:
        item = await service.create(
            ContentCalendarItemCreate(
                business_profile_id=profile.id,
                title=f"{post.platform.title()} {post.type} — {post.date.isoformat()}",
                content_type=ContentType(post.type),
                platform=SocialMediaPlatform(post.platform),
                caption=post.caption,
                hashtags=post.hashtags,
                image_prompt=post.image_prompt,
                call_to_action=post.cta,
                scheduled_datetime=datetime.combine(post.date, post.post_time),
                status=ContentStatus.DRAFT,
                ai_generated=True,
            )
        )
        created.append(item)

    return ContentCalendarGenerateResponse(items=created)
