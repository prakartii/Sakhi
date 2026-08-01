-- =====================================================================
-- Migration 04: users, user_preferences
-- =====================================================================
-- public.users is a 1:1 profile extension of Supabase's built-in
-- auth.users (id shared, FK'd with ON DELETE CASCADE). This migration
-- does NOT implement authentication — it only links to the auth schema
-- Supabase already provisions, which is the standard Supabase pattern
-- for storing app-level profile data next to an auth identity.
-- =====================================================================

create table if not exists public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  email varchar(255) not null unique,
  full_name varchar(200),
  phone varchar(20),
  avatar_url text,
  preferred_language_id uuid references public.languages (id) on delete set null,
  onboarding_completed boolean not null default false,
  status public.user_status_enum not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_users_updated_at
  before update on public.users
  for each row execute function public.set_updated_at();

create index if not exists idx_users_status on public.users (status);
create index if not exists idx_users_preferred_language on public.users (preferred_language_id);

comment on table public.users is
  'App-level profile data, 1:1 with auth.users. All other tables hang off this id, not auth.users directly.';

-- ---------------------------------------------------------------------
-- user_preferences: 1:1 with users. Split out from users so frequently
-- updated preference toggles don't rewrite the core identity row, and
-- so the users table stays lean for joins used almost everywhere.
-- ---------------------------------------------------------------------
create table if not exists public.user_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references public.users (id) on delete cascade,
  currency varchar(10) not null default 'INR',
  timezone varchar(50) not null default 'Asia/Kolkata',
  theme varchar(20) not null default 'system',
  notify_email boolean not null default true,
  notify_sms boolean not null default false,
  notify_push boolean not null default true,
  notify_whatsapp boolean not null default false,
  digest_frequency varchar(20) not null default 'daily',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_user_preferences_updated_at
  before update on public.user_preferences
  for each row execute function public.set_updated_at();

comment on table public.user_preferences is
  'One row per user. unique(user_id) both enforces 1:1 and serves as the lookup index.';
