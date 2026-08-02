"""Sarvam AI implementation of VoiceProvider — Saaras v3 for speech-to-
text, Bulbul v3 for text-to-speech, both covering Hindi and the other
BCP-47 codes this app targets out of the box.

Verified directly against the official `sarvamai` Python SDK (Fern-
generated — same pattern as groq/openai/together, so introspected the
same way rather than guessed): `AsyncSarvamAI(api_subscription_key=...,
timeout=...)`, `speech_to_text.transcribe(file=<bytes>, model=...,
language_code=...) -> SpeechToTextResponse(transcript, language_code,
language_probability)`, `text_to_speech.convert(text=...,
target_language_code=..., model=..., speaker=...) ->
TextToSpeechResponse(audios: list[base64 WAV str])`,
`text.translate(input=..., source_language_code=..., target_language_code=...)
-> TranslationResponse(translated_text, source_language_code)`. The SDK
has no built-in retry (no `max_retries` constructor param, unlike groq/
openai/together), so there's no double-retry risk to guard against here.
"""

from __future__ import annotations

import asyncio
import base64
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
import sarvamai
from sarvamai.core.api_error import ApiError

from app.ai.voice.base import (
    SynthesisResult,
    TranscriptionResult,
    VoiceProvider,
    VoiceProviderConfigError,
    VoiceProviderRequestError,
    VoiceProviderResponseError,
)

DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_RETRY_BACKOFF_SECONDS = 0.5

# Sarvam's status-code exceptions worth retrying once: rate limit and
# 5xx are plausibly transient. BadRequestError/ForbiddenError/
# NotFoundError/UnprocessableEntityError/ContentTooLargeError are
# permanent client errors — retrying wastes the backoff.
_RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    sarvamai.TooManyRequestsError,
    sarvamai.InternalServerError,
    sarvamai.ServiceUnavailableError,
    # The SDK doesn't wrap network/timeout failures into its own
    # exception type — those surface as raw httpx errors.
    httpx.TransportError,  # covers httpx.TimeoutException too (its base class)
)

SleepFn = Callable[[float], Awaitable[None]]


class SarvamVoiceProvider(VoiceProvider):
    def __init__(
        self,
        *,
        api_key: str | None,
        stt_model: str,
        tts_model: str,
        tts_speaker: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        sleep: SleepFn | None = None,
    ) -> None:
        if not api_key:
            raise VoiceProviderConfigError(
                "SARVAM_API_KEY is not set — required when VOICE_PROVIDER=sarvam."
            )
        # A request timeout so a slow/hung Sarvam call can't hang the demo.
        self._client = sarvamai.AsyncSarvamAI(api_subscription_key=api_key, timeout=timeout_seconds)
        self._stt_model = stt_model
        self._tts_model = tts_model
        self._tts_speaker = tts_speaker
        self._retry_backoff_seconds = retry_backoff_seconds
        self._sleep: SleepFn = sleep or asyncio.sleep

    async def transcribe(self, audio: bytes, language: str) -> TranscriptionResult:
        # Every recording this app sends comes from the browser's
        # MediaRecorder, which the frontend always labels "audio/webm" (see
        # use-voice-companion.ts / use-voice-transcribe.ts) — without
        # input_audio_codec telling Sarvam that explicitly, it silently
        # mis-decodes the bytes and returns a 200 with an empty transcript
        # instead of an error, which is indistinguishable from real silence
        # further down this method.
        response = await self._with_retry(
            lambda: self._client.speech_to_text.transcribe(
                file=audio,
                model=self._stt_model,
                language_code=language,
                input_audio_codec="webm",
            )
        )
        if not response.transcript:
            raise VoiceProviderResponseError("Sarvam returned an empty transcript")
        return TranscriptionResult(
            text=response.transcript,
            detected_language=response.language_code or language,
            confidence=response.language_probability,
        )

    async def synthesize(self, text: str, language: str) -> SynthesisResult:
        response = await self._with_retry(
            lambda: self._client.text_to_speech.convert(
                text=text,
                target_language_code=language,
                model=self._tts_model,
                speaker=self._tts_speaker,
            )
        )
        if not response.audios:
            raise VoiceProviderResponseError("Sarvam returned no audio")
        audio_bytes = base64.b64decode(response.audios[0])
        return SynthesisResult(audio_bytes=audio_bytes, format="wav")

    async def translate(self, text: str, source_language: str, target_language: str = "en-IN") -> str:
        """Translate `text` via Sarvam's translate endpoint.

        Not part of the VoiceProvider interface — this is the optional
        pivot capability (see app.ai.voice.pivot.should_pivot), only
        meaningful for this provider; browser_provider has no equivalent.
        """
        response = await self._with_retry(
            lambda: self._client.text.translate(
                input=text,
                source_language_code=source_language,
                target_language_code=target_language,
            )
        )
        if not response.translated_text:
            raise VoiceProviderResponseError("Sarvam returned an empty translation")
        return response.translated_text

    async def _with_retry(self, call: Callable[[], Awaitable[Any]]) -> Any:
        try:
            return await call()
        except _RETRYABLE_ERRORS:
            await self._sleep(self._retry_backoff_seconds)
            try:
                return await call()
            except (ApiError, httpx.TransportError) as retry_exc:
                raise VoiceProviderRequestError(
                    f"Sarvam request failed after retry: {retry_exc}"
                ) from retry_exc
        except ApiError as exc:
            raise VoiceProviderRequestError(f"Sarvam request failed: {exc}") from exc
