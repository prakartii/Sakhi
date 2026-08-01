"""Pydantic schemas for "Why" explanation generation.

Shapes the output for the Why/Basis card pattern used throughout the
frontend (see src/components/sakhi/Cards.tsx's Why/Basis, and every routes/*
that renders a match, alert, or insight card).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExplanationRequest(BaseModel):
    """Input to explain(). `facts` must already be computed by the rules
    engine / forecasting layer / retrieval step — the model is only allowed
    to cite what's listed here, never invent a number or date itself."""

    subject: str = Field(
        ...,
        description="What is being explained, e.g. '92% match with PM Vishwakarma' "
        "or 'Reorder alert for Indigo dye'.",
    )
    facts: list[str] = Field(
        ...,
        min_length=1,
        description="Pre-computed facts the explanation may cite (numbers, dates, "
        "comparisons), in priority order.",
    )
    basis_period: str | None = Field(
        default=None,
        description="Timeframe the facts were drawn from, e.g. 'the past 8 weeks'. "
        "Used to compose the basis line; omit for a generic fallback.",
    )


class Explanation(BaseModel):
    why: str
    basis: str
