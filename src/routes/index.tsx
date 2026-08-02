import { useMemo } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Heart, Sparkles } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { Reveal } from "@/components/sakhi/Reveal";
import { BotanicalMark, ScrapbookBleed, StitchDivider } from "@/components/sakhi/CompanionAssets";
import {
  MemoryCard,
  StatusPill,
  StickyNote,
  TrustChip,
  VoiceCard,
} from "@/components/sakhi/CompanionHero";
import { FeaturedMetric, NoteMetric, TicketMetric } from "@/components/sakhi/CompanionMetrics";
import { MorningBriefing, type BriefingTask } from "@/components/sakhi/CompanionBriefing";
import { Action, Basis, Craft, Eyebrow, Why } from "@/components/sakhi/Cards";
import { ChatBubble, ChatThinkingBubble } from "@/components/sakhi/WebsiteChatAssets";
import { useTranslation } from "react-i18next";
import { useVoiceCompanion } from "@/hooks/use-voice-companion";
import { useAuth } from "@/hooks/use-auth";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import { useAISummary, useInventorySummary } from "@/hooks/use-dashboard-data";
import { useTransactions } from "@/hooks/use-transactions";
import { useBusinessMemories } from "@/hooks/use-memories";

const FOCUS_TONES: BriefingTask["tone"][] = ["rose", "leaf", "marigold", "indigo"];

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function thisMonthKey(): string {
  return new Date().toISOString().slice(0, 7);
}

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Sakhi Companion — she speaks, and her day appears" },
      {
        name: "description",
        content:
          "One voice check-in in your own language. Sakhi remembers every order, price and supplier — then tells you what to do next.",
      },
      { property: "og:title", content: "Sakhi Companion — she speaks, and her day appears" },
      {
        property: "og:description",
        content:
          "One voice check-in in your own language. Sakhi remembers every order, price and supplier — then tells you what to do next.",
      },
    ],
  }),
  component: Companion,
});

function Companion() {
  const { t } = useTranslation();
  const voice = useVoiceCompanion();
  const { user, loading: authLoading } = useAuth();
  const { profile, hasProfile } = usePrimaryBusinessProfile();
  const aiSummary = useAISummary();
  const transactions = useTransactions();
  const memories = useBusinessMemories();
  const inventorySummary = useInventorySummary();

  const signedIn = !authLoading && !!user;

  const { thisMonthNet, todaysSales, todaysOrderCount, pendingPayments, pendingBuyerCount } =
    useMemo(() => {
      const items = transactions.data?.items ?? [];
      const month = thisMonthKey();
      const today = todayISO();
      let net = 0;
      let salesToday = 0;
      let ordersToday = 0;
      let pending = 0;
      let pendingBuyers = 0;
      for (const t of items) {
        const sign = t.transaction_type === "income" ? 1 : -1;
        if (t.transaction_date.slice(0, 7) === month) net += sign * t.amount;
        if (t.transaction_type === "income" && t.transaction_date === today) {
          salesToday += t.amount;
          ordersToday += 1;
        }
        if (t.transaction_type === "income" && t.status === "pending") {
          pending += t.amount;
          pendingBuyers += 1;
        }
      }
      return {
        thisMonthNet: net,
        todaysSales: salesToday,
        todaysOrderCount: ordersToday,
        pendingPayments: pending,
        pendingBuyerCount: pendingBuyers,
      };
    }, [transactions.data]);

  const tasks: BriefingTask[] = (aiSummary.data?.highlights ?? []).map((highlight, i) => ({
    text: highlight,
    tag: "Insight",
    tone: FOCUS_TONES[i % FOCUS_TONES.length]!,
    icon: Sparkles,
  }));

  const latestMemory = memories.data?.items[0];
  const insightCards = (aiSummary.data?.top_actions ?? []).slice(0, 2);

  const voiceCardProps = (() => {
    switch (voice.state) {
      case "recording":
        return {
          title: t("home.listeningTitle"),
          quote: t("home.listeningQuote"),
          statusLabel: t("home.listeningStatus"),
        };
      case "processing":
        return {
          title: t("home.thinkingTitle"),
          quote: voice.result ? voice.result.transcript : t("home.thinkingQuote"),
          statusLabel: t("home.thinkingStatus"),
        };
      case "speaking":
        return {
          title: t("home.sakhiSaysTitle"),
          quote: voice.result?.answer ?? "",
          statusLabel: t("home.speakingStatus"),
        };
      case "error":
        return {
          title: t("home.talkToSakhiTitle"),
          quote: voice.errorMessage ?? t("home.genericError"),
          statusLabel: t("home.tapToTalkStatus"),
        };
      default:
        return {
          title: voice.result ? t("home.sakhiSaysTitle") : t("home.talkToSakhiTitle"),
          quote: voice.result?.answer ?? t("home.defaultQuote"),
          statusLabel: t("home.tapToTalkStatus"),
        };
    }
  })();

  return (
    <Page>
      {/* ---------- Hero : memory wall ---------- */}
      <section className="relative overflow-hidden py-14 lg:py-20">
        <ScrapbookBleed className="pointer-events-none absolute inset-y-0 -right-10 hidden w-[52%] opacity-55 lg:block" />

        <div className="relative grid items-start gap-14 lg:grid-cols-[1fr_1.05fr] lg:gap-10">
          <Reveal>
            <div className="relative lg:pt-4">
              <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />

              <span className="relative inline-block rounded-full bg-sand px-3.5 py-1.5 text-[10px] font-semibold tracking-[0.22em] text-muted-foreground uppercase">
                {t("home.eyebrow")}
              </span>

              <h1 className="relative mt-6 font-display font-semibold tracking-tight text-foreground">
                <span className="block text-3xl sm:text-4xl">{t("home.titleLine1")}</span>
                <span className="block text-4xl sm:text-5xl">{t("home.titleLine2")}</span>
                <span className="relative inline-block text-5xl text-wine italic sm:text-6xl">
                  {t("home.titleAccent")}
                  <Heart className="absolute -top-1 -right-7 h-4 w-4 -rotate-12 text-wine/40" />
                </span>
              </h1>

              <p className="relative mt-6 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground sm:text-base">
                {t("home.copy")}
              </p>

              <div className="relative mt-8 flex flex-wrap gap-2.5">
                <TrustChip>{t("home.trustVoiceFirst")}</TrustChip>
                <TrustChip>{t("home.trustRemembers")}</TrustChip>
                <TrustChip>{t("home.trustLanguages")}</TrustChip>
              </div>

              <StickyNote rotate={-3} className="relative z-10 mt-9">
                {t("home.stickyNote")}
              </StickyNote>
            </div>
          </Reveal>

          <Reveal delay={120}>
            <div className="relative mx-auto w-full max-w-md pt-4 lg:mx-0 lg:ml-auto lg:pt-10">
              {hasProfile && (
                <MemoryCard
                  tone="leaf"
                  label={t("home.todayLabel")}
                  rotate={-3}
                  className="relative z-20 mb-4 lg:absolute lg:top-0 lg:-left-6 lg:mb-0"
                >
                  <p className="text-xl leading-none font-semibold">
                    ₹{todaysSales.toLocaleString("en-IN")}
                  </p>
                  <p className="mt-1 text-[11px] font-normal text-foreground/60">
                    {todaysOrderCount}{" "}
                    {t(todaysOrderCount === 1 ? "home.ordersSuffixOne" : "home.ordersSuffixMany")}{" "}
                    in
                  </p>
                </MemoryCard>
              )}

              {aiSummary.data?.highlights[0] && (
                <StatusPill
                  tone="indigo"
                  rotate={2}
                  className="relative z-20 mb-4 lg:absolute lg:top-4 lg:-right-2 lg:mb-0"
                >
                  {aiSummary.data.highlights[0]}
                </StatusPill>
              )}

              <VoiceCard
                {...voiceCardProps}
                languages="हिंदी · বাংলা · தமிழ் · తెలుగు · मराठी · ਪੰਜਾਬੀ · മലയാളം · অসমীয়া · ગુજરાતી · ಕನ್ನಡ"
                className="relative z-10"
                isRecording={voice.isRecording}
                isBusy={voice.isBusy}
                onMicClick={voice.isRecording ? voice.stopRecording : voice.startRecording}
              />
              {inventorySummary.data && inventorySummary.data.low_stock_count > 0 && (
                <StatusPill
                  tone="rose"
                  rotate={-2}
                  className="relative z-20 mt-4 ml-auto w-fit lg:absolute lg:-bottom-3 lg:left-6 lg:mt-0"
                >
                  {inventorySummary.data.low_stock_count}{" "}
                  {t(
                    inventorySummary.data.low_stock_count === 1
                      ? "home.lowStockSuffixOne"
                      : "home.lowStockSuffixMany",
                  )}
                </StatusPill>
              )}
            </div>
          </Reveal>
        </div>
      </section>

      {voice.messages.length > 0 && (
        <Reveal>
          <section className="py-4">
            <div className="card-soft mx-auto max-w-2xl overflow-hidden rounded-3xl">
              <div className="flex items-center gap-2 border-b border-clay/15 bg-sand/60 px-4 py-3">
                <Sparkles className="h-4 w-4 text-wine" />
                <p className="text-[12.5px] font-semibold text-foreground">
                  {t("home.yourConversation")}
                </p>
              </div>
              <div className="max-h-96 space-y-3 overflow-y-auto px-4 py-4">
                {voice.messages.map((message, i) => (
                  <ChatBubble key={`${message.created_at}-${i}`} message={message} />
                ))}
                {voice.state === "processing" && <ChatThinkingBubble />}
              </div>
            </div>
          </section>
        </Reveal>
      )}

      <StitchDivider className="opacity-50" />

      {hasProfile && (
        <>
          {/* ---------- Metrics : three personalities ---------- */}
          <section className="grid gap-5 py-12 sm:grid-cols-12">
            <Reveal className="sm:col-span-5" delay={0}>
              <FeaturedMetric
                label="This month net"
                value={`₹${thisMonthNet.toLocaleString("en-IN")}`}
                note="Across every order, sale and supplier payment you've logged this month."
                className="h-full"
              />
            </Reveal>
            <Reveal className="sm:col-span-4" delay={90}>
              <TicketMetric
                label="Today's sales"
                value={`₹${todaysSales.toLocaleString("en-IN")}`}
                sub={`${todaysOrderCount} ${todaysOrderCount === 1 ? "order" : "orders"}`}
                className="h-full"
              />
            </Reveal>
            <Reveal className="sm:col-span-3" delay={180}>
              <NoteMetric
                label="Pending payments"
                value={`₹${pendingPayments.toLocaleString("en-IN")}`}
                sub={`${pendingBuyerCount} ${pendingBuyerCount === 1 ? "buyer" : "buyers"}`}
                className="h-full"
              />
            </Reveal>
          </section>

          {/* ---------- Good morning : editorial intelligence board ---------- */}
          <Reveal>
            <MorningBriefing
              time={new Date().toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" })}
              place={profile?.city ?? "your city"}
              name={profile?.owner_name ?? profile?.business_name ?? "there"}
              tasks={tasks}
              why="Grounded in your own transactions, stock levels and voice check-ins — not generic advice."
              basis="Based on what you've shared with Sakhi so far."
              note={
                memories.data
                  ? `Sakhi remembers ${memories.data.total} thing${memories.data.total === 1 ? "" : "s"} about your business so far.`
                  : "Talk to Sakhi and she'll start remembering things about your business."
              }
            />
          </Reveal>

          {/* ---------- Insight cards ---------- */}
          <section className="mt-10 grid gap-5 lg:grid-cols-12">
            {insightCards.map((action, i) => (
              <Reveal key={action.action} className="lg:col-span-6" delay={i * 100}>
                <Craft
                  tone={i === 0 ? "leaf" : "rose"}
                  className="relative h-full overflow-hidden rounded-tl-[2.5rem] rounded-br-[2.5rem] border-2 border-dashed border-leaf-ink/25"
                >
                  <Eyebrow>{i === 0 ? "Daily briefing" : "Smart suggestion"}</Eyebrow>
                  <h3 className="mt-2 font-display text-xl font-semibold">{action.action}</h3>
                  <Why>{action.why}</Why>
                  <Basis />
                  {i === 1 && <Action>See details</Action>}
                </Craft>
              </Reveal>
            ))}

            <Reveal className="lg:col-span-12" delay={200}>
              <Craft
                tone="marigold"
                className="relative rounded-[1.25rem] rounded-tl-[2.5rem] border-2 border-dashed border-wine/20"
              >
                <Eyebrow>What Sakhi last heard</Eyebrow>
                {latestMemory ? (
                  <>
                    <h3 className="mt-2 font-display text-xl font-semibold">
                      {latestMemory.title ?? latestMemory.memory_type}
                    </h3>
                    <p className="mt-2 text-[13px] text-foreground/75">{latestMemory.content}</p>
                    <Why>Spoken by you, not typed — Sakhi keeps what you tell her.</Why>
                    <Basis />
                  </>
                ) : (
                  <p className="mt-2 text-[13px] text-foreground/75">
                    Nothing yet — tap the mic above and tell Sakhi about your business.
                  </p>
                )}
              </Craft>
            </Reveal>
          </section>
        </>
      )}

      {signedIn && !hasProfile && (
        <Reveal>
          <Craft tone="sand" className="mt-10">
            <Eyebrow>Get started</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">
              Tell Sakhi about your business
            </h3>
            <p className="mt-2 text-[13px] text-foreground/75">
              Finish business setup and everything below will fill in with your own numbers.
            </p>
          </Craft>
        </Reveal>
      )}
    </Page>
  );
}
