-- =====================================================================
-- Migration 09: suppliers
-- =====================================================================
-- Created before inventory and transactions because both reference it
-- (an inventory item has a default supplier; a transaction may record
-- a payment made to a supplier).
-- =====================================================================

create table if not exists public.suppliers (
  id uuid primary key default gen_random_uuid(),
  business_profile_id uuid not null references public.business_profiles (id) on delete cascade,
  name varchar(200) not null,
  contact_person varchar(200),
  phone varchar(20),
  email varchar(255),
  address text,
  category varchar(100),
  rating numeric(3, 2),  -- 0.00 - 5.00
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint chk_suppliers_rating check (rating is null or rating between 0 and 5)
);

create trigger trg_suppliers_updated_at
  before update on public.suppliers
  for each row execute function public.set_updated_at();

create index if not exists idx_suppliers_business_profile on public.suppliers (business_profile_id);
create index if not exists idx_suppliers_active on public.suppliers (business_profile_id) where is_active = true;

comment on table public.suppliers is
  'Supplier directory per business. Referenced by inventory (default supplier) and transactions (counterparty).';
