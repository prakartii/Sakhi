"""Pydantic schemas for the rules engine: a small, generic criteria DSL used
to gate/score scheme, opportunity, and mentor matches against a business's
facts. See engine.py for the evaluator.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Operator = Literal["eq", "ne", "gte", "lte", "gt", "lt", "in", "not_in", "overlaps", "exists"]


class Criterion(BaseModel):
    """One rule: compare `field` (a key into the facts dict passed to
    evaluate_criteria) against `value` using `operator`.

    `required=True` means failing this criterion makes the subject
    ineligible outright (MatchResult.is_eligible=False), no matter how well
    other criteria score. `required=False` criteria only affect the
    weighted score — for "would qualify better if X" near-misses, like
    Stand-Up India's 61% match in schemes.tsx: the business passes the
    required women-led check but fails a soft ticket-size criterion, so
    it's still surfaced, just scored lower.
    """

    field: str
    operator: Operator
    value: Any = None
    weight: float = Field(default=1.0, gt=0)
    required: bool = False
    label: str = Field(
        ...,
        description="Human-readable description of what this criterion checks, "
        "used to build match_reason facts for app.ai.explanations.",
    )


class CriterionResult(BaseModel):
    criterion: Criterion
    met: bool
    actual_value: Any = None


class MatchResult(BaseModel):
    match_score: float = Field(..., ge=0, le=100)
    is_eligible: bool
    met: list[CriterionResult] = Field(default_factory=list)
    unmet: list[CriterionResult] = Field(default_factory=list)
