-- =====================================================================
-- Migration 16: forecast_history, notifications
-- =====================================================================
-- forecast_history stores each AI-generated forecast run as an
-- immutable snapshot (predicted_values jsonb), with actual_values
-- filled in later once the period closes — this is what lets Growth
-- Intelligence report forecast accuracy over time instead of only ever
-- showing the latest guess.
--
-- notifications is a generic outbox for every feature (scheme match,
-- inventory alert, forecast ready, ...). related_entity_type /
-- related_entity_id are a deliberately unenforced polymorphic
-- reference (no FK) so one notifications table can point at rows in
-- any of scheme_matches / opportunity_matches / mentor_matches /
-- inventory / forecast_history etc. without a union of nullable FKs.
-- =====================================================================

create table if not exists public.forecast_history (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  forecast_type public.forecast_type_enum not null,
  forecast_period_start date not null,
  forecast_period_end date not null,
  predicted_values jsonb not null default '{}'::jsonb,
  actual_values jsonb,
  confidence_score numeric(5, 2),
  model_version varchar(50),
  generated_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint chk_forecast_history_confidence check (confidence_score is null or confidence_score between 0 and 100),
  constraint chk_forecast_history_period check (forecast_period_end >= forecast_period_start)
);

create trigger trg_forecast_history_updated_at
  before update on public.forecast_history
  for each row execute function public.set_updated_at();

create index if not exists idx_forecast_history_business_profile
  on public.forecast_history (business_profile_id, forecast_period_start desc);
create index if not exists idx_forecast_history_type on public.forecast_history (forecast_type);

comment on table public.forecast_history is
  'Immutable snapshots of AI-generated forecasts (cashflow, revenue, inventory demand, growth score), with actual_values back-filled for accuracy tracking. Backs Growth Intelligence.';

-- ---------------------------------------------------------------------
create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  business_profile_id uuid references public.business_profiles (id) on delete cascade,
  notification_type public.notification_type_enum not null,
  title varchar(200) not null,
  body text,
  action_url text,
  related_entity_type varchar(50),  -- e.g. 'scheme_match', 'inventory' — no FK, see note above
  related_entity_id uuid,
  channel public.notification_channel_enum not null default 'in_app',
  priority public.notification_priority_enum not null default 'normal',
  is_read boolean not null default false,
  read_at timestamptz,
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_notifications_updated_at
  before update on public.notifications
  for each row execute function public.set_updated_at();

create index if not exists idx_notifications_user_unread
  on public.notifications (user_id, created_at desc) where is_read = false;
create index if not exists idx_notifications_business_profile on public.notifications (business_profile_id);
create index if not exists idx_notifications_type on public.notifications (notification_type);
create index if not exists idx_notifications_related_entity on public.notifications (related_entity_type, related_entity_id);

comment on table public.notifications is
  'Generic notification outbox for all features. related_entity_type/id is an intentionally unenforced polymorphic pointer.';
