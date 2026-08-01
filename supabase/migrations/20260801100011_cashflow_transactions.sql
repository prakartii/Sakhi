-- =====================================================================
-- Migration 11: transactions, transaction_items
-- =====================================================================
-- transactions is the Cashflow Health ledger (one row per money-in or
-- money-out event). transaction_items normalizes out the line items of
-- a single transaction (e.g. one sale invoice with 5 different
-- products) so per-item revenue/COGS can be analyzed without parsing
-- free text, and so each item can optionally tie back to an inventory
-- row to drive stock deduction.
-- =====================================================================

create table if not exists public.transactions (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  supplier_id uuid references public.suppliers (id) on delete set null,
  transaction_type public.transaction_type_enum not null,
  category varchar(100),
  amount numeric(14, 2) not null,
  currency varchar(10) not null default 'INR',
  payment_method public.payment_method_enum not null default 'cash',
  counterparty_name varchar(200),
  counterparty_contact varchar(50),
  transaction_date date not null default current_date,
  description text,
  receipt_url text,
  is_recurring boolean not null default false,
  recurring_frequency public.recurring_frequency_enum,
  status public.transaction_status_enum not null default 'completed',
  source public.transaction_source_enum not null default 'manual',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint chk_transactions_amount_positive check (amount >= 0)
);

create trigger trg_transactions_updated_at
  before update on public.transactions
  for each row execute function public.set_updated_at();

create index if not exists idx_transactions_business_profile_date
  on public.transactions (business_profile_id, transaction_date desc);
create index if not exists idx_transactions_type on public.transactions (business_profile_id, transaction_type);
create index if not exists idx_transactions_supplier on public.transactions (supplier_id);
create index if not exists idx_transactions_status on public.transactions (status) where status = 'pending';

comment on table public.transactions is
  'One row per income/expense event. Root of the Cashflow Health feature; forecast_history is derived from aggregates of this table.';

-- ---------------------------------------------------------------------
create table if not exists public.transaction_items (
  id uuid primary key default gen_random_uuid(),
  transaction_id uuid not null references public.transactions (id) on delete cascade,
  inventory_id uuid references public.inventory (id) on delete set null,
  item_name varchar(200) not null,
  quantity numeric(14, 3) not null default 1,
  unit varchar(20),
  unit_price numeric(12, 2) not null,
  total_price numeric(14, 2) not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint chk_transaction_items_quantity_positive check (quantity > 0)
);

create trigger trg_transaction_items_updated_at
  before update on public.transaction_items
  for each row execute function public.set_updated_at();

create index if not exists idx_transaction_items_transaction on public.transaction_items (transaction_id);
create index if not exists idx_transaction_items_inventory on public.transaction_items (inventory_id);

comment on table public.transaction_items is
  'Line items within a transaction. Optional inventory_id links a sale/purchase line to the stock item it moves.';
