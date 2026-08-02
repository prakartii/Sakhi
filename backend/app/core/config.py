"""Application settings, loaded once from the environment / .env file.

Uses pydantic-settings so every value is validated and type-checked at
startup — a missing or malformed DATABASE_URL fails fast instead of
surfacing as a confusing error on the first request.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

# ``env_file=".env"`` alone resolves relative to the process's current working
# directory, so it silently finds nothing (or the wrong file) depending on
# whether the app is started from the repo root or from backend/. Resolve
# both candidate locations from this file's own path instead, so startup is
# independent of cwd. Later paths override earlier ones for the same key, so
# a backend/.env (used by docker-compose) takes precedence over the repo
# root .env when both exist; pydantic-settings silently skips files that
# don't exist, so listing both is safe even if only one is present.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent
_ENV_FILES = (_REPO_ROOT / ".env", _BACKEND_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Sakhi API"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # --- CORS ---
    # Vite's dev server (via @lovable.dev/vite-tanstack-config's sandbox
    # port detection) falls back through 8080/8081/8082/... whenever the
    # preceding port is already taken, so localhost:5173 alone isn't
    # reliable for local dev — list the common fallbacks it actually lands
    # on instead of guessing one.
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8083",
        "http://localhost:3000",
    ]

    # --- Database (Supabase Postgres) ---
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # --- Supabase (service-level access, e.g. Storage — unused until a
    # feature needs it; kept here so it's configured in one place) ---
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    # --- Auth secret, stored but not wired up: authentication is out of
    # scope for this milestone. ---
    JWT_SECRET: str | None = None

    # --- AI provider (app.ai.providers) ---
    # AI_PROVIDER selects the implementation app.ai.providers.get_ai_provider()
    # returns; every call site codes against the AIProvider interface, so
    # switching to gemini/ollama later is a config change, not a call-site one.
    AI_PROVIDER: Literal["groq"] = "groq"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 1024
    # Vision-capable Groq model for app.ai.marketing's thumbnail/screenshot
    # analysis — a separate model from GROQ_MODEL above (text-only) since
    # not every model on Groq accepts image input.
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # --- Embedding provider (app.ai.embeddings) ---
    # Groq doesn't serve embedding models, so this is configured separately
    # from AI_PROVIDER above. EMBEDDING_DIM must match the fixed width of
    # memory_embeddings.embedding (see supabase/migrations/19) — changing
    # it requires a new migration, not just a settings change. Gemini is
    # the default: a genuinely free-tier API (Google AI Studio, no billing
    # setup) versus OpenAI's paid-only embeddings API — gemini-embedding-001
    # natively outputs 3072 dims but is truncated to EMBEDDING_DIM=1536 via
    # output_dimensionality (Matryoshka truncation), so no migration is
    # needed to match the existing column width.
    EMBEDDING_PROVIDER: Literal["gemini", "openai"] = "gemini"
    GEMINI_API_KEY: str | None = None
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    OPENAI_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # --- Image provider (app.ai.image) ---
    # Not an LLM call — a separate vendor/settings group from AI_PROVIDER.
    # FLUX.1-schnell-Free is Together's free-tier fast image model, good
    # enough for a demo; swap TOGETHER_IMAGE_MODEL for a paid one for
    # higher quality without touching code.
    IMAGE_PROVIDER: Literal["together"] = "together"
    TOGETHER_API_KEY: str | None = None
    TOGETHER_IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell-Free"

    # "Nano Banana" (Gemini 2.5 Flash Image) — a second, free-tier image
    # capability used specifically by Content Calendar and Marketing
    # Studio's reel-visual generation, alongside (not replacing)
    # IMAGE_PROVIDER above, which stays Together for Website Studio's hero
    # images. Reuses GEMINI_API_KEY (see the embedding provider settings).
    NANO_BANANA_MODEL: str = "gemini-2.5-flash-image"

    # --- Video provider (app.ai.video) ---
    # fal.ai: NOT free on an ongoing basis — a one-time signup credit
    # (~$10, roughly 50-100 generations on this model), then pay-per-
    # second. Every call through this provider is a real, billed request;
    # see app.ai.video's module docstring.
    VIDEO_PROVIDER: Literal["fal"] = "fal"
    FAL_API_KEY: str | None = None
    FAL_VIDEO_MODEL: str = "fal-ai/wan/v2.1/1.3b/text-to-video"

    # --- Voice provider (app.ai.voice) ---
    # Sarvam AI handles STT/TTS for Indian languages; Groq (AI_PROVIDER
    # above) remains the unchanged reasoning step — separate vendor/
    # settings group by design. VOICE_PROVIDER=browser is the fallback:
    # the Web Speech API handles STT client-side and sends text instead
    # of audio, guaranteeing a working demo path if Sarvam is slow/down.
    VOICE_PROVIDER: Literal["sarvam", "browser"] = "sarvam"
    SARVAM_API_KEY: str | None = None
    SARVAM_STT_MODEL: str = "saaras:v3"
    SARVAM_TTS_MODEL: str = "bulbul:v3"
    # "anushka" (a common Sarvam example speaker) is not in bulbul:v3's
    # speaker list — confirmed against the live API, which 400s on it.
    # "priya" is a valid bulbul:v3 speaker.
    SARVAM_TTS_SPEAKER: str = "priya"
    SARVAM_TIMEOUT_SECONDS: float = 15.0
    # Optional pivot: translate to English before Groq, then back before
    # TTS, for languages where Groq's own multilingual output is weak.
    # Default off — same-language round-trip is lower latency.
    VOICE_TRANSLATE_PIVOT: bool = False

    @property
    def sqlalchemy_database_uri(self) -> str:
        """DATABASE_URL rewritten for SQLAlchemy's async psycopg 3 dialect.

        Supabase issues standard ``postgresql://`` connection strings; psycopg 3
        (unlike asyncpg) parses libpq-style query params like ``sslmode``
        natively, so only the scheme needs rewriting — no query-string surgery.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def supabase_project_url(self) -> str | None:
        """SUPABASE_URL normalized to the bare project origin.

        The value in .env already has a `/rest/v1/` suffix baked in (a
        PostgREST base URL, not a project URL), so anything that needs a
        different Supabase API family — auth's `/auth/v1/...`, storage's
        `/storage/v1/...` — must not just string-concatenate onto it or it
        ends up with both suffixes stacked. Scheme + host is the only part
        guaranteed stable across API families.
        """
        if not self.SUPABASE_URL:
            return None
        parts = urlsplit(self.SUPABASE_URL)
        return f"{parts.scheme}://{parts.netloc}"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — usable as a FastAPI dependency and safe to
    override in tests via ``get_settings.cache_clear()``."""
    return Settings()


settings = get_settings()
