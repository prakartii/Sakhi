import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import {
  DECKLE_EDGE,
  DeckleCard,
  StitchDivider,
  TextileSwatch,
} from "@/components/sakhi/CompanionAssets";

/**
 * Companion-page-only metric cards. All three share one fabric-textured
 * card design (the "This month net" look). Not imported anywhere else.
 */

const TAG_EDGE =
  "polygon(0% 0%,100% 0%,100% 78%,91% 100%,82% 78%,73% 100%,64% 78%,55% 100%,46% 78%,37% 100%,28% 78%,19% 100%,10% 78%,0% 100%)";

/** The shared fabric-card shell every metric card is built on. */
function MetricCardShell({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <DeckleCard
      paperClassName="bg-card border border-clay/25"
      className={cn("overflow-visible", className)}
      style={{ boxShadow: "var(--shadow-lift)" }}
    >
      <TextileSwatch
        cell="baghPrint"
        className="pointer-events-none absolute inset-0 opacity-[0.09] mix-blend-multiply"
        style={{ clipPath: DECKLE_EDGE }}
      />
      {children}
    </DeckleCard>
  );
}

/** The "hero" metric — a large fabric-textured card. */
export function FeaturedMetric({
  label,
  value,
  tag,
  note,
  className,
}: {
  label: string;
  value: string;
  tag?: string;
  note?: string;
  className?: string;
}) {
  return (
    <MetricCardShell className={cn("px-7 py-7", className)}>
      {tag ? (
        <span
          aria-hidden
          className="absolute top-4 right-6 rounded-t-sm bg-leaf px-3 pt-1.5 pb-3 text-[11px] font-semibold text-leaf-ink"
          style={{ clipPath: TAG_EDGE, transform: "rotate(2deg)" }}
        >
          {tag}
        </span>
      ) : null}
      <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
        {label}
      </p>
      <p className="mt-3 font-display text-[2.75rem] leading-none font-semibold text-foreground">
        {value}
      </p>
      {note ? (
        <p className="mt-3 max-w-[26ch] text-[12.5px] text-muted-foreground">{note}</p>
      ) : null}
      <StitchDivider className="mt-5" />
    </MetricCardShell>
  );
}

/** A single-glance daily number — same fabric-card design as FeaturedMetric. */
export function TicketMetric({
  label,
  value,
  sub,
  detail,
  className,
}: {
  label: string;
  value: string;
  sub?: string;
  detail?: string;
  className?: string;
}) {
  return (
    <MetricCardShell className={cn("px-6 py-6", className)}>
      <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
        {label}
      </p>
      <p className="mt-2 font-display text-[1.85rem] leading-none font-semibold text-foreground">
        {value}
      </p>
      {sub ? <p className="mt-1.5 text-[11px] text-muted-foreground">{sub}</p> : null}
      {detail ? (
        <>
          <StitchDivider className="mt-3 mb-2.5" />
          <p className="text-[11px] text-muted-foreground">{detail}</p>
        </>
      ) : null}
    </MetricCardShell>
  );
}

/** The number that still needs attention — same fabric-card design as FeaturedMetric. */
export function NoteMetric({
  label,
  value,
  sub,
  detail,
  className,
}: {
  label: string;
  value: string;
  sub?: string;
  detail?: string;
  className?: string;
}) {
  return (
    <MetricCardShell className={cn("px-6 py-6", className)}>
      <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
        {label}
      </p>
      <p className="mt-2 font-display text-[1.85rem] leading-none font-semibold text-foreground">
        {value}
      </p>
      {sub ? <p className="mt-1.5 text-[11px] text-muted-foreground">{sub}</p> : null}
      {detail ? (
        <>
          <StitchDivider className="mt-3 mb-2.5" />
          <p className="text-[11px] text-muted-foreground">{detail}</p>
        </>
      ) : null}
    </MetricCardShell>
  );
}
