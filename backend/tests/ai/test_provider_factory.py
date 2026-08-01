"""Unit tests for get_ai_provider() — the AI_PROVIDER settings switch."""

from collections.abc import Iterator

import pytest

from app.ai.providers.base import AIProvider, AIProviderConfigError
from app.ai.providers.factory import get_ai_provider
from app.core.config import settings


@pytest.fixture(autouse=True)
def _clear_provider_cache() -> Iterator[None]:
    get_ai_provider.cache_clear()
    yield
    get_ai_provider.cache_clear()


def test_get_ai_provider_returns_groq_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    provider = get_ai_provider()

    assert isinstance(provider, AIProvider)


def test_get_ai_provider_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    assert get_ai_provider() is get_ai_provider()


def test_get_ai_provider_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", None)

    with pytest.raises(AIProviderConfigError):
        get_ai_provider()
