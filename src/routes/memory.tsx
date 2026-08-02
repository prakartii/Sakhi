import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { BookOpen, Loader2, Search, Sparkles } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import { Basis, Craft, Eyebrow, HandNote, Pill, Why } from "@/components/sakhi/Cards";
import { BotanicalMark, SpiralEdge } from "@/components/sakhi/CompanionAssets";
import { MemoryCard, StatusPill, StickyNote, TrustChip } from "@/components/sakhi/CompanionHero";
import {
  JournalWash,
  MemoryBanner,
  MemoryDot,
  PostageStamp,
} from "@/components/sakhi/MemoryAssets";
import { useBusinessMemories, useMemoryInsights, useSearchMemories } from "@/hooks/use-memories";
import type { BusinessMemory } from "@/lib/types";

export const Route = createFileRoute("/memory")({
  head: () => ({
    meta: [
      { title: "Business Memory — Sakhi" },
      {
        name: "description",
        content:
          "Every moment you've spoken about — kept in one timeline, extracted automatically from your voice check-ins.",
      },
    ],
  }),
  component: MemoryRoute,
});

function MemoryRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <Memory />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

const TYPE_TONE: Record<BusinessMemory["memory_type"], "rose" | "leaf" | "marigold" | "indigo"> = {
  fact: "indigo",
  milestone: "marigold",
  goal: "leaf",
  challenge: "rose",
  preference: "indigo",
  note: "indigo",
  decision: "leaf",
};

function formatDate(value: string | null): string {
  if (!value) return "Undated";
  return new Date(value).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function Memory() {
  const { data, isLoading } = useBusinessMemories();
  const memories = data?.items ?? [];
  const { data: aiInsights, isLoading: aiInsightsLoading } = useMemoryInsights();
  const [searchInput, setSearchInput] = useState("");
  const { data: searchResults, isFetching: isSearching } = useSearchMemories(searchInput);

  const insights = useMemo(() => {
    if (memories.length === 0) return null;
    const counts = new Map<string, number>();
    let importanceSum = 0;
    for (const m of memories) {
      counts.set(m.memory_type, (counts.get(m.memory_type) ?? 0) + 1);
      importanceSum += m.importance_score;
    }
    const topType = [...counts.entries()].sort((a, b) => b[1] - a[1])[0];
    const latest = memories[0];
    return {
      total: memories.length,
      avgImportance: (importanceSum / memories.length).toFixed(1),
      topType: topType ? `${topType[0]} (${topType[1]})` : "—",
      latest,
    };
  }, [memories]);

  return (
    <Page>
      <section className="relative overflow-hidden py-14 lg:py-20">
        <div className="relative grid items-start gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:gap-10">
          <Reveal>
            <div className="relative lg:pt-2">
              <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />

              <span className="relative inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
                Business Memory
              </span>

              <h1 className="relative mt-6 font-display font-semibold tracking-tight text-foreground">
                <span className="block text-3xl sm:text-4xl">Sakhi remembers</span>
                <span className="block text-4xl sm:text-5xl">what your business</span>
                <span className="block text-5xl text-wine italic sm:text-6xl">
                  already taught you.
                </span>
              </h1>

              <p className="relative mt-6 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
                Every moment you've spoken about with Sakhi — extracted automatically and kept in
                one timeline.
              </p>

              <div className="relative mt-7 flex flex-wrap gap-2.5">
                <TrustChip>One timeline</TrustChip>
                <TrustChip>Extracted from your voice</TrustChip>
                <TrustChip>Never re-typed</TrustChip>
              </div>

              <StickyNote rotate={-3} className="relative z-10 mt-8">
                ✎ she doesn't forget what mattered
              </StickyNote>
            </div>
          </Reveal>

          <Reveal delay={120}>
            <div className="relative mx-auto w-full max-w-sm pt-4 lg:mx-0 lg:ml-auto lg:pt-10">
              <JournalWash className="pointer-events-none absolute -inset-x-8 -inset-y-8 -z-10 hidden lg:block" />

              <MemoryCard
                tone="marigold"
                label="Remembered"
                rotate={-3}
                className="relative z-20 mb-4 lg:absolute lg:top-0 lg:-left-8 lg:mb-0"
              >
                <p className="text-xl leading-none font-semibold">{insights?.total ?? 0}</p>
                <p className="mt-1 text-[11px] font-normal text-foreground/60">
                  moments remembered
                </p>
              </MemoryCard>

              <StatusPill
                tone="rose"
                rotate={2}
                className="relative z-20 mb-4 w-fit lg:absolute lg:top-3 lg:-right-4 lg:mb-0"
              >
                {insights?.latest
                  ? `Latest: ${insights.latest.title ?? insights.latest.memory_type}`
                  : "Talk to Sakhi to begin"}
              </StatusPill>

              <div className="relative">
                <SpiralEdge className="absolute inset-y-4 -left-3 z-0 hidden w-5 sm:flex" />
                <span
                  aria-hidden
                  className="absolute -top-2.5 left-9 z-20 h-5 w-14 -rotate-3 bg-marigold/85"
                  style={{ boxShadow: "var(--shadow-soft)" }}
                />
                <span
                  aria-hidden
                  className="absolute -top-2.5 right-9 z-20 h-5 w-14 rotate-2 bg-rose/85"
                  style={{ boxShadow: "var(--shadow-soft)" }}
                />
                <MicPanel
                  title="Add a moment"
                  quote="&ldquo;Aaj kya hua?&rdquo;"
                  className="relative z-10"
                />
                <PostageStamp rotate={7} className="absolute -right-4 -bottom-5 z-20 h-12 w-10" />
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <div className="thread opacity-50" />

      <section className="py-10">
        <Reveal>
          <div className="flex items-center gap-2 text-foreground/70">
            <Search className="h-4 w-4" />
            <p className="text-sm font-semibold">Ask your memory</p>
          </div>
          <div className="mt-3 flex items-center gap-2 rounded-2xl border border-clay/25 bg-card px-4 py-2.5">
            <Search className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="e.g. what happened with pricing?"
              className="min-w-0 flex-1 bg-transparent text-[13px] text-foreground placeholder:text-muted-foreground focus:outline-none"
            />
            {isSearching && (
              <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-muted-foreground" />
            )}
          </div>
          <p className="mt-1.5 text-[11px] text-muted-foreground">
            Ranked by meaning, not just matching words — powered by semantic search over everything
            Sakhi remembers.
          </p>
        </Reveal>

        {searchInput.trim() && (
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {!isSearching && searchResults?.results.length === 0 ? (
              <p className="text-[12.5px] text-muted-foreground sm:col-span-2 lg:col-span-3">
                Nothing matched that yet.
              </p>
            ) : (
              searchResults?.results.map((r, i) => (
                <Reveal key={r.business_memory_id} delay={i * 60}>
                  <Craft tone="indigo" texture="weave">
                    <Eyebrow>{Math.round(r.similarity * 100)}% match</Eyebrow>
                    <h3 className="mt-1.5 font-display text-base font-semibold">
                      {r.title ?? "Memory"}
                    </h3>
                    <p className="mt-1 text-[12.5px] text-foreground/75">{r.content}</p>
                  </Craft>
                </Reveal>
              ))
            )}
          </div>
        )}
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-5 py-10 lg:grid-cols-[1.35fr_0.95fr]">
        <div className="relative space-y-5">
          <div className="mb-1 flex items-center gap-2 text-foreground/70">
            <BookOpen className="h-4 w-4" />
            <p className="text-sm font-semibold">Your Memory Journal</p>
          </div>
          <div
            aria-hidden
            className="absolute top-4 bottom-4 -left-1 hidden w-px bg-[repeating-linear-gradient(180deg,color-mix(in_oklab,var(--clay)_55%,transparent)_0_8px,transparent_8px_16px)] lg:block"
          />
          {isLoading ? (
            <div className="flex justify-center py-14">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : memories.length === 0 ? (
            <Craft tone="sand">
              <p className="text-[13px] text-foreground/75">
                No memories yet — talk to Sakhi on the Companion page and she'll start remembering
                the moments that matter for your business.
              </p>
            </Craft>
          ) : (
            memories.map((m, i) => (
              <Reveal key={m.id} delay={i * 70}>
                <Craft tone={i === 0 ? "sand" : "cream"} texture={i === 0 ? "weave" : undefined}>
                  <div className="flex items-center gap-2">
                    <MemoryDot tone={TYPE_TONE[m.memory_type]} />
                    <Eyebrow>{formatDate(m.occurred_at ?? m.created_at)}</Eyebrow>
                  </div>
                  <h3 className="mt-1.5 font-display text-xl font-semibold">
                    {m.title ?? m.memory_type}
                  </h3>
                  <p className="mt-1 text-[13px] text-foreground/75">{m.content}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Pill tone={TYPE_TONE[m.memory_type]}>{m.memory_type}</Pill>
                    <Pill>Importance {m.importance_score}/5</Pill>
                  </div>
                  <Basis>Extracted from a {m.source} conversation.</Basis>
                </Craft>
              </Reveal>
            ))
          )}
        </div>

        <Reveal delay={100}>
          <Craft
            tone="lilac"
            texture="blockprint"
            className="relative sticky top-28 overflow-hidden"
          >
            <BotanicalMark className="pointer-events-none absolute -top-6 -right-8 h-32 w-28 opacity-[0.1]" />
            <Eyebrow>Memory insights</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">What your memory says</h3>
            {aiInsightsLoading ? (
              <div className="mt-3 flex items-center gap-2 text-[12px] text-muted-foreground">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Sakhi is thinking it over…
              </div>
            ) : aiInsights ? (
              <>
                <Why>{aiInsights.why}</Why>
                <Basis>{aiInsights.basis}</Basis>
              </>
            ) : null}
            {insights ? (
              <div className="mt-4 space-y-3">
                <div className="flex items-start gap-3 rounded-2xl border border-clay/20 bg-card/80 px-4 py-3">
                  <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-lilac ring-1 ring-clay/20">
                    <Sparkles className="h-3.5 w-3.5 text-wine" />
                  </span>
                  <div className="min-w-0">
                    <Eyebrow>Moments remembered</Eyebrow>
                    <p className="mt-1 font-display text-xl font-semibold">{insights.total}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-2xl border border-clay/20 bg-card/80 px-4 py-3">
                  <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-lilac ring-1 ring-clay/20">
                    <Sparkles className="h-3.5 w-3.5 text-wine" />
                  </span>
                  <div className="min-w-0">
                    <Eyebrow>Most common type</Eyebrow>
                    <p className="mt-1 font-display text-xl font-semibold capitalize">
                      {insights.topType}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-2xl border border-clay/20 bg-card/80 px-4 py-3">
                  <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-lilac ring-1 ring-clay/20">
                    <Sparkles className="h-3.5 w-3.5 text-wine" />
                  </span>
                  <div className="min-w-0">
                    <Eyebrow>Average importance</Eyebrow>
                    <p className="mt-1 font-display text-xl font-semibold">
                      {insights.avgImportance} / 5
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-[12.5px] text-muted-foreground">
                Insights appear once Sakhi has remembered a few things about your business.
              </p>
            )}
            <HandNote>Your memory isn't nostalgia — it's working for you.</HandNote>
          </Craft>
        </Reveal>
      </section>

      <Reveal>
        <MemoryBanner
          quote="Sakhi remembers what your business already taught you."
          note="Your memory isn't nostalgia — it's working for you."
          className="mt-4"
        />
      </Reveal>
    </Page>
  );
}
