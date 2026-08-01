-- =====================================================================
-- Migration 08: conversation_history
-- =====================================================================
-- Append-only log of every turn in an AI conversation (text or voice).
-- session_id groups turns into one thread; a business can have many
-- sessions over time. Optionally links back to the voice_log that
-- produced a turn, and to a business_memory row the turn gave rise to.
-- =====================================================================

create table if not exists public.conversation_history (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  user_id uuid not null references public.users (id) on delete cascade,
  session_id uuid not null default gen_random_uuid(),
  role public.conversation_role_enum not null,
  message_type public.conversation_message_type_enum not null default 'text',
  content text not null,
  related_voice_log_id uuid references public.voice_logs (id) on delete set null,
  related_memory_id uuid references public.business_memory (id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_conversation_history_updated_at
  before update on public.conversation_history
  for each row execute function public.set_updated_at();

create index if not exists idx_conversation_history_session
  on public.conversation_history (session_id, created_at);
create index if not exists idx_conversation_history_business_profile
  on public.conversation_history (business_profile_id, created_at desc);
create index if not exists idx_conversation_history_related_memory
  on public.conversation_history (related_memory_id);

comment on table public.conversation_history is
  'Turn-by-turn AI conversation log, grouped by session_id. Feeds business_memory extraction and gives the companion short-term context.';
