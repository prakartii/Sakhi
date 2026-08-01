"""Selects and caches the configured EmbeddingProvider (settings.EMBEDDING_PROVIDER).

Mirrors app.ai.providers.factory's pattern — callers use get_embedding_provider()
rather than importing OpenAIEmbeddingProvider directly.
"""

from functools import lru_cache

from app.ai.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.providers.base import AIProviderConfigError
from app.core.config import settings


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    if settings.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIM,
        )
    raise AIProviderConfigError(
        f"Unsupported EMBEDDING_PROVIDER={settings.EMBEDDING_PROVIDER!r}. Add a matching "
        "branch in app.ai.embeddings.factory when a new provider is wired up."
    )
