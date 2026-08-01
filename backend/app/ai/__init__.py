"""AI integration layer. Implements all four AI/ML components from the
tech stack doc:

- app.ai.providers    The `aiProvider` wrapper: a provider-agnostic chat
                       interface, wired to Groq by default and swappable to
                       Gemini/Ollama via settings.AI_PROVIDER. Callers
                       should depend on `get_ai_provider()` and
                       `AIProvider`, never on a concrete vendor SDK.
- app.ai.voice_parsing Turns a raw voice-check-in transcript into structured
                       business_memory candidates + sentiment, via the
                       provider's JSON mode. See parse_voice_transcript().
- app.ai.explanations  Turns facts already computed elsewhere (rules engine
                       match scores, forecast deltas, retrieval results)
                       into the "Why" / "Based on..." text shown on cards
                       across the frontend. See explain(). Never computes
                       the facts itself — only the prose.
- app.ai.forecasting   Deterministic run-rate / moving-average math — no
                       LLM involved. forecast_stockout() projects reorder
                       dates from inventory_movements consumption;
                       forecast_run_rate() projects trend for any periodic
                       series (cashflow, revenue). Feeds app.ai.explanations,
                       never the other way round.
- app.ai.rules         Deterministic weighted-criteria DSL for scheme /
                       opportunity eligibility and mentor-fit gating.
                       evaluate_criteria() scores facts against Criterion
                       rules (hard `required` vs soft weighted); its result
                       feeds app.ai.explanations via to_explanation_facts().
- app.ai.embeddings    Retrieval ML: chunks + embeds business_memory.content
                       (OpenAI text-embedding-3-small by default, via
                       get_embedding_provider()) for pgvector semantic
                       search — real RAG, not an LLM call. Needs migration
                       19 (enables the `vector` extension and
                       memory_embeddings.embedding). retrieve() runs the
                       actual ANN query in Postgres via pgvector's `<=>`
                       operator, given a caller-supplied AsyncSession — the
                       one place app.ai touches a database, and only that.
                       cosine_similarity/top_k_similar rank a smaller,
                       already-fetched candidate set in Python instead.

On top of those four, the generation layer (idea -> brand -> website ->
content -> growth) — each service takes a BusinessProfile (or a value
derived from one) and returns a typed Pydantic response, via the same
providers.get_ai_provider().chat_json():

- app.ai.business     BusinessProfile: the central "digital twin" object
                       every other generation service reads. See
                       parse_onboarding() — builds one from a free-text/
                       voice business description.
- app.ai.brand         Brand Studio. generate_brand(profile) -> BrandKit
                       (naming, voice, palette, typography, bios,
                       logo_prompt). logo_prompt feeds app.ai.image.
- app.ai.image         The one generation service that ISN'T an LLM call —
                       generate_image(prompt, kind, size) -> GeneratedImage,
                       via get_image_provider() (Together AI / FLUX by
                       default, settings.IMAGE_PROVIDER). Reuses
                       app.ai.providers.base's exception hierarchy, same
                       "an aiProvider call failed" rationale as embeddings.
- app.ai.website       Website Studio. generate_site(profile, brand) ->
                       WebsiteSpec (landing/about/products/contact/FAQ +
                       SEO). Conditioned on BOTH the profile and its
                       already-generated BrandKit, so copy reuses the
                       brand's tagline/mission/story/voice instead of
                       reinventing it.
- app.ai.content       Content Calendar. generate_calendar(profile, brand,
                       month, platforms) -> list[ContentPost]. Rules +
                       LLM, deliberately split in two: scheduler.py picks
                       dates/platforms/post-types/times/festival mix with
                       NO LLM involved (schedule_month() is independently
                       testable with no provider at all); generator.py
                       makes one chat_json() call to write copy for every
                       slot at once, in the brand's voice.
- app.ai.analytics     Analytics narration. summarize(profile, metrics) ->
                       AnalyticsSummary (narrative, highlights, top_actions).
                       Same rules-computes/LLM-narrates split as content:
                       facts.build_facts() reuses app.ai.forecasting
                       directly (revenue trend via forecast_run_rate,
                       stockout risk via forecast_stockout) and is
                       independently testable with no provider; the LLM
                       only turns those facts into prose, never computes
                       a number itself. `metrics: MetricsRows` stands in
                       for what a real aggregation layer would return —
                       assumes seeded data.
- app.ai.orchestrator  The router tying every service above into one
                       grounded answer. handle(request, profile, context)
                       -> OrchestratorResponse. router.route() decides
                       which services a free-text request needs — no
                       LLM, phrase-matching rules, independently testable
                       (e.g. "I need more sales" -> analytics + content +
                       brand). Code then assembles facts from whatever
                       context is relevant (context.brand, context.metrics
                       via app.ai.analytics.facts, and — if a session is
                       given — retrieved business_memory via
                       app.ai.embeddings.retrieve()); one chat_json() call
                       writes the final answer from those facts. `session`
                       is optional and the second (and last) place app.ai
                       touches a database, only via a caller-supplied
                       AsyncSession — omitting it just skips retrieval.

Separately, app.ai.voice is the speech layer wrapped *around* the above —
not a generation service itself, and not aware any of them exist:

- app.ai.voice         Swappable multilingual speech I/O. Sarvam AI (Saaras
                       v3 STT, Bulbul v3 TTS) by default via
                       get_voice_provider() (settings.VOICE_PROVIDER), with
                       a browser fallback (VOICE_PROVIDER=browser) that
                       passes through text the Web Speech API already
                       transcribed client-side — same VoiceProvider
                       interface either way. Pipeline this composes around
                       (unchanged): audio -> transcribe() -> text -> Groq
                       (app.ai.providers, untouched) -> text -> synthesize()
                       -> audio. should_pivot() is a pure rule deciding
                       whether a language should route through an English
                       translation pivot (SarvamVoiceProvider.translate())
                       before/after Groq — off by default for latency.
                       Nothing in app.ai.voice imports app.ai.providers or
                       any other app.ai service; it only knows audio <-> text.

Still open: SQLAlchemy models/repositories for any of this to persist
end-to-end, and the FastAPI endpoints that call into these modules — both
live outside app.ai as features get wired up beyond the pgvector round trip
that app.ai.embeddings.retrieve already proves. For app.ai.voice
specifically: no endpoint exists yet to actually receive audio from the
frontend, and no real SARVAM_API_KEY has been available to verify a live
transcribe/synthesize round-trip — only mocked-provider tests confirm the
wrapping logic today.
"""
