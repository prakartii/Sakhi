import { Mic } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { BotanicalMark, PostageStamp, TextileSwatch } from "@/components/sakhi/CompanionAssets";
import { StickyNote } from "@/components/sakhi/CompanionHero";

/**
 * Memory-page-only decorative pieces, styled after the original Sakhi
 * "Memory Journal" screenshot. Not imported anywhere else — safe to
 * iterate on without touching the shared Cards/MicPanel/Layout system.
 */

export { PostageStamp };

/**
 * A faded page of ruled notebook paper — a CSS-drawn stand-in for a torn
 * diary sheet, used as a soft backdrop. Deliberately not a photo, so it
 * reads as its own thing rather than an echo of the Companion hero.
 */
export function JournalWash({ rotate = -2, className }: { rotate?: number; className?: string }) {
  return (
    <div
      aria-hidden
      className={cn("relative", className)}
      style={{ transform: `rotate(${rotate}deg)` }}
    >
      <div
        className="absolute inset-0 rounded-[2rem]"
        style={{
          backgroundColor: "var(--ivory)",
          backgroundImage:
            "linear-gradient(90deg, transparent 0 34px, color-mix(in oklab, var(--wine) 25%, transparent) 34px 35px, transparent 35px 100%), repeating-linear-gradient(0deg, transparent 0 25px, color-mix(in oklab, var(--clay) 32%, transparent) 25px 26px)",
        }}
      />
      <div
        className="absolute inset-0 rounded-[2rem]"
        style={{
          background:
            "radial-gradient(115% 95% at 50% 45%, transparent 30%, var(--background) 92%)",
        }}
      />
    </div>
  );
}

const DOT_TONE = {
  leaf: "bg-leaf-ink",
  rose: "bg-wine",
  marigold: "bg-[oklch(0.64_0.14_75)]",
  indigo: "bg-[oklch(0.52_0.12_255)]",
} as const;

/** A small colour-coded marker for a timeline row. */
export function MemoryDot({ tone }: { tone: keyof typeof DOT_TONE }) {
  return (
    <span
      aria-hidden
      className={cn("inline-block h-2 w-2 shrink-0 rounded-full ring-2 ring-card", DOT_TONE[tone])}
    />
  );
}

/** The closing "memory bank" banner — quote, sticky note, pinned stamps. */
export function MemoryBanner({
  quote,
  note,
  className,
}: {
  quote: ReactNode;
  note: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "weave relative overflow-hidden rounded-[2rem] bg-rose px-7 py-10 sm:px-10",
        className,
      )}
      style={{ boxShadow: "var(--shadow-lift)" }}
    >
      <TextileSwatch
        cell="sageZari"
        className="pointer-events-none absolute inset-y-0 right-0 hidden w-72 opacity-[0.22] mix-blend-multiply lg:block"
        style={{
          maskImage: "linear-gradient(to left, black, transparent)",
          WebkitMaskImage: "linear-gradient(to left, black, transparent)",
        }}
      />
      <BotanicalMark className="pointer-events-none absolute -bottom-12 -left-8 h-44 w-36 text-wine opacity-[0.12]" />
      <BotanicalMark className="pointer-events-none absolute -top-10 right-16 hidden h-32 w-28 rotate-180 text-wine opacity-[0.08] sm:block" />

      <div className="relative flex flex-col items-start gap-7 lg:flex-row lg:flex-wrap lg:items-center lg:justify-between lg:gap-8">
        <p className="max-w-xs font-display text-xl leading-snug text-wine-soft italic">{quote}</p>

        <StickyNote rotate={-3} className="shrink-0">
          {note}
        </StickyNote>

        <div className="flex shrink-0 flex-col items-start gap-2">
          <span
            className="inline-flex items-center gap-2 rounded-full bg-[oklch(0.24_0.02_30)] px-4 py-2.5 text-xs font-medium text-white"
            style={{ boxShadow: "var(--shadow-soft)" }}
          >
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white/60" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-white" />
            </span>
            <Mic className="h-3.5 w-3.5" /> Talk to Sakhi
          </span>
          <p className="pl-1 text-[10.5px] tracking-[0.04em] text-wine-soft/70">
            Voice-first · every language · always remembering
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3 self-center">
          <PostageStamp rotate={-6} />
          <PostageStamp rotate={4} />
        </div>
      </div>
    </div>
  );
}
