-- =====================================================================
-- Migration 17: cross-table performance indexes
-- =====================================================================
-- Composite indexes that don't naturally belong to a single table's
-- own migration because they exist purely to serve specific
-- multi-column query patterns anticipated at scale (millions of
-- users). Added last so every referenced table already exists.
-- =====================================================================

-- Cashflow Health dashboard: "this business's transactions of type X in
-- a date range" is the single hottest query in the app.
create index if not exists idx_transactions_profile_type_date
  on public.transactions (business_profile_id, transaction_type, transaction_date desc);

-- Smart Inventory: "items below reorder level" already has a partial
-- index (idx_inventory_low_stock); this covers ordinary paginated
-- listing by name within a business.
create index if not exists idx_inventory_profile_name
  on public.inventory (business_profile_id, item_name);

-- Growth Intelligence: latest forecast of each type per business.
create index if not exists idx_forecast_history_profile_type_generated
  on public.forecast_history (business_profile_id, forecast_type, generated_at desc);

-- Notifications badge count: unread count per user is computed on
-- every app open.
create index if not exists idx_notifications_user_type_unread
  on public.notifications (user_id, notification_type) where is_read = false;

comment on index public.idx_transactions_profile_type_date is
  'Serves the Cashflow Health dashboard date-range + type filter.';
