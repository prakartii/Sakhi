"""Unit tests for get_voice_provider() — the VOICE_PROVIDER settings switch."""

from collections.abc import Iterator

import pytest

from app.ai.voice.base import VoiceProvider, VoiceProviderConfigError
from app.ai.voice.browser_provider import BrowserVoiceProvider
from app.ai.voice.factory import get_voice_provider
from app.ai.voice.sarvam_provider import SarvamVoiceProvider
from app.core.config import settings


@pytest.fixture(autouse=True)
def _clear_provider_cache() -> Iterator[None]:
    get_voice_provider.cache_clear()
    yield
    get_voice_provider.cache_clear()


def test_get_voice_provider_returns_sarvam_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "VOICE_PROVIDER", "sarvam")
    monkeypatch.setattr(settings, "SARVAM_API_KEY", "test-key")

    provider = get_voice_provider()

    assert isinstance(provider, VoiceProvider)
    assert isinstance(provider, SarvamVoiceProvider)


def test_get_voice_provider_returns_browser_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "VOICE_PROVIDER", "browser")

    provider = get_voice_provider()

    assert isinstance(provider, VoiceProvider)
    assert isinstance(provider, BrowserVoiceProvider)


def test_get_voice_provider_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "VOICE_PROVIDER", "browser")

    assert get_voice_provider() is get_voice_provider()


def test_get_voice_provider_raises_without_sarvam_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "VOICE_PROVIDER", "sarvam")
    monkeypatch.setattr(settings, "SARVAM_API_KEY", None)

    with pytest.raises(VoiceProviderConfigError):
        get_voice_provider()
