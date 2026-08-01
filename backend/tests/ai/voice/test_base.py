"""Unit tests for SynthesisResult's audio-source validation."""

import pytest

from app.ai.voice.base import SynthesisResult


def test_both_audio_fields_none_is_valid() -> None:
    result = SynthesisResult(format="none")

    assert result.audio_bytes is None
    assert result.audio_url is None


def test_only_audio_bytes_is_valid() -> None:
    result = SynthesisResult(audio_bytes=b"wav-data", format="wav")

    assert result.audio_bytes == b"wav-data"


def test_only_audio_url_is_valid() -> None:
    result = SynthesisResult(audio_url="https://example.com/audio.wav", format="wav")

    assert result.audio_url == "https://example.com/audio.wav"


def test_both_audio_fields_set_is_rejected() -> None:
    with pytest.raises(ValueError):
        SynthesisResult(
            audio_bytes=b"wav-data",
            audio_url="https://example.com/audio.wav",
            format="wav",
        )
