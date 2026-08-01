import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { WashiTape } from "@/components/sakhi/CompanionAssets";

/**
 * Brand-Studio-page-only pieces, built on the shared CompanionAssets/Cards
 * kit. Not imported anywhere else — safe to iterate on without touching
 * the rest of the app.
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

/** One selectable font-pairing sample, showing a display + body glyph. */
export function FontSampleCard({
  displayFont,
  bodyFont,
  label,
  selected,
  onClick,
}: {
  displayFont: string;
  bodyFont: string;
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "card-soft lift relative flex flex-col items-start gap-1 rounded-2xl px-5 py-4 text-left transition-all",
        selected && "ring-2 ring-wine/50",
      )}
    >
      <span className="text-3xl font-semibold text-foreground" style={{ fontFamily: displayFont }}>
        Aa
      </span>
      <span className="text-[12px] text-foreground/70" style={{ fontFamily: bodyFont }}>
        The quick brown fox
      </span>
      <span className="mt-1.5 text-[10.5px] font-medium tracking-[0.08em] text-muted-foreground uppercase">
        {label}
      </span>
      {selected ? (
        <span className="absolute top-3 right-3 grid h-5 w-5 place-items-center rounded-full bg-wine text-primary-foreground">
          <Check className="h-3 w-3" />
        </span>
      ) : null}
    </button>
  );
}

/** A small printed business-card mockup. */
export function BusinessCardMockup({
  name,
  tagline,
  tone,
  rotate = -2,
  className,
}: {
  name: string;
  tagline: string;
  tone: JournalTone;
  rotate?: number;
  className?: string;
}) {
  return (
    <div
      className={cn("relative aspect-[16/9] w-full max-w-[15rem] overflow-hidden rounded-xl bg-card ring-1 ring-clay/25", className)}
      style={{ boxShadow: "var(--shadow-lift)", transform: `rotate(${rotate}deg)` }}
    >
      <div className="flex h-full flex-col justify-between p-4">
        <span className={cn("grid h-8 w-8 place-items-center rounded-full text-[13px] font-semibold text-wine", TONE_BG[tone])}>
          {name.charAt(0).toUpperCase()}
        </span>
        <div>
          <p className="font-display text-[15px] font-semibold text-foreground">{name}</p>
          <p className="text-[10px] text-muted-foreground">{tagline}</p>
        </div>
      </div>
    </div>
  );
}

/** A small hang-tag label mockup, like a product tag on string. */
export function LabelMockup({ name, tone, rotate = 3, className }: { name: string; tone: JournalTone; rotate?: number; className?: string }) {
  return (
    <div className={cn("relative w-fit pt-5", className)} style={{ transform: `rotate(${rotate}deg)` }}>
      <span
        aria-hidden
        className="absolute top-0 left-1/2 h-3 w-3 -translate-x-1/2 rounded-full ring-1 ring-clay/40"
        style={{ backgroundColor: "var(--background)" }}
      />
      <div
        className={cn("min-w-[6.5rem] rounded-md px-3.5 py-3 text-center ring-1 ring-clay/25", TONE_BG[tone])}
        style={{ boxShadow: "var(--shadow-soft)" }}
      >
        <p className="font-display text-[12px] font-semibold text-foreground/85">{name}</p>
        <p className="mt-0.5 text-[9px] tracking-[0.1em] text-foreground/55 uppercase">Handmade</p>
      </div>
    </div>
  );
}

/** A single do/don't row in the brand-guidelines sheet. */
export function GuidelineRow({ ok, children }: { ok: boolean; children: string }) {
  return (
    <li className="flex items-start gap-2 text-[12.5px] leading-snug text-foreground/75">
      {ok ? (
        <Check className="mt-[3px] h-3.5 w-3.5 shrink-0 text-leaf-ink" />
      ) : (
        <X className="mt-[3px] h-3.5 w-3.5 shrink-0 text-wine/70" />
      )}
      {children}
    </li>
  );
}

/** A small pinned reference photo, like a mockup tacked to the page. */
export function PinnedPhoto({
  src,
  alt,
  rotate = -2,
  tapeTone = "clay",
  className,
}: {
  src: string;
  alt: string;
  rotate?: number;
  tapeTone?: "marigold" | "rose" | "leaf" | "indigo" | "clay";
  className?: string;
}) {
  return (
    <div className={cn("relative", className)} style={{ transform: `rotate(${rotate}deg)` }}>
      <WashiTape tone={tapeTone} rotate={rotate * -1} className="left-1/2 -top-2.5 -translate-x-1/2" />
      <img
        src={src}
        alt={alt}
        className="w-full rounded-lg ring-1 ring-clay/25"
        style={{ boxShadow: "var(--shadow-lift)" }}
      />
    </div>
  );
}
