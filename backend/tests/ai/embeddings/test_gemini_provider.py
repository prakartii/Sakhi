"""Unit tests for GeminiEmbeddingProvider. The network call is always
mocked — these verify our wrapping logic, not Gemini's API."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from google.genai import errors as genai_errors

from app.ai.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)


class _FakeAPIError(genai_errors.APIError):
    """genai.errors.APIError's real __init__ requires SDK-internal
    response objects we don't have in a unit test; bypass it while staying
    an instance of the type the provider's except clause catches."""

    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


def make_provider() -> GeminiEmbeddingProvider:
    return GeminiEmbeddingProvider(
        api_key="test-key", model="gemini-embedding-001", dimensions=1536
    )


def fake_response(embeddings: list[list[float]]) -> SimpleNamespace:
    return SimpleNamespace(embeddings=[SimpleNamespace(values=vector) for vector in embeddings])


def test_missing_api_key_raises_config_error() -> None:
    with pytest.raises(AIProviderConfigError):
        GeminiEmbeddingProvider(api_key=None, model="gemini-embedding-001", dimensions=1536)


def test_model_name_and_dimensions_exposed() -> None:
    provider = make_provider()

    assert provider.model_name == "gemini-embedding-001"
    assert provider.dimensions == 1536


async def test_embed_empty_list_returns_empty_without_a_call() -> None:
    provider = make_provider()
    provider._client.aio.models.embed_content = AsyncMock()

    result = await provider.embed([])

    assert result == []
    provider._client.aio.models.embed_content.assert_not_called()


async def test_embed_returns_vectors_in_order() -> None:
    provider = make_provider()
    provider._client.aio.models.embed_content = AsyncMock(
        return_value=fake_response([[0.1, 0.2], [0.3, 0.4]])
    )

    result = await provider.embed(["first", "second"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]


async def test_embed_raises_on_count_mismatch() -> None:
    provider = make_provider()
    provider._client.aio.models.embed_content = AsyncMock(
        return_value=fake_response([[0.1, 0.2]])
    )

    with pytest.raises(AIProviderResponseError):
        await provider.embed(["first", "second"])


async def test_embed_wraps_api_errors() -> None:
    provider = make_provider()
    provider._client.aio.models.embed_content = AsyncMock(side_effect=_FakeAPIError("boom"))

    with pytest.raises(AIProviderRequestError):
        await provider.embed(["first"])


async def test_embed_passes_model_and_output_dimensionality() -> None:
    provider = make_provider()
    embed_content = AsyncMock(return_value=fake_response([[0.1, 0.2]]))
    provider._client.aio.models.embed_content = embed_content

    await provider.embed(["first"])

    assert embed_content.call_args.kwargs["model"] == "gemini-embedding-001"
    assert embed_content.call_args.kwargs["contents"] == ["first"]
    assert embed_content.call_args.kwargs["config"].output_dimensionality == 1536
