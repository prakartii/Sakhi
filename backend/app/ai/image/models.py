"""Pydantic schema + type aliases for image generation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ImageKind = Literal["logo", "post", "brand"]
ImageSize = Literal["square", "portrait", "landscape"]


class GeneratedImage(BaseModel):
    url: str
    provider: str
    prompt: str = Field(
        default=...,
        description="The final prompt actually sent to the image provider (kind's style hint included).",
    )
