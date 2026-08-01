-- =====================================================================
-- Migration 03: languages
-- =====================================================================
-- Lookup table for supported UI / voice languages. Referenced by
-- users, business_profiles and voice_logs so every locale-sensitive
-- table shares one source of truth instead of repeating a varchar code.
-- =====================================================================

create table if not exists public.languages (
  id uuid primary key default gen_random_uuid(),
  code varchar(10) not null unique,   -- BCP-47 / ISO 639-1, e.g. 'en', 'hi', 'mr'
  name varchar(100) not null,         -- English name, e.g. 'Hindi'
  native_name varchar(100) not null,  -- Native-script name, e.g. 'हिन्दी'
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_languages_updated_at
  before update on public.languages
  for each row execute function public.set_updated_at();

create index if not exists idx_languages_active on public.languages (is_active) where is_active = true;

comment on table public.languages is
  'Master list of supported languages. Referenced by users, business_profiles and voice_logs for locale/voice handling.';

insert into public.languages (code, name, native_name) values
  ('en', 'English', 'English'),
  ('hi', 'Hindi', 'हिन्दी'),
  ('mr', 'Marathi', 'मराठी'),
  ('ta', 'Tamil', 'தமிழ்'),
  ('te', 'Telugu', 'తెలుగు'),
  ('bn', 'Bengali', 'বাংলা'),
  ('gu', 'Gujarati', 'ગુજરાતી'),
  ('kn', 'Kannada', 'ಕನ್ನಡ')
on conflict (code) do nothing;
