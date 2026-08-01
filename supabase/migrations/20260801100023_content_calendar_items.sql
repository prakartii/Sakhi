-- =====================================================================
-- Migration 23: content_calendar_items
-- =====================================================================
-- New table, no existing table touched. Each row is one planned piece of
-- content for one business; social_connection_id optionally ties it to an
-- authenticated platform connection (social_media_connections, migration
-- 22) but is nullable — content can be planned before an account is
-- connected. Storage only: no AI generation happens as a result of this
-- table existing, and nothing here publishes to a platform.
-- =====================================================================

do $$ begin
  create type public.content_type_enum as enum (
    'post', 'story', 'reel', 'carousel', 'video'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.content_status_enum as enum (
    'draft', 'scheduled', 'published', 'failed', 'cancelled'
  );
exception when duplicate_object then null; end $$;

create table if not exists public.content_calendar_items (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  social_connection_id uuid references public.social_media_connections (id) on delete set null,
  title varchar(200) not null,
  content_type public.content_type_enum not null,
  platform public.social_media_platform_enum not null,
  caption text,
  hashtags text[],
  image_prompt text,
  call_to_action varchar(200),
  scheduled_datetime timestamptz,
  status public.content_status_enum not null default 'draft',
  ai_generated boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_content_calendar_items_updated_at
  before update on public.content_calendar_items
  for each row execute function public.set_updated_at();

create index if not exists idx_content_calendar_items_business_profile
  on public.content_calendar_items (business_profile_id);
create index if not exists idx_content_calendar_items_social_connection
  on public.content_calendar_items (social_connection_id);
create index if not exists idx_content_calendar_items_status
  on public.content_calendar_items (status);
create index if not exists idx_content_calendar_items_platform
  on public.content_calendar_items (platform);
-- Primary calendar access pattern: "this business's items in [date range)",
-- optionally further filtered by status/platform in the query itself.
create index if not exists idx_content_calendar_items_business_profile_scheduled
  on public.content_calendar_items (business_profile_id, scheduled_datetime);

comment on table public.content_calendar_items is
  'Planned social content for a business — caption, hashtags, scheduling, and lifecycle status. Storage only: no AI generation, no publishing. social_connection_id is optional and nullable (content can be planned before a platform account is connected).';
comment on column public.content_calendar_items.ai_generated is
  'Metadata flag set by the caller (e.g. a future AI captioning feature) to mark that caption/image_prompt originated from AI. Set/read only — this table never generates content itself.';
comment on column public.content_calendar_items.status is
  'draft / scheduled / published / failed / cancelled. published/failed are set by whatever future component actually publishes content — nothing in this module changes status as a side effect of publishing, because nothing in this module publishes.';
