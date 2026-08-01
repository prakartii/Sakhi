-- =====================================================================
-- Sakhi Database Schema
-- Migration 01: Extensions & shared helper functions
-- =====================================================================
-- Notes:
--   * pgcrypto / uuid-ossp give us gen_random_uuid() for UUID primary keys.
--   * pgvector is referenced (commented out) here so the extension is
--     provisioned in one obvious place once semantic search on
--     business_memory / conversation_history is built. Enabling it now
--     costs nothing and avoids a future migration just for the extension.
-- =====================================================================

create extension if not exists pgcrypto;
create extension if not exists "uuid-ossp";

-- Uncomment when embedding generation is wired up (see memory_embeddings table).
-- Supabase ships pgvector; this just needs enabling in the target project.
-- create extension if not exists vector;

-- ---------------------------------------------------------------------
-- Shared trigger function: keeps `updated_at` accurate on every UPDATE
-- without repeating application-side logic. Attached per-table below.
-- ---------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

comment on function public.set_updated_at() is
  'Generic BEFORE UPDATE trigger that stamps updated_at = now() on every row update.';
