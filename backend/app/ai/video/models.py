"""Pydantic schema for video generation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratedVideo(BaseModel):
    url: str
    provider: str
    prompt: str = Field(default=..., description="The final prompt actually sent to the video provider.")
