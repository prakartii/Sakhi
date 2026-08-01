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
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, HandNote, Pill, Why } from "@/components/sakhi/Cards";
import { BotanicalMark } from "@/components/sakhi/CompanionAssets";
import {
  FocusChip,
  GreetingCard,
  PostcardCard,
  SnapshotCard,
} from "@/components/sakhi/DashboardAssets";
import {
  BrandStamp,
  ChecklistNote,
  HashtagNote,
  InstagramPreviewMini,
  ReelPreview,
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
  component: Dashboard,
});

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

const SNAPSHOT = [
  { label: "Today's sales", value: "₹6,480", note: "4 orders · ₹1,620 avg" },
  { label: "Weekly revenue", value: "₹34,200", note: "+18% vs last week" },
  { label: "Pending payments", value: "₹12,900", note: "2 buyers, one 21 days overdue" },
  { label: "Orders completed", value: "112", note: "9 this week" },
  { label: "Inventory health", value: "62%", meter: 62, note: "Indigo fabric needs reordering" },
  { label: "Customer happiness", value: "91%", meter: 91, note: "From 19 voice check-ins" },
];

const SUGGESTIONS = [
  {
    title: "Raise crochet bag price by ₹50",
    why: "Your margin on this piece has stayed flat for 3 months while cotton yarn cost rose 12% — buyers haven't blinked at your last two increases.",
    impact: { text: "+₹2,100/month", tone: "leaf" as const },
    confidence: { text: "High confidence", tone: "indigo" as const },
    action: "Update the price",
  },
  {
    title: "Launch Rakhi collection next week",
    why: "Last year, 61% of Rakhi buyers ordered two pieces together the moment the collection went live — waiting until the week-of cost you orders.",
    impact: { text: "Est. ₹14,000 over the fortnight", tone: "marigold" as const },
    confidence: { text: "High confidence", tone: "indigo" as const },
    action: "Draft the collection",
  },
  {
    title: "Create a behind-the-scenes reel tomorrow",
    why: "Your last process video outperformed product photos 3-to-1 on saves — followers want to see the loom, not just the result.",
    impact: { text: "+400–600 reach", tone: "rose" as const },
    confidence: { text: "Medium confidence", tone: "marigold" as const },
    action: "Plan the reel",
  },
  {
    title: "Restock indigo fabric this week",
    why: "You're 8 days from running out, and this dyer's last two lead times ran 9 and 11 days — ordering today just clears it.",
    impact: { text: "Avoids ₹9,000 in slipped orders", tone: "rose" as const },
    confidence: { text: "High confidence", tone: "indigo" as const },
    action: "Reorder now",
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
            time="7:10 AM"
            place="Jaipur"
            name="Kavita"
            summary={
              <>
                Yesterday was productive — three dupatta orders were completed, one customer
                requested custom embroidery, and Rakhi demand is beginning to rise. Here's what
                deserves your attention today.
              </>
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
          {SUGGESTIONS.map((s, i) => (
            <Reveal key={s.title} delay={i * 80}>
              <Craft tone={i % 2 === 0 ? "rose" : "marigold"} texture={i % 2 === 0 ? "weave" : "blockprint"} className="h-full">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <Eyebrow>Suggestion</Eyebrow>
                    <h3 className="font-display mt-2 text-xl font-semibold">{s.title}</h3>
                  </div>
                  {i === 1 ? (
                    <ChecklistNote
                      title="Rakhi Collection ♡"
                      items={["Soft pastels + gold accents", "Reels + behind the scenes", "Launch: next week"]}
                      className="hidden shrink-0 sm:block"
                    />
                  ) : null}
                  {i === 2 ? (
                    <ReelPreview caption="From our hands to your hearts" className="hidden shrink-0 sm:block" />
                  ) : null}
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Pill tone={s.impact.tone}>{s.impact.text}</Pill>
                  <Pill tone={s.confidence.tone}>{s.confidence.text}</Pill>
                  {i === 2 ? <TornStat label="Best time to post" value="7:30 PM" rotate={-1} /> : null}
                </div>
                <Why>{s.why}</Why>
                <Basis />
                <Action>{s.action}</Action>
              </Craft>
            </Reveal>
          ))}
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
