-- =====================================================================
-- Migration 19: Enable pgvector, add memory_embeddings.embedding
-- =====================================================================
-- Migration 07 created memory_embeddings with its `embedding` column and
-- ANN index commented out, deferring both until the Business Memory
-- semantic-search feature (app.ai.embeddings) actually existed to use
-- them. That feature is now built — this migration enables the extension
-- and adds the column it was always designed for, without altering
-- migration 07 itself.
--
-- 1536 dimensions matches OpenAI text-embedding-3-small, the default
-- embedding model in app.ai.embeddings (see app/core/config.py's
-- EMBEDDING_DIM). Switching to a model with different dimensionality
-- later requires a new migration — pgvector columns are fixed-width.
-- =====================================================================

create extension if not exists vector;

alter table public.memory_embeddings
  add column if not exists embedding vector(1536);

comment on column public.memory_embeddings.embedding is
  'text-embedding-3-small vector (1536-dim), populated by app.ai.embeddings.embed_memory_content().';

-- ivfflat needs training data to be effective; lists = 100 is a reasonable
-- default for a table expected to stay in the tens-of-thousands-of-rows
-- range at this app's scale. Revisit `lists` if that assumption changes.
create index if not exists idx_memory_embeddings_vector
  on public.memory_embeddings
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
