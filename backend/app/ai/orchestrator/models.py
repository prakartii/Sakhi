"""Pydantic schema for the orchestrator — the router tying every
generation service together into one grounded answer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.ai.analytics.models import MetricsRows
from app.ai.brand.models import BrandKit


class OrchestratorContext(BaseModel):
    """Already-generated artifacts the orchestrator can draw on for this
    business, so it never regenerates a brand kit or re-crunches metrics
    from scratch on every request — callers pass in whatever's already
    available (or omit what isn't)."""

    brand: BrandKit | None = None
    metrics: MetricsRows | None = None


class OrchestratorResponse(BaseModel):
    answer: str
    used_services: list[str] = Field(default_factory=list)
    sources: list[str] = Field(
        default_factory=list, description="Retrieved business_memory snippets the answer drew on, if any."
    )
