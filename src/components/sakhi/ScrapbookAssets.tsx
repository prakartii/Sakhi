import { useId } from "react";
import { Check, Heart, MessageCircle, Play, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import { BotanicalMark, WashiTape } from "@/components/sakhi/CompanionAssets";

/**
 * Shared scrapbook-branding decor — logo concepts, stamps, tags, mini social
 * previews. Extracted from the brand-studio moodboard reference and reused
 * across the Dashboard and Business Setup pages. Not layout components —
 * purely decorative storytelling pieces built on the shared asset kit.
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

/** A circular rubber-stamp mark, like "Sakhi AI · Smart approved". */
export function BrandStamp({
  label = "Sakhi AI",
  sub = "Smart approved",
  rotate = -8,
  className,
}: {
  label?: string;
  sub?: string;
  rotate?: number;
  className?: string;
}) {
  const id = useId();
  const arcId = `stamp-arc-${id}`;
  return (
    <div
      aria-hidden
      className={cn("relative grid h-[5.5rem] w-[5.5rem] shrink-0 place-items-center text-wine", className)}
      style={{ transform: `rotate(${rotate}deg)` }}
    >
      <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full opacity-80">
        <circle cx="50" cy="50" r="47" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="2 3" />
        <circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.7" />
        <path id={arcId} d="M50,50 m-31,0 a31,31 0 1,1 62,0 a31,31 0 1,1 -62,0" fill="none" />
        <text fontSize="6.4" letterSpacing="1.5" fill="currentColor">
          <textPath href={`#${arcId}`} startOffset="3%">
            {label.toUpperCase()} · {sub.toUpperCase()} ·
          </textPath>
        </text>
      </svg>
      <BotanicalMark className="h-8 w-7 opacity-70" />
    </div>
  );
}

/** A small torn-paper tag pinned at an angle, for one AI stat. */
export function TornStat({ label, value, rotate = -3, className }: { label: string; value: string; rotate?: number; className?: string }) {
  return (
    <div
      className={cn("relative w-fit rounded-sm bg-ivory px-3.5 py-2.5 ring-1 ring-clay/25", className)}
      style={{
        boxShadow: "var(--shadow-soft)",
        transform: `rotate(${rotate}deg)`,
        clipPath: "polygon(0 3%,3% 0,97% 1%,100% 4%,99% 97%,96% 100%,2% 99%,0 96%)",
      }}
    >
      <p className="text-[9px] font-semibold tracking-[0.16em] text-muted-foreground uppercase">{label}</p>
      <p className="font-display mt-0.5 text-lg leading-none font-semibold text-wine">{value}</p>
    </div>
  );
}

/** A lined-notebook checklist note, like a campaign-planning page. */
export function ChecklistNote({
  title,
  items,
  rotate = -2,
  className,
}: {
  title: string;
  items: string[];
  rotate?: number;
  className?: string;
}) {
  return (
    <div
      className={cn("relative w-fit min-w-[13rem] rounded-sm px-4 pt-5 pb-3.5 ring-1 ring-clay/20", className)}
      style={{
        transform: `rotate(${rotate}deg)`,
        boxShadow: "var(--shadow-soft)",
        backgroundColor: "var(--ivory)",
        backgroundImage:
          "repeating-linear-gradient(0deg, transparent 0 22px, color-mix(in oklab, var(--clay) 28%, transparent) 22px 23px)",
      }}
    >
      <WashiTape tone="clay" rotate={-4} className="left-1/2 -top-2.5 h-4 w-11 -translate-x-1/2" />
      <p className="font-display text-[14.5px] font-semibold text-wine-soft">{title}</p>
      <ul className="mt-2 space-y-1.5">
        {items.map((it) => (
          <li key={it} className="flex items-start gap-1.5 text-[11.5px] leading-snug text-foreground/75">
            <Check className="mt-[3px] h-3 w-3 shrink-0 text-leaf-ink" /> {it}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** A small vertical phone-screen mockup — a "reel idea" preview. */
export function ReelPreview({
  caption,
  duration = "0:15",
  rotate = 2,
  className,
}: {
  caption: string;
  duration?: string;
  rotate?: number;
  className?: string;
}) {
  return (
    <div
      className={cn("relative w-[6.5rem] shrink-0 overflow-hidden rounded-2xl ring-1 ring-clay/25", className)}
      style={{
        transform: `rotate(${rotate}deg)`,
        boxShadow: "var(--shadow-lift)",
        background: "linear-gradient(160deg, oklch(0.28 0.03 30), oklch(0.19 0.02 30))",
      }}
    >
      <div className="flex h-32 flex-col items-center justify-center gap-2 px-2.5 text-center">
        <span className="grid h-7 w-7 place-items-center rounded-full bg-white/15 text-white">
          <Play className="h-3 w-3 fill-current" />
        </span>
        <p className="font-display text-[10px] leading-snug text-white/90">{caption}</p>
      </div>
      <div className="flex items-center justify-between bg-black/30 px-2 py-1 text-[8.5px] text-white/70">
        <span>▶ {duration}</span>
      </div>
    </div>
  );
}

/** A miniature Instagram-post preview card. */
export function InstagramPreviewMini({
  handle,
  tones,
  rotate = -2,
  className,
}: {
  handle: string;
  tones: JournalTone[];
  rotate?: number;
  className?: string;
}) {
  return (
    <div
      className={cn("w-[9rem] shrink-0 overflow-hidden rounded-xl bg-card ring-1 ring-clay/25", className)}
      style={{ transform: `rotate(${rotate}deg)`, boxShadow: "var(--shadow-soft)" }}
    >
      <div className="flex items-center gap-1.5 px-2.5 py-2">
        <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-rose text-[9px] font-semibold text-wine">
          {handle.charAt(0).toUpperCase()}
        </span>
        <p className="truncate text-[10px] font-medium text-foreground/80">{handle}</p>
      </div>
      <div className="grid grid-cols-3 gap-[2px] bg-clay/10 p-[2px]">
        {tones.map((t, i) => (
          <span key={i} className={cn("aspect-square", TONE_BG[t])} />
        ))}
      </div>
      <div className="flex items-center gap-2 px-2.5 py-1.5 text-foreground/45">
        <Heart className="h-3 w-3" />
        <MessageCircle className="h-3 w-3" />
        <Send className="h-3 w-3" />
      </div>
    </div>
  );
}

/** A small pink sticky note listing campaign hashtags. */
export function HashtagNote({ tags, rotate = 3, className }: { tags: string[]; rotate?: number; className?: string }) {
  return (
    <div
      className={cn("relative w-fit rounded-sm bg-rose px-3.5 py-3.5 ring-1 ring-clay/20", className)}
      style={{ boxShadow: "var(--shadow-soft)", transform: `rotate(${rotate}deg)` }}
    >
      <WashiTape tone="rose" rotate={rotate * -1} className="left-1/2 -top-2 h-4 w-10 -translate-x-1/2" />
      <ul className="space-y-0.5">
        {tags.map((t) => (
          <li key={t} className="text-[11px] font-medium text-wine-soft">
            #{t}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** A kraft tag-on-a-string showing a few brand-mood words. */
export function BrandMoodTag({ words, rotate = 4, className }: { words: string[]; rotate?: number; className?: string }) {
  return (
    <div className={cn("relative w-fit pt-6", className)} style={{ transform: `rotate(${rotate}deg)` }}>
      <svg
        aria-hidden
        width="34"
        height="22"
        viewBox="0 0 34 22"
        className="absolute top-0 left-1/2 -translate-x-1/2 text-wine/40"
      >
        <path d="M17 22 C 7 15, 7 6, 17 1" stroke="currentColor" strokeWidth="1" fill="none" strokeDasharray="2 2" />
      </svg>
      <div
        className="relative min-w-[9.5rem] rounded-lg px-4 pt-5 pb-4 text-center ring-1 ring-clay/30"
        style={{ backgroundColor: "oklch(0.93 0.02 75)", boxShadow: "var(--shadow-soft)" }}
      >
        <span
          aria-hidden
          className="absolute top-2 left-1/2 h-2 w-2 -translate-x-1/2 rounded-full bg-background ring-1 ring-clay/40"
        />
        <p className="font-display text-[12.5px] font-semibold text-wine-soft">Brand mood</p>
        <ul className="mt-1.5 space-y-0.5">
          {words.map((w) => (
            <li key={w} className="text-[10.5px] text-foreground/70">
              · {w}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/** One selectable logo-concept card, for the Business Identity step. */
export function LogoOption({
  label,
  tone,
  selected,
  onClick,
}: {
  label: string;
  tone: JournalTone;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "relative flex flex-1 flex-col items-center gap-2 rounded-2xl border border-clay/25 bg-card px-3 py-4 transition-transform hover:-translate-y-0.5",
        selected && "ring-2 ring-wine/50",
      )}
    >
      <span className={cn("grid h-12 w-12 place-items-center rounded-full", TONE_BG[tone])}>
        <BotanicalMark className="h-6 w-5 text-wine/70" />
      </span>
      <span className="text-[10.5px] font-medium text-foreground/75">{label}</span>
      {selected ? (
        <span className="absolute top-2 right-2 grid h-5 w-5 place-items-center rounded-full bg-wine text-primary-foreground">
          <Check className="h-2.5 w-2.5" />
        </span>
      ) : null}
    </button>
  );
}
