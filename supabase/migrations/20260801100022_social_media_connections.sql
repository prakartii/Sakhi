-- =====================================================================
-- Migration 22: social_media_connections
-- =====================================================================
-- New table, no existing table touched. Distinct from the plain
-- instagram_url/facebook_url/linkedin_url text columns already on
-- business_profiles (added by migration 19) — those are just profile
-- links; this table stores *authenticated* platform connections (OAuth
-- tokens, sync state) a business has actually gone through a connect flow
-- for. A business can connect each supported platform at most once — the
-- unique constraint below lets "connect" be an idempotent
-- connect-or-reconnect rather than accumulating duplicate rows for the
-- same platform.
--
-- Storage only: no platform API calls, no post publishing happen as a
-- result of this table existing. access_token/refresh_token are stored as
-- opaque text; app.services.social_media_connection is the single place
-- that reads/writes them, so encrypting them at rest later is a service-
-- layer change, not a schema or router change.
-- =====================================================================

do $$ begin
  create type public.social_media_platform_enum as enum (
    'instagram', 'linkedin', 'facebook', 'pinterest'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.social_connection_status_enum as enum (
    'connected', 'disconnected', 'expired', 'error'
  );
exception when duplicate_object then null; end $$;

create table if not exists public.social_media_connections (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  platform public.social_media_platform_enum not null,
  account_name varchar(200),
  account_id varchar(200),
  profile_url text,
  access_token text,
  refresh_token text,
  token_expiry timestamptz,
  connection_status public.social_connection_status_enum not null default 'connected',
  last_sync timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_social_media_connections_business_profile_platform
    unique (business_profile_id, platform)
);

create trigger trg_social_media_connections_updated_at
  before update on public.social_media_connections
  for each row execute function public.set_updated_at();

create index if not exists idx_social_media_connections_business_profile
  on public.social_media_connections (business_profile_id);
create index if not exists idx_social_media_connections_status
  on public.social_media_connections (connection_status);

comment on table public.social_media_connections is
  'Authenticated social platform connections (OAuth-style tokens + sync state) for a business — distinct from business_profiles.instagram_url/facebook_url/linkedin_url, which are plain profile links. Storage only: no platform API calls, no post publishing.';
comment on column public.social_media_connections.access_token is
  'Opaque provider access token. Only app.services.social_media_connection reads/writes this column — encrypting it at rest later is a service-layer change.';
comment on column public.social_media_connections.refresh_token is
  'Opaque provider refresh token, same access discipline as access_token.';
comment on column public.social_media_connections.connection_status is
  'connected / disconnected / expired / error. disconnect() clears access_token/refresh_token/token_expiry in addition to setting this to disconnected.';
