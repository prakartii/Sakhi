"""Selects and caches the configured AIProvider (settings.AI_PROVIDER).

Everything outside app.ai should call get_ai_provider() rather than
importing a concrete provider class (GroqProvider, ...) directly — that's
what makes swapping providers a settings change instead of a call-site one.
"""

from functools import lru_cache

from app.ai.providers.base import AIProvider, AIProviderConfigError
from app.ai.providers.groq_provider import GroqProvider
from app.core.config import settings


@lru_cache
def get_ai_provider() -> AIProvider:
    if settings.AI_PROVIDER == "groq":
        return GroqProvider(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            default_temperature=settings.AI_TEMPERATURE,
            default_max_tokens=settings.AI_MAX_TOKENS,
        )
    raise AIProviderConfigError(
        f"Unsupported AI_PROVIDER={settings.AI_PROVIDER!r}. Add a matching "
        "branch in app.ai.providers.factory when a new provider is wired up."
    )
