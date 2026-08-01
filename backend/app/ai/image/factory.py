"""Selects and caches the configured ImageProvider (settings.IMAGE_PROVIDER).
Mirrors app.ai.providers.factory / app.ai.embeddings.factory's pattern.
"""

from functools import lru_cache

from app.ai.image.provider import ImageProvider
from app.ai.image.together_provider import TogetherImageProvider
from app.ai.providers.base import AIProviderConfigError
from app.core.config import settings


@lru_cache
def get_image_provider() -> ImageProvider:
    if settings.IMAGE_PROVIDER == "together":
        return TogetherImageProvider(
            api_key=settings.TOGETHER_API_KEY,
            model=settings.TOGETHER_IMAGE_MODEL,
        )
    raise AIProviderConfigError(
        f"Unsupported IMAGE_PROVIDER={settings.IMAGE_PROVIDER!r}. Add a matching branch in "
        "app.ai.image.factory when a new provider is wired up."
    )
