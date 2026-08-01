import { createFileRoute } from "@tanstack/react-router";
import { CheckCircle2, Landmark, Loader2, Sparkles, TriangleAlert } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import {
  useAISummary,
  useInventorySummary,
  useNotifications,
  useScheduledPostsQueue,
} from "@/hooks/use-dashboard-data";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import { useBusinessMemories } from "@/hooks/use-memories";
import { Reveal } from "@/components/sakhi/Reveal";
import { Basis, Craft, Eyebrow, HandNote, Pill, Why } from "@/components/sakhi/Cards";
import { BotanicalMark } from "@/components/sakhi/CompanionAssets";
import {
  FocusChip,
  GreetingCard,
  PostcardCard,
  SnapshotCard,
} from "@/components/sakhi/DashboardAssets";
import { BrandStamp, TornStat } from "@/components/sakhi/ScrapbookAssets";
import type { BusinessMemory } from "@/lib/types";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Sakhi" },
      {
        name: "description",
        content:
          "Your business wakes up with you — what happened, what needs attention, and what to do next.",
      },
    ],
  }),
  component: DashboardRoute,
});

function DashboardRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <Dashboard />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

const FOCUS_TONES = ["rose", "marigold", "indigo", "leaf", "lilac"] as const;

function memoryDate(m: BusinessMemory): string {
  const value = m.occurred_at ?? m.created_at;
  return new Date(value).toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

function Dashboard() {
  const { profile } = usePrimaryBusinessProfile();
  const inventorySummary = useInventorySummary();
  const notifications = useNotifications();
  const scheduledPosts = useScheduledPostsQueue();
  const aiSummary = useAISummary();
  const memories = useBusinessMemories();

  const memoryItems = memories.data?.items ?? [];
  const milestones = memoryItems.filter((m) => m.memory_type === "milestone");
  const opportunities = memoryItems.filter(
    (m) => m.memory_type === "goal" || m.memory_type === "challenge",
  );
  const latestMemory = memoryItems[0];

  const SNAPSHOT = [
    {
      label: "Stock value",
      value: inventorySummary.data
        ? `₹${inventorySummary.data.total_stock_value.toLocaleString("en-IN")}`
        : "—",
      note: inventorySummary.data
        ? `${inventorySummary.data.total_products} products tracked`
        : "Loading…",
    },
    {
      label: "Low stock alerts",
      value: inventorySummary.data ? String(inventorySummary.data.low_stock_count) : "—",
      note: inventorySummary.data?.out_of_stock_count
        ? `${inventorySummary.data.out_of_stock_count} out of stock`
        : "Nothing critical",
      ...(inventorySummary.data
        ? { meter: Math.max(0, 100 - inventorySummary.data.low_stock_count * 20) }
        : {}),
    },
    {
      label: "Unread notifications",
      value: notifications.data ? String(notifications.data.total) : "—",
      note:
        (notifications.data && notifications.data.total > 0
          ? notifications.data.items[0]?.title
          : undefined) ?? "You're all caught up",
    },
    {
      label: "Posts in queue",
      value: scheduledPosts.data ? String(scheduledPosts.data.total) : "—",
      note: "Scheduled via Content Calendar",
    },
  ];

  return (
    <Page>
      <section className="relative py-14 lg:py-16">
        <Reveal>
          <span className="relative inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
            Daily overview
          </span>
          <h1 className="font-display mt-5 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Your business wakes up <span className="text-wine italic">with you.</span>
          </h1>
        </Reveal>

        <Reveal delay={90} className="mt-8">
          <GreetingCard
            time={new Date().toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" })}
            place={profile?.city ?? "your city"}
            name={profile?.owner_name ?? profile?.business_name ?? "there"}
            summary={
              aiSummary.data?.narrative ??
              (aiSummary.isLoading
                ? "Loading today's summary…"
                : "Log a voice check-in or add a transaction so Sakhi has something to summarize.")
            }
          />
        </Reveal>

        {aiSummary.data && aiSummary.data.highlights.length > 0 && (
          <Reveal delay={150} className="mt-8">
            <div className="mb-3 flex items-center gap-2 text-foreground/70">
              <Sparkles className="h-4 w-4" />
              <p className="text-sm font-semibold">Today's focus</p>
            </div>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {aiSummary.data.highlights.map((highlight, i) => (
                <FocusChip
                  key={highlight}
                  icon={Sparkles}
                  tone={FOCUS_TONES[i % FOCUS_TONES.length]!}
                  label={highlight}
                  note="From your latest AI summary"
                />
              ))}
            </div>
          </Reveal>
        )}
      </section>

      <div className="thread opacity-50" />

      <section className="py-10">
        <Reveal>
          <Eyebrow>Business snapshot</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            Everything, at a glance
          </h2>
        </Reveal>
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {SNAPSHOT.map((s, i) => (
            <Reveal key={s.label} delay={i * 70}>
              <SnapshotCard {...s} />
            </Reveal>
          ))}
        </div>
      </section>

      <div className="thread opacity-50" />

      <section className="py-10">
        <Reveal className="flex items-start justify-between gap-4">
          <div>
            <Eyebrow>AI suggestions</Eyebrow>
            <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
              Notes from Sakhi
            </h2>
          </div>
          <BrandStamp className="hidden sm:grid" />
        </Reveal>
        <div className="mt-6 grid gap-5 lg:grid-cols-2">
          {aiSummary.isLoading ? (
            <Reveal>
              <Craft tone="rose" texture="weave" className="h-full">
                <Eyebrow>Suggestion</Eyebrow>
                <h3 className="font-display mt-2 text-xl font-semibold">Reading your numbers…</h3>
                <Why>Sakhi is looking at your recent transactions and stock levels.</Why>
              </Craft>
            </Reveal>
          ) : aiSummary.isError || !aiSummary.data?.top_actions.length ? (
            <Reveal>
              <Craft tone="rose" texture="weave" className="h-full">
                <Eyebrow>Suggestion</Eyebrow>
                <h3 className="font-display mt-2 text-xl font-semibold">Not enough data yet</h3>
                <Why>
                  Log a few transactions or a voice check-in and Sakhi will start suggesting
                  concrete next steps here.
                </Why>
              </Craft>
            </Reveal>
          ) : (
            aiSummary.data.top_actions.map((action, i) => (
              <Reveal key={action.action} delay={i * 80}>
                <Craft
                  tone={i % 2 === 0 ? "rose" : "marigold"}
                  texture={i % 2 === 0 ? "weave" : "blockprint"}
                  className="h-full"
                >
                  <Eyebrow>Suggestion</Eyebrow>
                  <h3 className="font-display mt-2 text-xl font-semibold">{action.action}</h3>
                  {aiSummary.data!.highlights[i] ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Pill tone="indigo">{aiSummary.data!.highlights[i]}</Pill>
                    </div>
                  ) : null}
                  <Why>{action.why}</Why>
                  <Basis>Based on your recent transactions and stock levels.</Basis>
                </Craft>
              </Reveal>
            ))
          )}
        </div>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-5 py-10 lg:grid-cols-[1.35fr_0.95fr]">
        <div className="relative space-y-5">
          <Reveal>
            <Eyebrow>Growth timeline</Eyebrow>
            <h2 className="font-display mt-1.5 mb-5 text-2xl font-semibold text-foreground">
              Your business, so far
            </h2>
          </Reveal>
          <div
            aria-hidden
            className="absolute top-16 bottom-4 left-4 hidden w-px bg-[repeating-linear-gradient(180deg,color-mix(in_oklab,var(--clay)_55%,transparent)_0_8px,transparent_8px_16px)] sm:block"
          />
          {memories.isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : milestones.length === 0 ? (
            <p className="text-[12.5px] text-muted-foreground">
              No milestones yet — Sakhi marks these automatically as she notices them in your voice
              check-ins.
            </p>
          ) : (
            milestones.map((m, i) => (
              <Reveal key={m.id} delay={i * 70}>
                <div className="relative flex items-center gap-4 rounded-2xl bg-card/60 px-4 py-3.5 ring-1 ring-clay/10 transition-transform hover:-translate-y-0.5 sm:pl-9">
                  <span
                    className="grid h-9 w-9 shrink-0 place-items-center rounded-full ring-2 ring-card sm:absolute sm:left-0"
                    style={{ background: "var(--card)" }}
                  >
                    <CheckCircle2 className="h-5 w-5 text-leaf-ink" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-[9.5px] font-semibold tracking-[0.16em] text-muted-foreground uppercase">
                      {memoryDate(m)}
                    </p>
                    <p className="font-display mt-0.5 text-base font-semibold text-foreground">
                      {m.title ?? m.content}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))
          )}
        </div>

        <Reveal delay={100}>
          <Craft
            tone="lilac"
            texture="blockprint"
            className="relative sticky top-28 overflow-hidden"
          >
            <BotanicalMark className="pointer-events-none absolute -top-6 -right-8 h-32 w-28 opacity-[0.1]" />
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <Eyebrow>Voice memory</Eyebrow>
                <h3 className="font-display mt-2 text-xl font-semibold">What Sakhi last heard</h3>
              </div>
              {latestMemory && (
                <TornStat
                  label="Importance"
                  value={`${latestMemory.importance_score}/5`}
                  rotate={4}
                  className="shrink-0"
                />
              )}
            </div>
            {latestMemory ? (
              <>
                <p className="hand mt-4 text-[1.05rem] leading-relaxed">{latestMemory.content}</p>
                <Why>{`Extracted from a ${latestMemory.source} conversation and remembered as a ${latestMemory.memory_type}.`}</Why>
                <Basis />
              </>
            ) : (
              <p className="mt-4 text-[12.5px] text-muted-foreground">
                Nothing yet — talk to Sakhi on the Companion page and she'll remember it here.
              </p>
            )}
            <HandNote>She's always listening, so you don't have to write it down.</HandNote>
          </Craft>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="py-10">
        <Reveal>
          <Eyebrow>Opportunity corner</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            Worth a look this week
          </h2>
        </Reveal>
        {opportunities.length === 0 ? (
          <p className="mt-6 text-[12.5px] text-muted-foreground">
            Sakhi surfaces goals and challenges here as she notices them in your voice check-ins —
            nothing yet.
          </p>
        ) : (
          <div className="mt-8 grid gap-x-8 gap-y-20 sm:grid-cols-2 lg:grid-cols-3">
            {opportunities.map((o, i) => (
              <Reveal key={o.id} delay={i * 80}>
                <PostcardCard
                  icon={o.memory_type === "challenge" ? TriangleAlert : Landmark}
                  tone={o.memory_type === "challenge" ? "rose" : "leaf"}
                  eyebrow={o.memory_type === "challenge" ? "Challenge noticed" : "Goal noticed"}
                  title={o.title ?? o.content.slice(0, 60)}
                  note={o.content}
                  rotate={i % 2 === 0 ? -2 : 2}
                />
              </Reveal>
            ))}
          </div>
        )}
      </section>
    </Page>
  );
}
