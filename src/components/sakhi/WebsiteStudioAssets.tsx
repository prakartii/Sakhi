import type { ReactNode } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Website-Studio-page-only pieces, built on the shared design tokens.
 * Not imported anywhere else — safe to iterate on without touching the
 * rest of the app.
 */

/** A desktop browser-chrome frame wrapping a live preview. */
export function BrowserFrame({
  url,
  children,
  className,
}: {
  url: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn("overflow-hidden rounded-2xl border border-clay/25 bg-card", className)}
      style={{ boxShadow: "var(--shadow-lift)" }}
    >
      <div className="flex items-center gap-2 border-b border-clay/15 bg-sand/60 px-3.5 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-rose" />
        <span className="h-2.5 w-2.5 rounded-full bg-marigold" />
        <span className="h-2.5 w-2.5 rounded-full bg-leaf" />
        <span className="ml-2 flex-1 truncate rounded-full bg-card px-3 py-1 text-center text-[10.5px] text-muted-foreground ring-1 ring-clay/15">
          {url}
        </span>
      </div>
      {children}
    </div>
  );
}

/** A mobile phone frame wrapping a live preview. */
export function PhoneFrame({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn("relative mx-auto w-[10.5rem] overflow-hidden rounded-[1.5rem] border-[6px] border-card bg-card ring-1 ring-clay/25", className)}
      style={{ boxShadow: "var(--shadow-lift)" }}
    >
      <span className="absolute top-1 left-1/2 z-10 h-3 w-14 -translate-x-1/2 rounded-full bg-clay/30" />
      {children}
    </div>
  );
}

const STAGES = ["Draft", "Preview", "Published"] as const;

/** A small linear publish-workflow stepper. */
export function PublishStepper({ current, className }: { current: number; className?: string }) {
  return (
    <div className={cn("flex items-center", className)}>
      {STAGES.map((label, i) => (
        <div key={label} className="flex flex-1 items-center last:flex-none">
          <div className="flex flex-col items-center gap-1.5">
            <span
              className={cn(
                "grid h-7 w-7 place-items-center rounded-full text-[11px] font-semibold ring-1",
                i < current && "bg-leaf text-leaf-ink ring-leaf-ink/30",
                i === current && "bg-primary text-primary-foreground ring-wine",
                i > current && "bg-card text-muted-foreground ring-clay/30",
              )}
            >
              {i < current ? <Check className="h-3.5 w-3.5" /> : i + 1}
            </span>
            <span className="text-[10.5px] font-medium text-foreground/70">{label}</span>
          </div>
          {i < STAGES.length - 1 ? (
            <span
              className={cn("mx-2 h-px flex-1", i < current ? "bg-leaf-ink/40" : "bg-clay/25")}
              aria-hidden
            />
          ) : null}
        </div>
      ))}
    </div>
  );
}
