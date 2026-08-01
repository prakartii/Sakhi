import { createFileRoute } from "@tanstack/react-router";
import { Check, Coins, FileText, Hammer, ShieldCheck, Users } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import {
  Action,
  Basis,
  Craft,
  Eyebrow,
  HandNote,
  Meter,
  Pill,
  Why,
} from "@/components/sakhi/Cards";
import { IconBadge, PostageStamp } from "@/components/sakhi/CompanionAssets";

export const Route = createFileRoute("/schemes")({
  head: () => ({
    meta: [
      { title: "Schemes — five schemes are looking for someone exactly like you" },
      {
        name: "description",
        content:
          "Government and lending schemes matched against your own records, with the reason you qualify and the reason you don't yet.",
      },
      { property: "og:title", content: "Schemes matched to your records — Sakhi" },
      {
        property: "og:description",
        content: "PM Vishwakarma, Mudra, Udyam and more, matched to your business.",
      },
    ],
  }),
  component: Schemes,
});

const SCHEMES = [
  {
    name: "PM Vishwakarma",
    sub: "For traditional craft workers — block printing is a listed trade.",
    match: 92,
    pill: "₹15,000 toolkit + ₹3,00,000 credit at 5%",
    tone: "leaf" as const,
    icon: Hammer,
    why: "Your trade is on the 18-craft list, you have Aadhaar-linked Udyam registration, and six months of logged sales cover the income-proof requirement.",
  },
  {
    name: "Mudra — Kishore",
    sub: "Working-capital loan for micro-enterprises.",
    match: 88,
    pill: "Up to ₹1,50,000 collateral-free",
    tone: "rose" as const,
    icon: Coins,
    why: "Average monthly net of ₹19,800 over six months and no missed supplier payments put you inside the Kishore band; you'd have failed this in March.",
  },
  {
    name: "MSME Udyam benefits",
    sub: "Registration-linked benefits for micro units.",
    match: 84,
    pill: "Subsidised credit, ₹1,00,000 tender access",
    tone: "marigold" as const,
    icon: FileText,
    why: "You are already Udyam-registered — the unclaimed part is the interest subvention on your existing fabric credit line.",
  },
  {
    name: "Stand-Up India",
    sub: "Bank loans for women and SC/ST entrepreneurs.",
    match: 61,
    pill: "₹10,00,000 — ₹1,00,00,000",
    tone: "indigo" as const,
    icon: Users,
    why: "You qualify as a woman-led unit, but the minimum ticket size assumes a project around ₹10,00,000 — your current scale is a tenth of that.",
  },
  {
    name: "CGTMSE guarantee",
    sub: "Credit guarantee so banks don't ask for collateral.",
    match: 57,
    pill: "Guarantee covers up to ₹1,50,00,000",
    tone: "sand" as const,
    icon: ShieldCheck,
    why: "Applies once you take a loan above ₹1,50,000 — useful after Mudra, not instead of it.",
  },
];

const READINESS = [
  { done: true, title: "Udyam registration", sub: "UDYAM-RJ-17-004339" },
  { done: true, title: "6 months of records", sub: "47 logged entries" },
  { done: true, title: "Bank account linked to business", sub: "Jaipur co-op, since 2024" },
  { done: false, title: "GST registration", sub: "Not needed under ₹40L, but unlocks tenders" },
  { done: false, title: "Digital payment history", sub: "Only 34% of sales via UPI — aim for 70%" },
];

function Schemes() {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.1fr_0.9fr]">
        <Reveal>
          <div className="relative">
            <span className="inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
              Financial inclusion
            </span>
            <h1 className="mt-6 font-display font-semibold tracking-tight text-foreground">
              <span className="block text-3xl sm:text-4xl">Five schemes are</span>
              <span className="block text-4xl sm:text-5xl">looking for someone</span>
              <span className="block text-5xl text-[oklch(0.42_0.09_70)] italic sm:text-6xl">
                exactly like you.
              </span>
            </h1>
            <p className="mt-6 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
              Matched against your own records — with the reason you qualify, and the reason you
              don't yet.
            </p>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <div className="relative mx-auto w-full max-w-sm">
            <PostageStamp rotate={-8} className="absolute -top-5 -left-4 z-20 h-14 w-12" />
            <PostageStamp rotate={6} className="absolute -top-3 -right-5 z-20 h-14 w-12" />
            <MicPanel
              title="Ask about schemes"
              quote="&ldquo;Mujhe loan mil sakta hai?&rdquo;"
              className="relative z-10"
            />
          </div>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-5 py-10 lg:grid-cols-2">
        {SCHEMES.map((s, i) => (
          <Reveal key={s.name} delay={i * 70} className={i === 0 ? "lg:row-span-1" : ""}>
            <Craft tone={s.tone} texture={i % 2 === 0 ? "blockprint" : "weave"} className="h-full">
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-start gap-3">
                  <IconBadge icon={s.icon} tone={s.tone} />
                  <div className="min-w-0">
                    <h3 className="font-display text-xl font-semibold">{s.name}</h3>
                    <p className="mt-1 text-[12.5px] text-foreground/70">{s.sub}</p>
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <p className="font-display text-lg font-semibold text-wine">{s.match}%</p>
                  <Eyebrow>match</Eyebrow>
                </div>
              </div>
              <div className="mt-3">
                <Pill
                  tone={
                    s.tone === "leaf"
                      ? "leaf"
                      : s.tone === "indigo"
                        ? "indigo"
                        : s.tone === "marigold"
                          ? "marigold"
                          : "rose"
                  }
                >
                  {s.pill}
                </Pill>
              </div>
              <Meter value={s.match} />
              <Why>{s.why}</Why>
              <Basis />
              <Action>Start application</Action>
            </Craft>
          </Reveal>
        ))}

        <Reveal delay={120}>
          <Craft tone="leaf" texture="weave" className="h-full">
            <Eyebrow>Financial readiness</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">
              3 of 5 done — 2 unlock bigger money
            </h3>
            <ul className="mt-4 space-y-3">
              {READINESS.map((r) => (
                <li key={r.title} className="flex items-start gap-3">
                  <span
                    className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full ${
                      r.done ? "bg-leaf-ink text-primary-foreground" : "border border-clay/40"
                    }`}
                  >
                    {r.done ? <Check className="h-3 w-3" /> : null}
                  </span>
                  <span className="min-w-0">
                    <span className="block text-[13px] font-semibold">{r.title}</span>
                    <span className="block text-[11px] text-muted-foreground">{r.sub}</span>
                  </span>
                </li>
              ))}
            </ul>
            <Why>
              Moving UPI collections from 34% to 70% is the single fastest lift — lenders read
              digital receipts as verified income, and it raises your Mudra band by roughly ₹40,000.
            </Why>
            <Basis />
            <HandNote>Two boxes stand between you and ₹40,000 more.</HandNote>
          </Craft>
        </Reveal>
      </section>
    </Page>
  );
}
