"""Unit tests for generate_image(). The provider is always mocked."""

import pytest

from app.ai.image.generator import generate_image
from app.ai.image.models import GeneratedImage
from app.ai.image.provider import ImageProvider


class FakeImageProvider(ImageProvider):
    def __init__(self, url: str = "https://example.com/fake.png") -> None:
        self.url = url
        self.calls: list[dict] = []

    @property
    def name(self) -> str:
        return "fake-provider"

    async def generate(self, prompt: str, *, width: int, height: int) -> str:
        self.calls.append({"prompt": prompt, "width": width, "height": height})
        return self.url


async def test_generate_image_returns_generated_image() -> None:
    provider = FakeImageProvider()

    image = await generate_image("a crochet handbag icon", "logo", "square", provider=provider)

    assert isinstance(image, GeneratedImage)
    assert image.url == "https://example.com/fake.png"
    assert image.provider == "fake-provider"


async def test_generate_image_applies_kind_style_hint() -> None:
    provider = FakeImageProvider()

    image = await generate_image("a crochet handbag icon", "logo", provider=provider)

    assert "a crochet handbag icon" in image.prompt
    assert "no text" in image.prompt
    assert provider.calls[0]["prompt"] == image.prompt


async def test_generate_image_uses_different_style_hints_per_kind() -> None:
    provider = FakeImageProvider()

    logo = await generate_image("a bag", "logo", provider=provider)
    post = await generate_image("a bag", "post", provider=provider)

    assert logo.prompt != post.prompt


async def test_generate_image_maps_size_to_dimensions() -> None:
    provider = FakeImageProvider()

    await generate_image("prompt", "post", "landscape", provider=provider)

    assert provider.calls[0]["width"] == 1024
    assert provider.calls[0]["height"] == 768


async def test_generate_image_defaults_to_square() -> None:
    provider = FakeImageProvider()

    await generate_image("prompt", "brand", provider=provider)

    assert provider.calls[0]["width"] == provider.calls[0]["height"] == 1024


async def test_generate_image_rejects_empty_prompt() -> None:
    provider = FakeImageProvider()

    with pytest.raises(ValueError):
        await generate_image("   ", "logo", provider=provider)

    assert provider.calls == []
