import type { ComponentType } from "react";
import { Page } from "@/components/sakhi/Layout";
import { Reveal } from "@/components/sakhi/Reveal";
import { Craft, Eyebrow, HandNote } from "@/components/sakhi/Cards";
import { IconBadge } from "@/components/sakhi/CompanionAssets";

type ComingSoonTone = "rose" | "leaf" | "marigold" | "indigo" | "lilac" | "sand";

export function ComingSoon({
  eyebrow,
  title,
  accent,
  copy,
  icon,
  tone = "rose",
  capabilities,
}: {
  eyebrow: string;
  title: string;
  accent?: string;
  copy: string;
  icon: ComponentType<{ className?: string }>;
  tone?: ComingSoonTone;
  capabilities: string[];
}) {
  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <div className="relative">
            <span className="inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
              {eyebrow}
            </span>
            <h1 className="font-display mt-6 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {title} {accent ? <span className="text-wine italic">{accent}</span> : null}
            </h1>
            <p className="mt-4 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
              {copy}
            </p>
            <span className="mt-6 inline-flex items-center gap-1.5 rounded-full bg-marigold px-3 py-1.5 text-[11px] font-semibold text-[oklch(0.42_0.09_70)]">
              Coming soon
            </span>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <div className="mx-auto grid w-full max-w-sm place-items-center">
            <IconBadge icon={icon} tone={tone} className="h-24 w-24 [&>svg]:h-10 [&>svg]:w-10" />
          </div>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-2 lg:grid-cols-4">
        {capabilities.map((c, i) => (
          <Reveal key={c} delay={i * 80}>
            <Craft tone={tone} className="h-full">
              <Eyebrow>Planned</Eyebrow>
              <p className="mt-2 text-[13.5px] leading-relaxed text-foreground/80">{c}</p>
            </Craft>
          </Reveal>
        ))}
      </section>

      <Reveal className="mt-6">
        <HandNote>This module is on the roadmap and isn't wired up to real data yet.</HandNote>
      </Reveal>
    </Page>
  );
}
