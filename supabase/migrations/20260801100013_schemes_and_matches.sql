-- =====================================================================
-- Migration 13: government_schemes, scheme_matches
-- =====================================================================
-- government_schemes is a GLOBAL catalog (central/state government
-- schemes), populated independently of any one user — think of it as
-- reference data refreshed by an ingestion job, not user-generated.
--
-- scheme_matches is added beyond the literal requested table list to
-- normalize the "Scheme Match" feature correctly: it is the join
-- between a business and a scheme, carrying the match score and the
-- business's reaction to it (viewed/saved/applied). Without it, a
-- feature named "Scheme Match" would have nowhere to persist a match.
-- This mirrors the mentor_profiles/mentor_matches split already
-- requested, so the pattern is consistent across all three matching
-- features (schemes, opportunities, mentors).
-- =====================================================================

create table if not exists public.government_schemes (
  id uuid primary key default gen_random_uuid(),
  scheme_name varchar(300) not null,
  scheme_code varchar(50) unique,
  description text,
  issuing_authority varchar(200),
  scheme_level public.scheme_level_enum not null default 'central',
  applicable_states text[],  -- null/empty = nationwide
  eligibility_criteria jsonb not null default '{}'::jsonb,
  benefits text,
  application_url text,
  documents_required jsonb not null default '[]'::jsonb,
  category varchar(100),
  min_business_age_months integer,
  max_annual_turnover numeric(16, 2),
  target_gender varchar(20) not null default 'women',
  is_active boolean not null default true,
  valid_from date,
  valid_until date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_government_schemes_updated_at
  before update on public.government_schemes
  for each row execute function public.set_updated_at();

create index if not exists idx_government_schemes_active on public.government_schemes (is_active) where is_active = true;
create index if not exists idx_government_schemes_category on public.government_schemes (category);
create index if not exists idx_government_schemes_level on public.government_schemes (scheme_level);
create index if not exists idx_government_schemes_states on public.government_schemes using gin (applicable_states);
create index if not exists idx_government_schemes_eligibility on public.government_schemes using gin (eligibility_criteria);

comment on table public.government_schemes is
  'Global catalog of government schemes (central/state), independent of any business. Matched to businesses via scheme_matches.';

-- ---------------------------------------------------------------------
create table if not exists public.scheme_matches (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  scheme_id uuid not null references public.government_schemes (id) on delete cascade,
  match_score numeric(5, 2) not null,
  match_reason text,
  status public.match_status_enum not null default 'suggested',
  matched_at timestamptz not null default now(),
  applied_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_scheme_matches_business_scheme unique (business_profile_id, scheme_id),
  constraint chk_scheme_matches_score check (match_score between 0 and 100)
);

create trigger trg_scheme_matches_updated_at
  before update on public.scheme_matches
  for each row execute function public.set_updated_at();

create index if not exists idx_scheme_matches_business_profile
  on public.scheme_matches (business_profile_id, match_score desc);
create index if not exists idx_scheme_matches_scheme on public.scheme_matches (scheme_id);
create index if not exists idx_scheme_matches_status on public.scheme_matches (status);

comment on table public.scheme_matches is
  'Join of business_profiles <-> government_schemes with a match score and the business''s reaction (viewed/saved/applied).';
