"""Deterministic intent routing: decides which generation services a
free-text request is relevant to. No LLM — phrase-matching rules only,
same "rules decide structure" principle as app.ai.content.scheduler and
app.ai.analytics.facts. Independently testable with no provider at all.
"""

from __future__ import annotations

# Checked in order; a request can match more than one rule (e.g. "I need
# more sales" matches the growth rule, pulling in three services at once —
# that's what makes the orchestrator feel like one AI instead of a menu).
_INTENT_RULES: list[tuple[list[str], list[str]]] = [
    (
        [
            "more sales",
            "increase sales",
            "boost sales",
            "grow my sales",
            "more customers",
            "grow my business",
        ],
        ["analytics", "content", "brand"],
    ),
    (
        ["logo", "brand name", "tagline", "brand voice", "brand identity", "colors", "palette"],
        ["brand"],
    ),
    (["website", "landing page", "online store", "web page"], ["website"]),
    (
        ["post", "instagram", "caption", "reel", "content calendar", "social media", "hashtags"],
        ["content"],
    ),
    (
        ["revenue", "sales report", "performance", "how am i doing", "my numbers", "profit"],
        ["analytics"],
    ),
]

_DEFAULT_SERVICES = ["analytics"]


def route(request: str) -> list[str]:
    """Return which generation services `request` is relevant to, in
    first-matched order with no duplicates. Falls back to
    `_DEFAULT_SERVICES` if nothing matches — a general "how's my business
    doing" default is reasonable for an otherwise-unclassifiable request.
    """
    lowered = request.lower()
    services: list[str] = []
    for phrases, mapped_services in _INTENT_RULES:
        if any(phrase in lowered for phrase in phrases):
            for service in mapped_services:
                if service not in services:
                    services.append(service)
    return services or list(_DEFAULT_SERVICES)
