"""Unit tests for summarize(). The provider is always mocked — these
verify the facts+LLM wiring, not a live model's narration quality."""

from datetime import date, timedelta

import pytest

from app.ai.analytics.models import (
    AnalyticsSummary,
    InventoryUsage,
    MetricsRows,
    ProductSales,
)
from app.ai.analytics.summarizer import summarize
from app.ai.business.models import BusinessProfile
from app.ai.forecasting.schemas import RunRatePoint, UsagePoint
from app.ai.providers.base import AIProvider, AIProviderResponseError, ChatMessage

TODAY = date(2026, 8, 1)


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
        target_audience="fashion-conscious urban buyers",
        location="Jaipur",
        goals=["sell online"],
    )


VALID_SUMMARY_RESPONSE = {
    "narrative": "Your revenue is climbing steadily and crochet handbags are your best seller.",
    "highlights": ["Revenue up month over month", "Crochet handbags lead sales"],
    "top_actions": [
        {"action": "Restock crochet handbag materials", "why": "It's your top-selling product."}
    ],
}


async def test_summarize_returns_valid_summary() -> None:
    metrics = MetricsRows(
        revenue_by_period=[
            RunRatePoint(period_start=date(2026, m, 1), value=v)
            for m, v in zip(range(2, 8), [12000, 14500, 17000, 19500, 21340, 24000])
        ]
    )
    provider = FakeProvider(VALID_SUMMARY_RESPONSE)

    summary = await summarize(make_profile(), metrics, provider=provider)

    assert isinstance(summary, AnalyticsSummary)
    assert summary.narrative
    assert len(summary.top_actions) == 1


async def test_summarize_conditions_prompt_on_profile_and_computed_facts() -> None:
    metrics = MetricsRows(
        revenue_by_period=[
            RunRatePoint(period_start=date(2026, m, 1), value=v)
            for m, v in zip(range(2, 8), [12000, 14500, 17000, 19500, 21340, 24000])
        ],
        top_products=[ProductSales(name="Crochet handbags", units_sold=40, revenue=48000)],
    )
    provider = FakeProvider(VALID_SUMMARY_RESPONSE)
    profile = make_profile()

    await summarize(profile, metrics, provider=provider)

    assert provider.last_messages is not None
    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    # profile fields
    assert profile.name in prompt_text
    assert profile.goals[0] in prompt_text
    # computed facts — proves the numbers came from app.ai.forecasting,
    # not that the model was left to guess them
    assert "rising" in prompt_text
    assert "Crochet handbags" in prompt_text


async def test_summarize_handles_empty_metrics_without_crashing() -> None:
    provider = FakeProvider(VALID_SUMMARY_RESPONSE)

    summary = await summarize(make_profile(), MetricsRows(), provider=provider)

    assert isinstance(summary, AnalyticsSummary)
    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert "No metrics data is available yet." in prompt_text


async def test_summarize_uses_as_of_for_stockout_facts() -> None:
    usage = [UsagePoint(movement_date=TODAY - timedelta(days=i), quantity=5.0) for i in range(14)]
    metrics = MetricsRows(
        inventory_usage=[InventoryUsage(item_name="Indigo dye", current_quantity=20, usage=usage)]
    )
    provider = FakeProvider(VALID_SUMMARY_RESPONSE)

    await summarize(make_profile(), metrics, as_of=TODAY, provider=provider)

    prompt_text = " ".join(m["content"] for m in provider.last_messages)
    assert "Indigo dye" in prompt_text
    assert "projected to run out on" in prompt_text


async def test_summarize_raises_on_malformed_response() -> None:
    provider = FakeProvider({"narrative": 123})  # wrong type

    with pytest.raises(AIProviderResponseError):
        await summarize(make_profile(), MetricsRows(), provider=provider)
