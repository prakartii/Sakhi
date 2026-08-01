"""Brand Studio: generate_brand() turns a BusinessProfile into a complete
BrandKit (naming, voice, palette, typography, bios, logo prompt), using
the configured aiProvider's JSON mode. This is the demo centerpiece — its
output is what app.ai.image.generate_image() renders a logo from, and
what app.ai.website reuses for site copy/styling.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.ai.brand.models import BrandKit
from app.ai.brand.prompts import SYSTEM_PROMPT, build_user_message
from app.ai.business.models import BusinessProfile
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider


async def generate_brand(
    profile: BusinessProfile,
    *,
    provider: AIProvider | None = None,
) -> BrandKit:
    """Generate a full brand identity kit conditioned on `profile`.

    Raises AIProviderResponseError if the model's output is empty, isn't
    valid JSON, or doesn't match the expected schema.
    """
    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(profile)},
    ]

    # Higher temperature than extraction/explanation tasks: brand naming
    # and story benefit from more creative variance than factual parsing.
    raw = await ai.chat_json(messages, temperature=0.7)
    try:
        return BrandKit.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Brand generation result failed schema validation: {exc}"
        ) from exc
