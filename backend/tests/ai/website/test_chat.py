"""Unit tests for converse(). The provider is always mocked — these verify
our wiring (schema, profile+brand+current-site conditioning), not a live
model's creative output."""

import pytest

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile, Product
from app.ai.providers.base import AIProvider, AIProviderResponseError, ChatMessage
from app.ai.website.chat import WebsiteChatTurn, converse
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
        goals=["sell online"],
        brand_voice="warm and traditional",
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


SITE_JSON = {
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


def first_turn_response(reply: str) -> dict:
    return {"reply": reply, "site": SITE_JSON}


async def test_converse_first_turn_returns_reply_and_site() -> None:
    provider = FakeProvider(first_turn_response("Here's your first draft!"))

    turn = await converse(make_profile(), make_brand(), "Build me a site", provider=provider)

    assert isinstance(turn, WebsiteChatTurn)
    assert turn.reply == "Here's your first draft!"
    assert turn.site.pages.landing.hero.cta == "Shop the collection"


async def test_converse_first_turn_states_no_current_site_in_prompt() -> None:
    provider = FakeProvider(first_turn_response("Here's your first draft!"))

    await converse(make_profile(), make_brand(), "Build me a site", provider=provider)

    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert "none yet" in prompt_text


async def test_converse_refinement_turn_passes_current_site_json_in_prompt() -> None:
    provider = FakeProvider(first_turn_response("Updated the hero for you."))
    current_site = WebsiteSpec.model_validate(SITE_JSON)

    await converse(
        make_profile(),
        make_brand(),
        "Make the hero warmer",
        current_site=current_site,
        provider=provider,
    )

    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert "Handwoven crochet bags from Jaipur" in prompt_text  # from current_site's JSON
    assert "Make the hero warmer" in prompt_text


async def test_converse_conditions_prompt_on_profile_and_brand() -> None:
    provider = FakeProvider(first_turn_response("Here you go."))
    profile = make_profile()
    brand = make_brand()

    await converse(profile, brand, "Build me a site", provider=provider)

    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert profile.name in prompt_text
    assert profile.products[0].name in prompt_text
    assert brand.tagline in prompt_text
    assert brand.voice.tone in prompt_text


async def test_converse_rejects_empty_message() -> None:
    provider = FakeProvider(first_turn_response("irrelevant"))

    with pytest.raises(ValueError):
        await converse(make_profile(), make_brand(), "   ", provider=provider)

    assert provider.last_messages is None


async def test_converse_raises_on_malformed_response() -> None:
    provider = FakeProvider({"reply": "Here you go."})  # missing "site"

    with pytest.raises(AIProviderResponseError):
        await converse(make_profile(), make_brand(), "Build me a site", provider=provider)
