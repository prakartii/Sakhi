import type { ComponentType, ReactNode } from "react";
import { Check, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { IconBadge, StitchDivider, WashiTape } from "@/components/sakhi/CompanionAssets";

/**
 * Business-Setup-page-only pieces, built on the shared CompanionAssets/Cards
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

export const SETUP_STEPS = [
  "Business Story",
  "Products",
  "Customers",
  "Goals",
  "Business Identity",
] as const;

/** The stitched-thread step rail across the top of the setup journey. */
export function StepRail({ current, className }: { current: number; className?: string }) {
  return (
    <div className={cn("relative flex items-start justify-between gap-2", className)}>
      <StitchDivider className="absolute top-4 right-4 left-4 -z-10" />
      {SETUP_STEPS.map((label, i) => {
        const state = i < current ? "done" : i === current ? "active" : "upcoming";
        return (
          <div key={label} className="flex flex-1 flex-col items-center gap-2 text-center">
            <span
              className={cn(
                "grid h-8 w-8 shrink-0 place-items-center rounded-full bg-background text-[12px] font-semibold ring-1 transition-colors",
                state === "active" && "bg-primary text-primary-foreground ring-wine",
                state === "done" && "bg-leaf text-leaf-ink ring-leaf-ink/30",
                state === "upcoming" && "text-muted-foreground ring-clay/30",
              )}
            >
              {state === "done" ? <Check className="h-3.5 w-3.5" /> : i + 1}
            </span>
            <span
              className={cn(
                "hidden text-[10.5px] font-medium sm:block",
                state === "upcoming" ? "text-muted-foreground" : "text-foreground",
              )}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** A small handwritten AI tip, pinned in the margin of a step. */
export function MarginNote({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-xl bg-why/80 px-3.5 py-3 ring-1 ring-clay/15",
        className,
      )}
    >
      <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-wine" />
      <p className="hand text-[0.95rem] leading-snug">{children}</p>
    </div>
  );
}

/** A clickable example-prompt chip for the conversational Step 1 card. */
export function PromptChip({
  children,
  onClick,
  selected,
}: {
  children: ReactNode;
  onClick?: () => void;
  selected?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3.5 py-1.5 text-[12.5px] transition-colors",
        selected
          ? "border-wine/40 bg-rose text-wine"
          : "border-clay/25 bg-card text-foreground/70 hover:border-wine/30 hover:text-wine",
      )}
    >
      {children}
    </button>
  );
}

/** A pinned, washi-taped product card for Step 2. */
export function ProductCard({
  icon: Icon,
  tone,
  name,
  category,
  price,
  materials,
  note,
  rotate = -2,
  className,
}: {
  icon: ComponentType<{ className?: string }>;
  tone: JournalTone;
  name: string;
  category: string;
  price: string;
  materials: string;
  note?: string;
  rotate?: number;
  className?: string;
}) {
  return (
    <div className={cn("relative", className)} style={{ transform: `rotate(${rotate}deg)` }}>
      <WashiTape tone={TAPE_TONE[tone]} rotate={rotate * -1} className="left-6 -top-2.5" />
      <div
        className="relative overflow-hidden rounded-2xl border border-clay/25 bg-card px-5 py-5"
        style={{ boxShadow: "var(--shadow-soft)" }}
      >
        <span className={cn("grid h-14 w-14 place-items-center rounded-xl", TONE_BG[tone])}>
          <Icon className="h-6 w-6 text-foreground/55" />
        </span>
        <p className="font-display mt-3 text-lg font-semibold text-foreground">{name}</p>
        <p className="text-[11px] text-muted-foreground">
          {category} · {materials}
        </p>
        <p className="font-display mt-1 text-base font-semibold text-wine">{price}</p>
        {note ? <p className="hand mt-2 text-[0.95rem]">{note}</p> : null}
      </div>
    </div>
  );
}

/** A selectable scrapbook card, shared by the Customers and Goals steps. */
export function SelectableCard({
  icon: Icon,
  tone,
  label,
  note,
  selected,
  onClick,
}: {
  icon: ComponentType<{ className?: string }>;
  tone: JournalTone;
  label: string;
  note: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "card-soft lift group relative flex w-full flex-col items-start gap-2 overflow-hidden rounded-2xl px-4 py-4 text-left transition-all",
        selected && "ring-2 ring-wine/50",
      )}
    >
      <IconBadge icon={Icon} tone={tone} />
      <p className="text-[13.5px] font-semibold text-foreground">{label}</p>
      <p className="text-[11.5px] text-muted-foreground">{note}</p>
      {selected ? (
        <span className="absolute top-3 right-3 grid h-5 w-5 place-items-center rounded-full bg-wine text-primary-foreground">
          <Check className="h-3 w-3" />
        </span>
      ) : null}
    </button>
  );
}

const SWATCH_TONE: Record<JournalTone, string> = TONE_BG;

/** One selectable colour-palette swatch for the Business Identity step. */
export function ColorSwatch({
  tone,
  selected,
  onClick,
}: {
  tone: JournalTone;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      aria-label={`${tone} palette`}
      className={cn(
        "grid h-11 w-11 shrink-0 place-items-center rounded-full ring-1 ring-clay/20 transition-transform hover:scale-105",
        SWATCH_TONE[tone],
        selected && "ring-2 ring-wine ring-offset-2 ring-offset-card",
      )}
    >
      {selected ? <Check className="h-4 w-4 text-wine" /> : null}
    </button>
  );
}
