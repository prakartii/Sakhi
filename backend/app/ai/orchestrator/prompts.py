"""Prompt for handle() (see orchestrator.py). Routing (which services are
relevant) and fact assembly both happen in code before this prompt is
built — the model only writes the final grounded answer.
"""

from __future__ import annotations

from app.ai.business.models import BusinessProfile

# BCP-47 codes this app's voice pipeline targets (see app.ai.voice) mapped
# to the language name the model should actually answer in. Text-only
# callers (Advisor chat) never pass a code and get the "en-IN" default.
LANGUAGE_NAMES: dict[str, str] = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "mr-IN": "Marathi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "pa-IN": "Punjabi",
    "as-IN": "Assamese",
    "od-IN": "Odia",
}

SYSTEM_PROMPT = """You are Sakhi, an AI business companion for Indian \
women micro-entrepreneurs, answering a business owner's question \
directly. You are given the business's profile and a list of facts \
already assembled from the relevant parts of the system (brand identity, \
analytics, past business memory) — you never invent a fact that isn't \
given to you.

Respond with a single JSON object matching exactly this shape:

{"answer": string}

Rules:
- "answer": 2-5 sentences, in the reply language stated below, second \
  person ("you"/"your"), answering the owner's actual question directly \
  and specifically — reference the given facts by name/number where \
  relevant, don't just restate generic encouragement.
- Write ONLY in the stated reply language — not a translation note, not \
  mixed with English unless that language naturally mixes English loan \
  words in everyday speech (e.g. Hindi commonly keeps English business \
  terms). Numbers, dates and product names may stay as given.
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
    *,
    language: str = "en-IN",
) -> str:
    facts_block = "\n".join(f"- {fact}" for fact in facts) or "No additional facts were available for this request."
    reply_language = LANGUAGE_NAMES.get(language, "English")
    return (
        f"Business name: {profile.name}\n"
        f"Business type: {profile.business_type}\n"
        f"Target audience: {profile.target_audience}\n"
        f"Goals: {', '.join(profile.goals) or 'not specified'}\n\n"
        f"Owner's request: {request}\n"
        f"Relevant services: {', '.join(used_services)}\n"
        f"Reply language: {reply_language}\n\n"
        f"Facts assembled for this request:\n{facts_block}"
    )
