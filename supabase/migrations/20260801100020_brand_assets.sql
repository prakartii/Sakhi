-- =====================================================================
-- Migration 20: brand_assets
-- =====================================================================
-- New table, no existing table touched. A business can have many
-- brand_assets rows — successive rebrands, or a draft being iterated on
-- before it goes live — status distinguishes which one, if any, is
-- currently active. Core module #2 of the AI Business Growth Operating
-- System vision (see the architecture review): stores branding data only,
-- no logo generation, no AI calls.
-- =====================================================================

do $$ begin
  create type public.brand_asset_status_enum as enum ('draft', 'active', 'archived');
exception when duplicate_object then null; end $$;

create table if not exists public.brand_assets (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  brand_name varchar(200) not null,
  tagline varchar(300),
  brand_story text,
  mission text,
  vision text,
  primary_color varchar(7),    -- hex, e.g. '#8F2F56' or '#FFF'
  secondary_color varchar(7),
  typography varchar(200),     -- free-text font pairing, e.g. 'Poppins / Inter'
  logo_url text,
  favicon_url text,
  brand_voice text,            -- free-text tone description, e.g. 'warm, playful, direct'
  packaging_notes text,
  status public.brand_asset_status_enum not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_brand_assets_updated_at
  before update on public.brand_assets
  for each row execute function public.set_updated_at();

create index if not exists idx_brand_assets_business_profile
  on public.brand_assets (business_profile_id);
create index if not exists idx_brand_assets_status
  on public.brand_assets (status);
create index if not exists idx_brand_assets_business_profile_status
  on public.brand_assets (business_profile_id, status);

comment on table public.brand_assets is
  'Branding identity data for a business — name, story, voice, colors, typography, logo/favicon links. One business may have many rows (drafts, rebrands); status marks which is current. Storage only: no logo generation, no AI.';
comment on column public.brand_assets.status is
  'draft (being defined) / active (current brand) / archived (superseded). No uniqueness enforced on "one active per business" — that''s a product decision left for the service layer if/when it''s needed, not a schema constraint.';
