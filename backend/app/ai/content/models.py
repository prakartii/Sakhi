"""Pydantic schema for the Content Calendar. `ScheduledSlot` is the pure
rule-based scheduling output (see scheduler.py) — no copy yet.
`ContentPost` is the full result after generator.py fills in copy for
each slot via the LLM.
"""

from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field

PostType = Literal["post", "reel", "carousel", "story"]


class ScheduledSlot(BaseModel):
    """One rule-decided calendar slot: date, platform, post type, and
    posting time — decided entirely by scheduler.py, no LLM involved."""

    date: date
    platform: str
    type: PostType
    post_time: time
    festival: str | None = Field(default=None, description="Name of a festival this date falls on, if any.")


class ContentPost(BaseModel):
    date: date
    platform: str
    type: PostType
    caption: str
    hashtags: list[str] = Field(default_factory=list)
    reel_script: str | None = None
    carousel_slides: list[str] | None = None
    image_prompt: str
    cta: str
    post_time: time
