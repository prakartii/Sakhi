"""Selects and caches the configured VideoProvider (settings.VIDEO_PROVIDER).
Mirrors app.ai.image.factory's pattern.
"""

from functools import lru_cache

from app.ai.providers.base import AIProviderConfigError
from app.ai.video.fal_provider import FalVideoProvider
from app.ai.video.provider import VideoProvider
from app.core.config import settings


@lru_cache
def get_video_provider() -> VideoProvider:
    if settings.VIDEO_PROVIDER == "fal":
        return FalVideoProvider(api_key=settings.FAL_API_KEY, model=settings.FAL_VIDEO_MODEL)
    raise AIProviderConfigError(
        f"Unsupported VIDEO_PROVIDER={settings.VIDEO_PROVIDER!r}. Add a matching branch in "
        "app.ai.video.factory when a new provider is wired up."
    )
