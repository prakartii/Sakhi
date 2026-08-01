import { createFileRoute } from "@tanstack/react-router";
import { Heart, Landmark, Package, PartyPopper, TriangleAlert } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { Reveal } from "@/components/sakhi/Reveal";
import { BotanicalMark, ScrapbookBleed, StitchDivider } from "@/components/sakhi/CompanionAssets";
import {
  MemoryCard,
  StatusPill,
  StickyNote,
  TrustChip,
  VoiceCard,
} from "@/components/sakhi/CompanionHero";
import { FeaturedMetric, NoteMetric, TicketMetric } from "@/components/sakhi/CompanionMetrics";
import { MorningBriefing, type BriefingTask } from "@/components/sakhi/CompanionBriefing";
import { Action, Basis, Craft, Eyebrow, Why } from "@/components/sakhi/Cards";

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
        content:
          "One voice check-in in your own language. Sakhi remembers every order, price and supplier — then tells you what to do next.",
      },
    ],
  }),
  component: Companion,
});

const TASKS: BriefingTask[] = [
  {
    text: "3 pending tasks — Meena's dupatta order ships today (₹4,200).",
    tag: "Order",
    tone: "rose",
    icon: Package,
  },
  {
    text: "New scheme match: PM Vishwakarma toolkit grant — 92% fit.",
    tag: "Scheme",
    tone: "indigo",
    icon: Landmark,
  },
  {
    text: "Rakhi is in 18 days — last year you sold ₹38,000 in that week.",
    tag: "Festival",
    tone: "marigold",
    icon: PartyPopper,
  },
  {
    text: "Low stock: indigo block-print fabric — 8 days left.",
    tag: "Stock",
    tone: "leaf",
    icon: TriangleAlert,
  },
];

function Companion() {
  return (
    <Page>
      {/* ---------- Hero : memory wall ---------- */}
      <section className="relative overflow-hidden py-14 lg:py-20">
        <ScrapbookBleed className="pointer-events-none absolute inset-y-0 -right-10 hidden w-[52%] opacity-55 lg:block" />

        <div className="relative grid items-start gap-14 lg:grid-cols-[1fr_1.05fr] lg:gap-10">
          <Reveal>
            <div className="relative lg:pt-4">
              <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />

              <span className="relative inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
                Voice Companion
              </span>

              <h1 className="relative mt-6 font-display font-semibold tracking-tight text-foreground">
                <span className="block text-3xl sm:text-4xl">She speaks,</span>
                <span className="block text-4xl sm:text-5xl">and her day</span>
                <span className="relative inline-block text-5xl text-wine italic sm:text-6xl">
                  appears.
                  <Heart className="absolute -top-1 -right-7 h-4 w-4 -rotate-12 text-wine/40" />
                </span>
              </h1>

              <p className="relative mt-6 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
                One check-in in your own language. Sakhi remembers every order, price and supplier —
                then tells you what to do next.
              </p>

              <div className="relative mt-8 flex flex-wrap gap-2.5">
                <TrustChip>Voice-first</TrustChip>
                <TrustChip>Remembers everything</TrustChip>
                <TrustChip>7 Indian languages</TrustChip>
              </div>

              <StickyNote rotate={-3} className="relative z-10 mt-9">
                ✎ she remembers, so you don't have to
              </StickyNote>
            </div>
          </Reveal>

          <Reveal delay={120}>
            <div className="relative mx-auto w-full max-w-md pt-4 lg:mx-0 lg:ml-auto lg:pt-10">
              <MemoryCard
                tone="leaf"
                label="Today"
                rotate={-3}
                className="relative z-20 mb-4 lg:absolute lg:top-0 lg:-left-6 lg:mb-0"
              >
                <p className="text-xl leading-none font-semibold">₹6,480</p>
                <p className="mt-1 text-[11px] font-normal text-foreground/60">4 orders in</p>
              </MemoryCard>

              <StatusPill
                tone="indigo"
                rotate={2}
                className="relative z-20 mb-4 lg:absolute lg:top-4 lg:-right-2 lg:mb-0"
              >
                PM Vishwakarma — 92% fit
              </StatusPill>

              <VoiceCard
                title="Talk to Sakhi"
                quote="&ldquo;Aaj 12 dupatte beche, 3 hazaar ka kapda kharida.&rdquo;"
                languages="हिंदी · বাংলা · தமிழ் · తెలుగు · मराठी · ગુજરાતી · ಕನ್ನಡ"
                className="relative z-10"
              />

              <StatusPill
                tone="rose"
                rotate={-2}
                className="relative z-20 mt-4 ml-auto w-fit lg:absolute lg:-bottom-3 lg:left-6 lg:mt-0"
              >
                Low stock: indigo fabric
              </StatusPill>
            </div>
          </Reveal>
        </div>
      </section>

      <StitchDivider className="opacity-50" />

      {/* ---------- Metrics : three personalities ---------- */}
      <section className="grid gap-5 py-12 sm:grid-cols-12">
        <Reveal className="sm:col-span-5" delay={0}>
          <FeaturedMetric
            label="This month net"
            value="₹21,340"
            tag="+18% vs June"
            note="Across every order, sale and supplier payment you've logged this month."
            className="h-full"
          />
        </Reveal>
        <Reveal className="sm:col-span-4" delay={90}>
          <TicketMetric
            label="Today's sales"
            value="₹6,480"
            sub="4 orders"
            detail="≈ ₹1,620 per order"
            className="h-full"
          />
        </Reveal>
        <Reveal className="sm:col-span-3" delay={180}>
          <NoteMetric
            label="Pending payments"
            value="₹12,900"
            sub="2 buyers"
            detail="₹8,700 of it from the Bengaluru store"
            className="h-full"
          />
        </Reveal>
      </section>

      {/* ---------- Good morning : editorial intelligence board ---------- */}
      <Reveal>
        <MorningBriefing
          time="7:10 AM"
          place="Jaipur"
          name="Kavita ji"
          tasks={TASKS}
          why="Each line is drawn from 19 voice check-ins you logged this month, matched against your own order and payment history — not generic advice."
          basis="Based on what you've shared over the past 3 weeks."
          note="You've logged 19 days in a row. That's a business, not a hobby."
        />
      </Reveal>

      {/* ---------- Insight cards : distinct character each ---------- */}
      <section className="mt-10 grid gap-5 lg:grid-cols-12">
        <Reveal className="lg:col-span-4" delay={0}>
          <Craft
            tone="leaf"
            className="relative h-full overflow-hidden rounded-tl-[2.5rem] rounded-br-[2.5rem] border-2 border-dashed border-leaf-ink/25"
          >
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
          <Craft
            tone="rose"
            className="relative h-full overflow-hidden rounded-tr-[2.5rem] rounded-bl-[2.5rem] border-2 border-dashed border-wine/15"
          >
            <BotanicalMark className="pointer-events-none absolute -top-6 -right-6 h-32 w-28 opacity-[0.12]" />
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
          <Craft
            tone="marigold"
            className="relative h-full rounded-[1.25rem] rounded-tl-[2.5rem] border-2 border-dashed border-wine/20"
          >
            <span
              aria-hidden
              className="absolute -top-2.5 left-6 h-4 w-4 rounded-full ring-2 ring-wine/30"
              style={{ boxShadow: "0 1px 2px oklch(0.4 0.06 40 / 20%)" }}
            />
            <Eyebrow>Upcoming reminders</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">4 things this week</h3>
            <ul className="mt-3 space-y-2 text-[12.5px] text-foreground/75">
              <li>Today · Ship Meena's order — ₹4,200</li>
              <li>Wed · Follow up ₹8,700 payment from Bengaluru store</li>
              <li>Fri · Reorder indigo fabric — 40 metres</li>
              <li>Sun · Upload 6 Rakhi photos to marketplace</li>
            </ul>
            <Why>
              These four were spoken by you, not typed — Sakhi keeps the dates you mentioned.
            </Why>
            <Basis />
          </Craft>
        </Reveal>
      </section>
    </Page>
  );
}
