"""Provider-agnostic voice interface: speech-to-text (transcribe) and
text-to-speech (synthesize). Sarvam AI is the default implementation
(sarvam_provider.py); browser_provider.py is a client-side-STT passthrough
fallback (settings.VOICE_PROVIDER=browser). Both implement this same
interface so callers never change based on which is configured.

This layer is deliberately narrow: it only turns audio into text and text
into audio. The reasoning step (Groq, via app.ai.providers) is untouched
and unaware this layer exists — nothing here imports app.ai.providers or
any other app.ai service. Language codes are BCP-47-style strings (e.g.
'hi-IN', 'ta-IN', 'te-IN', 'bn-IN', 'mr-IN', 'gu-IN', 'kn-IN', 'en-IN').
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, model_validator


class TranscriptionResult(BaseModel):
    text: str
    detected_language: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class SynthesisResult(BaseModel):
    audio_bytes: bytes | None = None
    audio_url: str | None = None
    format: str

    @model_validator(mode="after")
    def _at_most_one_audio_source(self) -> SynthesisResult:
        # Both None is valid (e.g. browser_provider's TTS-is-optional
        # no-op); both set at once would be contradictory.
        if self.audio_bytes is not None and self.audio_url is not None:
            raise ValueError(
                "SynthesisResult may set at most one of audio_bytes/audio_url, not both"
            )
        return self


class VoiceProviderError(Exception):
    """Base class for all voice provider failures."""


class VoiceProviderConfigError(VoiceProviderError):
    """Raised when a provider is selected/constructed without valid
    configuration (e.g. VOICE_PROVIDER=sarvam but SARVAM_API_KEY is unset)."""


class VoiceProviderRequestError(VoiceProviderError):
    """Raised when the underlying API call itself fails — network error,
    timeout, auth failure, rate limit, 5xx from the vendor."""


class VoiceProviderResponseError(VoiceProviderError):
    """Raised when a provider call succeeds but returns something callers
    can't use — empty transcript, no audio returned, etc."""


class VoiceProvider(ABC):
    """Provider-agnostic speech interface. One implementation per vendor
    (or, for browser_provider, per client-side capability)."""

    @abstractmethod
    async def transcribe(self, audio: bytes, language: str) -> TranscriptionResult:
        """Transcribe `audio` spoken in `language` (BCP-47) into text."""
        raise NotImplementedError

    @abstractmethod
    async def synthesize(self, text: str, language: str) -> SynthesisResult:
        """Synthesize `text` as spoken audio in `language` (BCP-47)."""
        raise NotImplementedError
