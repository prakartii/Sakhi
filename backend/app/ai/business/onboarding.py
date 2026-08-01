"""Turns a free-text or voice-transcript business description into a
BusinessProfile — the entry point that creates Sakhi's "digital twin" of a
business. Extends app.ai.voice_parsing's pattern (chat_json + Pydantic
validation of the LLM's output) but produces the structured profile
itself, not memory candidates.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, ValidationError

from app.ai.business.models import BusinessProfile, Product
from app.ai.business.prompts import SYSTEM_PROMPT, build_user_message
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider


class _ParsedFields(BaseModel):
    """Everything the model extracts — BusinessProfile minus `id`, which
    is generated here rather than by the model (a new profile has no
    identity yet; the model shouldn't invent one)."""

    name: str
    business_type: str
    products: list[Product] = Field(default_factory=list)
    target_audience: str
    location: str
    languages: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    has_website: bool = False
    has_instagram: bool = False
    has_logo: bool = False
    brand_voice: str | None = None


async def parse_onboarding(
    text_or_transcript: str,
    *,
    provider: AIProvider | None = None,
) -> BusinessProfile:
    """Extract a BusinessProfile from a free-text/voice description of a
    business (e.g. "I make crochet handbags in Jaipur").

    Raises ValueError on empty input, and AIProviderResponseError if the
    model's output doesn't match the expected schema.
    """
    if not text_or_transcript.strip():
        raise ValueError("text_or_transcript must not be empty")

    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(text_or_transcript)},
    ]

    raw = await ai.chat_json(messages, temperature=0.2)
    try:
        parsed = _ParsedFields.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Onboarding parse result failed schema validation: {exc}"
        ) from exc

    return BusinessProfile(id=str(uuid.uuid4()), **parsed.model_dump())
