"""Groq implementation of AIProvider — the default per Sakhi's tech stack
(Llama 3.3 on Groq for low-latency inference: voice-transcript parsing and
"Why" explanation generation).

Hardened for live failure modes: transient errors (rate limits, timeouts,
connection drops, 5xx) get exactly one retry with backoff before failing
with a clean AIProviderRequestError; malformed JSON from chat_json() gets
one corrective retry (re-asking the model) before failing with
AIProviderResponseError — callers of chat_json() never see raw/partial
JSON, only a valid dict or a typed exception.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

import groq

from app.ai.providers.base import (
    AIProvider,
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
    ChatMessage,
)

DEFAULT_RETRY_BACKOFF_SECONDS = 0.5

# Errors worth retrying once: rate limits, timeouts/connection drops, and
# 5xx — all conditions that can plausibly succeed a moment later. Anything
# else (auth, bad request, ...) is a permanent failure and retrying it
# would just waste the backoff.
_RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    groq.RateLimitError,
    groq.APIConnectionError,  # groq.APITimeoutError subclasses this
    groq.InternalServerError,
)

_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\n?|\n?```$")

SleepFn = Callable[[float], Awaitable[None]]


class GroqProvider(AIProvider):
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        default_temperature: float,
        default_max_tokens: int,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        sleep: SleepFn | None = None,
    ) -> None:
        if not api_key:
            raise AIProviderConfigError(
                "GROQ_API_KEY is not set — required when AI_PROVIDER=groq."
            )
        # max_retries=0: the SDK's own built-in retry is disabled so our
        # explicit single retry below is the only retry layer — otherwise
        # "retry once" would silently become "retry up to (2+1)^2 times".
        self._client = groq.AsyncGroq(api_key=api_key, max_retries=0)
        self._model = model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._retry_backoff_seconds = retry_backoff_seconds
        self._sleep: SleepFn = sleep or asyncio.sleep

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        completion = await self._create(messages, temperature=temperature, max_tokens=max_tokens)
        return self._content(completion)

    async def chat_json(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        completion = await self._create(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = self._content(completion)
        parsed = _try_parse_json_object(content)
        if parsed is not None:
            return parsed

        # Corrective retry: a genuinely malformed response is a content
        # problem, not a network one — ask the model to fix its own output
        # rather than blindly repeating the same request.
        corrective_messages: list[ChatMessage] = [
            *messages,
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": (
                    "That response was not a single valid JSON object. Reply again "
                    "with only valid JSON — no markdown code fences, no extra text."
                ),
            },
        ]
        retry_completion = await self._create(
            corrective_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        retry_content = self._content(retry_completion)
        parsed = _try_parse_json_object(retry_content)
        if parsed is not None:
            return parsed

        raise AIProviderResponseError(
            f"Groq returned invalid JSON even after a corrective retry: {retry_content!r}"
        )

    async def _create(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None,
        max_tokens: int | None,
        **extra: Any,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,  # type: ignore[arg-type]  # ChatMessage matches groq's expected shape
            "temperature": temperature if temperature is not None else self._default_temperature,
            "max_tokens": max_tokens if max_tokens is not None else self._default_max_tokens,
            **extra,
        }
        try:
            return await self._client.chat.completions.create(**kwargs)
        except _RETRYABLE_ERRORS:
            await self._sleep(self._retry_backoff_seconds)
            try:
                return await self._client.chat.completions.create(**kwargs)
            except groq.APIError as retry_exc:
                raise AIProviderRequestError(
                    f"Groq request failed after retry: {retry_exc}"
                ) from retry_exc
        except groq.APIError as exc:
            raise AIProviderRequestError(f"Groq request failed: {exc}") from exc

    @staticmethod
    def _content(completion: Any) -> str:
        content = completion.choices[0].message.content
        if not content:
            raise AIProviderResponseError("Groq returned an empty completion")
        return content


def _try_parse_json_object(content: str) -> dict[str, Any] | None:
    """Parse `content` as a JSON object, tolerating markdown code fences
    some models wrap JSON-mode output in despite instructions not to.
    Returns None (never raises) so callers can decide whether to retry."""
    stripped = _CODE_FENCE_RE.sub("", content.strip()).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
