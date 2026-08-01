import { Mic } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { BotanicalMark, DeckleCard } from "@/components/sakhi/CompanionAssets";

/**
 * Companion-page-only pieces (hero memory-wall, voice card).
 * Not imported anywhere else — safe to iterate on without
 * touching the shared Cards/MicPanel/Layout design system.
 */

const BARS = [0.5, 0.85, 0.35, 1, 0.6, 0.95, 0.45, 0.8, 0.3, 0.7, 0.5];

/** A small hand-annotated paper note, pinned at a slight tilt. */
export function StickyNote({
  children,
  rotate = -4,
  className,
}: {
  children: ReactNode;
  rotate?: number;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative w-fit max-w-[11rem] rounded-sm bg-marigold px-3.5 pt-4 pb-3 text-[13px] ring-1 ring-clay/20",
        className,
      )}
      style={{ boxShadow: "var(--shadow-soft)", transform: `rotate(${rotate}deg)` }}
    >
      <span
        aria-hidden
        className="absolute -top-2 left-1/2 h-4 w-9 -translate-x-1/2 rounded-[2px] bg-rose/70 opacity-80"
        style={{ transform: "translateX(-50%) rotate(-3deg)" }}
      />
      <p className="hand leading-snug text-wine-soft">{children}</p>
    </div>
  );
}

/** A small pinned status pill, like a business update tacked to a wall. */
export function StatusPill({
  children,
  tone = "leaf",
  rotate = 0,
  className,
}: {
  children: ReactNode;
  tone?: "leaf" | "rose" | "marigold" | "indigo";
  rotate?: number;
  className?: string;
}) {
  const toneClass = {
    leaf: "bg-leaf text-leaf-ink",
    rose: "bg-rose text-wine",
    marigold: "bg-marigold text-wine-soft",
    indigo: "bg-indigo-tint text-[oklch(0.42_0.09_255)]",
  }[tone];
  return (
    <div
      className={cn(
        "flex w-fit items-center gap-1.5 rounded-full px-3.5 py-2 text-[11.5px] font-medium ring-1 ring-clay/15",
        toneClass,
        className,
      )}
      style={{ boxShadow: "var(--shadow-soft)", transform: `rotate(${rotate}deg)` }}
    >
      <span aria-hidden className="h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-60" />
      {children}
    </div>
  );
}

/** A small colour-blocked memory tile, echoing a corkboard note card. */
export function MemoryCard({
  tone,
  label,
  children,
  rotate = 0,
  className,
}: {
  tone: "rose" | "leaf" | "marigold" | "indigo";
  label: string;
  children: ReactNode;
  rotate?: number;
  className?: string;
}) {
  const toneClass = {
    rose: "bg-rose",
    leaf: "bg-leaf",
    marigold: "bg-marigold",
    indigo: "bg-indigo-tint",
  }[tone];
  return (
    <div
      className={cn(
        "w-fit min-w-[10rem] rounded-2xl px-4 py-3.5 ring-1 ring-clay/15",
        toneClass,
        className,
      )}
      style={{ boxShadow: "var(--shadow-soft)", transform: `rotate(${rotate}deg)` }}
    >
      <p className="text-[9.5px] font-semibold tracking-[0.18em] text-foreground/60 uppercase">
        {label}
      </p>
      <div className="mt-1 font-display text-foreground">{children}</div>
    </div>
  );
}

export function TrustChip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-clay/25 bg-card px-3 py-1.5 text-[11px] font-medium text-foreground/75">
      <span aria-hidden className="h-1 w-1 rounded-full bg-wine/50" />
      {children}
    </span>
  );
}

/** Premium, layered voice-assistant panel — the hero's focal point. */
export function VoiceCard({
  title,
  quote,
  languages,
  className,
  onMicClick,
  isRecording = false,
  isBusy = false,
  statusLabel,
}: {
  title: string;
  quote: string;
  languages?: string;
  className?: string;
  onMicClick?: () => void;
  isRecording?: boolean;
  isBusy?: boolean;
  statusLabel?: string;
}) {
  return (
    <div className={cn("relative", className)}>
      {/* stacked paper behind the card, for depth */}
      <div
        aria-hidden
        className="absolute inset-3 -z-10 rounded-[1.5rem] bg-clay/20"
        style={{ transform: "rotate(2.4deg)" }}
      />
      <div
        aria-hidden
        className="absolute inset-2 -z-10 rounded-[1.5rem]"
        style={{
          transform: "rotate(-1.6deg)",
          backgroundImage: "url(/companion/purple-floral.png)",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      />

      <DeckleCard
        paperClassName="bg-card border-2 border-dashed border-wine/25"
        className="overflow-hidden px-7 py-9 text-center"
        style={{ boxShadow: "var(--shadow-lift)" }}
      >
        <BotanicalMark className="pointer-events-none absolute -bottom-10 -left-10 h-36 w-32 opacity-[0.1]" />

        <div className="flex items-center justify-center gap-1.5">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-wine/60" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-wine" />
          </span>
          <p className="text-[10px] font-semibold tracking-[0.24em] text-muted-foreground uppercase">
            {statusLabel ?? "Listening"}
          </p>
        </div>

        <button
          type="button"
          aria-label={title}
          aria-pressed={isRecording}
          onClick={onMicClick}
          disabled={isBusy}
          className={cn(
            "relative mx-auto mt-6 grid h-[4.75rem] w-[4.75rem] place-items-center rounded-full text-primary-foreground ring-4 ring-card ring-offset-2 transition-transform hover:scale-105 disabled:pointer-events-none disabled:opacity-70",
            isRecording ? "bg-wine ring-offset-wine/30" : "bg-primary ring-offset-wine/10",
          )}
          style={{ animation: isBusy ? undefined : "halo 2.6s ease-out infinite" }}
        >
          <Mic className="h-6 w-6" />
        </button>

        <div className="mt-5 flex h-6 items-end justify-center gap-[3px]">
          {BARS.map((h, i) => (
            <span
              key={i}
              className="w-[3px] origin-bottom rounded-full bg-wine/60"
              style={{
                height: `${h * 24}px`,
                animation: isRecording
                  ? `wave ${900 + i * 130}ms ease-in-out ${i * 70}ms infinite`
                  : "none",
                opacity: isRecording ? 1 : 0.35,
              }}
            />
          ))}
        </div>

        <p className="mt-6 font-display text-lg font-semibold text-foreground">{title}</p>

        <div className="relative mx-auto mt-3 max-w-[15rem]">
          <span aria-hidden className="font-display absolute -top-3 -left-2 text-4xl text-wine/15">
            &ldquo;
          </span>
          <p className="hand relative px-3 text-[1.1rem]">{quote}</p>
        </div>

        {languages ? (
          <p className="mt-4 border-t border-clay/20 pt-3 text-[10.5px] tracking-[0.04em] text-muted-foreground">
            {languages}
          </p>
        ) : null}
      </DeckleCard>
    </div>
  );
}
