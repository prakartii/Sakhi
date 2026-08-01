-- =====================================================================
-- Migration 07: business_memory, memory_embeddings
-- =====================================================================
-- business_memory is the durable, structured "facts the AI knows about
-- this business" store — the whole point of the Business Memory
-- feature. memory_embeddings is a child table holding one row per
-- text chunk + vector, so long memory entries can be split into
-- multiple embeddable chunks (standard RAG chunking pattern) without
-- denormalizing the embedding onto business_memory itself.
-- =====================================================================

create table if not exists public.business_memory (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  source_voice_log_id uuid references public.voice_logs (id) on delete set null,
  memory_type public.memory_type_enum not null default 'note',
  title varchar(200),
  content text not null,
  source public.memory_source_enum not null default 'manual',
  importance_score smallint not null default 3, -- 1 (trivial) - 5 (critical), used to rank recall/context-window inclusion
  is_archived boolean not null default false,
  occurred_at timestamptz,  -- when the fact/event happened, if different from when it was recorded
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint chk_business_memory_importance check (importance_score between 1 and 5)
);

create trigger trg_business_memory_updated_at
  before update on public.business_memory
  for each row execute function public.set_updated_at();

create index if not exists idx_business_memory_business_profile
  on public.business_memory (business_profile_id, created_at desc);
create index if not exists idx_business_memory_type on public.business_memory (memory_type);
create index if not exists idx_business_memory_active
  on public.business_memory (business_profile_id) where is_archived = false;
create index if not exists idx_business_memory_source_voice_log on public.business_memory (source_voice_log_id);

comment on table public.business_memory is
  'Structured long-term memory the AI companion has about a business (facts, goals, milestones, decisions). Core of the Business Memory feature.';

-- ---------------------------------------------------------------------
-- memory_embeddings: prepared for pgvector, kept as a separate table so
-- a single business_memory row can map to N chunks (long content gets
-- split for embedding) and so the heavy vector column never bloats the
-- business_memory table's own row size or its non-vector indexes.
--
-- IMPORTANT: the `embedding` column is commented out below because the
-- `vector` extension is not enabled by default (see migration 01).
-- Once `create extension vector;` has been run, uncomment the column
-- and the ivfflat index, matching the embedding_dim you standardize on
-- (1536 for OpenAI text-embedding-3-small, 768 for many open models).
-- ---------------------------------------------------------------------
create table if not exists public.memory_embeddings (
  id uuid primary key default gen_random_uuid(),
  business_memory_id uuid not null references public.business_memory (id) on delete cascade,
  chunk_index integer not null default 0,
  chunk_text text not null,
  -- embedding vector(1536),
  embedding_model varchar(100),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_memory_embeddings_chunk unique (business_memory_id, chunk_index)
);

create trigger trg_memory_embeddings_updated_at
  before update on public.memory_embeddings
  for each row execute function public.set_updated_at();

create index if not exists idx_memory_embeddings_business_memory on public.memory_embeddings (business_memory_id);

-- Once pgvector + the embedding column are enabled, add an ANN index, e.g.:
-- create index idx_memory_embeddings_vector on public.memory_embeddings
--   using ivfflat (embedding vector_cosine_ops) with (lists = 100);

comment on table public.memory_embeddings is
  'Chunked vector embeddings of business_memory content, for future semantic search / RAG. Vector column intentionally left commented until pgvector is enabled.';
