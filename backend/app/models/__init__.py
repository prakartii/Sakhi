"""SQLAlchemy ORM models mapping to the Supabase schema.

Empty for now by design — the schema already exists in Supabase via the raw
SQL migrations in supabase/migrations/. Models are added here as each
feature's business logic is implemented; every model must be imported in
this file so Alembic's env.py (which imports app.models) can discover it
through Base.metadata.
"""
