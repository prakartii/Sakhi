"""fal.ai implementation of VideoProvider — text-to-video via a Wan model
(a smaller/cheaper tier by default; see settings.FAL_VIDEO_MODEL). No
free tier: fal.ai gives a one-time signup credit, then bills per second of
generated video. Every call this class makes is a real, billed request.

fal_client.subscribe() blocks until the generation finishes — video
generation routinely takes tens of seconds, well past this app's other AI
calls, so callers should expect this to be the slowest AI action in the
app and set caller-side timeouts/UI expectations accordingly.
"""

from __future__ import annotations

import fal_client

from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)
from app.ai.video.provider import VideoProvider

_DEFAULT_TIMEOUT_SECONDS = 180.0


class FalVideoProvider(VideoProvider):
    def __init__(self, *, api_key: str | None, model: str) -> None:
        if not api_key:
            raise AIProviderConfigError(
                "FAL_API_KEY is not set — required when VIDEO_PROVIDER=fal."
            )
        self._client = fal_client.AsyncClient(key=api_key, default_timeout=_DEFAULT_TIMEOUT_SECONDS)
        self._model = model

    @property
    def name(self) -> str:
        return f"fal:{self._model}"

    async def generate(self, prompt: str) -> str:
        try:
            result = await self._client.subscribe(self._model, arguments={"prompt": prompt})
        except fal_client.FalClientError as exc:
            raise AIProviderRequestError(f"fal.ai video request failed: {exc}") from exc

        video = result.get("video") if isinstance(result, dict) else None
        url = video.get("url") if isinstance(video, dict) else None
        if not url:
            raise AIProviderResponseError(f"fal.ai returned no video url: {result!r}")
        return url
