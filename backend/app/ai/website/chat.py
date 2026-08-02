"""Chat-driven website curation: converse() lets a user iteratively refine
a WebsiteSpec through natural-language messages, one at a time — the
interactive flow behind Website Studio's chat. Complements generate_site()
rather than replacing it: this is for the turn-by-turn conversation loop
(first message creates, later messages edit); a caller with no interest
in chat can still call generate_site() directly for a one-shot result.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider
from app.ai.website.models import WebsiteSpec
from app.ai.website.prompts import CHAT_SYSTEM_PROMPT, build_chat_user_message


class WebsiteChatTurn(BaseModel):
    reply: str
    site: WebsiteSpec


async def converse(
    profile: BusinessProfile,
    brand: BrandKit,
    message: str,
    *,
    current_site: WebsiteSpec | None = None,
    provider: AIProvider | None = None,
) -> WebsiteChatTurn:
    """Advance a Website Studio chat by one turn.

    If `current_site` is None, this is the conversation's first turn — the
    model both creates an initial site and replies conversationally about
    it. Otherwise it edits `current_site` per `message`, changing only
    what the message asks for and returning the full updated spec (not a
    diff) alongside a short reply describing what changed.

    Raises ValueError on an empty message. Raises AIProviderResponseError
    if the model's output is empty, isn't valid JSON, or doesn't match the
    expected schema.
    """
    if not message.strip():
        raise ValueError("message must not be empty")

    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_chat_user_message(profile, brand, message, current_site),
        },
    ]

    raw = await ai.chat_json(messages, temperature=0.5)
    try:
        return WebsiteChatTurn.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Website chat result failed schema validation: {exc}"
        ) from exc
