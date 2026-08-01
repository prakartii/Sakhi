"""Deterministic rules engine: a generic weighted-criteria DSL for scheme
eligibility, opportunity eligibility, and mentor-fit gating. No LLM
involvement — see engine.py's evaluate_criteria(). Its output feeds
app.ai.explanations via to_explanation_facts(), never generates prose.
"""

from app.ai.rules.engine import evaluate_criteria, to_explanation_facts
from app.ai.rules.schemas import Criterion, CriterionResult, MatchResult

__all__ = [
    "Criterion",
    "CriterionResult",
    "MatchResult",
    "evaluate_criteria",
    "to_explanation_facts",
]
