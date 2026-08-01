"""Provider-agnostic image-generation interface — the image counterpart
to app.ai.providers' chat AIProvider and app.ai.embeddings' EmbeddingProvider.
This is NOT an LLM call. Implementations wrap one vendor's image API; call
sites depend on this interface, never a concrete SDK, so swapping image
vendors is a factory.py change.

Reuses app.ai.providers.base's exception hierarchy, same rationale as
app.ai.embeddings.provider: every vendor call in app.ai is "an aiProvider
call failed", and callers should be able to catch AIProviderError anywhere.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ImageProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier stored as GeneratedImage.provider, e.g.
        'together:black-forest-labs/FLUX.1-schnell-Free'."""
        raise NotImplementedError

    @abstractmethod
    async def generate(self, prompt: str, *, width: int, height: int) -> str:
        """Generate an image from `prompt` and return its URL."""
        raise NotImplementedError
