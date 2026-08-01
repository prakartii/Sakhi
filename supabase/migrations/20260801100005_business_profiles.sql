-- =====================================================================
-- Migration 05: business_profiles
-- =====================================================================
-- A user can run more than one business (common among the target
-- users — e.g. a tailoring business plus a side catering business),
-- so this is a 1:N relationship from users, not 1:1. Every downstream
-- feature table (memory, transactions, inventory, matches...) hangs
-- off business_profiles.id rather than users.id directly, because the
-- app's unit of "business context" is the business, not the person.
-- =====================================================================

create table if not exists public.business_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  business_name varchar(200) not null,
  business_category varchar(100),
  industry varchar(100),
  registration_type public.business_registration_type_enum not null default 'unregistered',
  gstin varchar(15),
  pan varchar(10),
  udyam_registration_number varchar(30),
  year_established smallint,
  employee_count_range varchar(20),
  monthly_revenue_range varchar(30),
  preferred_language_id uuid references public.languages (id) on delete set null,
  city varchar(100),
  state varchar(100),
  country varchar(100) not null default 'India',
  pincode varchar(10),
  address text,
  logo_url text,
  is_primary boolean not null default true,
  status public.business_status_enum not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_business_profiles_updated_at
  before update on public.business_profiles
  for each row execute function public.set_updated_at();

create index if not exists idx_business_profiles_user_id on public.business_profiles (user_id);
create index if not exists idx_business_profiles_status on public.business_profiles (status);
create index if not exists idx_business_profiles_category on public.business_profiles (business_category);
create index if not exists idx_business_profiles_geo on public.business_profiles (state, city);

-- At most one primary business per user (partial unique index rather
-- than a boolean everyone forgets to unset).
create unique index if not exists uq_business_profiles_primary_per_user
  on public.business_profiles (user_id)
  where is_primary = true;

comment on table public.business_profiles is
  'One row per business a user runs. Root entity for all feature data (memory, cashflow, inventory, matches).';
