-- =====================================================================
-- Migration 15: mentor_profiles, mentor_matches
-- =====================================================================
-- mentor_profiles.user_id is nullable and optional: a mentor may or may
-- not also be a platform user (some mentors are imported/curated
-- without ever logging in). mentor_matches carries a human-scheduling
-- lifecycle (requested/accepted/completed) distinct from the
-- apply-to-a-listing lifecycle used by scheme/opportunity matches.
-- =====================================================================

create table if not exists public.mentor_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users (id) on delete set null,
  full_name varchar(200) not null,
  bio text,
  expertise_areas text[] not null default '{}',
  industry_focus varchar(100),
  years_experience integer,
  linkedin_url text,
  avatar_url text,
  rating numeric(3, 2),
  total_sessions integer not null default 0,
  is_verified boolean not null default false,
  is_active boolean not null default true,
  availability_status public.mentor_availability_enum not null default 'available',
  hourly_rate numeric(10, 2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint chk_mentor_profiles_rating check (rating is null or rating between 0 and 5)
);

create trigger trg_mentor_profiles_updated_at
  before update on public.mentor_profiles
  for each row execute function public.set_updated_at();

create index if not exists idx_mentor_profiles_user on public.mentor_profiles (user_id);
create index if not exists idx_mentor_profiles_active
  on public.mentor_profiles (is_active) where is_active = true;
create index if not exists idx_mentor_profiles_availability on public.mentor_profiles (availability_status);
create index if not exists idx_mentor_profiles_expertise on public.mentor_profiles using gin (expertise_areas);

comment on table public.mentor_profiles is
  'Mentor directory. user_id is optional — a mentor is not required to be a platform account holder.';

-- ---------------------------------------------------------------------
create table if not exists public.mentor_matches (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  mentor_id uuid not null references public.mentor_profiles (id) on delete cascade,
  match_score numeric(5, 2) not null,
  match_reason text,
  status public.mentor_match_status_enum not null default 'suggested',
  requested_at timestamptz,
  session_scheduled_at timestamptz,
  completed_at timestamptz,
  feedback_rating smallint,
  feedback_text text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_mentor_matches_business_mentor unique (business_profile_id, mentor_id),
  constraint chk_mentor_matches_score check (match_score between 0 and 100),
  constraint chk_mentor_matches_feedback_rating check (feedback_rating is null or feedback_rating between 1 and 5)
);

create trigger trg_mentor_matches_updated_at
  before update on public.mentor_matches
  for each row execute function public.set_updated_at();

create index if not exists idx_mentor_matches_business_profile
  on public.mentor_matches (business_profile_id, match_score desc);
create index if not exists idx_mentor_matches_mentor on public.mentor_matches (mentor_id);
create index if not exists idx_mentor_matches_status on public.mentor_matches (status);

comment on table public.mentor_matches is
  'Join of business_profiles <-> mentor_profiles with match score and the human-scheduling lifecycle (requested -> accepted -> completed).';
