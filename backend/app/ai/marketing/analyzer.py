"""Marketing Studio: analyze_content() explains why a piece of already-
posted content performed the way it did; generate_reel_brief() plans a new
one. Both are a single chat_json() call each — engagement_rate is the only
number computed in code rather than asked of the model (see
_engagement_rate), same "the model narrates, code computes" principle as
app.ai.analytics.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile
from app.ai.marketing.models import ContentAnalysis, ContentMetrics, ReelBrief
from app.ai.marketing.prompts import (
    ANALYZE_SYSTEM_PROMPT,
    REEL_BRIEF_SYSTEM_PROMPT,
    VISION_DESCRIBE_PROMPT,
    build_analyze_user_message,
    build_reel_brief_user_message,
)
from app.ai.marketing.vision import analyze_image_json
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider


def engagement_rate(metrics: ContentMetrics) -> float | None:
    """(likes + comments + shares + saves) / views * 100, or None if views
    isn't reported — never divides by an assumed number."""
    if not metrics.views:
        return None
    interactions = sum(
        v for v in (metrics.likes, metrics.comments, metrics.shares, metrics.saves) if v
    )
    return round((interactions / metrics.views) * 100, 2)


async def describe_thumbnail(image_data_url: str) -> str:
    """A short factual description of an uploaded thumbnail/screenshot,
    via Groq's vision model — feeds analyze_content() as text context
    rather than being re-sent as an image on every subsequent call.

    Raises AIProviderError subclasses (see app.ai.marketing.vision) on
    failure — callers should treat this as best-effort and degrade
    gracefully (thumbnail_analysis stays null) rather than fail the whole
    analysis over a vision hiccup.
    """
    raw = await analyze_image_json(image_data_url, VISION_DESCRIBE_PROMPT, max_tokens=300)
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        raise AIProviderResponseError("Groq vision did not return a usable description")
    return description.strip()


async def analyze_content(
    profile: BusinessProfile,
    brand: BrandKit,
    *,
    caption: str | None,
    hashtags: list[str],
    metrics: ContentMetrics,
    comments_sample: list[str],
    thumbnail_description: str | None = None,
    provider: AIProvider | None = None,
) -> ContentAnalysis:
    """Analyze one piece of already-posted content. Raises
    AIProviderResponseError if the model's output doesn't match
    ContentAnalysis's schema."""
    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_analyze_user_message(
                profile,
                brand,
                caption=caption,
                hashtags=hashtags,
                metrics=metrics,
                comments_sample=comments_sample,
                thumbnail_description=thumbnail_description,
                engagement_rate=engagement_rate(metrics),
            ),
        },
    ]

    raw = await ai.chat_json(messages, temperature=0.4, max_tokens=2048)
    try:
        return ContentAnalysis.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Content analysis result failed schema validation: {exc}"
        ) from exc


async def generate_reel_brief(
    profile: BusinessProfile,
    brand: BrandKit,
    *,
    angle: str | None = None,
    past_learnings: list[str] | None = None,
    provider: AIProvider | None = None,
) -> ReelBrief:
    """Plan one new reel (script/shot list/caption/hashtags/CTA) — a
    shootable brief, not a rendered video; this app has no video-generation
    capability. `past_learnings` are short facts pulled from this
    business's own Marketing Studio history, if any, so the idea builds on
    what's actually worked before."""
    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": REEL_BRIEF_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_reel_brief_user_message(
                profile, brand, angle=angle, past_learnings=past_learnings or []
            ),
        },
    ]

    raw = await ai.chat_json(messages, temperature=0.6, max_tokens=1536)
    try:
        return ReelBrief.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Reel brief result failed schema validation: {exc}"
        ) from exc
