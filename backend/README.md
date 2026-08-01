# Sakhi Backend

FastAPI service skeleton for Sakhi. **Structure only** — no CRUD endpoints,
no business logic, no AI, no authentication are implemented yet. This
document explains what each folder is for and how to run what exists today.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 (async, psycopg 3) · Alembic ·
Pydantic v2 · Supabase Postgres.

## Folder responsibilities

```
backend/
├── app/
│   ├── main.py          FastAPI app factory: middleware, routers, /docs toggle.
│   ├── api/              HTTP layer only — routers translate HTTP ⇄ schemas ⇄ services.
│   │   ├── deps.py           Shared DI dependencies (get_db_session today; current-user,
│   │   │                     pagination, etc. later). Routers depend on this, not on
│   │   │                     app.db directly, so the DI surface stays stable.
│   │   ├── health.py         GET /health — unversioned infra endpoint.
│   │   └── v1/                Versioned public API.
│   │       ├── router.py         Aggregates all v1 endpoint routers (empty for now).
│   │       └── endpoints/        One module per resource, added as features land.
│   ├── core/              App-wide config, logging — no DB or HTTP code.
│   │   ├── config.py          Settings (pydantic-settings), loaded once from .env.
│   │   ├── settings.py        Conventional-name re-export of config.py's Settings.
│   │   └── logging.py         setup_logging() / get_logger() — call once at startup.
│   ├── db/                Database wiring, nothing feature-specific.
│   │   ├── base.py            Declarative Base every ORM model inherits from.
│   │   └── session.py         Async engine + session factory + get_db() dependency.
│   ├── models/             SQLAlchemy ORM models mapping to the Supabase schema.
│   │                        Empty — the schema already exists via supabase/migrations/
│   │                        raw SQL. Add models here as each feature is implemented.
│   │   └── mixins.py          UUIDPrimaryKeyMixin / TimestampMixin matching the
│   │                          schema's id/created_at/updated_at convention.
│   ├── schemas/            Pydantic v2 request/response DTOs. Kept separate from
│   │                        models so the API contract and storage shape evolve
│   │                        independently. Empty until endpoints exist.
│   ├── repositories/       Data-access layer, one repository per aggregate.
│   │   └── base.py            Generic BaseRepository — construction only, no
│   │                          query methods yet.
│   ├── services/           Business logic layer. Routers call services; services
│   │                        call repositories; services never touch AsyncSession
│   │                        directly. Empty until business logic is implemented.
│   ├── ai/                 AI integration layer — the four AI/ML components,
│   │   │                    plus the generation layer built on top of them
│   │   │                    (idea -> brand -> website -> content -> growth).
│   │   ├── providers/          Provider-agnostic `AIProvider` chat interface
│   │   │                        (Groq by default), via get_ai_provider().
│   │   ├── voice_parsing/      Transcript -> structured business_memory
│   │   │                        candidates + sentiment (chat_json).
│   │   ├── explanations/       Facts computed elsewhere -> "Why"/"Based on"
│   │   │                        prose for frontend cards (chat_json).
│   │   ├── forecasting/        Deterministic run-rate/moving-average math:
│   │   │                        stockout dates, cashflow/revenue trend.
│   │   ├── rules/               Deterministic weighted-criteria DSL: scheme/
│   │   │                        opportunity eligibility, mentor-fit gating.
│   │   ├── embeddings/          Chunk + embed business_memory.content
│   │   │                        (OpenAI text-embedding-3-small by default,
│   │   │                        get_embedding_provider()) for pgvector
│   │   │                        semantic search — needs migration 19.
│   │   ├── business/            BusinessProfile — the central "digital
│   │   │                        twin" every generation service reads.
│   │   │                        parse_onboarding() builds one from a
│   │   │                        free-text/voice description.
│   │   ├── brand/                Brand Studio: generate_brand(profile) ->
│   │   │                        BrandKit (naming, voice, palette,
│   │   │                        typography, bios, logo_prompt).
│   │   ├── image/                generate_image(prompt, kind, size) ->
│   │   │                        GeneratedImage — the one generation
│   │   │                        service that isn't an LLM call, via
│   │   │                        get_image_provider() (Together AI/FLUX by
│   │   │                        default, settings.IMAGE_PROVIDER).
│   │   ├── website/              generate_site(profile, brand) ->
│   │   │                        WebsiteSpec (landing/about/products/
│   │   │                        contact/FAQ + SEO) — conditioned on both
│   │   │                        the profile and its BrandKit.
│   │   ├── content/              generate_calendar(profile, brand, month,
│   │   │                        platforms) -> list[ContentPost]. Rules +
│   │   │                        LLM split in two: scheduler.py picks
│   │   │                        dates/platforms/types/times/festivals
│   │   │                        with no LLM; generator.py writes copy for
│   │   │                        every slot in one chat_json() call.
│   │   ├── analytics/            summarize(profile, metrics) ->
│   │   │                        AnalyticsSummary. Same rules/LLM split:
│   │   │                        facts.py reuses app.ai.forecasting
│   │   │                        directly (revenue trend, stockout risk),
│   │   │                        no LLM; summarizer.py only narrates.
│   │   ├── orchestrator/         handle(request, profile, context) ->
│   │   │                        OrchestratorResponse — the router tying
│   │   │                        every service above together. router.py
│   │   │                        decides which services a request needs
│   │   │                        (no LLM, phrase rules); code assembles
│   │   │                        brand/analytics/retrieved-memory facts;
│   │   │                        one chat_json() call answers from them.
│   │   └── voice/                 Swappable speech I/O wrapped AROUND the
│   │                            above (not a generation service, not
│   │                            aware they exist): transcribe()/
│   │                            synthesize() via get_voice_provider()
│   │                            (Sarvam AI by default, settings.
│   │                            VOICE_PROVIDER) or a browser_provider.py
│   │                            fallback that passes through text the Web
│   │                            Speech API already transcribed
│   │                            client-side. should_pivot() is a pure
│   │                            rule for an optional English-translation
│   │                            pivot around Groq (off by default).
│   │                            Callers everywhere depend on each
│   │                            subpackage's interface, never a vendor SDK
│   │                            directly.
│   ├── middleware/          ASGI middleware.
│   │   └── logging.py          Per-request method/path/status/duration + request-id.
│   ├── utils/               Small stateless helpers shared across layers. Empty —
│   │                        not pre-populated with speculative code.
│   ├── scheduler/           Future background/cron jobs (re-matching, forecasts,
│   │                        digests). No scheduler library wired up yet.
│   └── crawlers/            Future ingestion jobs for the government_schemes /
│                            opportunities catalog tables. Empty.
├── alembic/                Migration environment for future SQLAlchemy-model-driven
│   ├── env.py                 schema changes. Configured for SQLAlchemy 2.0 async,
│   └── versions/               reads the DB URL from app.core.config.settings.
├── tests/                  Pytest suite, mirrors app/ layout as it grows.
│   ├── conftest.py            Shared fixtures (in-process ASGI HTTP client).
│   └── test_health.py         Smoke test for GET /health.
├── requirements.txt        Runtime dependencies.
├── requirements-dev.txt    + testing/linting, layered on top of requirements.txt.
├── Dockerfile               Multi-stage, non-root runtime user, gunicorn+uvicorn workers.
├── docker-compose.yml       Local dev orchestration (API only — DB is Supabase-hosted).
└── .env.example             Template for backend/.env (never committed).
```

## Why the Supabase schema doesn't have models yet

`supabase/migrations/` already created and pushed the full schema as raw SQL.
`app/models/` is intentionally empty: adding SQLAlchemy models is itself
schema-adjacent business logic, out of scope for this skeleton. When models
are added later, run `alembic stamp head` once they match the existing
schema — otherwise Alembic will try to `CREATE TABLE` things that already
exist in Supabase.

## Local setup

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements-dev.txt

cp .env.example .env            # then fill in DATABASE_URL etc. (same values as the repo-root .env)

uvicorn app.main:app --reload   # http://localhost:8000/health
```

## Tests

```bash
pytest
```

## Docker

```bash
docker compose up --build       # reads backend/.env, hot-reloads app/ and alembic/
```

## Alembic (once models exist)

```bash
alembic revision --autogenerate -m "add business_profiles model"
alembic upgrade head
```
