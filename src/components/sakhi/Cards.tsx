import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const TONES = {
  cream: "bg-card",
  sand: "bg-sand",
  leaf: "bg-leaf",
  rose: "bg-rose",
  marigold: "bg-marigold",
  indigo: "bg-indigo-tint",
  lilac: "bg-lilac",
} as const;

export type Tone = keyof typeof TONES;

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground uppercase">
      {children}
    </p>
  );
}

export function Why({ children }: { children: ReactNode }) {
  return (
    <p className="mt-3 rounded-xl bg-why/90 px-3 py-2.5 text-[12px] leading-relaxed text-foreground/80 ring-1 ring-clay/15 transition-colors group-hover:bg-why group-hover:ring-wine/20">
      <span className="font-semibold text-wine">Why:</span> {children}
    </p>
  );
}

export function Basis({ children }: { children?: ReactNode }) {
  return (
    <p className="mt-2 text-[11px] text-muted-foreground">
      {children ?? "Based on what you've shared over the past 3 weeks."}
    </p>
  );
}

export function HandNote({ children }: { children: ReactNode }) {
  return (
    <p className="hand mt-6 flex items-start gap-2">
      <span aria-hidden className="text-base">
        ✎
      </span>
      <span>{children}</span>
    </p>
  );
}

export function Pill({
  children,
  tone = "rose",
}: {
  children: ReactNode;
  tone?: "rose" | "leaf" | "marigold" | "indigo";
}) {
  const map = {
    rose: "bg-rose text-wine",
    leaf: "bg-leaf text-leaf-ink",
    marigold: "bg-marigold text-[oklch(0.42_0.09_70)]",
    indigo: "bg-indigo-tint text-[oklch(0.42_0.09_255)]",
  } as const;
  return (
    <span className={cn("inline-block rounded-md px-2 py-1 text-[11px] font-medium", map[tone])}>
      {children}
    </span>
  );
}

export function Craft({
  tone = "cream",
  className,
  children,
  texture,
}: {
  tone?: Tone;
  className?: string;
  children: ReactNode;
  texture?: "weave" | "blockprint";
}) {
  return (
    <article
      className={cn(
        "group card-soft lift relative overflow-hidden rounded-[1.75rem] p-6",
        TONES[tone],
        className,
      )}
    >
      {texture ? (
        <div
          aria-hidden
          className={cn(
            "pointer-events-none absolute -top-8 -right-8 h-36 w-36 opacity-0 transition-opacity duration-500 group-hover:opacity-60",
            texture,
          )}
        />
      ) : null}
      <div className="relative">{children}</div>
    </article>
  );
}

export function Stat({
  label,
  value,
  sub,
  className,
}: {
  label: string;
  value: string;
  sub?: string;
  className?: string;
}) {
  return (
    <div className={cn("card-soft lift rounded-2xl bg-card px-5 py-4", className)}>
      <Eyebrow>{label}</Eyebrow>
      <p className="mt-1.5 font-display text-2xl font-semibold text-foreground">{value}</p>
      {sub ? <p className="text-[11px] text-muted-foreground">{sub}</p> : null}
    </div>
  );
}

export function Meter({ value, tone = "wine" }: { value: number; tone?: "wine" | "clay" }) {
  return (
    <div className="mt-3 h-1 w-full rounded-full bg-clay/20">
      <div
        className={cn("h-1 rounded-full", tone === "wine" ? "bg-wine" : "bg-clay")}
        style={{ width: `${Math.min(100, value)}%` }}
      />
    </div>
  );
}

export function Action({ children }: { children: ReactNode }) {
  return (
    <button className="mt-4 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-xs font-medium text-primary-foreground transition-transform hover:translate-x-0.5">
      {children} <span aria-hidden>→</span>
    </button>
  );
}

export function Hero({
  eyebrow,
  title,
  accent,
  copy,
}: {
  eyebrow: string;
  title: string;
  accent?: string;
  copy: string;
}) {
  return (
    <div>
      <span className="inline-block rounded-full bg-sand px-3 py-1 text-[10px] font-semibold tracking-[0.18em] text-muted-foreground uppercase">
        {eyebrow}
      </span>
      <h1 className="mt-5 font-display text-4xl leading-[1.08] font-semibold tracking-tight text-foreground sm:text-5xl">
        {title} {accent ? <span className="text-wine">{accent}</span> : null}
      </h1>
      <p className="mt-4 max-w-md text-sm leading-relaxed text-muted-foreground">{copy}</p>
    </div>
  );
}
