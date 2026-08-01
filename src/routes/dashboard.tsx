import { createFileRoute } from "@tanstack/react-router";
import {
  CheckCircle2,
  Instagram,
  IndianRupee,
  Landmark,
  Package,
  PartyPopper,
  Sparkles,
  TriangleAlert,
  Users2,
} from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import {
  useAISummary,
  useInventorySummary,
  useNotifications,
  useScheduledPostsQueue,
} from "@/hooks/use-dashboard-data";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Basis, Craft, Eyebrow, HandNote, Pill, Why } from "@/components/sakhi/Cards";
import { BotanicalMark } from "@/components/sakhi/CompanionAssets";
import {
  FocusChip,
  GreetingCard,
  PostcardCard,
  SnapshotCard,
} from "@/components/sakhi/DashboardAssets";
import {
  BrandStamp,
  HashtagNote,
  InstagramPreviewMini,
  TornStat,
} from "@/components/sakhi/ScrapbookAssets";

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

const FOCUS = [
  {
    icon: Package,
    tone: "rose" as const,
    label: "Orders to ship",
    note: "3 dupatta orders ready — Meena's leaves today.",
  },
  {
    icon: IndianRupee,
    tone: "marigold" as const,
    label: "Payments to collect",
    note: "₹9,700 pending from the Bengaluru boutique.",
  },
  {
    icon: PartyPopper,
    tone: "indigo" as const,
    label: "Festival opportunity",
    note: "Rakhi is in 18 days — demand is already rising.",
  },
  {
    icon: TriangleAlert,
    tone: "leaf" as const,
    label: "Inventory running low",
    note: "Indigo block-print fabric — 8 days of stock left.",
  },
  {
    icon: Landmark,
    tone: "lilac" as const,
    label: "Scheme recommendation",
    note: "PM Vishwakarma toolkit grant — 92% fit for you.",
  },
];

const MILESTONES = [
  { title: "Sold your first online order", date: "January", tone: "rose" as const },
  { title: "Welcomed a repeat customer", date: "March", tone: "marigold" as const },
  { title: "Crossed ₹50,000 in revenue", date: "May", tone: "leaf" as const },
  { title: "Completed your 100th product", date: "June", tone: "indigo" as const },
  { title: "Joined your first exhibition", date: "July", tone: "lilac" as const },
];

const OPPORTUNITIES = [
  {
    icon: PartyPopper,
    tone: "rose" as const,
    eyebrow: "Upcoming festival",
    title: "Rakhi, in 18 days",
    note: "Bundle two pieces — last year's buyers already expect it.",
  },
  {
    icon: Sparkles,
    tone: "marigold" as const,
    eyebrow: "Trending products",
    title: "Gift-wrapped bundles",
    note: "Searches for festive gift sets are up across your category.",
  },
  {
    icon: Landmark,
    tone: "indigo" as const,
    eyebrow: "Government scheme",
    title: "PM Vishwakarma toolkit grant",
    note: "92% fit — covers new loom equipment.",
  },
  {
    icon: Users2,
    tone: "leaf" as const,
    eyebrow: "Collaboration",
    title: "Two nearby makers, same buyers",
    note: "A joint festival stall could split your booth cost in half.",
  },
  {
    icon: Instagram,
    tone: "lilac" as const,
    eyebrow: "Instagram trend",
    title: "Process reels are outperforming",
    note: "Loom and dyeing clips are getting 3× the saves of product shots.",
  },
];

function Dashboard() {
  const { profile } = usePrimaryBusinessProfile();
  const inventorySummary = useInventorySummary();
  const notifications = useNotifications();
  const scheduledPosts = useScheduledPostsQueue();
  const aiSummary = useAISummary();

  const SNAPSHOT = [
    {
      label: "Stock value",
      value: inventorySummary.data ? `₹${inventorySummary.data.total_stock_value.toLocaleString("en-IN")}` : "—",
      note: inventorySummary.data ? `${inventorySummary.data.total_products} products tracked` : "Loading…",
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
        <img
          src="/images/instagram-preview.png"
          alt="Instagram preview of threads_of_jaipur"
          className="pointer-events-none absolute top-16 right-6 z-20 hidden w-56 rotate-3 select-none xl:block"
          style={{ boxShadow: "var(--shadow-lift)", borderRadius: "1rem" }}
        />
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

        <Reveal delay={150} className="mt-8">
          <div className="mb-3 flex items-center gap-2 text-foreground/70">
            <Sparkles className="h-4 w-4" />
            <p className="text-sm font-semibold">Today's focus</p>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {FOCUS.map((f) => (
              <FocusChip key={f.label} {...f} />
            ))}
          </div>
        </Reveal>
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
          {MILESTONES.map((m, i) => (
            <Reveal key={m.title} delay={i * 70}>
              <div className="relative flex items-center gap-4 rounded-2xl bg-card/60 px-4 py-3.5 ring-1 ring-clay/10 transition-transform hover:-translate-y-0.5 sm:pl-9">
                <span
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-full ring-2 ring-card sm:absolute sm:left-0"
                  style={{ background: "var(--card)" }}
                >
                  <CheckCircle2 className="h-5 w-5 text-leaf-ink" />
                </span>
                <div className="min-w-0">
                  <p className="text-[9.5px] font-semibold tracking-[0.16em] text-muted-foreground uppercase">
                    {m.date}
                  </p>
                  <p className="font-display mt-0.5 text-base font-semibold text-foreground">
                    {m.title}
                  </p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={100}>
          <Craft tone="lilac" texture="blockprint" className="relative sticky top-28 overflow-hidden">
            <BotanicalMark className="pointer-events-none absolute -top-6 -right-8 h-32 w-28 opacity-[0.1]" />
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <Eyebrow>Voice memory</Eyebrow>
                <h3 className="font-display mt-2 text-xl font-semibold">What Sakhi last heard</h3>
              </div>
              <TornStat label="AI confidence" value="96%" rotate={4} className="shrink-0" />
            </div>
            <MicPanel
              title="Latest voice memory"
              quote="&ldquo;Aaj 12 dupatte beche, 3 hazaar ka kapda kharida.&rdquo;"
              className="mt-4"
            />
            <Why>
              Twelve dupattas sold and ₹3,000 spent on fabric — your best single day this month,
              and margin held steady.
            </Why>
            <Basis />
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
        <div className="mt-8 grid gap-x-8 gap-y-20 sm:grid-cols-2 lg:grid-cols-3">
          {OPPORTUNITIES.map((o, i) => (
            <Reveal key={o.title} delay={i * 80}>
              <div className="relative">
                <PostcardCard {...o} rotate={i % 2 === 0 ? -2 : 2} />
                {i === 0 ? (
                  <HashtagNote
                    tags={["RakhiLove", "Handmade"]}
                    rotate={5}
                    className="absolute -right-5 -bottom-4 z-20 hidden lg:block"
                  />
                ) : null}
                {o.title.includes("Instagram") ? (
                  <InstagramPreviewMini
                    handle="threads_of_jaipur"
                    tones={["rose", "sand", "marigold"]}
                    rotate={-3}
                    className="absolute -bottom-8 left-1/2 z-20 hidden -translate-x-1/2 lg:block"
                  />
                ) : null}
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </Page>
  );
}
