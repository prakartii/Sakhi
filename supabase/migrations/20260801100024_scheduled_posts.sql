-- =====================================================================
-- Migration 24: scheduled_posts
-- =====================================================================
-- New table, no existing table touched. Each row is one publishing
-- attempt: a content_calendar_items row queued to go out through a
-- specific social_media_connections account at a given time.
-- content_calendar_id and social_connection_id are both required — unlike
-- content_calendar_items.social_connection_id (nullable, content can be
-- planned before a connection exists), a *scheduled* post has nothing to
-- publish through without one.
--
-- Storage only: no platform API calls, no publishing happen as a result
-- of this table existing. published_url/provider_response/error_log are
-- populated by whatever future component actually attempts publishing —
-- this table only records what that component reports back.
-- =====================================================================

do $$ begin
  create type public.publishing_status_enum as enum (
    'queued', 'publishing', 'published', 'failed', 'cancelled'
  );
exception when duplicate_object then null; end $$;

create table if not exists public.scheduled_posts (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  content_calendar_id uuid not null references public.content_calendar_items (id) on delete cascade,
  social_connection_id uuid not null references public.social_media_connections (id) on delete cascade,
  scheduled_time timestamptz not null,
  publishing_status public.publishing_status_enum not null default 'queued',
  retry_count integer not null default 0,
  published_url text,
  provider_response jsonb,
  error_log text,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint chk_scheduled_posts_retry_count_non_negative check (retry_count >= 0)
);

create trigger trg_scheduled_posts_updated_at
  before update on public.scheduled_posts
  for each row execute function public.set_updated_at();

create index if not exists idx_scheduled_posts_business_profile
  on public.scheduled_posts (business_profile_id);
create index if not exists idx_scheduled_posts_content_calendar
  on public.scheduled_posts (content_calendar_id);
create index if not exists idx_scheduled_posts_social_connection
  on public.scheduled_posts (social_connection_id);
create index if not exists idx_scheduled_posts_status
  on public.scheduled_posts (publishing_status);
-- Primary queue-processing access pattern: "this business's pending items,
-- soonest first."
create index if not exists idx_scheduled_posts_business_profile_scheduled_time
  on public.scheduled_posts (business_profile_id, scheduled_time);

comment on table public.scheduled_posts is
  'Publishing queue/history for content_calendar_items — when, through which connection, and what happened. Storage only: no platform API calls, no publishing. A future publishing worker is the only intended writer of publishing_status/published_url/provider_response/error_log/published_at; this table just holds what it reports.';
comment on column public.scheduled_posts.retry_count is
  'Incremented each time a failed post is requeued via "Retry Failed Post." No cap enforced at this layer.';
comment on column public.scheduled_posts.provider_response is
  'Raw response captured from the platform API by whatever component actually publishes — opaque JSON, not interpreted by this table or its service.';
