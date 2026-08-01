"""Unit tests for SarvamVoiceProvider. The network call is always mocked —
these verify our wrapping logic, not Sarvam's API."""

import base64

import httpx
import pytest
import sarvamai
from sarvamai.types.speech_to_text_response import SpeechToTextResponse
from sarvamai.types.text_to_speech_response import TextToSpeechResponse
from sarvamai.types.translation_response import TranslationResponse
from unittest.mock import AsyncMock

from app.ai.voice.base import (
    VoiceProviderConfigError,
    VoiceProviderRequestError,
    VoiceProviderResponseError,
)
from app.ai.voice.sarvam_provider import SarvamVoiceProvider


def make_provider(*, sleep: AsyncMock | None = None) -> SarvamVoiceProvider:
    return SarvamVoiceProvider(
        api_key="test-key",
        stt_model="saaras:v3",
        tts_model="bulbul:v3",
        tts_speaker="anushka",
        retry_backoff_seconds=0.01,
        sleep=sleep or AsyncMock(),
    )


def test_missing_api_key_raises_config_error() -> None:
    with pytest.raises(VoiceProviderConfigError):
        SarvamVoiceProvider(api_key=None, stt_model="m", tts_model="m", tts_speaker="s")


# --- transcribe() ---


async def test_transcribe_returns_text_and_detected_language() -> None:
    provider = make_provider()
    provider._client.speech_to_text.transcribe = AsyncMock(
        return_value=SpeechToTextResponse(
            transcript="Namaste, mera naam Priya hai",
            language_code="hi-IN",
            language_probability=0.97,
        )
    )

    result = await provider.transcribe(b"fake-audio-bytes", "hi-IN")

    assert result.text == "Namaste, mera naam Priya hai"
    assert result.detected_language == "hi-IN"
    assert result.confidence == 0.97


async def test_transcribe_passes_audio_model_and_language() -> None:
    provider = make_provider()
    transcribe_mock = AsyncMock(
        return_value=SpeechToTextResponse(transcript="hello", language_code="hi-IN")
    )
    provider._client.speech_to_text.transcribe = transcribe_mock

    await provider.transcribe(b"fake-audio-bytes", "hi-IN")

    assert transcribe_mock.call_args.kwargs["file"] == b"fake-audio-bytes"
    assert transcribe_mock.call_args.kwargs["model"] == "saaras:v3"
    assert transcribe_mock.call_args.kwargs["language_code"] == "hi-IN"


async def test_transcribe_falls_back_to_requested_language_if_none_detected() -> None:
    provider = make_provider()
    provider._client.speech_to_text.transcribe = AsyncMock(
        return_value=SpeechToTextResponse(transcript="hello", language_code=None)
    )

    result = await provider.transcribe(b"fake-audio-bytes", "hi-IN")

    assert result.detected_language == "hi-IN"


async def test_transcribe_raises_on_empty_transcript() -> None:
    provider = make_provider()
    provider._client.speech_to_text.transcribe = AsyncMock(
        return_value=SpeechToTextResponse(transcript="")
    )

    with pytest.raises(VoiceProviderResponseError):
        await provider.transcribe(b"fake-audio-bytes", "hi-IN")


# --- synthesize() ---


async def test_synthesize_returns_decoded_audio_bytes() -> None:
    provider = make_provider()
    encoded = base64.b64encode(b"raw-wav-bytes").decode("ascii")
    provider._client.text_to_speech.convert = AsyncMock(
        return_value=TextToSpeechResponse(audios=[encoded])
    )

    result = await provider.synthesize("Namaste", "hi-IN")

    assert result.audio_bytes == b"raw-wav-bytes"
    assert result.format == "wav"
    assert result.audio_url is None


async def test_synthesize_passes_text_language_model_and_speaker() -> None:
    provider = make_provider()
    encoded = base64.b64encode(b"raw-wav-bytes").decode("ascii")
    convert_mock = AsyncMock(return_value=TextToSpeechResponse(audios=[encoded]))
    provider._client.text_to_speech.convert = convert_mock

    await provider.synthesize("Namaste", "hi-IN")

    assert convert_mock.call_args.kwargs["text"] == "Namaste"
    assert convert_mock.call_args.kwargs["target_language_code"] == "hi-IN"
    assert convert_mock.call_args.kwargs["model"] == "bulbul:v3"
    assert convert_mock.call_args.kwargs["speaker"] == "anushka"


async def test_synthesize_raises_on_no_audio() -> None:
    provider = make_provider()
    provider._client.text_to_speech.convert = AsyncMock(return_value=TextToSpeechResponse(audios=[]))

    with pytest.raises(VoiceProviderResponseError):
        await provider.synthesize("Namaste", "hi-IN")


# --- translate() (the optional pivot capability) ---


async def test_translate_returns_translated_text() -> None:
    provider = make_provider()
    provider._client.text.translate = AsyncMock(
        return_value=TranslationResponse(translated_text="Hello, my name is Priya", source_language_code="hi-IN")
    )

    result = await provider.translate("Namaste, mera naam Priya hai", "hi-IN")

    assert result == "Hello, my name is Priya"


async def test_translate_raises_on_empty_result() -> None:
    provider = make_provider()
    provider._client.text.translate = AsyncMock(
        return_value=TranslationResponse(translated_text="", source_language_code="hi-IN")
    )

    with pytest.raises(VoiceProviderResponseError):
        await provider.translate("Namaste", "hi-IN")


# --- retry / error handling ---


async def test_transient_sarvam_error_retries_once_then_succeeds() -> None:
    sleep = AsyncMock()
    provider = make_provider(sleep=sleep)
    provider._client.speech_to_text.transcribe = AsyncMock(
        side_effect=[
            sarvamai.TooManyRequestsError(body="rate limited"),
            SpeechToTextResponse(transcript="hello", language_code="hi-IN"),
        ]
    )

    result = await provider.transcribe(b"fake-audio-bytes", "hi-IN")

    assert result.text == "hello"
    sleep.assert_awaited_once()


async def test_transient_timeout_retries_once_then_succeeds() -> None:
    sleep = AsyncMock()
    provider = make_provider(sleep=sleep)
    provider._client.speech_to_text.transcribe = AsyncMock(
        side_effect=[
            httpx.ConnectTimeout("timed out"),
            SpeechToTextResponse(transcript="hello", language_code="hi-IN"),
        ]
    )

    result = await provider.transcribe(b"fake-audio-bytes", "hi-IN")

    assert result.text == "hello"
    sleep.assert_awaited_once()


async def test_transient_error_raises_clean_error_if_retry_also_fails() -> None:
    sleep = AsyncMock()
    provider = make_provider(sleep=sleep)
    provider._client.speech_to_text.transcribe = AsyncMock(
        side_effect=[
            sarvamai.TooManyRequestsError(body="rate limited again"),
            sarvamai.InternalServerError(body="still failing"),
        ]
    )

    with pytest.raises(VoiceProviderRequestError):
        await provider.transcribe(b"fake-audio-bytes", "hi-IN")

    sleep.assert_awaited_once()


async def test_non_retryable_error_fails_immediately_without_sleeping() -> None:
    sleep = AsyncMock()
    provider = make_provider(sleep=sleep)
    provider._client.speech_to_text.transcribe = AsyncMock(
        side_effect=sarvamai.BadRequestError(body="bad audio format")
    )

    with pytest.raises(VoiceProviderRequestError):
        await provider.transcribe(b"fake-audio-bytes", "hi-IN")

    sleep.assert_not_awaited()
    assert provider._client.speech_to_text.transcribe.call_count == 1
