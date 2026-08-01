"""Unit tests for OpenAIEmbeddingProvider. The network call is always
mocked — these verify our wrapping logic, not OpenAI's API."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import openai
import pytest

from app.ai.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)


class _FakeAPIError(openai.APIError):
    """openai.APIError's real __init__ requires SDK-internal request/body
    objects we don't have in a unit test; bypass it while staying an
    instance of the type the provider's except clause catches."""

    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


def make_provider() -> OpenAIEmbeddingProvider:
    return OpenAIEmbeddingProvider(api_key="test-key", model="text-embedding-3-small", dimensions=1536)


def fake_response(embeddings: list[list[float]]) -> SimpleNamespace:
    return SimpleNamespace(
        data=[
            SimpleNamespace(index=i, embedding=vector) for i, vector in enumerate(embeddings)
        ]
    )


def test_missing_api_key_raises_config_error() -> None:
    with pytest.raises(AIProviderConfigError):
        OpenAIEmbeddingProvider(api_key=None, model="text-embedding-3-small", dimensions=1536)


def test_model_name_and_dimensions_exposed() -> None:
    provider = make_provider()

    assert provider.model_name == "text-embedding-3-small"
    assert provider.dimensions == 1536


async def test_embed_empty_list_returns_empty_without_a_call() -> None:
    provider = make_provider()
    provider._client.embeddings.create = AsyncMock()

    result = await provider.embed([])

    assert result == []
    provider._client.embeddings.create.assert_not_called()


async def test_embed_returns_vectors_in_order() -> None:
    provider = make_provider()
    provider._client.embeddings.create = AsyncMock(
        return_value=fake_response([[0.1, 0.2], [0.3, 0.4]])
    )

    result = await provider.embed(["first", "second"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]


async def test_embed_reorders_by_index_defensively() -> None:
    provider = make_provider()
    response = fake_response([[0.1, 0.2], [0.3, 0.4]])
    response.data.reverse()  # simulate an out-of-order response
    provider._client.embeddings.create = AsyncMock(return_value=response)

    result = await provider.embed(["first", "second"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]


async def test_embed_raises_on_count_mismatch() -> None:
    provider = make_provider()
    provider._client.embeddings.create = AsyncMock(return_value=fake_response([[0.1, 0.2]]))

    with pytest.raises(AIProviderResponseError):
        await provider.embed(["first", "second"])


async def test_embed_wraps_api_errors() -> None:
    provider = make_provider()
    provider._client.embeddings.create = AsyncMock(side_effect=_FakeAPIError("boom"))

    with pytest.raises(AIProviderRequestError):
        await provider.embed(["first"])


async def test_embed_passes_model_and_dimensions() -> None:
    provider = make_provider()
    create = AsyncMock(return_value=fake_response([[0.1, 0.2]]))
    provider._client.embeddings.create = create

    await provider.embed(["first"])

    assert create.call_args.kwargs["model"] == "text-embedding-3-small"
    assert create.call_args.kwargs["dimensions"] == 1536
    assert create.call_args.kwargs["input"] == ["first"]
