import { createFileRoute } from "@tanstack/react-router";
import {
  CalendarClock,
  Gauge,
  LineChart,
  Loader2,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { Reveal } from "@/components/sakhi/Reveal";
import { Basis, Craft, Eyebrow, Hero, Why } from "@/components/sakhi/Cards";
import { IconBadge } from "@/components/sakhi/CompanionAssets";
import { useGrowthForecast, useScheduledPostsQueue } from "@/hooks/use-dashboard-data";
import type { RunRatePoint } from "@/lib/types";

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Analytics — Sakhi" },
      {
        name: "description",
        content:
          "Trend analysis and future growth predictions, projected from your own revenue history.",
      },
    ],
  }),
  component: AnalyticsRoute,
});

function AnalyticsRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <Analytics />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

function weekLabel(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

/** Solid historical line + dashed future-projection line, sharing one
 * continuous path so the projection visually picks up where history ends. */
function ForecastChart({
  historical,
  projected,
}: {
  historical: RunRatePoint[];
  projected: RunRatePoint[];
}) {
  const w = 640;
  const h = 160;
  const all = [...historical, ...projected];
  const values = all.map((p) => p.value);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const y = (v: number) => h - ((v - min) / (max - min || 1)) * h;
  const x = (i: number) => (i / (all.length - 1)) * w;

  const histPath = historical
    .map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`)
    .join(" ");
  const projPoints = [historical[historical.length - 1]!, ...projected];
  const projPath = projPoints
    .map((p, i) => {
      const idx = historical.length - 1 + i;
      return `${i === 0 ? "M" : "L"}${x(idx).toFixed(1)},${y(p.value).toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="mt-4">
      <svg
        viewBox={`0 0 ${w} ${h + 24}`}
        className="w-full"
        role="img"
        aria-label="Revenue trend and projection"
      >
        {[0, 1, 2, 3].map((g) => (
          <line
            key={g}
            x1="0"
            x2={w}
            y1={(h / 3) * g}
            y2={(h / 3) * g}
            stroke="currentColor"
            className="text-clay/20"
            strokeDasharray="3 6"
          />
        ))}
        <path
          d={`${histPath} L${x(historical.length - 1)},${h} L0,${h} Z`}
          fill="color-mix(in oklab, var(--wine) 8%, transparent)"
        />
        <path d={histPath} fill="none" stroke="var(--wine)" strokeWidth="2" strokeLinecap="round" />
        <path
          d={projPath}
          fill="none"
          stroke="var(--wine)"
          strokeOpacity="0.55"
          strokeWidth="2"
          strokeDasharray="6 5"
          strokeLinecap="round"
        />
        {historical.map((p, i) => (
          <text
            key={`h-${p.period_start}`}
            x={x(i)}
            y={h + 18}
            textAnchor={i === 0 ? "start" : "middle"}
            className="fill-[oklch(0.53_0.025_50)] text-[10px]"
          >
            {i === 0 || i === historical.length - 1 ? weekLabel(p.period_start) : ""}
          </text>
        ))}
        {projected.map((p, i) => (
          <text
            key={`p-${p.period_start}`}
            x={x(historical.length + i)}
            y={h + 18}
            textAnchor={i === projected.length - 1 ? "end" : "middle"}
            className="fill-wine text-[10px]"
          >
            {i === projected.length - 1 ? weekLabel(p.period_start) : ""}
          </text>
        ))}
      </svg>
      <div className="mt-1 flex items-center justify-end gap-1.5 text-[10.5px] text-muted-foreground">
        <span
          className="inline-block h-0.5 w-4 rounded-full bg-wine/55"
          style={{ borderTop: "2px dashed var(--wine)" }}
        />
        projected
      </div>
    </div>
  );
}

function Analytics() {
  const {
    data: forecast,
    isLoading: forecastLoading,
    isError: forecastError,
  } = useGrowthForecast();
  const { data: postsQueue, isLoading: postsLoading } = useScheduledPostsQueue();

  const trend = forecast?.trend_per_period ?? 0;
  const trendUp = trend >= 0;
  const nextProjected = forecast?.projected[0]?.value;

  const STATS = [
    {
      label: "Weekly trend",
      value: forecast?.has_sufficient_data
        ? `${trendUp ? "+" : "−"}₹${Math.abs(trend).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
        : "—",
      sub: trendUp ? "growing per week" : "shrinking per week",
      icon: trendUp ? TrendingUp : TrendingDown,
      tone: trendUp ? ("leaf" as const) : ("rose" as const),
    },
    {
      label: "Next week, projected",
      value:
        forecast?.has_sufficient_data && nextProjected !== undefined
          ? `₹${nextProjected.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
          : "—",
      sub: "from your revenue trend",
      icon: LineChart,
      tone: "marigold" as const,
    },
    {
      label: "Trend confidence",
      value: forecast?.has_sufficient_data ? `${Math.round(forecast.confidence_score ?? 0)}%` : "—",
      sub: "how well the trend fits",
      icon: Gauge,
      tone: "indigo" as const,
    },
  ];

  return (
    <Page>
      <section className="py-14 lg:py-16">
        <Reveal>
          <Hero
            eyebrow="Growth data"
            title="Where you're"
            accent="headed, not just where you've been."
            copy="A linear trend fit over your own logged revenue, projected forward — the same math a real forecast uses, not a guess."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-4 py-10 sm:grid-cols-3">
        {forecastLoading ? (
          <div className="col-span-full flex justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          STATS.map((s, i) => (
            <Reveal key={s.label} delay={i * 90}>
              <div className="card-soft lift flex items-center gap-3 rounded-2xl px-5 py-4">
                <IconBadge icon={s.icon} tone={s.tone} />
                <div className="min-w-0">
                  <Eyebrow>{s.label}</Eyebrow>
                  <p className="mt-1 font-display text-xl font-semibold text-foreground">
                    {s.value}
                  </p>
                  <p className="text-[11px] text-muted-foreground">{s.sub}</p>
                </div>
              </div>
            </Reveal>
          ))
        )}
      </section>

      <Reveal className="mt-2">
        <Craft tone="marigold" texture="weave">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-wine" />
            <Eyebrow>Revenue trend & forecast</Eyebrow>
          </div>
          {forecastLoading ? (
            <div className="mt-3 flex items-center gap-2 text-[12.5px] text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Fitting your trend line…
            </div>
          ) : forecastError || !forecast ? (
            <p className="mt-3 text-[12.5px] text-muted-foreground">
              Couldn't load your forecast right now — try again shortly.
            </p>
          ) : !forecast.has_sufficient_data ? (
            <p className="mt-3 text-[12.5px] text-muted-foreground">
              Log income across at least two different weeks and Sakhi will project a trend line
              here.
            </p>
          ) : (
            <>
              <ForecastChart historical={forecast.historical} projected={forecast.projected} />
              {forecast.why && <Why>{forecast.why}</Why>}
              <Basis>
                {forecast.basis ??
                  "A linear trend fit over your logged weekly income, projected forward."}
              </Basis>
            </>
          )}
        </Craft>
      </Reveal>

      <Reveal className="mt-6" delay={40}>
        <Craft tone="indigo" texture="blockprint">
          <div className="flex items-center gap-2">
            <CalendarClock className="h-4 w-4 text-wine" />
            <Eyebrow>Content pipeline</Eyebrow>
          </div>
          {postsLoading ? (
            <div className="mt-3 flex items-center gap-2 text-[12.5px] text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Checking your queue…
            </div>
          ) : (
            <p className="mt-2 text-[13px] text-foreground/75">
              {postsQueue?.total
                ? `${postsQueue.total} post${postsQueue.total === 1 ? "" : "s"} scheduled in your content queue.`
                : "No posts scheduled yet — Content Calendar can generate a month's worth in one go."}
            </p>
          )}
        </Craft>
      </Reveal>

      <Reveal className="mt-6" delay={80}>
        <Craft tone="sand">
          <div className="flex items-center gap-2">
            <LineChart className="h-4 w-4 text-wine" />
            <Eyebrow>Social & website metrics</Eyebrow>
          </div>
          <p className="mt-2 text-[13px] text-foreground/75">
            Followers, reach, engagement and website visitors need a connected Instagram/website
            account to measure — nothing's connected yet, so nothing is shown here.
          </p>
          <p className="mt-2 text-[11.5px] text-muted-foreground">
            Connect a social account once that's available, and this section fills in with real
            numbers — never estimated ones.
          </p>
        </Craft>
      </Reveal>
    </Page>
  );
}
