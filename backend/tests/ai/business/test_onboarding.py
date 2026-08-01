"""Unit tests for parse_onboarding(). The provider is always mocked —
these verify our extraction wiring, not a live model's output quality."""

import uuid

import pytest

from app.ai.business.models import BusinessProfile
from app.ai.business.onboarding import parse_onboarding
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


CROCHET_RESPONSE = {
    "name": "Jaipur Crochet Co.",
    "business_type": "handmade accessories",
    "products": [
        {
            "name": "Crochet handbags",
            "description": "Handmade crochet handbags",
            "price": None,
            "category": "bags",
        }
    ],
    "target_audience": "fashion-conscious urban buyers",
    "location": "Jaipur",
    "languages": ["Hindi", "English"],
    "goals": [],
    "has_website": False,
    "has_instagram": False,
    "has_logo": False,
    "brand_voice": None,
}


async def test_parse_onboarding_extracts_expected_fields() -> None:
    provider = FakeProvider(CROCHET_RESPONSE)

    profile = await parse_onboarding("I make crochet handbags in Jaipur", provider=provider)

    assert isinstance(profile, BusinessProfile)
    assert profile.name == "Jaipur Crochet Co."
    assert profile.business_type == "handmade accessories"
    assert profile.location == "Jaipur"
    assert len(profile.products) == 1
    assert profile.products[0].name == "Crochet handbags"
    assert profile.languages == ["Hindi", "English"]
    assert profile.has_website is False
    uuid.UUID(profile.id)  # a real id was generated, not left to the model


async def test_parse_onboarding_generates_unique_ids_per_call() -> None:
    provider = FakeProvider(CROCHET_RESPONSE)

    profile1 = await parse_onboarding("I make crochet handbags in Jaipur", provider=provider)
    profile2 = await parse_onboarding("I make crochet handbags in Jaipur", provider=provider)

    assert profile1.id != profile2.id


async def test_parse_onboarding_passes_transcript_into_the_prompt() -> None:
    provider = FakeProvider(CROCHET_RESPONSE)
    transcript = "I make crochet handbags in Jaipur"

    await parse_onboarding(transcript, provider=provider)

    assert provider.last_messages is not None
    assert any(transcript in m["content"] for m in provider.last_messages)


async def test_parse_onboarding_rejects_empty_input() -> None:
    provider = FakeProvider(CROCHET_RESPONSE)

    with pytest.raises(ValueError):
        await parse_onboarding("   ", provider=provider)

    assert provider.last_messages is None  # never even called the model


async def test_parse_onboarding_raises_on_malformed_response() -> None:
    provider = FakeProvider({"name": "Missing required fields"})

    with pytest.raises(AIProviderResponseError):
        await parse_onboarding("I make crochet handbags in Jaipur", provider=provider)
