import type { ComponentType, ReactNode } from "react";
import { cn } from "@/lib/utils";
import {
  BotanicalMark,
  IconBadge,
  SpiralEdge,
  TextileSwatch,
} from "@/components/sakhi/CompanionAssets";

/**
 * Companion-page-only "morning briefing" — an editorial intelligence
 * board, not a plain container. Not imported anywhere else.
 */

export type BriefingTask = {
  text: string;
  tag: string;
  tone: "rose" | "leaf" | "marigold" | "indigo";
  icon: ComponentType<{ className?: string }>;
};

const TONE_CLASS: Record<BriefingTask["tone"], string> = {
  rose: "bg-rose text-wine",
  leaf: "bg-leaf text-leaf-ink",
  marigold: "bg-marigold text-wine-soft",
  indigo: "bg-indigo-tint text-[oklch(0.42_0.09_255)]",
};

export function MorningBriefing({
  time,
  place,
  name,
  tasks,
  why,
  basis,
  note,
  className,
}: {
  time: string;
  place: string;
  name: string;
  tasks: BriefingTask[];
  why: ReactNode;
  basis: ReactNode;
  note: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "card-soft relative overflow-hidden rounded-tl-[3rem] rounded-tr-2xl rounded-br-[3rem] rounded-bl-2xl",
        className,
      )}
      style={{ boxShadow: "var(--shadow-lift)" }}
    >
      <div className="flex">
        <SpiralEdge className="hidden w-10 shrink-0 bg-sand py-10 sm:flex" />

        <div className="min-w-0 flex-1 px-6 pt-10 pb-0 sm:px-9">
          <BotanicalMark className="pointer-events-none absolute top-6 right-6 h-24 w-20 opacity-[0.08]" />

          <span
            className="relative inline-flex items-center gap-1.5 rounded-sm bg-ivory px-3 py-1.5 text-[10.5px] font-semibold tracking-[0.16em] text-muted-foreground uppercase ring-1 ring-clay/25"
            style={{ boxShadow: "var(--shadow-soft)", transform: "rotate(-1.5deg)" }}
          >
            <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-wine/50" />
            {time} · {place}
          </span>

          <h2 className="mt-4 font-display text-3xl font-semibold text-foreground sm:text-4xl">
            Good morning, {name}
          </h2>
          <div className="mt-3 h-[2px] w-16 rounded-full bg-wine/40" />

          <div className="mt-7 grid gap-3 pb-8 sm:grid-cols-2">
            {tasks.map((task) => (
              <div
                key={task.text}
                className={cn(
                  "relative flex items-start gap-3 overflow-hidden rounded-2xl px-4 py-3.5 ring-1 ring-clay/10 transition-transform hover:-translate-y-0.5",
                  TONE_CLASS[task.tone],
                )}
              >
                <IconBadge icon={task.icon} tone={task.tone} className="mt-0.5 bg-card/70" />
                <div className="min-w-0">
                  <p className="text-[9.5px] font-semibold tracking-[0.16em] uppercase opacity-60">
                    {task.tag}
                  </p>
                  <p className="mt-1 text-[13px] leading-relaxed text-foreground/85">{task.text}</p>
                </div>
              </div>
            ))}
          </div>

          <blockquote className="border-l-2 border-wine/30 pb-7 pl-4 text-[13px] leading-relaxed text-foreground/75 italic">
            <span className="font-semibold text-wine not-italic">Why:</span> {why}
            <p className="mt-1.5 text-[11px] text-muted-foreground not-italic">{basis}</p>
          </blockquote>
        </div>
      </div>

      {/* pinned note banner */}
      <div className="relative flex items-center gap-4 bg-rose px-6 py-5 sm:px-9">
        <TextileSwatch
          cell="sageZari"
          className="pointer-events-none absolute inset-y-0 right-0 hidden w-40 opacity-25 mix-blend-multiply sm:block"
          style={{
            maskImage: "linear-gradient(to left, black, transparent)",
            WebkitMaskImage: "linear-gradient(to left, black, transparent)",
          }}
        />
        <span
          aria-hidden
          className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-card ring-1 ring-wine/20"
        >
          <span className="h-2.5 w-2.5 rounded-full border-2 border-wine/40" />
        </span>
        <p className="hand relative text-[1.15rem] text-wine-soft">{note}</p>
      </div>
    </div>
  );
}
