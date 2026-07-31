import { Mic } from "lucide-react";

const BARS = [0.5, 0.85, 0.35, 1, 0.6, 0.95, 0.45, 0.8, 0.3, 0.7, 0.5];

export function MicPanel({
  title,
  quote,
  languages,
  className = "",
}: {
  title: string;
  quote: string;
  languages?: string;
  className?: string;
}) {
  return (
    <div
      className={`card-soft weave relative overflow-hidden rounded-3xl px-6 py-8 text-center ${className}`}
    >
      <div
        aria-hidden
        className="blockprint pointer-events-none absolute -top-6 -right-6 h-32 w-32 opacity-40"
      />
      <button
        aria-label={title}
        className="relative mx-auto grid h-16 w-16 place-items-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-105"
        style={{ animation: "halo 2.6s ease-out infinite" }}
      >
        <Mic className="h-6 w-6" />
      </button>

      <div className="mt-4 flex h-6 items-end justify-center gap-[3px]">
        {BARS.map((h, i) => (
          <span
            key={i}
            className="w-[3px] origin-bottom rounded-full bg-wine/60"
            style={{
              height: `${h * 24}px`,
              animation: `wave ${900 + i * 130}ms ease-in-out ${i * 70}ms infinite`,
            }}
          />
        ))}
      </div>

      <p className="mt-3 font-display text-base font-semibold text-foreground">{title}</p>
      <p className="hand mt-1">{quote}</p>
      {languages ? <p className="mt-2 text-[11px] text-muted-foreground">{languages}</p> : null}
    </div>
  );
}
