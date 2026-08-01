"""Selects and caches the configured VoiceProvider (settings.VOICE_PROVIDER).
Mirrors app.ai.providers.factory's pattern — callers use get_voice_provider()
rather than importing SarvamVoiceProvider/BrowserVoiceProvider directly.
"""

from functools import lru_cache

from app.ai.voice.base import VoiceProvider, VoiceProviderConfigError
from app.ai.voice.browser_provider import BrowserVoiceProvider
from app.ai.voice.sarvam_provider import SarvamVoiceProvider
from app.core.config import settings


@lru_cache
def get_voice_provider() -> VoiceProvider:
    if settings.VOICE_PROVIDER == "sarvam":
        return SarvamVoiceProvider(
            api_key=settings.SARVAM_API_KEY,
            stt_model=settings.SARVAM_STT_MODEL,
            tts_model=settings.SARVAM_TTS_MODEL,
            tts_speaker=settings.SARVAM_TTS_SPEAKER,
            timeout_seconds=settings.SARVAM_TIMEOUT_SECONDS,
        )
    if settings.VOICE_PROVIDER == "browser":
        return BrowserVoiceProvider()
    raise VoiceProviderConfigError(
        f"Unsupported VOICE_PROVIDER={settings.VOICE_PROVIDER!r}. Add a matching "
        "branch in app.ai.voice.factory when a new provider is wired up."
    )
