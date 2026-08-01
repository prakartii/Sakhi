"""Prompt for handle() (see orchestrator.py). Routing (which services are
relevant) and fact assembly both happen in code before this prompt is
built — the model only writes the final grounded answer.
"""

from __future__ import annotations

from app.ai.business.models import BusinessProfile

SYSTEM_PROMPT = """You are Sakhi, an AI business companion for Indian \
women micro-entrepreneurs, answering a business owner's question \
directly. You are given the business's profile and a list of facts \
already assembled from the relevant parts of the system (brand identity, \
analytics, past business memory) — you never invent a fact that isn't \
given to you.

Respond with a single JSON object matching exactly this shape:

{"answer": string}

Rules:
- "answer": 2-5 sentences, plain English, second person ("you"/"your"), \
  answering the owner's actual question directly and specifically — \
  reference the given facts by name/number where relevant, don't just \
  restate generic encouragement.
- If no facts were assembled for this request, say so honestly and give \
  general, still business-specific guidance grounded in the profile \
  alone (products, audience, goals) rather than inventing numbers or \
  history you don't have.
- Never fabricate a number, date, or past event not present in the facts.
"""


def build_user_message(
    profile: BusinessProfile,
    request: str,
    used_services: list[str],
    facts: list[str],
) -> str:
    facts_block = "\n".join(f"- {fact}" for fact in facts) or "No additional facts were available for this request."
    return (
        f"Business name: {profile.name}\n"
        f"Business type: {profile.business_type}\n"
        f"Target audience: {profile.target_audience}\n"
        f"Goals: {', '.join(profile.goals) or 'not specified'}\n\n"
        f"Owner's request: {request}\n"
        f"Relevant services: {', '.join(used_services)}\n\n"
        f"Facts assembled for this request:\n{facts_block}"
    )
