"""Generic rules-engine evaluator: scores a set of facts against a list of
Criterion rules. Deterministic, no LLM — same "the LLM never does the math"
principle as app.ai.forecasting. Feeds app.ai.explanations via
to_explanation_facts(); never generates prose itself.
"""

from __future__ import annotations

from typing import Any

from app.ai.rules.schemas import Criterion, CriterionResult, MatchResult


def evaluate_criteria(facts: dict[str, Any], criteria: list[Criterion]) -> MatchResult:
    """Evaluate every criterion in `criteria` against `facts` and produce a
    weighted match score plus an eligibility gate.

    `match_score` is 100 * (weight of met criteria) / (total weight) —
    partial credit for soft criteria regardless of eligibility. The subject
    is `is_eligible` only if every `required=True` criterion is met; a
    failed non-required criterion lowers the score but doesn't exclude it.
    A field missing from `facts` is treated the same as an explicit `None`
    — unmet for every operator except nothing (there's no "unknown" state).
    """
    if not criteria:
        return MatchResult(match_score=0.0, is_eligible=True)

    met: list[CriterionResult] = []
    unmet: list[CriterionResult] = []
    is_eligible = True

    for criterion in criteria:
        actual = facts.get(criterion.field)
        satisfied = _evaluate(criterion.operator, actual, criterion.value)
        result = CriterionResult(criterion=criterion, met=satisfied, actual_value=actual)
        if satisfied:
            met.append(result)
        else:
            unmet.append(result)
            if criterion.required:
                is_eligible = False

    total_weight = sum(c.weight for c in criteria)
    met_weight = sum(r.criterion.weight for r in met)
    match_score = round((met_weight / total_weight) * 100, 2) if total_weight else 0.0

    return MatchResult(match_score=match_score, is_eligible=is_eligible, met=met, unmet=unmet)


def _evaluate(operator: str, actual: Any, expected: Any) -> bool:
    if operator == "exists":
        return actual is not None
    if actual is None:
        return False  # every other operator needs a real value to compare
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "gte":
        return actual >= expected
    if operator == "lte":
        return actual <= expected
    if operator == "gt":
        return actual > expected
    if operator == "lt":
        return actual < expected
    if operator == "in":
        return actual in expected
    if operator == "not_in":
        return actual not in expected
    if operator == "overlaps":
        return bool(set(actual) & set(expected))
    raise ValueError(f"Unknown operator: {operator!r}")


def to_explanation_facts(result: MatchResult, *, include_unmet: bool = True) -> list[str]:
    """Turn a MatchResult into fact strings ready for
    app.ai.explanations.ExplanationRequest.facts — the rules engine
    computes what's true, app.ai.explanations turns it into prose."""
    facts = [r.criterion.label for r in result.met]
    if include_unmet:
        for r in result.unmet:
            prefix = "Missing" if r.criterion.required else "Not yet"
            facts.append(f"{prefix}: {r.criterion.label}")
    return facts
