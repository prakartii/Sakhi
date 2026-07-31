import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, HandNote, Hero, Stat, Why } from "@/components/sakhi/Cards";

export const Route = createFileRoute("/cashflow")({
  head: () => ({
    meta: [
      { title: "Cashflow — your money, explained in sentences" },
      {
        name: "description",
        content:
          "What came in, what went out, and the one thing to fix this month before it costs you. Sakhi explains cashflow in plain sentences, not spreadsheets.",
      },
      { property: "og:title", content: "Cashflow — your money, explained in sentences" },
      {
        property: "og:description",
        content: "Financial health for micro-entrepreneurs, without spreadsheets.",
      },
    ],
  }),
  component: Cashflow,
});

const POINTS = [
  { m: "Feb", v: 32000 },
  { m: "Mar", v: 34500 },
  { m: "Apr", v: 38000 },
  { m: "May", v: 41000 },
  { m: "Jun", v: 52000 },
  { m: "Jul", v: 61800 },
];

function TrendLine() {
  const w = 640;
  const h = 150;
  const min = 30000;
  const max = 64000;
  const path = POINTS.map((p, i) => {
    const x = (i / (POINTS.length - 1)) * w;
    const y = h - ((p.v - min) / (max - min)) * h;
    return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

  return (
    <div className="mt-4">
      <svg viewBox={`0 0 ${w} ${h + 22}`} className="w-full" role="img" aria-label="Sales trend">
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
        {POINTS.map((p, i) => (
          <text
            key={p.m}
            x={(i / (POINTS.length - 1)) * w}
            y={h + 16}
            textAnchor={i === 0 ? "start" : i === POINTS.length - 1 ? "end" : "middle"}
            className="fill-[oklch(0.53_0.025_50)] text-[10px]"
          >
            {p.m}
          </text>
        ))}
      </svg>
    </div>
  );
}

const STAGES = [
  { n: 1, title: "Getting started", copy: "First voice check-in, Feb 2026", done: true },
  { n: 2, title: "First sale logged", copy: "₹640 dupatta, 9 Feb", done: true },
  {
    n: 3,
    title: "Finance-Ready",
    copy: "6 months of records · Mudra & Vishwakarma eligible",
    done: true,
  },
  { n: 4, title: "Marketplace-Ready", copy: "Needs 12 product photos + GST — 2 steps left", done: false },
];

function Cashflow() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <Hero
            eyebrow="Cashflow & financial health"
            title="Your money, explained in sentences —"
            accent="not spreadsheets."
            copy="What came in, what went out, and the one thing to fix this month before it costs you."
          />
        </Reveal>
        <Reveal delay={120}>
          <MicPanel title="Ask about money" quote="&ldquo;Is mahine kitna bacha?&rdquo;" />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {[
          { label: "Money in (July)", value: "₹61,800", sub: "22 orders" },
          { label: "Money out (July)", value: "₹40,460", sub: "fabric, dye, courier, labour" },
          { label: "Net kept", value: "₹21,340", sub: "+18% vs June" },
        ].map((s, i) => (
          <Reveal key={s.label} delay={i * 90}>
            <Stat {...s} />
          </Reveal>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-12">
        <Reveal className="lg:col-span-5">
          <Craft tone="sand" texture="weave" className="h-full">
            <Eyebrow>Watch this</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">
              Sales are up, but expenses are rising faster
            </h3>
            <p className="mt-2 text-[13px] text-foreground/75">
              Sales grew 18% since June. Costs grew 36% — if both hold, your monthly savings drop
              from ₹21,340 to about ₹18,600 by September.
            </p>
            <p className="mt-3 text-sm font-semibold text-wine">−₹2,740 / month if unchanged</p>
            <Why>
              Cotton base cloth went up ₹28 a metre on 16 July and courier charges rose ₹15 a parcel
              — together that's ₹57 more cost on every piece you sell.
            </Why>
            <Basis />
            <Action>Adjust prices by ₹60</Action>
          </Craft>
        </Reveal>

        <Reveal className="lg:col-span-7" delay={110}>
          <Craft tone="leaf" texture="blockprint" className="h-full">
            <Eyebrow>Good news</Eyebrow>
            <h3 className="mt-2 font-display text-2xl font-semibold">
              You now qualify for a micro-loan
            </h3>
            <p className="mt-2 text-[13px] text-foreground/75">
              Up to ₹1,50,000 under Mudra Kishore, collateral-free. At your current margin, a
              ₹60,000 loan for fabric stock pays for itself in about 5 months.
            </p>
            <p className="mt-3 text-sm font-semibold text-leaf-ink">₹1,50,000 available</p>
            <Why>
              Six unbroken months of logged sales, average monthly net above ₹15,000, and no missed
              supplier payments put you inside the Kishore band — you'd have failed this in March.
            </Why>
            <Basis />
            <Action>See scheme match</Action>
          </Craft>
        </Reveal>
      </section>

      <Reveal className="mt-6">
        <Craft tone="cream">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <Eyebrow>Sales trend · last 6 months</Eyebrow>
            <span className="text-[11px] text-muted-foreground">₹32,000 → ₹61,800</span>
          </div>
          <TrendLine />
          <Why>
            The step up in June is the price change you logged on 12 June, not more customers — your
            order count only moved from 21 to 22.
          </Why>
          <Basis />
        </Craft>
      </Reveal>

      <Reveal className="mt-6" delay={80}>
        <Craft tone="lilac" texture="weave">
          <Eyebrow>Growth journey</Eyebrow>
          <h3 className="mt-2 font-display text-xl font-semibold">
            You are 2 steps from Marketplace-Ready
          </h3>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {STAGES.map((s) => (
              <div
                key={s.n}
                className="rounded-2xl border border-clay/20 bg-card/85 px-4 py-3 transition-transform hover:-translate-y-1"
              >
                <span
                  className={`grid h-6 w-6 place-items-center rounded-full text-[11px] font-semibold ${
                    s.done ? "bg-wine text-primary-foreground" : "bg-sand text-muted-foreground"
                  }`}
                >
                  {s.n}
                </span>
                <p className="mt-2 text-[13px] font-semibold">{s.title}</p>
                <p className="mt-1 text-[11px] text-muted-foreground">{s.copy}</p>
              </div>
            ))}
          </div>
          <Why>
            Each stage is earned from your own records: 47 logged entries, ₹2,94,000 of tracked
            sales and a linked bank account. Photos and GST are the only gaps left.
          </Why>
          <Basis />
          <HandNote>Six months ago you weren't sure you had a business. The records say you do.</HandNote>
        </Craft>
      </Reveal>
    </Page>
  );
}
