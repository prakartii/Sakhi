"""Unit tests for get_image_provider() — the IMAGE_PROVIDER settings switch."""

from collections.abc import Iterator

import pytest

from app.ai.image.factory import get_image_provider
from app.ai.image.provider import ImageProvider
from app.ai.providers.base import AIProviderConfigError
from app.core.config import settings


@pytest.fixture(autouse=True)
def _clear_provider_cache() -> Iterator[None]:
    get_image_provider.cache_clear()
    yield
    get_image_provider.cache_clear()


def test_get_image_provider_returns_together_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "IMAGE_PROVIDER", "together")
    monkeypatch.setattr(settings, "TOGETHER_API_KEY", "test-key")

    provider = get_image_provider()

    assert isinstance(provider, ImageProvider)


def test_get_image_provider_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "IMAGE_PROVIDER", "together")
    monkeypatch.setattr(settings, "TOGETHER_API_KEY", "test-key")

    assert get_image_provider() is get_image_provider()


def test_get_image_provider_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "IMAGE_PROVIDER", "together")
    monkeypatch.setattr(settings, "TOGETHER_API_KEY", None)

    with pytest.raises(AIProviderConfigError):
        get_image_provider()
