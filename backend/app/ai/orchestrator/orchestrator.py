"""The orchestrator: handle() is the single entry point that makes all
six generation services feel like one AI. Routing (router.route(), no
LLM) decides which services a request needs; code assembles facts from
whatever context is available (brand kit, analytics metrics via
app.ai.analytics.facts, retrieved business_memory via
app.ai.embeddings.retrieve); one chat_json() call then writes a grounded
answer from those facts — the model never invents a fact itself.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.analytics.facts import build_facts
from app.ai.business.models import BusinessProfile
from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.embeddings.retrieve import retrieve
from app.ai.orchestrator.models import OrchestratorContext, OrchestratorResponse
from app.ai.orchestrator.prompts import SYSTEM_PROMPT, build_user_message
from app.ai.orchestrator.router import route
from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider

DEFAULT_MEMORY_TOP_K = 3


class _AnswerOnly(BaseModel):
    answer: str


async def handle(
    request: str,
    profile: BusinessProfile,
    context: OrchestratorContext | None = None,
    *,
    session: AsyncSession | None = None,
    top_k_memories: int = DEFAULT_MEMORY_TOP_K,
    provider: AIProvider | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> OrchestratorResponse:
    """Answer `request` for `profile`, grounded in whatever's available.

    `context.brand`/`context.metrics` are consulted only if the router
    decides they're relevant to `request` (see router.route()) — the
    orchestrator never regenerates a brand kit or re-crunches metrics
    itself, it only reads what's already been generated elsewhere.

    `session`, if given, retrieves the top `top_k_memories` relevant
    business_memory chunks via app.ai.embeddings.retrieve() — the one
    place this touches a database, and only via a caller-supplied
    AsyncSession. Retrieval is skipped entirely (empty `sources`) when no
    session is given, so this remains fully testable without a database.

    Raises ValueError on an empty request. Raises AIProviderResponseError
    if the model's output doesn't match the expected schema.
    """
    if not request.strip():
        raise ValueError("request must not be empty")

    context = context or OrchestratorContext()
    used_services = route(request)

    facts: list[str] = []
    sources: list[str] = []

    if "brand" in used_services and context.brand is not None:
        facts.append(f"Brand tagline: {context.brand.tagline}")
        facts.append(f"Brand mission: {context.brand.mission}")
        facts.append(f"Brand voice: {context.brand.voice.tone}")

    if "analytics" in used_services and context.metrics is not None:
        facts.extend(build_facts(context.metrics))

    if session is not None:
        retrieved = await retrieve(
            session,
            request,
            k=top_k_memories,
            business_profile_id=profile.id,
            provider=embedding_provider,
        )
        for memory in retrieved:
            facts.append(f"Past memory: {memory.content}")
            sources.append(memory.content)

    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(profile, request, used_services, facts)},
    ]

    raw = await ai.chat_json(messages, temperature=0.4)
    try:
        parsed = _AnswerOnly.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Orchestrator answer failed schema validation: {exc}"
        ) from exc

    return OrchestratorResponse(answer=parsed.answer, used_services=used_services, sources=sources)
