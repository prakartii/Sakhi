import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle, Bell, Link2, Loader2, TriangleAlert } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Basis, Craft, Eyebrow, HandNote, type Tone, Why } from "@/components/sakhi/Cards";
import { BotanicalMark, IconBadge } from "@/components/sakhi/CompanionAssets";
import { StickyNote } from "@/components/sakhi/CompanionHero";
import { useNoticedSummary } from "@/hooks/use-dashboard-data";

export const Route = createFileRoute("/noticed")({
  head: () => ({
    meta: [
      { title: "Sakhi noticed something before you had to" },
      {
        name: "description",
        content:
          "What's compounding across your stock, revenue and memory this week — connected in one narrative, not a demo.",
      },
    ],
  }),
  component: NoticedRoute,
});

function NoticedRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <Noticed />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

function SignalCard({
  tag,
  tone,
  title,
  copy,
  actionLabel,
  actionTo,
  index,
}: {
  tag: string;
  tone: Tone;
  title: string;
  copy: string;
  actionLabel: string;
  actionTo: string;
  index: number;
}) {
  return (
    <Reveal delay={index * 80} className="lg:col-span-6">
      <Craft tone={tone} texture={index % 2 === 0 ? "weave" : "blockprint"} className="h-full">
        <Eyebrow>{tag}</Eyebrow>
        <h3 className="mt-2 font-display text-xl leading-snug font-semibold">{title}</h3>
        <p className="mt-2 text-[13px] text-foreground/75">{copy}</p>
        <Link
          to={actionTo}
          className="mt-4 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-xs font-medium text-primary-foreground transition-transform hover:translate-x-0.5"
        >
          {actionLabel} <span aria-hidden>→</span>
        </Link>
      </Craft>
    </Reveal>
  );
}

function Noticed() {
  const { data: summary, isLoading } = useNoticedSummary();

  const stockSignals = summary?.stock_signals ?? [];
  const memorySignals = summary?.memory_signals ?? [];
  const revenueDeclining = summary?.revenue_declining ?? false;
  const hasConnection = !!summary?.connected_why;

  const domainsWithSignals =
    (stockSignals.length > 0 ? 1 : 0) +
    (revenueDeclining ? 1 : 0) +
    (memorySignals.length > 0 ? 1 : 0);
  const signalCount = stockSignals.length + memorySignals.length + (revenueDeclining ? 1 : 0);

  let index = 0;

  return (
    <Page>
      <section className="grid items-center gap-10 py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <div className="relative">
            <BotanicalMark className="pointer-events-none absolute -top-8 -left-12 hidden h-48 w-36 opacity-[0.1] lg:block" />
            <span className="relative inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
              Cross-module intelligence
            </span>
            <h1 className="relative mt-6 font-display font-semibold tracking-tight text-foreground">
              <span className="block text-3xl sm:text-4xl">Sakhi noticed</span>
              <span className="block text-4xl sm:text-5xl">something</span>
              <span className="block text-5xl text-wine italic sm:text-6xl">
                before you had to.
              </span>
            </h1>
            <p className="relative mt-6 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
              Not a matched list, and not something you asked — this is what's compounding across
              your stock, revenue and memory this week, connected into one picture.
            </p>
            <div className="relative mt-7 flex items-center gap-3 rounded-2xl bg-marigold/60 px-4 py-3">
              <IconBadge icon={Bell} tone="marigold" />
              <p className="text-[13px] font-medium text-wine-soft">
                {isLoading
                  ? "Checking your records…"
                  : signalCount === 0
                    ? "Nothing urgent spotted yet"
                    : `${signalCount} signal${signalCount === 1 ? "" : "s"} spotted, ${domainsWithSignals} area${domainsWithSignals === 1 ? "" : "s"} of your business involved`}
              </p>
            </div>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <div className="relative mx-auto w-full max-w-sm">
            <StickyNote rotate={4} className="absolute -top-6 -right-6 z-20 hidden sm:block">
              ✎ before it costs you
            </StickyNote>
            <MicPanel
              title="Ask Sakhi why"
              quote="&ldquo;Iska kya matlab hai?&rdquo;"
              className="relative z-10"
            />
          </div>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      {isLoading ? (
        <div className="flex justify-center py-14">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : signalCount === 0 ? (
        <Reveal>
          <Craft tone="sand" className="py-10 text-center">
            <Eyebrow>Nothing urgent yet</Eyebrow>
            <p className="mt-2 text-[13.5px] text-foreground/75">
              As you log sales, stock and voice notes, Sakhi starts spotting patterns across them —
              and connecting the ones that relate to each other.
            </p>
          </Craft>
        </Reveal>
      ) : (
        <>
          {hasConnection && (
            <Reveal className="py-10">
              <Craft tone="lilac" texture="weave">
                <div className="flex items-center gap-2">
                  <Link2 className="h-4 w-4 text-wine" />
                  <Eyebrow>What's connected this week</Eyebrow>
                </div>
                <Why>{summary!.connected_why}</Why>
                <Basis>{summary!.connected_basis ?? undefined}</Basis>
              </Craft>
            </Reveal>
          )}

          <section className={`grid gap-5 ${hasConnection ? "" : "py-10"} lg:grid-cols-12`}>
            {stockSignals.map((s) => (
              <SignalCard
                key={s.inventory_id}
                index={index++}
                tag="Stockout predicted"
                tone="marigold"
                title={`${s.item_name} will run out in about ${s.days_remaining} day${s.days_remaining === 1 ? "" : "s"}.`}
                copy={`${s.current_quantity} ${s.unit} left, based on your own logged sales.`}
                actionLabel="Reorder in Inventory"
                actionTo="/inventory"
              />
            ))}
            {revenueDeclining && (
              <SignalCard
                index={index++}
                tag="Revenue dip"
                tone="indigo"
                title={`Your weekly revenue is trending down by about ₹${Math.abs(summary?.revenue_trend_per_week ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}/week.`}
                copy="Worth a look before it compounds — see the full trend and projection."
                actionLabel="See the trend"
                actionTo="/analytics"
              />
            )}
            {memorySignals.map((m) => (
              <SignalCard
                key={m.business_memory_id}
                index={index++}
                tag="Challenge noticed"
                tone="rose"
                title={m.title ?? m.content.slice(0, 80)}
                copy={m.content}
                actionLabel="See your Memory"
                actionTo="/memory"
              />
            ))}
          </section>
        </>
      )}

      {signalCount > 0 && (
        <HandNote>
          {domainsWithSignals >= 2 ? (
            <>
              <AlertTriangle className="mr-1 inline h-3.5 w-3.5" />
              Every signal above traces back to something you actually logged — connected, not
              guessed.
            </>
          ) : (
            <>
              <TriangleAlert className="mr-1 inline h-3.5 w-3.5" />
              Every signal above traces back to something you actually logged.
            </>
          )}
        </HandNote>
      )}
    </Page>
  );
}
