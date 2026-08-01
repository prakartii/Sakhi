"""Pydantic schema for Brand Studio output. Every field is generated from
a BusinessProfile (see generator.py) — nothing here is filled with
placeholder/generic content.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VoiceGuide(BaseModel):
    tone: str
    keywords: list[str] = Field(default_factory=list)


class PaletteColor(BaseModel):
    name: str
    hex: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    role: str = Field(..., description="e.g. 'primary', 'accent', 'background'")


class Typography(BaseModel):
    heading: str
    body: str


class Bios(BaseModel):
    instagram: str
    linkedin: str


class BrandKit(BaseModel):
    name_suggestions: list[str] = Field(default_factory=list)
    tagline: str
    mission: str
    brand_story: str
    voice: VoiceGuide
    palette: list[PaletteColor] = Field(default_factory=list)
    typography: Typography
    bios: Bios
    packaging_ideas: list[str] = Field(default_factory=list)
    logo_prompt: str = Field(
        ..., description="Standalone image-generation prompt — feeds app.ai.image.generate_image()."
    )
