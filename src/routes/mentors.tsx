import { createFileRoute } from "@tanstack/react-router";
import { Heart, IndianRupee, Users2, Video } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, HandNote, Pill, Why } from "@/components/sakhi/Cards";
import { IconBadge, WashiTape } from "@/components/sakhi/CompanionAssets";

export const Route = createFileRoute("/mentors")({
  head: () => ({
    meta: [
      { title: "Mentors — women who already solved what you're facing" },
      {
        name: "description",
        content:
          "Mentors matched to the exact problem in your records — supplier risk, pricing, marketplace listing — with the reason each one fits.",
      },
      { property: "og:title", content: "Mentors — Sakhi" },
      {
        property: "og:description",
        content: "Matched to the exact problem your records show this month.",
      },
    ],
  }),
  component: Mentors,
});

const MENTORS = [
  {
    name: "Shabnam Qureshi",
    role: "Block-print exporter · Bagru, 14 years",
    match: "93% match",
    copy: "Runs three dyers on rotation and has never missed a festival order.",
    pill: { text: "Solves your ₹27,000 supplier risk", tone: "rose" as const },
    tone: "rose" as const,
    why: "Your three logged Bagru delays are the exact problem she solved in 2019 by splitting lots across Sanganer and Bagru.",
    action: "Request 30 minutes",
    span: "lg:col-span-7",
  },
  {
    name: "Lakshmi Iyer",
    role: "Pricing & margin coach · Yuukke Catalyst",
    match: "89% match",
    copy: "Works with craft sellers on cost-plus pricing that survives raw-material swings.",
    pill: { text: "Protects ₹2,740/month", tone: "marigold" as const },
    tone: "marigold" as const,
    why: "Your costs are rising 36% against 18% sales growth — her price-ladder method is built for exactly this squeeze.",
    action: "Book a session",
    span: "lg:col-span-5",
  },
  {
    name: "Priya Nandakumar",
    role: "ONDC & marketplace seller · Coimbatore",
    match: "86% match",
    copy: "Took a 6-piece handloom catalogue to ₹40,000 a month online in nine months.",
    pill: { text: "Unlocks ₹25,000/month channel", tone: "leaf" as const },
    tone: "leaf" as const,
    why: "Photos and GST are your last two Marketplace-Ready steps — the same two she cleared before her first online sale.",
    action: "Ask how she listed",
    span: "lg:col-span-5",
  },
  {
    name: "Farida Bano",
    role: "Peer entrepreneur · Sanganer",
    match: "84% match",
    copy: "Buys the same cotton base cloth in the same lot sizes as you.",
    pill: { text: "Saves ₹18/metre together", tone: "indigo" as const },
    tone: "indigo" as const,
    why: "A peer, not a teacher — your combined 300-metre order clears the mill's bulk band that neither of you reaches alone.",
    action: "Send an introduction",
    span: "lg:col-span-7",
  },
];

const STATS = [
  {
    label: "Mentors matched",
    value: "4",
    sub: "to problems in your own records",
    icon: Users2,
    tone: "lilac" as const,
  },
  {
    label: "Sessions taken",
    value: "7",
    sub: "since February",
    icon: Video,
    tone: "indigo" as const,
  },
  {
    label: "Value traced back",
    value: "₹31,000",
    sub: "from the June pricing session",
    icon: IndianRupee,
    tone: "leaf" as const,
  },
];

function Mentors() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <div className="relative">
            <span className="inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
              Mentor network
            </span>
            <h1 className="mt-6 font-display font-semibold tracking-tight text-foreground">
              <span className="block text-3xl sm:text-4xl">Women who</span>
              <span className="block text-4xl sm:text-5xl">already solved</span>
              <span className="relative inline-block text-5xl text-[oklch(0.42_0.1_300)] italic sm:text-6xl">
                what you're facing.
                <Heart className="absolute -top-1 -right-7 h-4 w-4 -rotate-12 text-[oklch(0.42_0.1_300)]/40" />
              </span>
            </h1>
            <p className="mt-6 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
              Matched to the exact problem in your records this month — not a directory to scroll
              through.
            </p>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <div className="relative mx-auto w-full max-w-sm pt-3">
            <WashiTape tone="indigo" rotate={-4} className="left-8 -top-2.5" />
            <WashiTape tone="rose" rotate={3} className="right-8 -top-2.5" />
            <MicPanel
              title="Ask for a mentor"
              quote="&ldquo;Isme kaun madad kar sakta hai?&rdquo;"
              className="relative z-10"
            />
          </div>
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

      <section className="grid gap-5 lg:grid-cols-12">
        {MENTORS.map((m, i) => (
          <Reveal key={m.name} delay={i * 80} className={m.span}>
            <Craft tone={m.tone} texture={i % 2 === 0 ? "weave" : "blockprint"} className="h-full">
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-card font-display text-sm text-wine ring-1 ring-wine/20">
                    {m.name.charAt(0)}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate font-display text-lg font-semibold">
                      {m.name}
                    </span>
                    <span className="block text-[11px] text-muted-foreground">{m.role}</span>
                  </span>
                </div>
                <span className="shrink-0 text-[11px] font-semibold text-wine">{m.match}</span>
              </div>
              <p className="mt-3 text-[13px] text-foreground/75">{m.copy}</p>
              <div className="mt-3">
                <Pill tone={m.pill.tone}>{m.pill.text}</Pill>
              </div>
              <Why>{m.why}</Why>
              <Basis />
              <Action>{m.action}</Action>
            </Craft>
          </Reveal>
        ))}
      </section>

      <Reveal className="mt-6">
        <Craft tone="lilac" texture="weave">
          <Eyebrow>Next conversation</Eyebrow>
          <h3 className="mt-2 font-display text-xl font-semibold">
            One call before 4 August is worth more than four in September
          </h3>
          <p className="mt-2 text-[13px] text-foreground/75">
            Shabnam's dyer rotation takes two weeks to set up — starting after Rakhi means carrying
            the same risk through Diwali.
          </p>
          <Why>
            Your two costliest months, June and October last year, both followed a supplier delay
            that a second dyer would have absorbed.
          </Why>
          <Basis />
          <Action>Request 30 minutes with Shabnam</Action>
          <HandNote>Every woman on this list was where you are, with worse records.</HandNote>
        </Craft>
      </Reveal>
    </Page>
  );
}
