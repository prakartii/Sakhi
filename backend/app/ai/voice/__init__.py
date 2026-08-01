"""Swappable multilingual voice layer: speech-to-text and text-to-speech
around the unchanged Groq reasoning step. Sarvam AI is the default
provider (sarvam_provider.py); a browser fallback (browser_provider.py,
settings.VOICE_PROVIDER=browser) passes through text the Web Speech API
already transcribed client-side, guaranteeing a working demo path if
Sarvam is slow/down.

- get_voice_provider()    Selects the configured VoiceProvider.
- VoiceProvider           The interface: transcribe(audio, language),
                          synthesize(text, language). Both providers
                          implement it identically.
- should_pivot()          Decides whether a language should be routed
                          through an English translation pivot before/
                          after Groq (settings.VOICE_TRANSLATE_PIVOT) —
                          a pure rule, not a call to Groq or Sarvam itself.

Nothing here imports app.ai.providers or any other app.ai service — the
reasoning step is composed by a future higher-level pipeline, not by this
package.
"""

from app.ai.voice.base import (
    SynthesisResult,
    TranscriptionResult,
    VoiceProvider,
    VoiceProviderConfigError,
    VoiceProviderError,
    VoiceProviderRequestError,
    VoiceProviderResponseError,
)
from app.ai.voice.factory import get_voice_provider
from app.ai.voice.pivot import should_pivot

__all__ = [
    "SynthesisResult",
    "TranscriptionResult",
    "VoiceProvider",
    "VoiceProviderConfigError",
    "VoiceProviderError",
    "VoiceProviderRequestError",
    "VoiceProviderResponseError",
    "get_voice_provider",
    "should_pivot",
]
