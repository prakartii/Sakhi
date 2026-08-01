"""Unit tests for handle(). The chat provider is always mocked, and the
pgvector retrieval path (already proven in
tests/ai/embeddings/test_pgvector_integration.py) is monkeypatched here
rather than re-exercised against a real database — these tests verify the
orchestrator's own wiring (routing, fact assembly, response shape), not
retrieve()'s correctness."""

from datetime import date

import pytest

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile
from app.ai.analytics.models import MetricsRows, ProductSales
from app.ai.embeddings.schemas import RetrievedMemory
from app.ai.orchestrator.models import OrchestratorContext, OrchestratorResponse
from app.ai.orchestrator.orchestrator import handle
from app.ai.providers.base import AIProvider, AIProviderResponseError, ChatMessage
from app.ai.forecasting.schemas import RunRatePoint


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


VALID_ANSWER_RESPONSE = {"answer": "Here's what your business is doing right now."}


def make_profile() -> BusinessProfile:
    return BusinessProfile(
        id="profile-1",
        name="Jaipur Crochet Co.",
        business_type="handmade accessories",
        target_audience="fashion-conscious urban buyers",
        location="Jaipur",
        goals=["sell online"],
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


async def test_handle_returns_valid_response_with_no_context_or_session() -> None:
    provider = FakeProvider(VALID_ANSWER_RESPONSE)

    result = await handle("How is my business doing?", make_profile(), provider=provider)

    assert isinstance(result, OrchestratorResponse)
    assert result.answer
    assert result.used_services == ["analytics"]  # router's default
    assert result.sources == []


async def test_handle_rejects_empty_request() -> None:
    provider = FakeProvider(VALID_ANSWER_RESPONSE)

    with pytest.raises(ValueError):
        await handle("   ", make_profile(), provider=provider)


async def test_used_services_come_from_the_router_not_the_model() -> None:
    provider = FakeProvider(VALID_ANSWER_RESPONSE)

    result = await handle("I need more sales", make_profile(), provider=provider)

    assert result.used_services == ["analytics", "content", "brand"]


async def test_brand_facts_reach_the_prompt_when_brand_is_relevant() -> None:
    provider = FakeProvider(VALID_ANSWER_RESPONSE)
    brand = make_brand()
    context = OrchestratorContext(brand=brand)

    await handle("I want a new logo", make_profile(), context, provider=provider)

    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert brand.tagline in prompt_text
    assert brand.mission in prompt_text
    assert brand.voice.tone in prompt_text


async def test_brand_facts_are_skipped_when_brand_is_not_relevant() -> None:
    provider = FakeProvider(VALID_ANSWER_RESPONSE)
    brand = make_brand()
    context = OrchestratorContext(brand=brand)

    await handle("how is my revenue doing", make_profile(), context, provider=provider)

    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert brand.tagline not in prompt_text


async def test_analytics_facts_reach_the_prompt_when_analytics_is_relevant() -> None:
    provider = FakeProvider(VALID_ANSWER_RESPONSE)
    metrics = MetricsRows(
        revenue_by_period=[
            RunRatePoint(period_start=date(2026, m, 1), value=v)
            for m, v in zip(range(2, 8), [12000, 14500, 17000, 19500, 21340, 24000])
        ],
        top_products=[ProductSales(name="Crochet handbags", units_sold=40, revenue=48000)],
    )
    context = OrchestratorContext(metrics=metrics)

    await handle("how is my revenue doing", make_profile(), context, provider=provider)

    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert "rising" in prompt_text
    assert "Crochet handbags" in prompt_text


async def test_retrieved_memory_populates_sources_and_facts(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeProvider(VALID_ANSWER_RESPONSE)

    async def fake_retrieve(session, query, *, k=3, business_profile_id=None, provider=None):
        return [
            RetrievedMemory(
                business_memory_id="mem-1",
                title="Price change",
                content="Raised dupatta price from Rs 640 to Rs 820.",
                chunk_index=0,
                chunk_text="Raised dupatta price from Rs 640 to Rs 820.",
                similarity=0.92,
            )
        ]

    monkeypatch.setattr("app.ai.orchestrator.orchestrator.retrieve", fake_retrieve)

    result = await handle(
        "how is my revenue doing",
        make_profile(),
        session=object(),  # never touched — retrieve() itself is mocked out
        provider=provider,
    )

    assert result.sources == ["Raised dupatta price from Rs 640 to Rs 820."]
    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert "Raised dupatta price from Rs 640 to Rs 820." in prompt_text


async def test_no_session_means_no_retrieval_attempted(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeProvider(VALID_ANSWER_RESPONSE)
    called = False

    async def fake_retrieve(*args, **kwargs):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr("app.ai.orchestrator.orchestrator.retrieve", fake_retrieve)

    result = await handle("how is my revenue doing", make_profile(), provider=provider)

    assert called is False
    assert result.sources == []


async def test_handle_raises_on_malformed_response() -> None:
    provider = FakeProvider({"not_answer": "oops"})

    with pytest.raises(AIProviderResponseError):
        await handle("how is my revenue doing", make_profile(), provider=provider)
