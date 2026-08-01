"""Unit tests for generate_site(). The provider is always mocked — these
verify our wiring (schema, profile+brand conditioning), not a live
model's creative output."""

import pytest

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile, Product
from app.ai.providers.base import AIProvider, AIProviderResponseError, ChatMessage
from app.ai.website.generator import generate_site
from app.ai.website.models import WebsiteSpec


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
        products=[Product(name="Crochet handbags", description="Handmade crochet handbags", price=1200)],
        target_audience="fashion-conscious urban buyers",
        location="Jaipur",
        languages=["Hindi", "English"],
        goals=["sell online"],
        brand_voice="warm and traditional",
    )


def make_brand() -> BrandKit:
    return BrandKit(
        name_suggestions=["Jaipur Crochet Co."],
        tagline="Handwoven stories, one stitch at a time",
        mission="We craft handmade crochet handbags in Jaipur for buyers who value slow craftsmanship.",
        brand_story="Born from generations of Jaipur artisans, every bag is hand-crocheted.",
        voice={"tone": "warm, traditional, confident", "keywords": ["handmade", "heritage"]},
        palette=[{"name": "Terracotta", "hex": "#C1440E", "role": "primary"}],
        typography={"heading": "Playfair Display", "body": "Lato"},
        bios={"instagram": "Handmade crochet bags from Jaipur.", "linkedin": "Jaipur Crochet Co."},
        packaging_ideas=["Hand-stamped kraft paper pouches"],
        logo_prompt="A minimalist icon of an interlocking crochet stitch, no text.",
    )


VALID_SITE_RESPONSE = {
    "pages": {
        "landing": {
            "hero": {
                "headline": "Handwoven crochet bags from Jaipur",
                "subhead": "Slow-crafted heritage pieces for the modern wardrobe.",
                "cta": "Shop the collection",
            },
            "sections": [
                {"type": "story", "heading": "Rooted in Jaipur craft", "body": "Every bag is hand-crocheted."}
            ],
        },
        "about": {"body": "Jaipur Crochet Co. was born from generations of artisans."},
        "products": [
            {"name": "Crochet handbags", "description": "Handmade crochet handbags, made to order", "price": 1200}
        ],
        "contact": {"body": "Reach out — we'd love to hear from you, based in Jaipur."},
        "faq": [{"q": "Do you ship pan-India?", "a": "Yes, we ship across India."}],
    },
    "seo": {
        "title": "Jaipur Crochet Co. | Handmade Crochet Handbags",
        "description": "Handmade crochet handbags from Jaipur, crafted slowly for buyers who value heritage.",
        "keywords": ["crochet handbags", "Jaipur handmade", "handcrafted bags"],
    },
}


async def test_generate_site_returns_valid_website_spec() -> None:
    provider = FakeProvider(VALID_SITE_RESPONSE)

    site = await generate_site(make_profile(), make_brand(), provider=provider)

    assert isinstance(site, WebsiteSpec)
    assert site.pages.landing.hero.cta == "Shop the collection"
    assert len(site.pages.products) == 1
    assert site.pages.products[0].price == 1200
    assert len(site.pages.faq) == 1
    assert site.seo.title.startswith("Jaipur Crochet Co.")


async def test_generate_site_conditions_prompt_on_profile_and_brand() -> None:
    provider = FakeProvider(VALID_SITE_RESPONSE)
    profile = make_profile()
    brand = make_brand()

    await generate_site(profile, brand, provider=provider)

    assert provider.last_messages is not None
    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    # profile fields
    assert profile.name in prompt_text
    assert profile.target_audience in prompt_text
    assert profile.location in prompt_text
    assert profile.products[0].name in prompt_text
    # brand fields — proves site copy is grounded in the *same* brand kit,
    # not regenerated independently
    assert brand.tagline in prompt_text
    assert brand.mission in prompt_text
    assert brand.brand_story in prompt_text
    assert brand.voice.tone in prompt_text


async def test_generate_site_raises_on_malformed_response() -> None:
    provider = FakeProvider({"pages": {"landing": {}}})

    with pytest.raises(AIProviderResponseError):
        await generate_site(make_profile(), make_brand(), provider=provider)
