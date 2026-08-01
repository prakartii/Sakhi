"""Unit tests for generate_brand(). The provider is always mocked — these
verify our wiring (schema, profile-conditioning), not a live model's
creative output."""

import pytest

from app.ai.brand.generator import generate_brand
from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile, Product
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
        languages=["Hindi", "English"],
        goals=["sell online"],
        brand_voice="warm and traditional",
    )


VALID_BRAND_KIT_RESPONSE = {
    "name_suggestions": ["Jaipur Crochet Co.", "Threadwork Jaipur", "Crochet & Co."],
    "tagline": "Handwoven stories, one stitch at a time",
    "mission": "We craft handmade crochet handbags in Jaipur for buyers who value slow, "
    "traditional craftsmanship.",
    "brand_story": "Born from generations of Jaipur artisans, every bag is hand-crocheted "
    "using techniques passed down through the family.",
    "voice": {"tone": "warm, traditional, confident", "keywords": ["handmade", "heritage", "slow-crafted"]},
    "palette": [
        {"name": "Terracotta", "hex": "#C1440E", "role": "primary"},
        {"name": "Ivory", "hex": "#FFF8E7", "role": "background"},
        {"name": "Indigo", "hex": "#2C3E70", "role": "accent"},
    ],
    "typography": {"heading": "Playfair Display", "body": "Lato"},
    "bios": {
        "instagram": "Handmade crochet bags from Jaipur 🧶 Slow-crafted, one stitch at a time.",
        "linkedin": "Jaipur Crochet Co. creates handmade crochet handbags rooted in traditional "
        "craftsmanship for fashion-conscious buyers.",
    },
    "packaging_ideas": ["Hand-stamped kraft paper pouches", "Reusable cotton drawstring bags"],
    "logo_prompt": "A minimalist icon-only mark of an interlocking crochet stitch, no text, "
    "warm terracotta and indigo palette, hand-drawn feel.",
}


async def test_generate_brand_returns_valid_brand_kit() -> None:
    provider = FakeProvider(VALID_BRAND_KIT_RESPONSE)

    brand = await generate_brand(make_profile(), provider=provider)

    assert isinstance(brand, BrandKit)
    assert brand.tagline == "Handwoven stories, one stitch at a time"
    assert len(brand.palette) == 3
    assert brand.palette[0].hex == "#C1440E"
    assert brand.typography.heading == "Playfair Display"
    assert brand.logo_prompt


async def test_generate_brand_conditions_prompt_on_profile_fields() -> None:
    provider = FakeProvider(VALID_BRAND_KIT_RESPONSE)
    profile = make_profile()

    await generate_brand(profile, provider=provider)

    assert provider.last_messages is not None
    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert profile.name in prompt_text
    assert profile.target_audience in prompt_text
    assert profile.location in prompt_text
    assert profile.products[0].name in prompt_text
    assert profile.brand_voice in prompt_text


async def test_generate_brand_without_stated_brand_voice_still_prompts_for_one() -> None:
    provider = FakeProvider(VALID_BRAND_KIT_RESPONSE)
    profile = make_profile()
    profile.brand_voice = None

    await generate_brand(profile, provider=provider)

    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert "No existing brand voice stated" in prompt_text


async def test_generate_brand_raises_on_malformed_response() -> None:
    provider = FakeProvider({"tagline": "Missing everything else"})

    with pytest.raises(AIProviderResponseError):
        await generate_brand(make_profile(), provider=provider)


async def test_generate_brand_raises_on_invalid_hex_color() -> None:
    bad_response = {**VALID_BRAND_KIT_RESPONSE, "palette": [{"name": "Bad", "hex": "not-a-hex", "role": "primary"}]}
    provider = FakeProvider(bad_response)

    with pytest.raises(AIProviderResponseError):
        await generate_brand(make_profile(), provider=provider)
