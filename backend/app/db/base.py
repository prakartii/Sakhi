"""Shared SQLAlchemy declarative base.

Every ORM model in app.models must inherit from this Base so that:
  * Base.metadata is the single source of truth Alembic's env.py
    autogenerates migrations against.
  * all models share the same mapper registry / configuration.

This module intentionally defines nothing beyond the base class — table
models are added under app.models as business logic is implemented.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
