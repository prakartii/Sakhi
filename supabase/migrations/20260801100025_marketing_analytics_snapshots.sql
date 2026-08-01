-- =====================================================================
-- Migration 25: marketing_analytics_snapshots
-- =====================================================================
-- New table, no existing table touched. Each row is one point-in-time
-- analytics reading for a business — optionally scoped to one connected
-- social account (social_connection_id, nullable: a snapshot can also
-- represent an aggregate across all of a business's platforms). No
-- platform column: when social_connection_id is set, the platform is
-- reachable via that connection; an aggregate snapshot has no single
-- platform to name.
--
-- Storage + simple SQL aggregation only. Nothing here calls a platform
-- API, and nothing here forecasts — the app.services.marketing_analytics
-- period views (daily/weekly/monthly/compare/summary) are sum/avg/count
-- over stored rows, computed in Postgres, not predicted.
-- =====================================================================

create table if not exists public.marketing_analytics_snapshots (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  social_connection_id uuid references public.social_media_connections (id) on delete set null,
  followers integer,
  reach integer,
  impressions integer,
  engagement integer,
  likes integer,
  comments integer,
  shares integer,
  saves integer,
  profile_visits integer,
  website_clicks integer,
  follower_growth integer,
  engagement_rate numeric(6, 3),
  captured_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_marketing_analytics_snapshots_updated_at
  before update on public.marketing_analytics_snapshots
  for each row execute function public.set_updated_at();

create index if not exists idx_marketing_analytics_snapshots_business_profile
  on public.marketing_analytics_snapshots (business_profile_id);
create index if not exists idx_marketing_analytics_snapshots_social_connection
  on public.marketing_analytics_snapshots (social_connection_id);
create index if not exists idx_marketing_analytics_snapshots_captured_at
  on public.marketing_analytics_snapshots (captured_at);
-- Primary access pattern: "this business's readings in [date range),
-- chronologically" — every daily/weekly/monthly/compare/summary query
-- filters and orders on exactly this pair.
create index if not exists idx_marketing_analytics_snapshots_business_profile_captured_at
  on public.marketing_analytics_snapshots (business_profile_id, captured_at);

comment on table public.marketing_analytics_snapshots is
  'Point-in-time social/marketing metrics for a business, optionally scoped to one connected account. All metric columns are nullable — different platforms/pulls report different subsets. Storage + simple aggregation only: no platform API calls, no AI, no forecasting.';
comment on column public.marketing_analytics_snapshots.follower_growth is
  'Net follower change the caller attributes to this snapshot (e.g. vs. the prior pull) — reported, not computed by this table.';
comment on column public.marketing_analytics_snapshots.engagement_rate is
  'Reported engagement rate as a percentage (e.g. 4.250 = 4.25%) — reported, not computed by this table.';
