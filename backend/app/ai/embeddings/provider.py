"""Provider-agnostic embedding interface — the embedding-generation
counterpart to app.ai.providers' chat AIProvider. Implementations wrap one
vendor's embedding API; call sites depend on this interface, never a
concrete SDK, so swapping embedding vendors is a factory.py change.

Reuses app.ai.providers.base's exception hierarchy (AIProviderConfigError /
AIProviderRequestError / AIProviderResponseError) rather than redefining
parallel ones — both chat and embeddings are "an aiProvider call failed",
and callers should be able to catch AIProviderError everywhere in app.ai.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier stored as memory_embeddings.embedding_model."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Length of every vector this provider returns. Must match the
        fixed width of memory_embeddings.embedding (see migration 19)."""
        raise NotImplementedError

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, returning one vector per input, in the
        same order as `texts`."""
        raise NotImplementedError
