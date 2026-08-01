"""Unit tests for BrowserVoiceProvider — the client-side-STT passthrough
fallback. No network involved at all; these verify the passthrough
contract itself."""

import pytest

from app.ai.voice.base import VoiceProviderResponseError
from app.ai.voice.browser_provider import BrowserVoiceProvider


async def test_transcribe_passes_text_through_unchanged() -> None:
    provider = BrowserVoiceProvider()
    text = "Namaste, mera naam Priya hai"

    result = await provider.transcribe(text.encode("utf-8"), "hi-IN")

    assert result.text == text
    assert result.detected_language == "hi-IN"
    assert result.confidence == 1.0


async def test_transcribe_rejects_non_utf8_bytes() -> None:
    provider = BrowserVoiceProvider()

    with pytest.raises(VoiceProviderResponseError):
        await provider.transcribe(b"\xff\xfe\x00\x01", "hi-IN")


async def test_transcribe_rejects_empty_text() -> None:
    provider = BrowserVoiceProvider()

    with pytest.raises(VoiceProviderResponseError):
        await provider.transcribe("   ".encode("utf-8"), "hi-IN")


async def test_synthesize_is_a_no_op() -> None:
    provider = BrowserVoiceProvider()

    result = await provider.synthesize("Namaste", "hi-IN")

    assert result.audio_bytes is None
    assert result.audio_url is None
    assert result.format == "none"
