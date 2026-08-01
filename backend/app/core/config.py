"""Application settings, loaded once from the environment / .env file.

Uses pydantic-settings so every value is validated and type-checked at
startup — a missing or malformed DATABASE_URL fails fast instead of
surfacing as a confusing error on the first request.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

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

    # --- Embedding provider (app.ai.embeddings) ---
    # Groq doesn't serve embedding models, so this is configured separately
    # from AI_PROVIDER above. EMBEDDING_DIM must match the fixed width of
    # memory_embeddings.embedding (see supabase/migrations/19) — changing
    # it requires a new migration, not just a settings change.
    EMBEDDING_PROVIDER: Literal["openai"] = "openai"
    OPENAI_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

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


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — usable as a FastAPI dependency and safe to
    override in tests via ``get_settings.cache_clear()``."""
    return Settings()


settings = get_settings()
