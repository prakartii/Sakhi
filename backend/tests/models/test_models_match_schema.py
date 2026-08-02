"""Schema-coverage checks for app.models — no database connection used.

These parse supabase/migrations/*.sql directly (the single source of truth
per project convention) rather than hand-maintaining a duplicate table list,
so the check can't silently go stale as new migrations are added. If a
future migration adds a table with no matching model, or a model's
__tablename__ drifts from the table it's supposed to map, these tests fail.
"""

import re
from pathlib import Path

from sqlalchemy.orm import configure_mappers

import app.models as models_package
from app.db.base import Base

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "supabase" / "migrations"

_CREATE_TABLE_RE = re.compile(
    r"create table if not exists public\.([a-z_]+)", re.IGNORECASE
)


def _tables_declared_in_migrations() -> set[str]:
    sql = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(MIGRATIONS_DIR.glob("*.sql"))
    )
    return set(_CREATE_TABLE_RE.findall(sql))


def _tables_registered_on_metadata() -> set[str]:
    # Excludes schema-qualified entries (currently just "auth.users") — those
    # are external reference stubs for FK resolution, not tables this app
    # owns or maps a model to; see app/models/user.py.
    return {name for name in Base.metadata.tables if "." not in name}


def test_migrations_directory_is_found():
    assert MIGRATIONS_DIR.is_dir(), f"Expected migrations at {MIGRATIONS_DIR}"


def test_every_migrated_table_has_a_model():
    migrated = _tables_declared_in_migrations()
    modeled = _tables_registered_on_metadata()

    missing = migrated - modeled
    assert not missing, f"Tables with no SQLAlchemy model: {sorted(missing)}"


def test_no_model_maps_a_table_absent_from_migrations():
    migrated = _tables_declared_in_migrations()
    modeled = _tables_registered_on_metadata()

    extra = modeled - migrated
    assert (
        not extra
    ), f"Models mapping tables not found in any migration: {sorted(extra)}"


def test_all_29_feature_tables_are_modeled():
    # Pinned count as a tripwire: if this drifts, __all__ in
    # app/models/__init__.py and/or the migrations disagree about how many
    # tables exist — worth a human looking rather than silently passing.
    assert len(_tables_declared_in_migrations()) == 29
    assert len(models_package.__all__) == 29


def test_all_mappers_configure_without_error():
    """Forces resolution of every relationship()/back_populates pair and
    every string-based ForeignKey target. Import alone doesn't trigger this
    — SQLAlchemy resolves relationships lazily on first mapper use."""
    configure_mappers()
