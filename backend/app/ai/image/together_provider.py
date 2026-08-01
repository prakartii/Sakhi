"""Together AI implementation of ImageProvider — FLUX.1-schnell-Free by
default (Together's free-tier fast image model, good enough for a demo).
This is the one place app.ai calls a non-LLM external API.
"""

from __future__ import annotations

import together

from app.ai.image.provider import ImageProvider
from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)


class TogetherImageProvider(ImageProvider):
    def __init__(self, *, api_key: str | None, model: str) -> None:
        if not api_key:
            raise AIProviderConfigError(
                "TOGETHER_API_KEY is not set — required when IMAGE_PROVIDER=together."
            )
        self._client = together.AsyncTogether(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return f"together:{self._model}"

    async def generate(self, prompt: str, *, width: int, height: int) -> str:
        try:
            response = await self._client.images.generate(
                model=self._model,
                prompt=prompt,
                width=width,
                height=height,
                n=1,
                response_format="url",
            )
        except together.APIError as exc:
            raise AIProviderRequestError(f"Together image request failed: {exc}") from exc

        if not response.data:
            raise AIProviderResponseError("Together returned no image data")
        url = response.data[0].url
        if not url:
            raise AIProviderResponseError("Together returned an image entry without a url")
        return url
