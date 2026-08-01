"""Analytics narration: summarize() combines deterministic aggregation
(facts.build_facts() — entirely app.ai.forecasting, no LLM) with a single
LLM call that narrates those facts into AnalyticsSummary. The LLM never
computes a number; it only turns already-computed facts into prose, same
principle as app.ai.explanations.
"""

from __future__ import annotations

from datetime import date

from pydantic import ValidationError

from app.ai.analytics.facts import build_facts
from app.ai.analytics.models import AnalyticsSummary, MetricsRows
from app.ai.analytics.prompts import SYSTEM_PROMPT, build_user_message
from app.ai.business.models import BusinessProfile
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider


async def summarize(
    profile: BusinessProfile,
    metrics: MetricsRows,
    *,
    as_of: date | None = None,
    provider: AIProvider | None = None,
) -> AnalyticsSummary:
    """Narrate `metrics` into an AnalyticsSummary, grounded in `profile`.

    All numbers are computed by facts.build_facts() (app.ai.forecasting)
    before the model ever sees them — the model only narrates. `as_of`
    anchors stockout projections (default: today).

    Raises AIProviderResponseError if the model's output is empty, isn't
    valid JSON, or doesn't match the expected schema.
    """
    facts = build_facts(metrics, as_of=as_of)

    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(profile, facts)},
    ]

    raw = await ai.chat_json(messages, temperature=0.4)
    try:
        return AnalyticsSummary.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Analytics summary result failed schema validation: {exc}"
        ) from exc
