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
  Meter,
  Pill,
  Stat,
  Why,
} from "@/components/sakhi/Cards";

export const Route = createFileRoute("/inventory")({
  head: () => ({
    meta: [
      { title: "Smart Inventory — you counted your stock out loud" },
      {
        name: "description",
        content:
          "Every bought 100, sold 72 becomes a date — the day you run out, and the day to reorder before it.",
      },
      { property: "og:title", content: "Smart Inventory — Sakhi did the rest" },
      {
        property: "og:description",
        content: "Voice-logged stock turned into reorder dates and protected revenue.",
      },
    ],
  }),
  component: Inventory,
});

const ITEMS = [
  {
    name: "Indigo block-print base cloth",
    quote: "&ldquo;100 metre khareeda, 72 metre stock re raya.&rdquo;",
    line: "Bought 100 · used 72 · 28 metres left",
    pct: 28,
    pills: [
      { text: "Runs out in ~8 days", tone: "rose" as const },
      { text: "₹11,200 of promised orders at risk", tone: "marigold" as const },
    ],
    why: "5.1 metres a day since 3 July, and Rakhi orders will push it to 6.4 — that's a stockout on 4 August.",
    tone: "cream" as const,
    span: "lg:col-span-7",
  },
  {
    name: "Finished dupattas (ready to ship)",
    quote: "&ldquo;Aaj 12 bache, 1 aur bana.&rdquo;",
    line: "Bought 64 · used 51 · 13 pieces left",
    pct: 20,
    pills: [
      { text: "Runs out in ~5 days", tone: "rose" as const },
      { text: "Incl. ₹8,900 in invoiced Rakhi sales", tone: "marigold" as const },
    ],
    why: "You sell 3 a day normally, but festival weeks have run at 7 a day for the last two years.",
    tone: "sand" as const,
    span: "lg:col-span-5",
  },
  {
    name: "Natural indigo dye",
    quote: "&ldquo;Rang 8 kilo saya tha, 2 bacha hai.&rdquo;",
    line: "Bought 6 · used 4 · 2 kg left",
    pct: 33,
    pills: [
      { text: "Runs out in ~14 days", tone: "indigo" as const },
      { text: "Comfortable — order in 5 days", tone: "leaf" as const },
    ],
    why: "Usage is steady at ₹410 per metre dyed; Bagru delivery takes 9 days, so order by 5 August.",
    tone: "indigo" as const,
    span: "lg:col-span-5",
  },
  {
    name: "Gift packaging boxes",
    quote: "&ldquo;Dabbe khatam hone wale hain.&rdquo;",
    line: "Bought 150 · used 132 · 18 boxes left",
    pct: 12,
    pills: [
      { text: "Runs out in ~4 days", tone: "rose" as const },
      { text: "Blocks the ₹18,000 bundle plan", tone: "marigold" as const },
    ],
    why: "The ₹899 Rakhi bundle needs one box per order — 14 confirmed orders leave you 4 short.",
    tone: "rose" as const,
    span: "lg:col-span-7",
  },
];

function Inventory() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <Hero
            eyebrow="Smart inventory"
            title="You counted your stock out loud."
            accent="Sakhi did the rest."
            copy="Every bought 100, sold 72 becomes a date — the day you run out, and the day to reorder before it."
          />
        </Reveal>
        <Reveal delay={120}>
          <MicPanel title="Update stock" quote="&ldquo;Aaj 12 bache.&rdquo;" />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {[
          { label: "Items tracked by voice", value: "11", sub: "no forms, no typing" },
          { label: "Nearest stockout", value: "4 days", sub: "gift packaging boxes" },
          { label: "Revenue protected", value: "₹35,000", sub: "if all 4 reorders go out this week" },
        ].map((s, i) => (
          <Reveal key={s.label} delay={i * 90}>
            <Stat {...s} />
          </Reveal>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-12">
        {ITEMS.map((it, i) => (
          <Reveal key={it.name} delay={i * 80} className={it.span}>
            <Craft tone={it.tone} texture={i % 2 === 0 ? "weave" : "blockprint"} className="h-full">
              <h3 className="font-display text-xl font-semibold">{it.name}</h3>
              <p className="hand mt-1" dangerouslySetInnerHTML={{ __html: it.quote }} />
              <p className="mt-2 text-[12.5px] text-foreground/70">{it.line}</p>
              <Meter value={it.pct} tone={it.pct < 25 ? "wine" : "clay"} />
              <div className="mt-3 flex flex-wrap gap-2">
                {it.pills.map((p) => (
                  <Pill key={p.text} tone={p.tone}>
                    {p.text}
                  </Pill>
                ))}
              </div>
              <Why>{it.why}</Why>
              <Basis />
              <Action>Reorder now</Action>
            </Craft>
          </Reveal>
        ))}
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-2">
        <Reveal>
          <Craft tone="marigold" className="h-full">
            <Eyebrow>Restock reminders</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">Three calls to make this week</h3>
            <ul className="mt-3 space-y-2 text-[12.5px] text-foreground/75">
              <li>Mon · Packaging supplier, Johari Bazaar — 200 boxes, ₹3,400</li>
              <li>Wed · Bagru dyer — 40 metres indigo cloth, ₹9,200 (9-day lead)</li>
              <li>Fri · Sanganer backup dyer — first trial order, 10 metres</li>
            </ul>
            <Why>
              The Friday trial order costs ₹2,300 and removes the single supplier risk that has
              already cost you ₹27,000 in slipped orders.
            </Why>
            <Basis />
          </Craft>
        </Reveal>

        <Reveal delay={90}>
          <Craft tone="rose" texture="weave" className="h-full">
            <Eyebrow>Festival demand plan</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">
              Rakhi in 18 days · Diwali in 96
            </h3>
            <p className="mt-2 text-[13px] text-foreground/75">
              Hold back 30 finished dupattas for Rakhi week and keep 30 metres of cloth in reserve —
              last Rakhi you sold ₹38,000 and turned away 7 buyers.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Pill tone="leaf">Last Rakhi: ₹38,000 in 7 days</Pill>
              <Pill tone="marigold">7 buyers turned away</Pill>
            </div>
            <Why>
              Your festival curve runs 2.2× a normal week and starts 10 days before the date — stock
              bought after 30 July will arrive too late to sell.
            </Why>
            <Basis />
            <HandNote>Last year you ran out on day four. This year you already know.</HandNote>
          </Craft>
        </Reveal>
      </section>
    </Page>
  );
}
