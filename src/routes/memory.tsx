import { createFileRoute } from "@tanstack/react-router";
import { BookOpen, Clock, Sparkles, TrendingDown, TrendingUp } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Basis, Craft, Eyebrow, HandNote, Pill, Why } from "@/components/sakhi/Cards";
import { BotanicalMark, SpiralEdge } from "@/components/sakhi/CompanionAssets";
import { MemoryCard, StatusPill, StickyNote, TrustChip } from "@/components/sakhi/CompanionHero";
import {
  JournalWash,
  MemoryBanner,
  MemoryDot,
  PostageStamp,
} from "@/components/sakhi/MemoryAssets";

export const Route = createFileRoute("/memory")({
  head: () => ({
    meta: [
      { title: "Business Memory — Sakhi remembers what your business taught you" },
      {
        name: "description",
        content:
          "Every moment you've spoken about — priced, delayed, ordered, asked — kept in one timeline, tied to what it did to your money.",
      },
      { property: "og:title", content: "Business Memory — Sakhi" },
      {
        property: "og:description",
        content: "One timeline of every voice moment, tied to rupees.",
      },
    ],
  }),
  component: Memory,
});

const MOMENTS = [
  {
    date: "12 June · Price change",
    title: "Raised dupatta price ₹640 → ₹820",
    quote: "&ldquo;Kapda mehnga ho gaya, daam badha rahe hain.&rdquo;",
    pill: { text: "Sales +27% · margin ₹138 → ₹176", tone: "leaf" as const },
    why: "Buyers in Jaipur's craft market read hand-block work above ₹800 as premium; your repeat rate did not drop in the 6 weeks after.",
  },
  {
    date: "24 June · Supplier delay",
    title: "Indigo dye lot from Bagru delayed 9 days",
    quote: "&ldquo;Rangwala bola na hi 10 late ker dhiya.&rdquo;",
    pill: { text: "₹9,400 of orders slipped to July", tone: "rose" as const },
    why: "This is the third delay from the same dyer in 4 months — each one has cost you between ₹7,000 and ₹11,000 in slipped orders.",
  },
  {
    date: "2 July · Bulk order",
    title: "Bengaluru boutique ordered 40 dupattas",
    quote: "&ldquo;Bada order aaya hai, 40 piece.&rdquo;",
    pill: { text: "₹32,800 · ₹9,700 still pending", tone: "marigold" as const },
    why: "Your first order above ₹30,000. Six months of consistent invoices is what a lender looks for — this one moved you into loan range.",
  },
  {
    date: "8 July · Enquiry",
    title: "5 enquiries for Rakhi gift sets",
    quote: "&ldquo;Log rakhi ke liye do-do maang rahe hain.&rdquo;",
    pill: { text: "Est. ₹15,000 if bundled at ₹899", tone: "indigo" as const },
    why: "Paired enquiries jumped from 1/week to 5/week — the same shape as last year's pre-Rakhi curve.",
  },
  {
    date: "16 July · Cost",
    title: "Cotton base cloth up ₹28/metre",
    quote: "&ldquo;Kapda phir mehnga hua.&rdquo;",
    pill: { text: "Cost per piece +₹62", tone: "marigold" as const },
    why: "Your expenses are now growing faster than sales; at this rate the June price gain is gone by September unless you adjust again.",
  },
];

const INSIGHTS = [
  {
    label: "Moments remembered",
    value: "47",
    sub: "across 19 voice check-ins",
    icon: Sparkles,
  },
  {
    label: "Best decision so far",
    value: "₹18,600",
    sub: "extra revenue from the June price change",
    icon: TrendingUp,
  },
  {
    label: "Costliest pattern",
    value: "₹27,000",
    sub: "lost to one supplier's repeat delays",
    icon: TrendingDown,
  },
  {
    label: "Cash still owed to you",
    value: "₹9,700",
    sub: "one buyer, 21 days overdue",
    icon: Clock,
  },
];

function Memory() {
  return (
    <Page>
      <section className="relative overflow-hidden py-14 lg:py-20">
        <div className="relative grid items-start gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:gap-10">
          <Reveal>
            <div className="relative lg:pt-2">
              <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />

              <span className="relative inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
                Business Memory
              </span>

              <h1 className="relative mt-6 font-display font-semibold tracking-tight text-foreground">
                <span className="block text-3xl sm:text-4xl">Sakhi remembers</span>
                <span className="block text-4xl sm:text-5xl">what your business</span>
                <span className="block text-5xl text-wine italic sm:text-6xl">
                  already taught you.
                </span>
              </h1>

              <p className="relative mt-6 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
                Every moment you've spoken about — priced, delayed, ordered, asked — kept in one
                timeline, each tied to what it did to your money.
              </p>

              <div className="relative mt-7 flex flex-wrap gap-2.5">
                <TrustChip>One timeline</TrustChip>
                <TrustChip>Tied to your money</TrustChip>
                <TrustChip>Never re-typed</TrustChip>
              </div>

              <StickyNote rotate={-3} className="relative z-10 mt-8">
                ✎ she doesn't forget what mattered
              </StickyNote>
            </div>
          </Reveal>

          <Reveal delay={120}>
            <div className="relative mx-auto w-full max-w-sm pt-4 lg:mx-0 lg:ml-auto lg:pt-10">
              <JournalWash className="pointer-events-none absolute -inset-x-8 -inset-y-8 -z-10 hidden lg:block" />

              <MemoryCard
                tone="marigold"
                label="Remembered"
                rotate={-3}
                className="relative z-20 mb-4 lg:absolute lg:top-0 lg:-left-8 lg:mb-0"
              >
                <p className="text-xl leading-none font-semibold">47</p>
                <p className="mt-1 text-[11px] font-normal text-foreground/60">
                  moments, 19 check-ins
                </p>
              </MemoryCard>

              <StatusPill
                tone="rose"
                rotate={2}
                className="relative z-20 mb-4 w-fit lg:absolute lg:top-3 lg:-right-4 lg:mb-0"
              >
                Latest: price raised to ₹820
              </StatusPill>

              <div className="relative">
                <SpiralEdge className="absolute inset-y-4 -left-3 z-0 hidden w-5 sm:flex" />
                <span
                  aria-hidden
                  className="absolute -top-2.5 left-9 z-20 h-5 w-14 -rotate-3 bg-marigold/85"
                  style={{ boxShadow: "var(--shadow-soft)" }}
                />
                <span
                  aria-hidden
                  className="absolute -top-2.5 right-9 z-20 h-5 w-14 rotate-2 bg-rose/85"
                  style={{ boxShadow: "var(--shadow-soft)" }}
                />
                <MicPanel
                  title="Add a moment"
                  quote="&ldquo;Aaj kya hua?&rdquo;"
                  className="relative z-10"
                />
                <PostageStamp rotate={7} className="absolute -right-4 -bottom-5 z-20 h-12 w-10" />
              </div>

              <StatusPill
                tone="indigo"
                rotate={-2}
                className="relative z-20 mt-4 ml-auto w-fit lg:absolute lg:-bottom-4 lg:left-10 lg:mt-0"
              >
                8 weeks of memory kept
              </StatusPill>
            </div>
          </Reveal>
        </div>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-5 py-10 lg:grid-cols-[1.35fr_0.95fr]">
        <div className="relative space-y-5">
          <div className="mb-1 flex items-center gap-2 text-foreground/70">
            <BookOpen className="h-4 w-4" />
            <p className="text-sm font-semibold">Your Memory Journal</p>
          </div>
          <div
            aria-hidden
            className="absolute top-4 bottom-4 -left-1 hidden w-px bg-[repeating-linear-gradient(180deg,color-mix(in_oklab,var(--clay)_55%,transparent)_0_8px,transparent_8px_16px)] lg:block"
          />
          {MOMENTS.map((m, i) => (
            <Reveal key={m.title} delay={i * 70}>
              <Craft tone={i === 0 ? "sand" : "cream"} texture={i === 0 ? "weave" : undefined}>
                <div className="flex items-center gap-2">
                  <MemoryDot tone={m.pill.tone} />
                  <Eyebrow>{m.date}</Eyebrow>
                </div>
                <h3 className="mt-1.5 font-display text-xl font-semibold">{m.title}</h3>
                <p className="hand mt-1" dangerouslySetInnerHTML={{ __html: m.quote }} />
                <div className="mt-3">
                  <Pill tone={m.pill.tone}>{m.pill.text}</Pill>
                </div>
                <Why>{m.why}</Why>
                <Basis />
              </Craft>
            </Reveal>
          ))}
        </div>

        <Reveal delay={100}>
          <Craft
            tone="lilac"
            texture="blockprint"
            className="relative sticky top-28 overflow-hidden"
          >
            <BotanicalMark className="pointer-events-none absolute -top-6 -right-8 h-32 w-28 opacity-[0.1]" />
            <Eyebrow>Memory insights</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">What 8 weeks of memory says</h3>
            <div className="mt-4 space-y-3">
              {INSIGHTS.map((s) => (
                <div
                  key={s.label}
                  className="flex items-start gap-3 rounded-2xl border border-clay/20 bg-card/80 px-4 py-3 transition-transform hover:-translate-y-0.5"
                >
                  <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-lilac ring-1 ring-clay/20">
                    <s.icon className="h-3.5 w-3.5 text-wine" />
                  </span>
                  <div className="min-w-0">
                    <Eyebrow>{s.label}</Eyebrow>
                    <p className="mt-1 font-display text-xl font-semibold">{s.value}</p>
                    <p className="text-[11px] text-muted-foreground">{s.sub}</p>
                  </div>
                </div>
              ))}
            </div>
            <Why>
              Two of your five biggest revenue swings trace back to one dyer in Bagru. Adding a
              second one is worth more to you this quarter than any new product.
            </Why>
            <Basis />
            <HandNote>Your memory isn't nostalgia — it's working for you.</HandNote>
          </Craft>
        </Reveal>
      </section>

      <Reveal>
        <MemoryBanner
          quote="Sakhi remembers what your business already taught you."
          note="Your memory isn't nostalgia — it's working for you."
          className="mt-4"
        />
      </Reveal>
    </Page>
  );
}
