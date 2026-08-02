"""Vision analysis for Marketing Studio's thumbnail/screenshot input —
Groq's multimodal chat models accept image content alongside text in the
same chat-completions call, so this is a thin sibling to
app.ai.providers.groq_provider rather than a new provider hierarchy: one
capability (a Groq vision model), not swappable across vendors the way
AIProvider is, so it doesn't implement that interface.

Deliberately stateless and image-in/JSON-out only — nothing here persists
the image. Callers pass a base64 data URL; nothing is ever written to
disk or object storage, matching how voice audio is processed in-memory
elsewhere in this app (see app.services.voice).
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import groq

from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)
from app.core.config import settings

_RETRY_BACKOFF_SECONDS = 0.5
_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\n?|\n?```$")

_RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    groq.RateLimitError,
    groq.APIConnectionError,
    groq.InternalServerError,
)


async def analyze_image_json(
    image_data_url: str,
    prompt: str,
    *,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """Send one image + text prompt to Groq's vision model and parse the
    reply as a JSON object. `image_data_url` must be a data: URL (e.g.
    "data:image/jpeg;base64,...") — Groq also accepts https:// image URLs,
    but this app never has one to give it since nothing is uploaded to
    storage first.

    Raises AIProviderConfigError if GROQ_API_KEY is unset,
    AIProviderRequestError on a request failure (after one retry),
    AIProviderResponseError if the reply isn't valid JSON.
    """
    if not settings.GROQ_API_KEY:
        raise AIProviderConfigError(
            "GROQ_API_KEY is not set — required for Marketing Studio's image analysis."
        )

    client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY, max_retries=0)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ],
        }
    ]
    kwargs: dict[str, Any] = {
        "model": settings.GROQ_VISION_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    try:
        completion = await client.chat.completions.create(**kwargs)
    except _RETRYABLE_ERRORS:
        await asyncio.sleep(_RETRY_BACKOFF_SECONDS)
        try:
            completion = await client.chat.completions.create(**kwargs)
        except groq.APIError as retry_exc:
            raise AIProviderRequestError(
                f"Groq vision request failed after retry: {retry_exc}"
            ) from retry_exc
    except groq.APIError as exc:
        raise AIProviderRequestError(f"Groq vision request failed: {exc}") from exc

    content = completion.choices[0].message.content
    if not content:
        raise AIProviderResponseError("Groq vision returned an empty completion")

    stripped = _CODE_FENCE_RE.sub("", content.strip()).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise AIProviderResponseError(
            f"Groq vision returned invalid JSON: {content!r}"
        ) from exc
    if not isinstance(parsed, dict):
        raise AIProviderResponseError("Groq vision's JSON reply was not an object")
    return parsed
