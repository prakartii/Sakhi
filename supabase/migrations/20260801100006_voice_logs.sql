-- =====================================================================
-- Migration 06: voice_logs
-- =====================================================================
-- One row per voice check-in recording. Audio itself lives in Supabase
-- Storage (bucket path stored here, not the binary). Created before
-- business_memory / conversation_history so both can reference back to
-- the voice_log that originated them without a circular dependency.
-- =====================================================================

create table if not exists public.voice_logs (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  user_id uuid not null references public.users (id) on delete cascade,
  language_id uuid references public.languages (id) on delete set null,
  audio_storage_path text not null,     -- Supabase Storage object path, e.g. 'voice-checkins/<uuid>.m4a'
  duration_seconds integer,
  transcript text,
  transcript_confidence numeric(5, 4),  -- 0.0000 - 1.0000
  sentiment varchar(20),                -- 'positive' | 'neutral' | 'negative' | 'mixed' (free text, not enum: sentiment taxonomy is AI-model-owned)
  status public.voice_log_status_enum not null default 'pending',
  recorded_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_voice_logs_updated_at
  before update on public.voice_logs
  for each row execute function public.set_updated_at();

create index if not exists idx_voice_logs_business_profile on public.voice_logs (business_profile_id, recorded_at desc);
create index if not exists idx_voice_logs_user on public.voice_logs (user_id);
create index if not exists idx_voice_logs_status on public.voice_logs (status) where status in ('pending', 'processing');

comment on table public.voice_logs is
  'Raw voice check-in recordings + their transcripts. Source of truth for the Voice Check-ins feature; business_memory rows may cite a voice_log as their origin.';
