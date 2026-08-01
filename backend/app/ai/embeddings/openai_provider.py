"""OpenAI implementation of EmbeddingProvider — text-embedding-3-small by
default, per the tech stack doc. 1536 dimensions matches
memory_embeddings.embedding's fixed width (see migration 19); Groq doesn't
serve embedding models, so this is a separate vendor from app.ai.providers.
"""

from __future__ import annotations

import openai

from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, api_key: str | None, model: str, dimensions: int) -> None:
        if not api_key:
            raise AIProviderConfigError(
                "OPENAI_API_KEY is not set — required when EMBEDDING_PROVIDER=openai."
            )
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimensions = dimensions

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions,
            )
        except openai.APIError as exc:
            raise AIProviderRequestError(f"OpenAI embeddings request failed: {exc}") from exc

        if len(response.data) != len(texts):
            raise AIProviderResponseError(
                f"OpenAI returned {len(response.data)} embeddings for {len(texts)} inputs"
            )
        # Ordered by `.index` defensively — the API documents input order is
        # preserved, but this costs nothing and removes the assumption.
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]
