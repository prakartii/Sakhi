"""generate_image(): the public entry point for image generation — the one
genuinely new external capability in the generation layer, not an LLM
call. Provider-swappable via settings.IMAGE_PROVIDER (Together by
default), mirroring app.ai.providers' aiProvider pattern.
"""

from __future__ import annotations

from app.ai.image.factory import get_image_provider
from app.ai.image.models import GeneratedImage, ImageKind, ImageSize
from app.ai.image.provider import ImageProvider

_SIZE_DIMENSIONS: dict[ImageSize, tuple[int, int]] = {
    "square": (1024, 1024),
    "portrait": (768, 1024),
    "landscape": (1024, 768),
}

_KIND_STYLE_HINTS: dict[ImageKind, str] = {
    "logo": "flat vector icon style, centered composition, plain solid background, no text",
    "post": "social-media-ready photo, natural lighting, vibrant colors, high detail",
    "brand": "editorial brand photography style, clean composition, high detail",
}


async def generate_image(
    prompt: str,
    kind: ImageKind,
    size: ImageSize = "square",
    *,
    provider: ImageProvider | None = None,
) -> GeneratedImage:
    """Generate an image for `prompt`, styled per `kind`, at `size`.

    `kind` isn't just metadata — it appends a style hint to the prompt
    (e.g. "logo" asks for a text-free flat icon on a plain background),
    since the same raw prompt renders very differently depending on
    whether it's headed for a logo mark, a social post, or brand imagery.

    Raises ValueError on an empty prompt. Raises AIProviderRequestError /
    AIProviderResponseError (from app.ai.providers.base — reused here
    since both are just "an aiProvider call failed") on API/response
    failures from the underlying image provider.
    """
    if not prompt.strip():
        raise ValueError("prompt must not be empty")

    width, height = _SIZE_DIMENSIONS[size]
    styled_prompt = f"{prompt.strip()}. Style: {_KIND_STYLE_HINTS[kind]}."

    image_provider = provider or get_image_provider()
    url = await image_provider.generate(styled_prompt, width=width, height=height)

    return GeneratedImage(url=url, provider=image_provider.name, prompt=styled_prompt)
