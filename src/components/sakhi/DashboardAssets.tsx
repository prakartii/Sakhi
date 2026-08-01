import type { ComponentType, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Meter } from "@/components/sakhi/Cards";
import {
  BotanicalMark,
  DECKLE_EDGE,
  DeckleCard,
  IconBadge,
  StitchDivider,
  TextileSwatch,
  WashiTape,
} from "@/components/sakhi/CompanionAssets";

/**
 * Dashboard-page-only pieces, built on the shared CompanionAssets/Cards
 * kit. Not imported anywhere else — safe to iterate on without touching
 * the Companion or Memory pages.
 */

export type JournalTone = "rose" | "leaf" | "marigold" | "indigo" | "lilac" | "sand";

const TONE_BG: Record<JournalTone, string> = {
  rose: "bg-rose",
  leaf: "bg-leaf",
  marigold: "bg-marigold",
  indigo: "bg-indigo-tint",
  lilac: "bg-lilac",
  sand: "bg-sand",
};

const TAPE_TONE: Record<JournalTone, "marigold" | "rose" | "leaf" | "indigo" | "clay"> = {
  rose: "rose",
  leaf: "leaf",
  marigold: "marigold",
  indigo: "indigo",
  lilac: "clay",
  sand: "clay",
};

/** The large "Good morning" journal card that opens the dashboard. */
export function GreetingCard({
  time,
  place,
  name,
  summary,
  className,
}: {
  time: string;
  place: string;
  name: string;
  summary: ReactNode;
  className?: string;
}) {
  return (
    <DeckleCard
      paperClassName="bg-card border-2 border-dashed border-wine/20"
      className={cn("relative overflow-hidden px-7 py-9 sm:px-10 sm:py-10", className)}
      style={{ boxShadow: "var(--shadow-lift)" }}
    >
      <BotanicalMark className="pointer-events-none absolute -top-8 -right-10 h-40 w-32 opacity-[0.08]" />
      <span
        className="relative inline-flex items-center gap-1.5 rounded-sm bg-ivory px-3 py-1.5 text-[10.5px] font-semibold tracking-[0.16em] text-muted-foreground uppercase ring-1 ring-clay/25"
        style={{ boxShadow: "var(--shadow-soft)", transform: "rotate(-1.5deg)" }}
      >
        <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-wine/50" />
        {time} · {place}
      </span>
      <h1 className="font-display relative mt-5 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
        Good morning, {name} <span aria-hidden>🌸</span>
      </h1>
      <p className="relative mt-4 max-w-xl text-[14.5px] leading-relaxed text-foreground/75">
        {summary}
      </p>
      <StitchDivider className="relative mt-6" />
    </DeckleCard>
  );
}

/** One card in the horizontally-scrolling Daily Focus strip. */
export function FocusChip({
  icon: Icon,
  tone,
  label,
  note,
  className,
}: {
  icon: ComponentType<{ className?: string }>;
  tone: JournalTone;
  label: string;
  note: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex min-w-[13.5rem] shrink-0 items-start gap-3 rounded-2xl px-4 py-3.5 ring-1 ring-clay/10 transition-transform hover:-translate-y-0.5",
        TONE_BG[tone],
        className,
      )}
    >
      <IconBadge icon={Icon} tone={tone} className="mt-0.5 bg-card/70" />
      <div className="min-w-0">
        <p className="text-[12.5px] font-semibold text-foreground/85">{label}</p>
        <p className="mt-0.5 text-[11.5px] leading-snug text-foreground/60">{note}</p>
      </div>
    </div>
  );
}

/** A single business-snapshot paper card — fabric-textured, deckle edge. */
export function SnapshotCard({
  label,
  value,
  note,
  quote,
  meter,
  className,
}: {
  label: string;
  value: string;
  note?: string;
  quote?: string;
  meter?: number;
  className?: string;
}) {
  return (
    <DeckleCard
      paperClassName="bg-card border border-clay/25"
      className={cn("overflow-visible px-6 py-6", className)}
      style={{ boxShadow: "var(--shadow-lift)" }}
    >
      <TextileSwatch
        cell="baghPrint"
        className="pointer-events-none absolute inset-0 opacity-[0.09] mix-blend-multiply"
        style={{ clipPath: DECKLE_EDGE }}
      />
      <p className="relative text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
        {label}
      </p>
      <p className="font-display relative mt-2 text-[1.85rem] leading-none font-semibold text-foreground">
        {value}
      </p>
      {meter !== undefined ? (
        <div className="relative">
          <Meter value={meter} tone={meter < 30 ? "wine" : "clay"} />
        </div>
      ) : null}
      {note ? <p className="relative mt-2 text-[11px] text-muted-foreground">{note}</p> : null}
      {quote ? <p className="hand relative mt-2 text-[0.95rem]">{quote}</p> : null}
    </DeckleCard>
  );
}

/** A pinned, washi-taped "postcard" for the Opportunity Corner. */
export function PostcardCard({
  icon: Icon,
  tone,
  eyebrow,
  title,
  note,
  rotate = -2,
  className,
}: {
  icon: ComponentType<{ className?: string }>;
  tone: JournalTone;
  eyebrow: string;
  title: string;
  note: string;
  rotate?: number;
  className?: string;
}) {
  return (
    <div className={cn("relative", className)} style={{ transform: `rotate(${rotate}deg)` }}>
      <WashiTape tone={TAPE_TONE[tone]} rotate={rotate * -1} className="left-1/2 -top-2.5 -translate-x-1/2" />
      <DeckleCard
        paperClassName="bg-card border border-clay/25"
        className="overflow-visible px-5 py-5"
        style={{ boxShadow: "var(--shadow-soft)" }}
      >
        <IconBadge icon={Icon} tone={tone} />
        <p className="relative mt-3 text-[9.5px] font-semibold tracking-[0.18em] text-muted-foreground uppercase">
          {eyebrow}
        </p>
        <p className="font-display relative mt-1 text-base font-semibold text-foreground">
          {title}
        </p>
        <p className="relative mt-1 text-[11.5px] leading-snug text-foreground/65">{note}</p>
      </DeckleCard>
    </div>
  );
}
