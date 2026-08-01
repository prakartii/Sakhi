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

Still open: SQLAlchemy models/repositories for any of this to persist
end-to-end, and the FastAPI endpoints that call into these modules — both
live outside app.ai as features get wired up beyond the pgvector round trip
that app.ai.embeddings.retrieve already proves.
"""
