"""Unit tests for get_embedding_provider() — the EMBEDDING_PROVIDER settings switch."""

from collections.abc import Iterator

import pytest

from app.ai.embeddings.factory import get_embedding_provider
from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.providers.base import AIProviderConfigError
from app.core.config import settings


@pytest.fixture(autouse=True)
def _clear_provider_cache() -> Iterator[None]:
    get_embedding_provider.cache_clear()
    yield
    get_embedding_provider.cache_clear()


def test_get_embedding_provider_returns_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

    provider = get_embedding_provider()

    assert isinstance(provider, EmbeddingProvider)


def test_get_embedding_provider_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

    assert get_embedding_provider() is get_embedding_provider()


def test_get_embedding_provider_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)

    with pytest.raises(AIProviderConfigError):
        get_embedding_provider()
