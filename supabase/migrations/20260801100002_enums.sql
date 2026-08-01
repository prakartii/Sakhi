-- =====================================================================
-- Migration 02: Enumerated types
-- =====================================================================
-- All enums are declared up front so every table below can reference a
-- stable, already-defined type. `DO` blocks make each CREATE TYPE
-- idempotent (Postgres has no CREATE TYPE IF NOT EXISTS).
-- =====================================================================

do $$ begin
  create type public.user_status_enum as enum ('active', 'suspended', 'deleted');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.business_registration_type_enum as enum (
    'unregistered', 'sole_proprietorship', 'partnership', 'llp',
    'private_limited', 'public_limited', 'section8', 'cooperative', 'other'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.business_status_enum as enum ('active', 'inactive', 'archived');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.voice_log_status_enum as enum ('pending', 'processing', 'transcribed', 'failed');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.memory_type_enum as enum (
    'fact', 'milestone', 'goal', 'challenge', 'preference', 'note', 'decision'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.memory_source_enum as enum ('voice', 'manual', 'ai_inferred', 'conversation', 'import');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.conversation_role_enum as enum ('user', 'assistant', 'system');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.conversation_message_type_enum as enum ('text', 'voice', 'system_event');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.transaction_type_enum as enum ('income', 'expense');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.payment_method_enum as enum (
    'cash', 'upi', 'bank_transfer', 'card', 'cheque', 'other'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.transaction_status_enum as enum ('pending', 'completed', 'failed', 'refunded');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.transaction_source_enum as enum ('manual', 'voice', 'import', 'pos');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.recurring_frequency_enum as enum ('daily', 'weekly', 'monthly', 'quarterly', 'yearly');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.inventory_movement_type_enum as enum (
    'restock', 'sale', 'adjustment', 'wastage', 'return'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.scheme_level_enum as enum ('central', 'state', 'district');
exception when duplicate_object then null; end $$;

-- Shared by scheme_matches and opportunity_matches: both are "surfaced to
-- a business, business reacts to it" workflows with identical lifecycles.
do $$ begin
  create type public.match_status_enum as enum (
    'suggested', 'viewed', 'saved', 'applied', 'rejected', 'expired'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.opportunity_type_enum as enum (
    'grant', 'tender', 'marketplace', 'collaboration', 'loan', 'competition', 'training'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.location_scope_enum as enum ('local', 'state', 'national', 'global');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.mentor_availability_enum as enum ('available', 'busy', 'unavailable');
exception when duplicate_object then null; end $$;

-- Distinct from match_status_enum: mentor matching has a human-scheduling
-- lifecycle (requested -> accepted -> completed) rather than an
-- apply-to-a-listing lifecycle.
do $$ begin
  create type public.mentor_match_status_enum as enum (
    'suggested', 'viewed', 'requested', 'accepted', 'completed', 'declined'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.notification_type_enum as enum (
    'scheme_match', 'opportunity_match', 'mentor_match', 'inventory_alert',
    'cashflow_alert', 'forecast_ready', 'system', 'reminder'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.notification_channel_enum as enum ('in_app', 'email', 'sms', 'push', 'whatsapp');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.notification_priority_enum as enum ('low', 'normal', 'high', 'urgent');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.forecast_type_enum as enum (
    'cashflow', 'revenue', 'inventory_demand', 'growth_score'
  );
exception when duplicate_object then null; end $$;
