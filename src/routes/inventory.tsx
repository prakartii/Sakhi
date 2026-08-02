import { useState, type SyntheticEvent } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { Clock, Loader2, Package, ShieldCheck } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, Hero, Meter, Pill } from "@/components/sakhi/Cards";
import { IconBadge } from "@/components/sakhi/CompanionAssets";
import {
  useCreateInventoryItem,
  useInventoryForecast,
  useInventoryList,
  useInventorySummary,
  useStockAction,
} from "@/hooks/use-inventory";
import { ApiError } from "@/lib/api-client";
import type { InventoryItem } from "@/lib/types";

export const Route = createFileRoute("/inventory")({
  head: () => ({
    meta: [
      { title: "Smart Inventory — Sakhi" },
      {
        name: "description",
        content:
          "Every product you stock, with reorder levels and stock value tracked automatically.",
      },
    ],
  }),
  component: InventoryRoute,
});

function InventoryRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <Inventory />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

function stockPercent(item: InventoryItem): number {
  const ceiling = Math.max(item.reorder_level * 2, item.current_quantity, 1);
  return Math.round((item.current_quantity / ceiling) * 100);
}

function ItemCard({ item }: { item: InventoryItem }) {
  const stockAction = useStockAction(item.id);
  const { data: forecast } = useInventoryForecast(item.id);
  const pct = stockPercent(item);
  const isLow = item.current_quantity <= item.reorder_level;
  const isOut = item.current_quantity <= 0;

  function adjust(direction: "in" | "out") {
    stockAction.mutate(
      { direction, quantity: 1 },
      {
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't update stock"),
      },
    );
  }

  return (
    <Craft tone={isOut ? "rose" : isLow ? "marigold" : "cream"} className="h-full">
      <h3 className="font-display text-xl font-semibold">{item.item_name}</h3>
      <p className="mt-1 text-[12.5px] text-foreground/70">
        {item.current_quantity} {item.unit} on hand · reorder at {item.reorder_level} {item.unit}
      </p>
      <Meter value={pct} tone={isLow ? "wine" : "clay"} />
      <div className="mt-3 flex flex-wrap gap-2">
        {isOut && <Pill tone="rose">Out of stock</Pill>}
        {!isOut && isLow && <Pill tone="marigold">Low stock — reorder soon</Pill>}
        {item.selling_price != null && <Pill tone="indigo">₹{item.selling_price} each</Pill>}
        {!isOut && forecast?.has_sufficient_data && forecast.days_of_stock_remaining != null && (
          <Pill tone={forecast.days_of_stock_remaining <= 7 ? "rose" : "leaf"}>
            Runs out in ~{Math.round(forecast.days_of_stock_remaining)} days
          </Pill>
        )}
      </div>
      <Basis>
        {item.unit_cost != null
          ? `Stock value at cost: ₹${(item.unit_cost * item.current_quantity).toLocaleString("en-IN")}`
          : "No cost recorded for this item."}
      </Basis>
      {!isOut && forecast && !forecast.has_sufficient_data && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          Not enough sales history yet to project a stockout date.
        </p>
      )}
      {!isOut && forecast?.reorder_by_date && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          Sakhi suggests reordering by{" "}
          {new Date(forecast.reorder_by_date).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
          })}
          .
        </p>
      )}
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={() => adjust("in")}
          disabled={stockAction.isPending}
          className="rounded-full border border-clay/25 px-3 py-1.5 text-[11.5px] font-medium text-foreground/75 transition-colors hover:border-wine/30 hover:text-wine disabled:opacity-60"
        >
          +1 stock in
        </button>
        <button
          type="button"
          onClick={() => adjust("out")}
          disabled={stockAction.isPending || item.current_quantity <= 0}
          className="rounded-full border border-clay/25 px-3 py-1.5 text-[11.5px] font-medium text-foreground/75 transition-colors hover:border-wine/30 hover:text-wine disabled:opacity-60"
        >
          −1 stock out
        </button>
      </div>
    </Craft>
  );
}

function AddItemForm() {
  const createItem = useCreateInventoryItem();
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");

  function handleSubmit(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!name.trim()) return;
    createItem.mutate(
      { item_name: name.trim(), current_quantity: quantity ? Number(quantity) : 0 },
      {
        onSuccess: () => {
          toast.success(`${name.trim()} added to inventory`);
          setName("");
          setQuantity("");
        },
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't add item"),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 flex flex-wrap gap-2">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Product name"
        className="min-w-0 flex-1 rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13.5px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
      />
      <input
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        placeholder="Starting stock"
        type="number"
        min={0}
        className="w-32 rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13.5px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
      />
      <button
        type="submit"
        disabled={createItem.isPending}
        className="flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-70"
      >
        {createItem.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
        Add product
      </button>
    </form>
  );
}

function Inventory() {
  const { data, isLoading } = useInventoryList();
  const { data: summary } = useInventorySummary();
  const items = data?.items ?? [];

  const STATS = [
    {
      label: "Products tracked",
      value: String(summary?.total_products ?? 0),
      sub: "across your inventory",
      icon: Package,
      tone: "indigo" as const,
    },
    {
      label: "Low or out of stock",
      value: String((summary?.low_stock_count ?? 0) + (summary?.out_of_stock_count ?? 0)),
      sub: "need a reorder soon",
      icon: Clock,
      tone: "rose" as const,
    },
    {
      label: "Stock value",
      value: `₹${(summary?.total_stock_value ?? 0).toLocaleString("en-IN")}`,
      sub: "at cost, right now",
      icon: ShieldCheck,
      tone: "leaf" as const,
    },
  ];

  return (
    <Page>
      <section className="py-14 lg:py-16">
        <Reveal>
          <Hero
            eyebrow="Smart inventory"
            title="Every product,"
            accent="tracked in one place."
            copy="Stock levels, reorder points and stock value — updated the moment you log a sale or restock."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {STATS.map((s, i) => (
          <Reveal key={s.label} delay={i * 90}>
            <div className="card-soft lift flex items-center gap-3 rounded-2xl px-5 py-4">
              <IconBadge icon={s.icon} tone={s.tone} />
              <div className="min-w-0">
                <Eyebrow>{s.label}</Eyebrow>
                <p className="mt-1 font-display text-xl font-semibold text-foreground">{s.value}</p>
                <p className="text-[11px] text-muted-foreground">{s.sub}</p>
              </div>
            </div>
          </Reveal>
        ))}
      </section>

      <section className="py-4">
        <Reveal>
          <Eyebrow>Add a product</Eyebrow>
          <AddItemForm />
        </Reveal>
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-2">
        {isLoading ? (
          <div className="col-span-full flex justify-center py-14">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : items.length === 0 ? (
          <div className="card-soft col-span-full rounded-2xl px-6 py-10 text-center text-sm text-muted-foreground">
            No products yet — add your first one above.
          </div>
        ) : (
          items.map((item, i) => (
            <Reveal key={item.id} delay={i * 60}>
              <ItemCard item={item} />
            </Reveal>
          ))
        )}
      </section>
    </Page>
  );
}
