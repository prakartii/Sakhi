-- =====================================================================
-- Migration 21: websites, website_versions
-- =====================================================================
-- New tables, no existing table touched. Core module #3 of the AI
-- Business Growth Operating System vision (see the architecture review):
-- stores website metadata and version history only — no deployment, no
-- generation. website_versions is an append-only snapshot ledger, the
-- same pattern already used by inventory_movements and forecast_history:
-- every meaningful write to a websites row is expected to also insert a
-- website_versions row capturing what changed (that orchestration lives
-- in the service layer, not here — this migration only shapes the table).
-- =====================================================================

do $$ begin
  create type public.website_status_enum as enum (
    'draft', 'building', 'live', 'maintenance', 'archived'
  );
exception when duplicate_object then null; end $$;

create table if not exists public.websites (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  website_name varchar(200) not null,
  deployment_url text,
  github_repository varchar(300),   -- full URL or 'org/repo' shorthand, either is valid
  template varchar(100),            -- free text, not an enum: templates are an extensible
                                     -- catalog that can grow without a schema migration
  status public.website_status_enum not null default 'draft',
  seo_title varchar(200),
  seo_description varchar(300),
  custom_domain varchar(255),
  favicon text,
  published boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_websites_updated_at
  before update on public.websites
  for each row execute function public.set_updated_at();

create index if not exists idx_websites_business_profile
  on public.websites (business_profile_id);
create index if not exists idx_websites_status on public.websites (status);
create index if not exists idx_websites_published
  on public.websites (business_profile_id) where published = true;
create unique index if not exists uq_websites_custom_domain
  on public.websites (custom_domain)
  where custom_domain is not null;

comment on table public.websites is
  'Website metadata for a business (deployment link, template choice, SEO fields, custom domain). Storage only: no deployment, no generation. `status` and `published` are independent fields, both stored as given — no rule ties them together at the schema level.';

-- ---------------------------------------------------------------------
create table if not exists public.website_versions (
  id uuid primary key default gen_random_uuid(),
  website_id uuid not null references public.websites (id) on delete cascade,
  version_number integer not null,
  website_name varchar(200) not null,
  deployment_url text,
  github_repository varchar(300),
  template varchar(100),
  status public.website_status_enum not null,
  seo_title varchar(200),
  seo_description varchar(300),
  custom_domain varchar(255),
  favicon text,
  published boolean not null,
  change_notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_website_versions_website_version unique (website_id, version_number)
);

create trigger trg_website_versions_updated_at
  before update on public.website_versions
  for each row execute function public.set_updated_at();

create index if not exists idx_website_versions_website
  on public.website_versions (website_id, version_number desc);

comment on table public.website_versions is
  'Append-only snapshot of a websites row at the time of a create/update/archive. Never edited after insert; version_number is assigned sequentially per website by the service layer, not a DB sequence, since it is scoped per-website rather than global.';
