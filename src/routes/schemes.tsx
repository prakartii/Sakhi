import { createFileRoute } from "@tanstack/react-router";
import {
  Check,
  Coins,
  FileText,
  Hammer,
  Landmark,
  Loader2,
  ShieldCheck,
  Users,
} from "lucide-react";
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
  type Tone,
  Why,
} from "@/components/sakhi/Cards";
import { IconBadge, PostageStamp } from "@/components/sakhi/CompanionAssets";
import { useSchemeMatches } from "@/hooks/use-schemes";
import type { SchemeMatch } from "@/lib/types";

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

const CARD_TONES: Tone[] = ["leaf", "rose", "marigold", "indigo", "sand"];
const PILL_TONES = ["leaf", "rose", "marigold", "indigo"] as const;

const SCHEME_ICONS: Record<string, typeof Hammer> = {
  "PM-VISHWAKARMA": Hammer,
  "MUDRA-KISHORE": Coins,
  "UDYAM-BENEFITS": FileText,
  "STANDUP-INDIA": Users,
  CGTMSE: ShieldCheck,
};

function iconFor(schemeCode: string | null) {
  return (schemeCode && SCHEME_ICONS[schemeCode]) || Landmark;
}

const READINESS = [
  {
    done: true,
    title: "Udyam registration",
    sub: "Add yours in Business Setup to unlock more matches",
  },
  {
    done: true,
    title: "Business profile complete",
    sub: "Registration type and business age drive your matches",
  },
  { done: false, title: "GST registration", sub: "Not needed under ₹40L, but unlocks tenders" },
  {
    done: false,
    title: "Digital payment history",
    sub: "More logged UPI sales strengthen your loan applications",
  },
];

function SchemeCard({ scheme, index }: { scheme: SchemeMatch; index: number }) {
  const tone = CARD_TONES[index % CARD_TONES.length]!;
  const Icon = iconFor(scheme.scheme_code);
  const roundedMatch = Math.round(scheme.match_score);

  return (
    <Craft tone={tone} texture={index % 2 === 0 ? "blockprint" : "weave"} className="h-full">
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <IconBadge icon={Icon} tone={tone === "cream" ? "rose" : tone} />
          <div className="min-w-0">
            <h3 className="font-display text-xl font-semibold">{scheme.scheme_name}</h3>
            <p className="mt-1 text-[12.5px] text-foreground/70">
              {scheme.issuing_authority ?? scheme.category ?? "Government scheme"}
            </p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <p className="font-display text-lg font-semibold text-wine">{roundedMatch}%</p>
          <Eyebrow>match</Eyebrow>
        </div>
      </div>
      {scheme.benefits ? (
        <div className="mt-3">
          <Pill tone={PILL_TONES[index % PILL_TONES.length]!}>{scheme.benefits}</Pill>
        </div>
      ) : null}
      {!scheme.is_eligible && (
        <div className="mt-2">
          <Pill tone="marigold">Not eligible yet</Pill>
        </div>
      )}
      <Meter value={roundedMatch} />
      <Why>{scheme.why}</Why>
      <Basis>{scheme.basis}</Basis>
      {scheme.application_url ? (
        <a
          href={scheme.application_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-xs font-medium text-primary-foreground transition-transform hover:translate-x-0.5"
        >
          Start application <span aria-hidden>→</span>
        </a>
      ) : (
        <Action>Start application</Action>
      )}
    </Craft>
  );
}

function Schemes() {
  const { data, isLoading, isError } = useSchemeMatches();
  const items = data?.items ?? [];

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
        {isLoading ? (
          <div className="col-span-full flex justify-center py-14">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : isError ? (
          <div className="card-soft col-span-full rounded-2xl px-6 py-10 text-center text-sm text-muted-foreground">
            Couldn't load your scheme matches right now — try again shortly.
          </div>
        ) : items.length === 0 ? (
          <div className="card-soft col-span-full rounded-2xl px-6 py-10 text-center text-sm text-muted-foreground">
            No schemes matched yet — complete your business profile in Business Setup for a better
            match.
          </div>
        ) : (
          items.map((scheme, i) => (
            <Reveal
              key={scheme.scheme_id}
              delay={i * 70}
              className={i === 0 ? "lg:row-span-1" : ""}
            >
              <SchemeCard scheme={scheme} index={i} />
            </Reveal>
          ))
        )}

        <Reveal delay={120}>
          <Craft tone="leaf" texture="weave" className="h-full">
            <Eyebrow>Financial readiness</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">
              {READINESS.filter((r) => r.done).length} of {READINESS.length} done
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
              A complete, Udyam-registered business profile is the single fastest lift — it raises
              your eligibility across every scheme on this page.
            </Why>
            <Basis />
            <HandNote>Two boxes stand between you and better matches.</HandNote>
          </Craft>
        </Reveal>
      </section>
    </Page>
  );
}
