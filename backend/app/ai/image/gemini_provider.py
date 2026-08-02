"""Google Gemini implementation of ImageProvider — "Nano Banana"
(gemini-2.5-flash-image), Google's multimodal image generation model.
Free-tier eligible (same GEMINI_API_KEY as app.ai.embeddings' Gemini
provider), used specifically by Content Calendar and Marketing Studio's
reel-visual generation — not the default IMAGE_PROVIDER (Together stays
default for Website Studio's hero images); see get_nano_banana_provider()
in factory.py for why this is a separate, explicitly-selected provider
rather than a IMAGE_PROVIDER=gemini switch.

Unlike Together (which returns a hosted URL), Gemini returns the image
inline as base64 bytes in the response — there's no upload step and
nothing in this app persists generated images to object storage, so
`generate()` returns a `data:` URL instead of a hosted one. That's a
larger string to store/transmit than a URL, but it's honest about what
this provider actually gives back rather than inventing a fake upload
step.
"""

from __future__ import annotations

import base64

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.ai.image.provider import ImageProvider
from app.ai.providers.base import (
    AIProviderConfigError,
    AIProviderRequestError,
    AIProviderResponseError,
)


class GeminiImageProvider(ImageProvider):
    def __init__(self, *, api_key: str | None, model: str) -> None:
        if not api_key:
            raise AIProviderConfigError(
                "GEMINI_API_KEY is not set — required for Nano Banana image generation."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return f"gemini:{self._model}"

    async def generate(self, prompt: str, *, width: int, height: int) -> str:
        # Nano Banana has no direct width/height parameter (unlike
        # Together's API) — the aspect ratio is steered via the prompt
        # instead, which is the documented way to influence its output shape.
        aspect_hint = "square" if width == height else "portrait" if height > width else "landscape"
        styled_prompt = f"{prompt} Image orientation: {aspect_hint}."

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=[styled_prompt],
                config=genai_types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )
        except genai_errors.APIError as exc:
            raise AIProviderRequestError(f"Gemini image request failed: {exc}") from exc

        candidates = response.candidates or []
        for candidate in candidates:
            parts = candidate.content.parts if candidate.content else []
            for part in parts or []:
                inline = getattr(part, "inline_data", None)
                if inline is not None and inline.data:
                    mime_type = inline.mime_type or "image/png"
                    encoded = base64.b64encode(inline.data).decode("ascii")
                    return f"data:{mime_type};base64,{encoded}"

        raise AIProviderResponseError("Gemini returned no image data")
