"""Website Studio: generate_site() turns a BusinessProfile + BrandKit into
a full structured WebsiteSpec (landing page, about, products, contact,
FAQ, SEO) the frontend renders directly, using the configured aiProvider's
JSON mode.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider
from app.ai.website.models import WebsiteSpec
from app.ai.website.prompts import SYSTEM_PROMPT, build_user_message


async def generate_site(
    profile: BusinessProfile,
    brand: BrandKit,
    *,
    provider: AIProvider | None = None,
) -> WebsiteSpec:
    """Generate a full one-page website spec conditioned on both `profile`
    and its already-generated `brand` — copy reuses the brand's tagline,
    mission, story, and voice rather than reinventing them.

    Raises AIProviderResponseError if the model's output is empty, isn't
    valid JSON, or doesn't match the expected schema.
    """
    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(profile, brand)},
    ]

    raw = await ai.chat_json(messages, temperature=0.5)
    try:
        return WebsiteSpec.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Website generation result failed schema validation: {exc}"
        ) from exc
