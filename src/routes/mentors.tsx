import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import {
  Action,
  Basis,
  Craft,
  Eyebrow,
  HandNote,
  Hero,
  Pill,
  Stat,
  Why,
} from "@/components/sakhi/Cards";

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

function Mentors() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <Hero
            eyebrow="Mentor network"
            title="Women who already solved"
            accent="what you're facing."
            copy="Matched to the exact problem in your records this month — not a directory to scroll through."
          />
        </Reveal>
        <Reveal delay={120}>
          <MicPanel title="Ask for a mentor" quote="&ldquo;Isme kaun madad kar sakta hai?&rdquo;" />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {[
          { label: "Mentors matched", value: "4", sub: "to problems in your own records" },
          { label: "Sessions taken", value: "7", sub: "since February" },
          { label: "Value traced back", value: "₹31,000", sub: "from the June pricing session" },
        ].map((s, i) => (
          <Reveal key={s.label} delay={i * 90}>
            <Stat {...s} />
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
