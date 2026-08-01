-- =====================================================================
-- Migration 14: opportunities, opportunity_matches
-- =====================================================================
-- Same pattern as migration 13: opportunities is a global catalog
-- (grants, tenders, marketplace listings, collaborations...) sourced
-- independently of any one business; opportunity_matches is the join
-- that records which opportunities were surfaced to which business and
-- how the business responded. Kept as two tables (rather than folding
-- match fields into opportunities) because one opportunity is matched
-- to many businesses, and one business sees many opportunities.
-- =====================================================================

create table if not exists public.opportunities (
  id uuid primary key default gen_random_uuid(),
  title varchar(300) not null,
  description text,
  opportunity_type public.opportunity_type_enum not null,
  source_name varchar(200),
  source_url text,
  eligibility_criteria jsonb not null default '{}'::jsonb,
  deadline date,
  location_scope public.location_scope_enum not null default 'national',
  category varchar(100),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_opportunities_updated_at
  before update on public.opportunities
  for each row execute function public.set_updated_at();

create index if not exists idx_opportunities_active on public.opportunities (is_active) where is_active = true;
create index if not exists idx_opportunities_type on public.opportunities (opportunity_type);
create index if not exists idx_opportunities_deadline on public.opportunities (deadline) where deadline is not null;
create index if not exists idx_opportunities_eligibility on public.opportunities using gin (eligibility_criteria);

comment on table public.opportunities is
  'Global catalog of business opportunities (grants, tenders, marketplace, collaborations). Matched to businesses via opportunity_matches.';

-- ---------------------------------------------------------------------
create table if not exists public.opportunity_matches (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  opportunity_id uuid not null references public.opportunities (id) on delete cascade,
  match_score numeric(5, 2) not null,
  match_reason text,
  status public.match_status_enum not null default 'suggested',
  matched_at timestamptz not null default now(),
  applied_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_opportunity_matches_business_opportunity unique (business_profile_id, opportunity_id),
  constraint chk_opportunity_matches_score check (match_score between 0 and 100)
);

create trigger trg_opportunity_matches_updated_at
  before update on public.opportunity_matches
  for each row execute function public.set_updated_at();

create index if not exists idx_opportunity_matches_business_profile
  on public.opportunity_matches (business_profile_id, match_score desc);
create index if not exists idx_opportunity_matches_opportunity on public.opportunity_matches (opportunity_id);
create index if not exists idx_opportunity_matches_status on public.opportunity_matches (status);

comment on table public.opportunity_matches is
  'Join of business_profiles <-> opportunities with a match score and the business''s reaction. Backs the Opportunity Engine feature.';
