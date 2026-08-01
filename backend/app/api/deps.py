"""Shared FastAPI dependencies, imported by routers as `Depends(...)`.

Routers should import from here rather than reaching into app.db.session
directly, so the DI surface stays stable even if the underlying session
implementation changes. Future shared dependencies (current-user resolution,
pagination params, etc.) are added here as they're needed.
"""

from app.db.session import get_db as get_db_session

__all__ = ["get_db_session"]
