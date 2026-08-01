"""Async SQLAlchemy engine and session factory.

One process-wide engine (connection-pooled) is created at import time;
get_db() hands out a scoped AsyncSession per request via FastAPI's
dependency injection and guarantees it's closed afterward.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.sqlalchemy_database_uri,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # recycles dead connections instead of surfacing them as request errors
)

SessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped AsyncSession."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
