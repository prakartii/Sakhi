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
│   ├── ai/                 Future home of LLM clients, prompt orchestration,
│   │                        embedding generation. Out of scope now — empty.
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
