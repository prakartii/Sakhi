import type { ComponentType, CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Shared decorative kit for the whole site redesign (every route under
 * src/routes/). Not part of the Lovable-generated Cards/MicPanel/Layout
 * system — those stay untouched so this can be iterated on freely.
 */

export function BotanicalMark({ className }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 220 280" fill="none" className={cn("text-wine", className)}>
      <path
        d="M132 18c42 12 56 58 39 94-11 23-36 32-31 56 4 20 27 27 25 46-2 17-21 26-38 20-31-11-48-43-44-74 3-25 21-39 19-61-2-23-23-37-17-59 6-20 27-29 47-22Z"
        stroke="currentColor"
        strokeWidth="1.1"
        strokeLinecap="round"
        opacity="0.5"
      />
      <path
        d="M112 58c15 19 17 44 4 65"
        stroke="currentColor"
        strokeWidth="0.9"
        strokeLinecap="round"
        opacity="0.4"
      />
      <path
        d="M101 100c11 15 11 34 0 49"
        stroke="currentColor"
        strokeWidth="0.9"
        strokeLinecap="round"
        opacity="0.35"
      />
      <path
        d="M97 152c8 11 8 25 0 36"
        stroke="currentColor"
        strokeWidth="0.9"
        strokeLinecap="round"
        opacity="0.3"
      />
      <circle cx="150" cy="52" r="2.2" fill="currentColor" opacity="0.4" />
      <circle cx="163" cy="70" r="1.4" fill="currentColor" opacity="0.3" />
    </svg>
  );
}

/** One cell of the /companion/textiles.jpg swatch sheet (4 cols × 2 rows). */
const TEXTILE_CELLS = {
  banarasiGold: { col: 0, row: 0 },
  banarasiWine: { col: 1, row: 0 },
  ajrakhFloral: { col: 2, row: 0 },
  baghPrint: { col: 3, row: 0 },
  ikat: { col: 0, row: 1 },
  sageZari: { col: 1, row: 1 },
  ajrakhNavy: { col: 2, row: 1 },
  bootiFestive: { col: 3, row: 1 },
} as const;

export function TextileSwatch({
  cell,
  className,
  style,
}: {
  cell: keyof typeof TEXTILE_CELLS;
  className?: string;
  style?: CSSProperties;
}) {
  const { col, row } = TEXTILE_CELLS[cell];
  return (
    <div
      aria-hidden
      className={cn("bg-clay/20", className)}
      style={{
        backgroundImage: "url(/companion/textiles.jpg)",
        backgroundSize: "400% 200%",
        backgroundPosition: `${(col / 3) * 100}% ${row * 100}%`,
        ...style,
      }}
    />
  );
}

/** The full scrapbook collage photo, faded into the page at every edge. */
export function ScrapbookBleed({ className }: { className?: string }) {
  return (
    <div aria-hidden className={cn("relative", className)}>
      <img
        src="/companion/scrapbook.jpg"
        alt=""
        loading="lazy"
        className="h-full w-full rounded-[2rem] object-cover"
      />
      <div
        className="absolute inset-0 rounded-[2rem]"
        style={{
          background:
            "radial-gradient(120% 100% at 50% 50%, transparent 40%, var(--background) 96%), linear-gradient(180deg, color-mix(in oklab, var(--background) 55%, transparent) 0%, transparent 18%, transparent 82%, color-mix(in oklab, var(--background) 55%, transparent) 100%)",
        }}
      />
    </div>
  );
}

/** Notebook-style punch holes, like a torn spiral binding. */
export function SpiralEdge({ className }: { className?: string }) {
  return (
    <div aria-hidden className={cn("flex flex-col items-center justify-between gap-2", className)}>
      {Array.from({ length: 7 }).map((_, i) => (
        <span
          key={i}
          className="h-2.5 w-2.5 shrink-0 rounded-full bg-background ring-1 ring-inset ring-clay/40"
        />
      ))}
    </div>
  );
}

/** A gently irregular, hand-torn paper edge — applied via clip-path. */
export const DECKLE_EDGE =
  "polygon(0% 2%,3% 0%,8% 1%,15% 0%,25% 1.5%,35% 0%,45% 1%,55% 0%,65% 1.5%,75% 0%,85% 1%,92% 0%,97% 1.5%,100% 0%,100% 3%,99% 8%,100% 15%,98.5% 25%,100% 35%,99% 45%,100% 55%,98.5% 65%,100% 75%,99% 85%,100% 92%,98.5% 97%,100% 100%,95% 99%,88% 100%,78% 99%,68% 100%,58% 99%,48% 100%,38% 99%,28% 100%,18% 99%,8% 100%,2% 99%,0% 100%,1% 95%,0% 88%,1.5% 78%,0% 68%,1% 58%,0% 48%,1.5% 38%,0% 28%,1% 18%,0% 8%)";

/**
 * A card with a soft hand-torn paper silhouette. The shadow lives on the
 * outer box (kept rectangular so it renders cleanly); the deckle edge,
 * background and texture live on a clipped inner layer.
 */
export function DeckleCard({
  children,
  className,
  paperClassName,
  paperStyle,
  style,
}: {
  children: ReactNode;
  className?: string;
  paperClassName?: string;
  paperStyle?: CSSProperties;
  style?: CSSProperties;
}) {
  return (
    <div className={cn("relative", className)} style={style}>
      <div
        aria-hidden
        className={cn("absolute inset-0", paperClassName)}
        style={{ clipPath: DECKLE_EDGE, ...paperStyle }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}

/** A hand-stitched dashed divider. */
export function StitchDivider({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn("h-px w-full opacity-60", className)}
      style={{
        backgroundImage:
          "repeating-linear-gradient(90deg, color-mix(in oklab, var(--clay) 60%, transparent) 0 8px, transparent 8px 16px)",
      }}
    />
  );
}

const BADGE_TONE = {
  rose: "bg-rose text-wine",
  leaf: "bg-leaf text-leaf-ink",
  marigold: "bg-marigold text-[oklch(0.42_0.09_70)]",
  indigo: "bg-indigo-tint text-[oklch(0.42_0.09_255)]",
  lilac: "bg-lilac text-[oklch(0.42_0.1_300)]",
  sand: "bg-sand text-wine",
} as const;

/** A pastel icon-circle badge, echoing the old Sakhi's metric/feature icons. */
export function IconBadge({
  icon: Icon,
  tone = "rose",
  className,
}: {
  icon: ComponentType<{ className?: string }>;
  tone?: keyof typeof BADGE_TONE;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "grid h-9 w-9 shrink-0 place-items-center rounded-full",
        BADGE_TONE[tone],
        className,
      )}
    >
      <Icon className="h-4 w-4" />
    </span>
  );
}

const TAPE_TONE = {
  marigold: "bg-marigold/85",
  rose: "bg-rose/85",
  leaf: "bg-leaf/85",
  indigo: "bg-indigo-tint/85",
  clay: "bg-clay/50",
} as const;

/** A single strip of washi tape, for pinning a card down at an angle. */
export function WashiTape({
  tone = "marigold",
  rotate = -3,
  className,
}: {
  tone?: keyof typeof TAPE_TONE;
  rotate?: number;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cn("absolute h-5 w-14 z-20", TAPE_TONE[tone], className)}
      style={{ boxShadow: "var(--shadow-soft)", transform: `rotate(${rotate}deg)` }}
    />
  );
}

/** A small vintage-style postage stamp, dashed edge, botanical centre. */
export function PostageStamp({ rotate = 0, className }: { rotate?: number; className?: string }) {
  return (
    <div
      className={cn(
        "relative grid h-16 w-[3.25rem] shrink-0 place-items-center rounded-[3px] border-2 border-dashed border-wine/30 bg-ivory",
        className,
      )}
      style={{ boxShadow: "var(--shadow-soft)", transform: `rotate(${rotate}deg)` }}
    >
      <BotanicalMark className="h-9 w-7 text-wine/55" />
    </div>
  );
}
