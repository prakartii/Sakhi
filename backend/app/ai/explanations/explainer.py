"""Turns already-computed facts (from the rules engine, forecasting layer,
or retrieval step) into the short "Why" / "Based on..." explanation shown
on match, alert, and insight cards across the frontend, using the
configured aiProvider's JSON mode.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.ai.explanations.prompts import SYSTEM_PROMPT, build_user_message
from app.ai.explanations.schemas import Explanation, ExplanationRequest
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider


async def explain(
    request: ExplanationRequest,
    *,
    provider: AIProvider | None = None,
) -> Explanation:
    """Generate a Why/Basis explanation grounded in `request.facts`.

    The model is instructed to cite only the given facts and never invent
    numbers or dates — callers own computing those facts (match scores,
    forecast deltas, eligibility checks); this only turns them into prose.

    Raises AIProviderResponseError if the model's output is empty, isn't
    valid JSON, or doesn't match the expected schema.
    """
    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(request)},
    ]

    raw = await ai.chat_json(messages, temperature=0.4)
    try:
        return Explanation.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Explanation result failed schema validation: {exc}"
        ) from exc
