"""Browser fallback: a no-op/passthrough VoiceProvider representing STT
handled client-side by the Web Speech API (settings.VOICE_PROVIDER=browser).
Guarantees a working demo path if Sarvam is slow/down.

The React app captures speech via Web Speech and sends the resulting text
(UTF-8 encoded, not real audio) as the `audio` argument — transcribe()
just decodes it back and returns it as already-transcribed ground truth.
synthesize() is a genuine no-op: TTS is optional in this mode, since the
browser can also speak the reply client-side via Web Speech's
SpeechSynthesis. The interface is identical to SarvamVoiceProvider, so
callers never branch on which provider is configured.
"""

from __future__ import annotations

from app.ai.voice.base import (
    SynthesisResult,
    TranscriptionResult,
    VoiceProvider,
    VoiceProviderResponseError,
)


class BrowserVoiceProvider(VoiceProvider):
    async def transcribe(self, audio: bytes, language: str) -> TranscriptionResult:
        try:
            text = audio.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise VoiceProviderResponseError(
                "browser provider expects UTF-8 text bytes (already transcribed "
                "client-side), not raw audio"
            ) from exc
        if not text.strip():
            raise VoiceProviderResponseError("browser provider received empty transcript text")
        return TranscriptionResult(text=text, detected_language=language, confidence=1.0)

    async def synthesize(self, text: str, language: str) -> SynthesisResult:
        # No server-side audio is produced — the client speaks the reply
        # itself via Web Speech's SpeechSynthesis. format="none" signals
        # "nothing to play back", distinct from a real empty-audio failure.
        return SynthesisResult(audio_bytes=None, audio_url=None, format="none")
