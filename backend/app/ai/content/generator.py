"""Content Calendar: generate_calendar() combines rule-based scheduling
(scheduler.py — dates, platforms, post types, times, festival mix; no
LLM) with a single LLM call that writes copy for every slot at once
(caption, hashtags, reel_script/carousel_slides, image_prompt, cta).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, ValidationError

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile
from app.ai.content.models import ContentPost
from app.ai.content.prompts import SYSTEM_PROMPT, build_user_message
from app.ai.content.scheduler import DEFAULT_POSTS_PER_WEEK, schedule_month
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider


class _SlotCopy(BaseModel):
    caption: str
    hashtags: list[str] = Field(default_factory=list)
    reel_script: str | None = None
    carousel_slides: list[str] | None = None
    image_prompt: str
    cta: str


class _CalendarCopyResponse(BaseModel):
    posts: list[_SlotCopy]


async def generate_calendar(
    profile: BusinessProfile,
    brand: BrandKit,
    month: date,
    platforms: list[str],
    *,
    posts_per_week: int = DEFAULT_POSTS_PER_WEEK,
    provider: AIProvider | None = None,
) -> list[ContentPost]:
    """Generate a full month's content calendar for `platforms`.

    Scheduling (which dates, which platform, which post type, what time,
    festival mix) is entirely rule-based via scheduler.schedule_month() —
    deterministic and LLM-free. A single chat_json() call then writes copy
    for every slot at once, in the brand's voice.

    Raises ValueError if `platforms` is empty (propagated from
    schedule_month). Raises AIProviderResponseError if the model's output
    doesn't match the expected schema or doesn't return copy for every
    slot.
    """
    slots = schedule_month(month, platforms, posts_per_week=posts_per_week)
    if not slots:
        return []

    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(profile, brand, slots)},
    ]

    raw = await ai.chat_json(messages, temperature=0.6)
    try:
        parsed = _CalendarCopyResponse.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Content calendar result failed schema validation: {exc}"
        ) from exc

    if len(parsed.posts) != len(slots):
        raise AIProviderResponseError(
            f"Expected copy for {len(slots)} slot(s), got {len(parsed.posts)}"
        )

    return [
        ContentPost(
            date=slot.date,
            platform=slot.platform,
            type=slot.type,
            post_time=slot.post_time,
            caption=copy.caption,
            hashtags=copy.hashtags,
            reel_script=copy.reel_script,
            carousel_slides=copy.carousel_slides,
            image_prompt=copy.image_prompt,
            cta=copy.cta,
        )
        for slot, copy in zip(slots, parsed.posts, strict=True)
    ]
