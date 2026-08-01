"""Unit tests for GroqProvider. The network call itself is always mocked —
these verify our wrapping logic (JSON parsing, empty-content, error
translation), not Groq's API."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import groq
import pytest

from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)
from app.ai.providers.groq_provider import GroqProvider


class _FakeAPIError(groq.APIError):
    """groq.APIError's real __init__ requires SDK-internal request/body
    objects we don't have in a unit test; bypass it while staying an
    instance of the type GroqProvider's except clause catches."""

    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


class _FakeRateLimitError(groq.RateLimitError):
    """Same bypass as _FakeAPIError, for the retryable-error branch."""

    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


def make_provider(*, sleep: AsyncMock | None = None) -> GroqProvider:
    return GroqProvider(
        api_key="test-key",
        model="llama-3.3-70b-versatile",
        default_temperature=0.3,
        default_max_tokens=1024,
        retry_backoff_seconds=0.01,
        sleep=sleep or AsyncMock(),
    )


def fake_completion(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_missing_api_key_raises_config_error() -> None:
    with pytest.raises(AIProviderConfigError):
        GroqProvider(api_key=None, model="m", default_temperature=0.3, default_max_tokens=1024)


async def test_chat_returns_message_content() -> None:
    provider = make_provider()
    provider._client.chat.completions.create = AsyncMock(return_value=fake_completion("hello"))

    result = await provider.chat([{"role": "user", "content": "hi"}])

    assert result == "hello"


async def test_chat_json_parses_content_and_requests_json_mode() -> None:
    provider = make_provider()
    create = AsyncMock(return_value=fake_completion(json.dumps({"amount": 500})))
    provider._client.chat.completions.create = create

    result = await provider.chat_json([{"role": "user", "content": "hi, respond in JSON"}])

    assert result == {"amount": 500}
    assert create.call_args.kwargs["response_format"] == {"type": "json_object"}


async def test_chat_json_raises_on_invalid_json() -> None:
    provider = make_provider()
    provider._client.chat.completions.create = AsyncMock(return_value=fake_completion("not json"))

    with pytest.raises(AIProviderResponseError):
        await provider.chat_json([{"role": "user", "content": "hi"}])


async def test_chat_raises_on_empty_content() -> None:
    provider = make_provider()
    provider._client.chat.completions.create = AsyncMock(return_value=fake_completion(None))

    with pytest.raises(AIProviderResponseError):
        await provider.chat([{"role": "user", "content": "hi"}])


async def test_chat_wraps_api_errors() -> None:
    provider = make_provider()
    provider._client.chat.completions.create = AsyncMock(
        side_effect=_FakeAPIError("boom")
    )

    with pytest.raises(AIProviderRequestError):
        await provider.chat([{"role": "user", "content": "hi"}])


async def test_default_temperature_and_max_tokens_are_used() -> None:
    provider = make_provider()
    create = AsyncMock(return_value=fake_completion("hello"))
    provider._client.chat.completions.create = create

    await provider.chat([{"role": "user", "content": "hi"}])

    assert create.call_args.kwargs["temperature"] == 0.3
    assert create.call_args.kwargs["max_tokens"] == 1024


async def test_explicit_temperature_and_max_tokens_override_defaults() -> None:
    provider = make_provider()
    create = AsyncMock(return_value=fake_completion("hello"))
    provider._client.chat.completions.create = create

    await provider.chat([{"role": "user", "content": "hi"}], temperature=0.9, max_tokens=50)

    assert create.call_args.kwargs["temperature"] == 0.9
    assert create.call_args.kwargs["max_tokens"] == 50


def test_client_disables_sdk_own_retries() -> None:
    # Our explicit single retry is the only retry layer — otherwise "retry
    # once" would silently compound with the SDK's own retry-on-failure.
    provider = make_provider()

    assert provider._client.max_retries == 0


# --- Transient-error retry (rate limits, timeouts, connection drops, 5xx) ---


async def test_transient_error_retries_once_then_succeeds() -> None:
    sleep = AsyncMock()
    provider = make_provider(sleep=sleep)
    create = AsyncMock(side_effect=[_FakeRateLimitError("rate limited"), fake_completion("hello")])
    provider._client.chat.completions.create = create

    result = await provider.chat([{"role": "user", "content": "hi"}])

    assert result == "hello"
    assert create.call_count == 2
    sleep.assert_awaited_once()


async def test_transient_error_raises_clean_error_if_retry_also_fails() -> None:
    sleep = AsyncMock()
    provider = make_provider(sleep=sleep)
    create = AsyncMock(side_effect=[_FakeRateLimitError("first"), _FakeAPIError("second")])
    provider._client.chat.completions.create = create

    with pytest.raises(AIProviderRequestError):
        await provider.chat([{"role": "user", "content": "hi"}])

    assert create.call_count == 2
    sleep.assert_awaited_once()


async def test_non_retryable_error_fails_immediately_without_sleeping() -> None:
    sleep = AsyncMock()
    provider = make_provider(sleep=sleep)
    create = AsyncMock(side_effect=_FakeAPIError("bad request"))
    provider._client.chat.completions.create = create

    with pytest.raises(AIProviderRequestError):
        await provider.chat([{"role": "user", "content": "hi"}])

    assert create.call_count == 1
    sleep.assert_not_awaited()


# --- chat_json() corrective retry (guarantees callers get a parsed dict) ---


async def test_chat_json_strips_markdown_code_fences() -> None:
    provider = make_provider()
    fenced = '```json\n{"amount": 42}\n```'
    provider._client.chat.completions.create = AsyncMock(return_value=fake_completion(fenced))

    result = await provider.chat_json([{"role": "user", "content": "hi"}])

    assert result == {"amount": 42}


async def test_chat_json_recovers_after_corrective_retry() -> None:
    provider = make_provider()
    create = AsyncMock(
        side_effect=[
            fake_completion("not json at all"),
            fake_completion(json.dumps({"ok": True})),
        ]
    )
    provider._client.chat.completions.create = create

    result = await provider.chat_json([{"role": "user", "content": "hi, respond in JSON"}])

    assert result == {"ok": True}
    assert create.call_count == 2
    second_call_messages = create.call_args_list[1].kwargs["messages"]
    assert second_call_messages[-1]["role"] == "user"
    assert "valid JSON" in second_call_messages[-1]["content"]
    assert create.call_args_list[1].kwargs["response_format"] == {"type": "json_object"}


async def test_chat_json_raises_after_corrective_retry_also_fails() -> None:
    provider = make_provider()
    create = AsyncMock(return_value=fake_completion("still not json"))
    provider._client.chat.completions.create = create

    with pytest.raises(AIProviderResponseError):
        await provider.chat_json([{"role": "user", "content": "hi"}])

    assert create.call_count == 2
