import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Basis, Craft, Eyebrow, HandNote, Hero, Pill, Why } from "@/components/sakhi/Cards";

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
  { label: "Moments remembered", value: "47", sub: "across 19 voice check-ins" },
  { label: "Best decision so far", value: "₹18,600", sub: "extra revenue from the June price change" },
  { label: "Costliest pattern", value: "₹27,000", sub: "lost to one supplier's repeat delays" },
  { label: "Cash still owed to you", value: "₹9,700", sub: "one buyer, 21 days overdue" },
];

function Memory() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.1fr_0.9fr]">
        <Reveal>
          <Hero
            eyebrow="Business Memory"
            title="Sakhi remembers what your business already"
            accent="taught you."
            copy="Every moment you've spoken about — priced, delayed, ordered, asked — kept in one timeline, each tied to what it did to your money."
          />
        </Reveal>
        <Reveal delay={120}>
          <MicPanel title="Add a moment" quote="&ldquo;Aaj kya hua?&rdquo;" />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-5 py-10 lg:grid-cols-[1.35fr_0.95fr]">
        <div className="relative space-y-5">
          <div
            aria-hidden
            className="absolute top-4 bottom-4 -left-1 hidden w-px bg-[repeating-linear-gradient(180deg,color-mix(in_oklab,var(--clay)_55%,transparent)_0_8px,transparent_8px_16px)] lg:block"
          />
          {MOMENTS.map((m, i) => (
            <Reveal key={m.title} delay={i * 70}>
              <Craft tone={i === 0 ? "sand" : "cream"} texture={i === 0 ? "weave" : undefined}>
                <Eyebrow>{m.date}</Eyebrow>
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
          <Craft tone="lilac" texture="blockprint" className="sticky top-28">
            <Eyebrow>Memory insights</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">What 8 weeks of memory says</h3>
            <div className="mt-4 space-y-3">
              {INSIGHTS.map((s) => (
                <div
                  key={s.label}
                  className="rounded-2xl border border-clay/20 bg-card/80 px-4 py-3 transition-transform hover:-translate-y-0.5"
                >
                  <Eyebrow>{s.label}</Eyebrow>
                  <p className="mt-1 font-display text-xl font-semibold">{s.value}</p>
                  <p className="text-[11px] text-muted-foreground">{s.sub}</p>
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
    </Page>
  );
}
