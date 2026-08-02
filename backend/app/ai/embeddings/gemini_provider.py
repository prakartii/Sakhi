"""Google Gemini implementation of EmbeddingProvider — a genuinely free-tier
alternative to OpenAI's paid embeddings API. Google AI Studio issues
GEMINI_API_KEY for free, no billing setup required, with a workable quota
for a demo.

gemini-embedding-001 natively outputs 3072 dimensions but supports
Matryoshka-truncated output via `output_dimensionality` — this app passes
1536 so vectors stay compatible with memory_embeddings.embedding's fixed
column width (see migration 19) without a schema change, matching what
EMBEDDING_DIM already pins for the OpenAI provider.
"""

from __future__ import annotations

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, api_key: str | None, model: str, dimensions: int) -> None:
        if not api_key:
            raise AIProviderConfigError(
                "GEMINI_API_KEY is not set — required when EMBEDDING_PROVIDER=gemini."
            )
        self._client = genai.Client(api_key=api_key)
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
            response = await self._client.aio.models.embed_content(
                model=self._model,
                contents=texts,
                config=genai_types.EmbedContentConfig(output_dimensionality=self._dimensions),
            )
        except genai_errors.APIError as exc:
            raise AIProviderRequestError(f"Gemini embeddings request failed: {exc}") from exc

        embeddings = response.embeddings or []
        if len(embeddings) != len(texts):
            raise AIProviderResponseError(
                f"Gemini returned {len(embeddings)} embeddings for {len(texts)} inputs"
            )
        # Gemini returns embeddings in the same order as `contents` (no
        # per-item index to re-sort by, unlike OpenAI's response shape).
        return [list(item.values) for item in embeddings]
