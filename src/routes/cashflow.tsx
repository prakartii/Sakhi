import { useMemo, useState, type SyntheticEvent } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { Loader2, PiggyBank, TrendingDown, TrendingUp } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { Reveal } from "@/components/sakhi/Reveal";
import { Craft, Eyebrow, Hero, Pill } from "@/components/sakhi/Cards";
import { IconBadge } from "@/components/sakhi/CompanionAssets";
import { useCreateTransaction, useTransactions } from "@/hooks/use-transactions";
import { ApiError } from "@/lib/api-client";
import type { Transaction } from "@/lib/types";

export const Route = createFileRoute("/cashflow")({
  head: () => ({
    meta: [
      { title: "Cashflow — Sakhi" },
      {
        name: "description",
        content: "What came in, what went out, and what you kept — tracked automatically.",
      },
    ],
  }),
  component: CashflowRoute,
});

function CashflowRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <Cashflow />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

function monthKey(dateStr: string): string {
  return dateStr.slice(0, 7); // "YYYY-MM"
}

function monthLabel(key: string): string {
  const parts = key.split("-").map(Number);
  const year = parts[0] ?? 1970;
  const month = parts[1] ?? 1;
  return new Date(year, month - 1, 1).toLocaleDateString("en-IN", { month: "short" });
}

function TrendLine({ points }: { points: { m: string; v: number }[] }) {
  if (points.length < 2) {
    return (
      <p className="mt-4 text-[12.5px] text-muted-foreground">
        Log a few more transactions to see a trend.
      </p>
    );
  }
  const w = 640;
  const h = 150;
  const values = points.map((p) => p.v);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const path = points
    .map((p, i) => {
      const x = (i / (points.length - 1)) * w;
      const y = h - ((p.v - min) / (max - min || 1)) * h;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="mt-4">
      <svg viewBox={`0 0 ${w} ${h + 22}`} className="w-full" role="img" aria-label="Income trend">
        {[0, 1, 2, 3].map((g) => (
          <line
            key={g}
            x1="0"
            x2={w}
            y1={(h / 3) * g}
            y2={(h / 3) * g}
            stroke="currentColor"
            className="text-clay/20"
            strokeDasharray="3 6"
          />
        ))}
        <path
          d={`${path} L${w},${h} L0,${h} Z`}
          fill="color-mix(in oklab, var(--wine) 8%, transparent)"
        />
        <path d={path} fill="none" stroke="var(--wine)" strokeWidth="2" strokeLinecap="round" />
        {points.map((p, i) => (
          <text
            key={p.m}
            x={(i / (points.length - 1)) * w}
            y={h + 16}
            textAnchor={i === 0 ? "start" : i === points.length - 1 ? "end" : "middle"}
            className="fill-[oklch(0.53_0.025_50)] text-[10px]"
          >
            {p.m}
          </text>
        ))}
      </svg>
    </div>
  );
}

function AddTransactionForm() {
  const createTransaction = useCreateTransaction();
  const [type, setType] = useState<"income" | "expense">("income");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");

  function handleSubmit(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    const value = Number(amount);
    if (!value || value <= 0) return;
    createTransaction.mutate(
      {
        transaction_type: type,
        amount: value,
        ...(description.trim() ? { description: description.trim() } : {}),
      },
      {
        onSuccess: () => {
          toast.success(`${type === "income" ? "Income" : "Expense"} of ₹${value} logged`);
          setAmount("");
          setDescription("");
        },
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't log transaction"),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 flex flex-wrap items-center gap-2">
      <div className="flex overflow-hidden rounded-xl border border-clay/25">
        <button
          type="button"
          onClick={() => setType("income")}
          className={`px-3 py-2 text-[12.5px] font-medium ${type === "income" ? "bg-leaf text-leaf-ink" : "bg-card text-foreground/60"}`}
        >
          Money in
        </button>
        <button
          type="button"
          onClick={() => setType("expense")}
          className={`px-3 py-2 text-[12.5px] font-medium ${type === "expense" ? "bg-rose text-wine" : "bg-card text-foreground/60"}`}
        >
          Money out
        </button>
      </div>
      <input
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        placeholder="Amount (₹)"
        type="number"
        min={0}
        className="w-32 rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13.5px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
      />
      <input
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="What was it for?"
        className="min-w-0 flex-1 rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13.5px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
      />
      <button
        type="submit"
        disabled={createTransaction.isPending}
        className="flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-70"
      >
        {createTransaction.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
        Log it
      </button>
    </form>
  );
}

function TransactionRow({ transaction }: { transaction: Transaction }) {
  const isIncome = transaction.transaction_type === "income";
  return (
    <div className="flex items-center justify-between gap-3 border-b border-clay/10 py-2.5 text-[13px] last:border-0">
      <div className="min-w-0">
        <p className="truncate text-foreground/85">
          {transaction.description ?? transaction.category ?? "Transaction"}
        </p>
        <p className="text-[11px] text-muted-foreground">{transaction.transaction_date}</p>
      </div>
      <Pill tone={isIncome ? "leaf" : "rose"}>
        {isIncome ? "+" : "−"}₹{transaction.amount.toLocaleString("en-IN")}
      </Pill>
    </div>
  );
}

function Cashflow() {
  const { data, isLoading } = useTransactions();
  const transactions = data?.items ?? [];

  const { totalIn, totalOut, trend } = useMemo(() => {
    let totalIn = 0;
    let totalOut = 0;
    const byMonth = new Map<string, number>();
    for (const t of transactions) {
      if (t.transaction_type === "income") {
        totalIn += t.amount;
        const key = monthKey(t.transaction_date);
        byMonth.set(key, (byMonth.get(key) ?? 0) + t.amount);
      } else {
        totalOut += t.amount;
      }
    }
    const trend = Array.from(byMonth.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-6)
      .map(([key, v]) => ({ m: monthLabel(key), v }));
    return { totalIn, totalOut, trend };
  }, [transactions]);

  const net = totalIn - totalOut;

  const SUMMARY = [
    {
      label: "Money in",
      value: `₹${totalIn.toLocaleString("en-IN")}`,
      sub: "all logged income",
      icon: TrendingUp,
      tone: "leaf" as const,
    },
    {
      label: "Money out",
      value: `₹${totalOut.toLocaleString("en-IN")}`,
      sub: "all logged expenses",
      icon: TrendingDown,
      tone: "rose" as const,
    },
    {
      label: "Net kept",
      value: `₹${net.toLocaleString("en-IN")}`,
      sub: net >= 0 ? "in the black" : "in the red",
      icon: PiggyBank,
      tone: "marigold" as const,
    },
  ];

  return (
    <Page>
      <section className="py-14 lg:py-16">
        <Reveal>
          <Hero
            eyebrow="Cashflow & financial health"
            title="Your money,"
            accent="tracked automatically."
            copy="What came in, what went out, and what you kept — every transaction you log, totalled for you."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {SUMMARY.map((s, i) => (
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

      <section>
        <Reveal>
          <Eyebrow>Log a transaction</Eyebrow>
          <AddTransactionForm />
        </Reveal>
      </section>

      <Reveal className="mt-8">
        <Craft tone="cream">
          <Eyebrow>Income trend · by month</Eyebrow>
          <TrendLine points={trend} />
        </Craft>
      </Reveal>

      <Reveal className="mt-6" delay={80}>
        <Craft tone="sand">
          <Eyebrow>Recent transactions</Eyebrow>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : transactions.length === 0 ? (
            <p className="mt-3 text-[12.5px] text-muted-foreground">No transactions logged yet.</p>
          ) : (
            <div className="mt-3">
              {transactions.slice(0, 12).map((t) => (
                <TransactionRow key={t.id} transaction={t} />
              ))}
            </div>
          )}
        </Craft>
      </Reveal>
    </Page>
  );
}
