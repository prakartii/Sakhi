-- =====================================================================
-- Migration 19: business_profiles onboarding/marketing fields
-- =====================================================================
-- Purely additive: extends the existing business_profiles table (created
-- in migration 05) with the fields the AI onboarding and business-growth
-- workflow needs — owner identity, description, positioning, growth
-- stage, and social/web links. No existing column, index, constraint, or
-- row is touched.
--
-- Every new column is nullable. business_profiles already has rows
-- (created before onboarding existed) that won't have these filled in —
-- that gap is exactly what the new onboarding-status endpoint reports on,
-- not something this migration should paper over with fake defaults.
-- =====================================================================

do $$ begin
  create type public.business_stage_enum as enum ('idea', 'startup', 'growing', 'scaling');
exception when duplicate_object then null; end $$;

alter table public.business_profiles
  add column if not exists owner_name varchar(200),
  add column if not exists business_description text,
  add column if not exists target_audience text,
  add column if not exists products_or_services text,
  add column if not exists business_stage public.business_stage_enum,
  add column if not exists website_url text,
  add column if not exists instagram_url text,
  add column if not exists facebook_url text,
  add column if not exists linkedin_url text;

comment on column public.business_profiles.owner_name is
  'Display name of the business owner as presented for this business — distinct from users.full_name, since one user can run multiple businesses under different personas.';
comment on column public.business_profiles.business_stage is
  'Self-reported growth stage (idea/startup/growing/scaling). Null until the owner sets it during onboarding.';
comment on column public.business_profiles.business_description is
  'Free-text description of what the business does, as entered during onboarding.';
