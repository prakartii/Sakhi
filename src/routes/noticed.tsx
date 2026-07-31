import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, HandNote, Hero, Pill, Why } from "@/components/sakhi/Cards";

export const Route = createFileRoute("/noticed")({
  head: () => ({
    meta: [
      { title: "Sakhi noticed something before you had to" },
      {
        name: "description",
        content:
          "Five predictive warnings from your own records — what happened, why it matters to your rupees, and the single next step.",
      },
      { property: "og:title", content: "Sakhi noticed something before you had to" },
      {
        property: "og:description",
        content: "Predictive intelligence built on your own voice-logged records.",
      },
    ],
  }),
  component: Noticed,
});

const SIGNALS = [
  {
    tag: "Stockout predicted",
    tone: "marigold" as const,
    title: "Indigo block-print base cloth will run out in about 8 days.",
    copy: "You have 14 Rakhi orders promised for that same week — ₹11,200 at risk.",
    pill: { text: "Protects ₹11,200", tone: "marigold" as const },
    why: "You've logged 100 metres in on 3 July and 72 metres sold by 28 July — a steady 5.1 metres a day.",
    action: "Reorder 40 metres from Bagru",
    span: "lg:col-span-7",
  },
  {
    tag: "Festival demand rising",
    tone: "rose" as const,
    title: "Rakhi enquiries jumped from 1 to 5 a week.",
    copy: "Last Rakhi week you did ₹38,000 — the curve is 6 days ahead of last year.",
    pill: { text: "Est. +₹15,000", tone: "rose" as const },
    why: "Paired-piece enquiries always lead your festival sales by about two weeks; the same pattern held for Diwali 2025.",
    action: "List the ₹899 gift bundle",
    span: "lg:col-span-5",
  },
  {
    tag: "Sales dip",
    tone: "indigo" as const,
    title: "Weekday sales fell 22% over the last 10 days.",
    copy: "That's roughly ₹4,600 less than your own July average.",
    pill: { text: "₹4,700 pending too", tone: "indigo" as const },
    why: "The dip started the day your Bengaluru boutique paused reorders — retail, not demand. Your direct buyers are steady.",
    action: "Call the boutique buyer",
    span: "lg:col-span-5",
  },
  {
    tag: "Supplier delay",
    tone: "rose" as const,
    title: "Your Bagru dyer is likely to be late again this month.",
    copy: "Three delays in four months have cost ₹27,000 in slipped orders.",
    pill: { text: "Avoids ₹9,000/month", tone: "rose" as const },
    why: "Each delay has landed in the second half of the month, right after his own festival-season bulk orders start.",
    action: "Add a backup dyer in Sanganer",
    span: "lg:col-span-7",
  },
  {
    tag: "New scheme match",
    tone: "leaf" as const,
    title: "You now match PM Vishwakarma at 92%.",
    copy: "A ₹15,000 toolkit grant plus collateral-free credit at 5%.",
    pill: { text: "₹15,000 grant", tone: "leaf" as const },
    why: "Your craft category, six months of logged sales and Udyam registration cleared the last three conditions you were missing in May.",
    action: "See eligibility reasoning",
    span: "lg:col-span-6",
  },
];

function Noticed() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <Hero
            eyebrow="Predictive intelligence"
            title="Sakhi noticed something"
            accent="before you had to."
            copy="Five things worth your attention this week. Each one says what happened, why it matters to your rupees, and the single next step."
          />
        </Reveal>
        <Reveal delay={120}>
          <MicPanel title="Ask Sakhi why" quote="&ldquo;Iska kya matlab hai?&rdquo;" />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-5 py-10 lg:grid-cols-12">
        {SIGNALS.map((s, i) => (
          <Reveal key={s.title} delay={i * 80} className={s.span}>
            <Craft tone={s.tone} texture={i % 2 === 0 ? "weave" : "blockprint"} className="h-full">
              <Eyebrow>{s.tag}</Eyebrow>
              <h3 className="mt-2 font-display text-xl leading-snug font-semibold">{s.title}</h3>
              <p className="mt-2 text-[13px] text-foreground/75">{s.copy}</p>
              <div className="mt-3">
                <Pill tone={s.pill.tone}>{s.pill.text}</Pill>
              </div>
              <Why>{s.why}</Why>
              <Basis />
              <Action>{s.action}</Action>
            </Craft>
          </Reveal>
        ))}
      </section>

      <HandNote>Five spotted warnings this week. Last month you caught three of them in time.</HandNote>
    </Page>
  );
}
