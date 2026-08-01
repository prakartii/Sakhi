-- =====================================================================
-- Migration 10: inventory
-- =====================================================================
-- Current-state snapshot of stock items. current_quantity is a
-- denormalized running total, kept in sync by application logic (or a
-- trigger, see note below) whenever an inventory_movements row is
-- inserted — movements are the append-only ledger, inventory is the
-- fast-read current state.
-- =====================================================================

create table if not exists public.inventory (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  supplier_id uuid references public.suppliers (id) on delete set null,
  sku varchar(50),
  item_name varchar(200) not null,
  category varchar(100),
  unit varchar(20) not null default 'pcs',
  current_quantity numeric(14, 3) not null default 0,
  reorder_level numeric(14, 3) not null default 0,
  unit_cost numeric(12, 2),
  selling_price numeric(12, 2),
  image_url text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_inventory_updated_at
  before update on public.inventory
  for each row execute function public.set_updated_at();

create index if not exists idx_inventory_business_profile on public.inventory (business_profile_id);
create index if not exists idx_inventory_supplier on public.inventory (supplier_id);
create index if not exists idx_inventory_active on public.inventory (business_profile_id) where is_active = true;
-- Low-stock alert queries ("what needs reordering") are hot-path for the
-- Smart Inventory feature, so they get a dedicated partial index.
create index if not exists idx_inventory_low_stock
  on public.inventory (business_profile_id)
  where current_quantity <= reorder_level;

create unique index if not exists uq_inventory_business_sku
  on public.inventory (business_profile_id, sku)
  where sku is not null;

comment on table public.inventory is
  'Current-state stock per item. current_quantity is maintained from inventory_movements (the ledger), not edited directly in normal operation.';
