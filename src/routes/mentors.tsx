import { createFileRoute } from "@tanstack/react-router";
import { Heart, Loader2, Percent, UserCheck, Users2 } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, type Tone, Why } from "@/components/sakhi/Cards";
import { IconBadge, WashiTape } from "@/components/sakhi/CompanionAssets";
import { useMentorMatches } from "@/hooks/use-mentors";
import type { MentorMatch } from "@/lib/types";

export const Route = createFileRoute("/mentors")({
  head: () => ({
    meta: [
      { title: "Mentors — women who already solved what you're facing" },
      {
        name: "description",
        content:
          "Mentors matched to your own business profile — expertise and availability, with the reason each one fits.",
      },
      { property: "og:title", content: "Mentors — Sakhi" },
      {
        property: "og:description",
        content: "Matched to your own business profile, not a directory to scroll through.",
      },
    ],
  }),
  component: Mentors,
});

const CARD_TONES: Tone[] = ["rose", "marigold", "leaf", "indigo"];

function MentorCard({ mentor, index }: { mentor: MentorMatch; index: number }) {
  const tone = CARD_TONES[index % CARD_TONES.length]!;
  const roundedMatch = Math.round(mentor.match_score);
  return (
    <Craft tone={tone} texture={index % 2 === 0 ? "weave" : "blockprint"} className="h-full">
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          {mentor.avatar_url ? (
            <img
              src={mentor.avatar_url}
              alt={mentor.full_name}
              className="h-10 w-10 shrink-0 rounded-full object-cover ring-1 ring-wine/20"
            />
          ) : (
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-card font-display text-sm text-wine ring-1 ring-wine/20">
              {mentor.full_name.charAt(0)}
            </span>
          )}
          <span className="min-w-0">
            <span className="block truncate font-display text-lg font-semibold">
              {mentor.full_name}
            </span>
            <span className="block text-[11px] text-muted-foreground">
              {mentor.industry_focus ?? "Mentor"}
              {mentor.years_experience ? ` · ${mentor.years_experience} years` : ""}
            </span>
          </span>
        </div>
        <span className="shrink-0 text-[11px] font-semibold text-wine">{roundedMatch}% match</span>
      </div>
      {mentor.bio ? <p className="mt-3 text-[13px] text-foreground/75">{mentor.bio}</p> : null}
      <p className="mt-2 text-[11px] text-muted-foreground">
        {mentor.availability_status === "available"
          ? "Available now"
          : mentor.availability_status === "busy"
            ? "Currently busy — worth a request anyway"
            : "Not currently available"}
      </p>
      <Why>{mentor.why}</Why>
      <Basis>{mentor.basis}</Basis>
      <Action>Request 30 minutes</Action>
    </Craft>
  );
}

function Mentors() {
  const { data, isLoading, isError } = useMentorMatches();
  const items = data?.items ?? [];
  const availableCount = items.filter((m) => m.availability_status === "available").length;
  const avgMatch = items.length
    ? Math.round(items.reduce((sum, m) => sum + m.match_score, 0) / items.length)
    : 0;

  const STATS = [
    {
      label: "Mentors matched",
      value: String(items.length),
      sub: "to your business profile",
      icon: Users2,
      tone: "lilac" as const,
    },
    {
      label: "Available now",
      value: String(availableCount),
      sub: "ready for a session",
      icon: UserCheck,
      tone: "indigo" as const,
    },
    {
      label: "Average match",
      value: items.length ? `${avgMatch}%` : "—",
      sub: "across your top matches",
      icon: Percent,
      tone: "leaf" as const,
    },
  ];

  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <div className="relative">
            <span className="inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
              Mentor network
            </span>
            <h1 className="mt-6 font-display font-semibold tracking-tight text-foreground">
              <span className="block text-3xl sm:text-4xl">Women who</span>
              <span className="block text-4xl sm:text-5xl">already solved</span>
              <span className="relative inline-block text-5xl text-[oklch(0.42_0.1_300)] italic sm:text-6xl">
                what you're facing.
                <Heart className="absolute -top-1 -right-7 h-4 w-4 -rotate-12 text-[oklch(0.42_0.1_300)]/40" />
              </span>
            </h1>
            <p className="mt-6 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
              Matched to your own business profile — not a directory to scroll through.
            </p>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <div className="relative mx-auto w-full max-w-sm pt-3">
            <WashiTape tone="indigo" rotate={-4} className="left-8 -top-2.5" />
            <WashiTape tone="rose" rotate={3} className="right-8 -top-2.5" />
            <MicPanel
              title="Ask for a mentor"
              quote="&ldquo;Isme kaun madad kar sakta hai?&rdquo;"
              className="relative z-10"
            />
          </div>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {STATS.map((s, i) => (
          <Reveal key={s.label} delay={i * 90}>
            <div className="card-soft lift flex items-center gap-3 rounded-2xl px-5 py-4">
              <IconBadge icon={s.icon} tone={s.tone} />
              <div className="min-w-0">
                <Eyebrow>{s.label}</Eyebrow>
                <p className="mt-1 font-display text-xl font-semibold text-foreground">{s.value}</p>
                <p className="text-[11px] text-muted-foreground">{s.sub}</p>
              </div>
            </div>
          </Reveal>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-12">
        {isLoading ? (
          <div className="col-span-full flex justify-center py-14">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : isError ? (
          <div className="card-soft col-span-full rounded-2xl px-6 py-10 text-center text-sm text-muted-foreground">
            Couldn't load your mentor matches right now — try again shortly.
          </div>
        ) : items.length === 0 ? (
          <Reveal className="col-span-full">
            <Craft tone="lilac" texture="weave">
              <Eyebrow>No mentors yet</Eyebrow>
              <h3 className="mt-2 font-display text-xl font-semibold">
                The mentor network is just getting started
              </h3>
              <p className="mt-2 text-[13px] text-foreground/75">
                As mentors join Sakhi, we'll match them to your business profile — expertise,
                industry and availability — the same way we match schemes to your records.
              </p>
              <Why>
                Nobody's been fabricated here — this list stays empty until a real mentor with real
                availability exists to match.
              </Why>
              <Basis />
            </Craft>
          </Reveal>
        ) : (
          items.map((mentor, i) => (
            <Reveal
              key={mentor.mentor_id}
              delay={i * 80}
              className={i % 2 === 0 ? "lg:col-span-7" : "lg:col-span-5"}
            >
              <MentorCard mentor={mentor} index={i} />
            </Reveal>
          ))
        )}
      </section>
    </Page>
  );
}
