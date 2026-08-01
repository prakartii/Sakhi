-- =====================================================================
-- Migration 12: inventory_movements
-- =====================================================================
-- Append-only stock ledger: every restock, sale, adjustment, wastage
-- or return is one row. inventory.current_quantity is a cached
-- snapshot that this ledger reconstructs/audits; quantity_before and
-- quantity_after are captured at write time so historical rows remain
-- correct even if current_quantity logic changes later.
-- =====================================================================

create table if not exists public.inventory_movements (
  id uuid primary key default gen_random_uuid(),
  inventory_id uuid not null references public.inventory (id) on delete cascade,
  related_transaction_id uuid references public.transactions (id) on delete set null,
  movement_type public.inventory_movement_type_enum not null,
  quantity numeric(14, 3) not null,
  quantity_before numeric(14, 3) not null,
  quantity_after numeric(14, 3) not null,
  notes text,
  movement_date timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_inventory_movements_updated_at
  before update on public.inventory_movements
  for each row execute function public.set_updated_at();

create index if not exists idx_inventory_movements_inventory
  on public.inventory_movements (inventory_id, movement_date desc);
create index if not exists idx_inventory_movements_transaction on public.inventory_movements (related_transaction_id);
create index if not exists idx_inventory_movements_type on public.inventory_movements (movement_type);

comment on table public.inventory_movements is
  'Append-only stock movement ledger. Source of truth for inventory history; inventory.current_quantity is a derived cache of this table.';
