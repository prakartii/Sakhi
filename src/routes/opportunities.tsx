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

export const Route = createFileRoute("/opportunities")({
  head: () => ({
    meta: [
      { title: "Opportunity Engine — the right opportunities before you even look" },
      {
        name: "description",
        content:
          "Sales, schemes, learning and partnerships matched to your own records — each with the reason it fits and what it's worth in rupees.",
      },
      { property: "og:title", content: "Opportunity Engine — Sakhi" },
      {
        property: "og:description",
        content: "Matched sales, schemes, learning and partnerships worth ₹1,36,000.",
      },
    ],
  }),
  component: Opportunities,
});

const FILTERS = ["All", "Sales", "Schemes", "Learning", "Partnerships"];

const OPPS = [
  {
    kind: "Sales",
    match: "94% match",
    title: "Festive buyer hunting exactly what you make",
    copy: "A Bengaluru gifting company needs 120 hand-block dupattas before 6 September.",
    pill: { text: "₹96,000 potential", tone: "leaf" as const },
    tone: "leaf" as const,
    why: "Their brief specifies natural-dye block print at ₹750–₹850 — your June price and your 40-piece Bengaluru order prove you can deliver at that band.",
    action: "Submit your catalogue",
    span: "lg:col-span-7",
  },
  {
    kind: "Sales",
    match: "91% match",
    title: "ONDC storefront ready in 2 steps",
    copy: "Your listing is drafted; 12 product photos and GST are the only blockers.",
    pill: { text: "₹25,000/month potential", tone: "marigold" as const },
    tone: "marigold" as const,
    why: "Sellers in your craft and price band average ₹25,000 a month in their first quarter on ONDC — you already meet the record-keeping bar.",
    action: "Finish the listing",
    span: "lg:col-span-5",
  },
  {
    kind: "Schemes",
    match: "92% match",
    title: "PM Vishwakarma toolkit window closes 31 August",
    copy: "₹15,000 grant plus credit at 5% — applications reviewed in 3 weeks.",
    pill: { text: "₹15,000 grant", tone: "rose" as const },
    tone: "rose" as const,
    why: "You cleared the last eligibility gap in June; the next review cycle after August opens in December, after your festival season.",
    action: "Start application",
    span: "lg:col-span-5",
  },
  {
    kind: "Partnerships",
    match: "87% match",
    title: "Joint fabric order with Farida Bano",
    copy: "300-metre cotton lot split two ways, delivered to Sanganer.",
    pill: { text: "Saves ₹18/metre", tone: "indigo" as const },
    tone: "indigo" as const,
    why: "You both buy the same base cloth in 40–100 metre lots and pay the small-lot premium; combining hits the mill's 300-metre price.",
    action: "Send a joint order request",
    span: "lg:col-span-7",
  },
  {
    kind: "Learning",
    match: "78% match",
    title: "Product photography clinic · Jaipur, 9 August",
    copy: "Free 3-hour session run by the Craft Sellers collective.",
    pill: { text: "Unlocks Marketplace-Ready", tone: "leaf" as const },
    tone: "cream" as const,
    why: "Photos are one of your two remaining Marketplace-Ready steps, and this clinic is 6 km from your workshop on a weekday you rarely ship.",
    action: "Reserve a seat",
    span: "lg:col-span-6",
  },
  {
    kind: "Partnerships",
    match: "85% match",
    title: "Backup dyer trial in Sanganer",
    copy: "A 10-metre trial run at ₹230/metre, 4-day turnaround.",
    pill: { text: "Protects ₹9,000/month", tone: "marigold" as const },
    tone: "sand" as const,
    why: "Your single Bagru dyer has slipped three times in four months; a tested second source removes the recurring festival-season risk.",
    action: "Book the trial",
    span: "lg:col-span-6",
  },
];

function Opportunities() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.1fr_0.9fr]">
        <Reveal>
          <Hero
            eyebrow="Opportunity engine"
            title="The right opportunities"
            accent="before you even look."
            copy="Sales, schemes, learning and partnerships matched against your own records — each with the reason it fits and what it's worth in rupees."
          />
        </Reveal>
        <Reveal delay={120}>
          <MicPanel title="Ask what's worth doing" quote="&ldquo;Ab kya karna chahiye?&rdquo;" />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {[
          { label: "Open opportunities", value: "6", sub: "matched this week" },
          { label: "Combined potential", value: "₹1,36,000", sub: "if the top three land" },
          { label: "Nearest deadline", value: "31 Aug", sub: "PM Vishwakarma window" },
        ].map((s, i) => (
          <Reveal key={s.label} delay={i * 90}>
            <Stat {...s} />
          </Reveal>
        ))}
      </section>

      <div className="mb-6 flex flex-wrap gap-2">
        {FILTERS.map((f, i) => (
          <button
            key={f}
            className={`rounded-full px-4 py-1.5 text-xs transition-colors ${
              i === 0
                ? "bg-primary text-primary-foreground"
                : "border border-clay/30 bg-card text-muted-foreground hover:border-wine/30 hover:text-wine"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <section className="grid gap-5 lg:grid-cols-12">
        {OPPS.map((o, i) => (
          <Reveal key={o.title} delay={i * 70} className={o.span}>
            <Craft tone={o.tone} texture={i % 2 === 0 ? "blockprint" : "weave"} className="h-full">
              <div className="flex items-start justify-between gap-3">
                <Eyebrow>{o.kind}</Eyebrow>
                <span className="shrink-0 text-[11px] font-semibold text-wine">{o.match}</span>
              </div>
              <h3 className="mt-2 font-display text-xl leading-snug font-semibold">{o.title}</h3>
              <p className="mt-2 text-[13px] text-foreground/75">{o.copy}</p>
              <div className="mt-3">
                <Pill tone={o.pill.tone}>{o.pill.text}</Pill>
              </div>
              <Why>{o.why}</Why>
              <Basis />
              <Action>{o.action}</Action>
            </Craft>
          </Reveal>
        ))}
      </section>

      <HandNote>You didn't go looking for any of these. They came to your records.</HandNote>
    </Page>
  );
}
