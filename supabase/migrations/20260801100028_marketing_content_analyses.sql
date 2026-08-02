-- =====================================================================
-- Migration 28: Marketing Studio content analyses
-- =====================================================================
-- Backs the AI Marketing Studio's "analyze existing content" flow: a
-- business pastes/uploads a reel's caption, hashtags, engagement metrics,
-- sample comments and (optionally) a thumbnail image, and Sakhi returns a
-- structured analysis (virality score, product detection, comment
-- intelligence, hook/CTA/caption/thumbnail critique, recommendations,
-- alternate captions, next-reel ideas) — see app.ai.marketing.
--
-- Deliberately two jsonb blobs rather than ~15 separate columns: `analysis`
-- (everything about the content that was analyzed) and `reel_brief`
-- (Sakhi's suggested next reel — script, shot list, hashtags, CTA), same
-- "one flexible jsonb per generated artifact" pattern as
-- websites.content/scheduled_slots elsewhere in this schema. No raw image/
-- video bytes are stored — only the derived analysis, matching how voice
-- audio is processed in-memory and never archived (see voice_logs).
-- =====================================================================

do $$ begin
  create type public.marketing_analysis_source_type_enum as enum (
    'manual', 'screenshot', 'video_frame', 'link'
  );
exception when duplicate_object then null; end $$;

create table if not exists public.marketing_content_analyses (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles(id) on delete cascade,
  social_connection_id uuid references public.social_media_connections(id) on delete set null,
  source_type marketing_analysis_source_type_enum not null default 'manual',
  source_url text,
  caption text,
  hashtags text[] not null default '{}',
  comments_sample text[] not null default '{}',
  metrics jsonb not null default '{}'::jsonb,
  analysis jsonb,
  reel_brief jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on column public.marketing_content_analyses.metrics is
  'Caller-supplied engagement numbers (views/likes/comments/shares/saves) this analysis was based on.';
comment on column public.marketing_content_analyses.analysis is
  'Full structured AI analysis of the content — see app.ai.marketing.models.ContentAnalysis. Null until analysis completes.';
comment on column public.marketing_content_analyses.reel_brief is
  'Sakhi-generated brief for a future reel (script/shot list/hashtags/CTA) — see app.ai.marketing.models.ReelBrief. Null unless a brief was generated for this row.';

create index idx_marketing_content_analyses_business_profile
  on public.marketing_content_analyses (business_profile_id, created_at desc);
create index idx_marketing_content_analyses_social_connection
  on public.marketing_content_analyses (social_connection_id);

create trigger set_updated_at
  before update on public.marketing_content_analyses
  for each row execute function public.set_updated_at();
