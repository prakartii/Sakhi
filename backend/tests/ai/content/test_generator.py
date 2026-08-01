"""Unit tests for generate_calendar(). The provider is always mocked —
these verify the rules+LLM wiring, not a live model's creative output."""

from datetime import date

import pytest

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile, Product
from app.ai.content.generator import generate_calendar
from app.ai.content.models import ContentPost
from app.ai.content.scheduler import schedule_month
from app.ai.providers.base import AIProvider, AIProviderResponseError, ChatMessage


class FakeProvider(AIProvider):
    def __init__(self, response: dict) -> None:
        self.response = response
        self.last_messages: list[ChatMessage] | None = None

    async def chat(
        self, messages: list[ChatMessage], *, temperature: float | None = None, max_tokens: int | None = None
    ) -> str:
        raise NotImplementedError

    async def chat_json(
        self, messages: list[ChatMessage], *, temperature: float | None = None, max_tokens: int | None = None
    ) -> dict:
        self.last_messages = messages
        return self.response


def make_profile() -> BusinessProfile:
    return BusinessProfile(
        id="profile-1",
        name="Jaipur Crochet Co.",
        business_type="handmade accessories",
        products=[Product(name="Crochet handbags", description="Handmade crochet handbags")],
        target_audience="fashion-conscious urban buyers",
        location="Jaipur",
    )


def make_brand() -> BrandKit:
    return BrandKit(
        name_suggestions=["Jaipur Crochet Co."],
        tagline="Handwoven stories, one stitch at a time",
        mission="We craft handmade crochet handbags in Jaipur.",
        brand_story="Born from generations of Jaipur artisans.",
        voice={"tone": "warm, traditional, confident", "keywords": ["handmade", "heritage"]},
        palette=[{"name": "Terracotta", "hex": "#C1440E", "role": "primary"}],
        typography={"heading": "Playfair Display", "body": "Lato"},
        bios={"instagram": "Handmade crochet bags from Jaipur.", "linkedin": "Jaipur Crochet Co."},
        packaging_ideas=["Hand-stamped kraft paper pouches"],
        logo_prompt="A minimalist icon of an interlocking crochet stitch, no text.",
    )


def _copy_for(n: int) -> dict:
    return {
        "posts": [
            {
                "caption": f"Caption {i}",
                "hashtags": ["handmade", "jaipurcraft"],
                "reel_script": None,
                "carousel_slides": None,
                "image_prompt": f"Image prompt {i}",
                "cta": "Shop now",
            }
            for i in range(n)
        ]
    }


async def test_generate_calendar_returns_one_content_post_per_slot() -> None:
    month = date(2026, 8, 1)
    platforms = ["instagram"]
    slots = schedule_month(month, platforms)
    provider = FakeProvider(_copy_for(len(slots)))

    posts = await generate_calendar(make_profile(), make_brand(), month, platforms, provider=provider)

    assert len(posts) == len(slots)
    assert all(isinstance(p, ContentPost) for p in posts)
    # Scheduling fields come straight from the (LLM-free) slots...
    assert [p.date for p in posts] == [s.date for s in slots]
    assert [p.platform for p in posts] == [s.platform for s in slots]
    assert [p.type for p in posts] == [s.type for s in slots]
    assert [p.post_time for p in posts] == [s.post_time for s in slots]
    # ...copy fields come from the model, in matching order.
    assert posts[0].caption == "Caption 0"
    assert posts[0].image_prompt == "Image prompt 0"


async def test_generate_calendar_conditions_prompt_on_profile_and_brand() -> None:
    month = date(2026, 8, 1)
    platforms = ["instagram"]
    slots = schedule_month(month, platforms)
    provider = FakeProvider(_copy_for(len(slots)))
    profile = make_profile()
    brand = make_brand()

    await generate_calendar(profile, brand, month, platforms, provider=provider)

    assert provider.last_messages is not None
    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert profile.name in prompt_text
    assert profile.products[0].name in prompt_text
    assert brand.tagline in prompt_text
    assert brand.voice.tone in prompt_text


async def test_generate_calendar_raises_when_copy_count_mismatches_slots() -> None:
    month = date(2026, 8, 1)
    platforms = ["instagram"]
    provider = FakeProvider(_copy_for(1))  # far fewer than the real slot count

    with pytest.raises(AIProviderResponseError):
        await generate_calendar(make_profile(), make_brand(), month, platforms, provider=provider)


async def test_generate_calendar_raises_on_malformed_response() -> None:
    month = date(2026, 8, 1)
    platforms = ["instagram"]
    provider = FakeProvider({"not_posts": []})

    with pytest.raises(AIProviderResponseError):
        await generate_calendar(make_profile(), make_brand(), month, platforms, provider=provider)


async def test_generate_calendar_propagates_empty_platforms_error() -> None:
    provider = FakeProvider(_copy_for(0))

    with pytest.raises(ValueError):
        await generate_calendar(make_profile(), make_brand(), date(2026, 8, 1), [], provider=provider)
