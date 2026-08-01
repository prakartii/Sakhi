"""Unit tests for TogetherImageProvider. The network call is always
mocked — these verify our wrapping logic, not Together's API."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import together
import pytest

from app.ai.image.together_provider import TogetherImageProvider
from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)


class _FakeAPIError(together.APIError):
    """together.APIError's real __init__ requires SDK-internal request/
    body objects we don't have in a unit test; bypass it while staying an
    instance of the type the provider's except clause catches."""

    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


def make_provider() -> TogetherImageProvider:
    return TogetherImageProvider(api_key="test-key", model="black-forest-labs/FLUX.1-schnell-Free")


def fake_response(url: str) -> SimpleNamespace:
    return SimpleNamespace(data=[SimpleNamespace(url=url)])


def fake_empty_response() -> SimpleNamespace:
    return SimpleNamespace(data=[])


def test_missing_api_key_raises_config_error() -> None:
    with pytest.raises(AIProviderConfigError):
        TogetherImageProvider(api_key=None, model="m")


def test_name_reflects_provider_and_model() -> None:
    provider = make_provider()

    assert provider.name == "together:black-forest-labs/FLUX.1-schnell-Free"


async def test_generate_returns_url() -> None:
    provider = make_provider()
    provider._client.images.generate = AsyncMock(
        return_value=fake_response("https://example.com/img.png")
    )

    url = await provider.generate("a logo", width=1024, height=1024)

    assert url == "https://example.com/img.png"


async def test_generate_passes_prompt_dimensions_and_model() -> None:
    provider = make_provider()
    create = AsyncMock(return_value=fake_response("https://example.com/img.png"))
    provider._client.images.generate = create

    await provider.generate("a logo", width=768, height=1024)

    assert create.call_args.kwargs["prompt"] == "a logo"
    assert create.call_args.kwargs["width"] == 768
    assert create.call_args.kwargs["height"] == 1024
    assert create.call_args.kwargs["response_format"] == "url"
    assert create.call_args.kwargs["model"] == "black-forest-labs/FLUX.1-schnell-Free"


async def test_generate_raises_on_empty_data() -> None:
    provider = make_provider()
    provider._client.images.generate = AsyncMock(return_value=fake_empty_response())

    with pytest.raises(AIProviderResponseError):
        await provider.generate("a logo", width=1024, height=1024)


async def test_generate_raises_on_blank_url() -> None:
    provider = make_provider()
    provider._client.images.generate = AsyncMock(return_value=fake_response(""))

    with pytest.raises(AIProviderResponseError):
        await provider.generate("a logo", width=1024, height=1024)


async def test_generate_wraps_api_errors() -> None:
    provider = make_provider()
    provider._client.images.generate = AsyncMock(side_effect=_FakeAPIError("boom"))

    with pytest.raises(AIProviderRequestError):
        await provider.generate("a logo", width=1024, height=1024)
