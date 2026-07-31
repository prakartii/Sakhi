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
  Stat,
  Why,
} from "@/components/sakhi/Cards";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Sakhi Companion — she speaks, and her day appears" },
      {
        name: "description",
        content:
          "One voice check-in in your own language. Sakhi remembers every order, price and supplier — then tells you what to do next.",
      },
      { property: "og:title", content: "Sakhi Companion — she speaks, and her day appears" },
      {
        property: "og:description",
        content: "Voice-first daily briefing for Indian women entrepreneurs.",
      },
    ],
  }),
  component: Companion,
});

function Companion() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <Hero
            eyebrow="Voice Companion"
            title="She speaks, and her day"
            accent="appears."
            copy="One check-in in your own language. Sakhi remembers every order, price and supplier — then tells you what to do next."
          />
        </Reveal>
        <Reveal delay={120}>
          <MicPanel
            title="Talk to Sakhi"
            quote="&ldquo;Aaj 12 dupatte beche, 3 hazaar ka kapda kharida.&rdquo;"
            languages="Works in हिंदी, বাংলা, தமிழ், తెలుగు, मराठी, ગુજરાતી, ಕನ್ನಡ"
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {[
          { label: "Today's sales", value: "₹6,480", sub: "4 orders" },
          { label: "Pending payments", value: "₹12,900", sub: "2 buyers" },
          { label: "This month net", value: "₹21,340", sub: "+18% vs June" },
        ].map((s, i) => (
          <Reveal key={s.label} delay={i * 90}>
            <Stat {...s} />
          </Reveal>
        ))}
      </section>

      <Reveal>
        <Craft tone="cream" texture="weave" className="p-7">
          <Eyebrow>7:10 AM · Jaipur</Eyebrow>
          <h2 className="mt-2 font-display text-2xl font-semibold">Good morning, Kavita ji</h2>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {[
              "3 pending tasks — Meena's dupatta order ships today (₹4,200).",
              "New scheme match: PM Vishwakarma toolkit grant — 92% fit.",
              "Rakhi is in 18 days — last year you sold ₹38,000 in that week.",
              "Low stock: indigo block-print fabric — 8 days left.",
            ].map((line) => (
              <p
                key={line}
                className="rounded-xl border border-clay/20 bg-ivory px-4 py-3 text-[13px] transition-colors hover:border-wine/25 hover:bg-sand"
              >
                {line}
              </p>
            ))}
          </div>
          <Why>
            Each line is drawn from 19 voice check-ins you logged this month, matched against your
            own order and payment history — not generic advice.
          </Why>
          <Basis />
          <HandNote>You've logged 19 days in a row. That's a business, not a hobby.</HandNote>
        </Craft>
      </Reveal>

      <section className="mt-6 grid gap-5 lg:grid-cols-12">
        <Reveal className="lg:col-span-4" delay={0}>
          <Craft tone="leaf" texture="blockprint" className="h-full">
            <Eyebrow>Daily briefing</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">Yesterday closed at ₹5,120</h3>
            <p className="mt-2 text-[13px] text-foreground/75">
              12 dupattas sold · ₹5,120 in. Fabric purchase · ₹3,000 out.
            </p>
            <p className="mt-3 text-sm font-semibold">
              Net for the day <span className="text-leaf-ink">₹2,120</span>
            </p>
            <Why>Margin per dupatta is ₹176 after the June price change — up from ₹138 in May.</Why>
            <Basis />
          </Craft>
        </Reveal>

        <Reveal className="lg:col-span-5" delay={110}>
          <Craft tone="rose" texture="weave" className="h-full">
            <Eyebrow>Smart suggestion</Eyebrow>
            <h3 className="mt-2 font-display text-2xl font-semibold">Raise Rakhi bundle to ₹899</h3>
            <p className="mt-2 text-[13px] text-foreground/75">
              A 2-dupatta gift bundle at ₹899 could add about ₹14,000 over the festival fortnight.
            </p>
            <Why>
              Last Rakhi, 61% of your buyers ordered two pieces together and none asked for a
              discount.
            </Why>
            <Basis />
            <Action>Create the bundle</Action>
          </Craft>
        </Reveal>

        <Reveal className="lg:col-span-3" delay={220}>
          <Craft tone="marigold" className="h-full">
            <Eyebrow>Upcoming reminders</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">4 things this week</h3>
            <ul className="mt-3 space-y-2 text-[12.5px] text-foreground/75">
              <li>Today · Ship Meena's order — ₹4,200</li>
              <li>Wed · Follow up ₹8,700 payment from Bengaluru store</li>
              <li>Fri · Reorder indigo fabric — 40 metres</li>
              <li>Sun · Upload 6 Rakhi photos to marketplace</li>
            </ul>
            <Why>These four were spoken by you, not typed — Sakhi keeps the dates you mentioned.</Why>
            <Basis />
          </Craft>
        </Reveal>
      </section>
    </Page>
  );
}
