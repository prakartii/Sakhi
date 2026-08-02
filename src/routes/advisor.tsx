import { useEffect, useRef, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { BadgeCheck, Loader2, Sparkles } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { Reveal } from "@/components/sakhi/Reveal";
import { Craft, Eyebrow, Hero, Pill } from "@/components/sakhi/Cards";
import { BotanicalMark } from "@/components/sakhi/CompanionAssets";
import { ChatBubble, ChatComposer, ChatThinkingBubble } from "@/components/sakhi/WebsiteChatAssets";
import { useAdvisorChatHistory, useSendAdvisorMessage } from "@/hooks/use-advisor-chat";
import { ApiError } from "@/lib/api-client";

export const Route = createFileRoute("/advisor")({
  head: () => ({
    meta: [
      { title: "AI Advisor — Sakhi" },
      {
        name: "description",
        content:
          "Ask Sakhi what to do next — advice grounded in your own business, brand and sales data.",
      },
    ],
  }),
  component: AdvisorRoute,
});

function AdvisorRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <Advisor />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

const SUGGESTIONS = [
  "How am I doing this month?",
  "What should I post about this week?",
  "How's my brand coming along?",
  "What should I focus on to grow sales?",
];

const SERVICE_LABELS: Record<string, string> = {
  brand: "Brand",
  analytics: "Revenue & stock",
  content: "Content ideas",
  website: "Website",
};

function Advisor() {
  const { messages: historyMessages, isLoading: historyLoading } = useAdvisorChatHistory();
  const sendMessage = useSendAdvisorMessage();

  const [input, setInput] = useState("");
  const [lastServices, setLastServices] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [historyMessages.length, sendMessage.isPending]);

  function send(message: string) {
    if (!message.trim()) return;
    setInput("");
    sendMessage.mutate(message, {
      onSuccess: (data) => setLastServices(data.used_services),
      onError: (error) =>
        toast.error(
          error instanceof ApiError ? error.message : "Sakhi couldn't respond — try again",
        ),
    });
  }

  const hasStarted = historyMessages.length > 0;

  return (
    <Page>
      <section className="relative overflow-hidden py-14 lg:py-16">
        <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />
        <Reveal>
          <Hero
            eyebrow="Ask Sakhi"
            title="&ldquo;What should I"
            accent="do this week?&rdquo;"
            copy="A running conversation grounded in your business profile, brand, sales and memory — not generic advice."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-6 py-10 lg:grid-cols-[1.15fr_0.85fr]">
        <Reveal>
          <div className="card-soft flex h-[34rem] flex-col overflow-hidden rounded-3xl">
            <div className="flex items-center gap-2 border-b border-clay/15 bg-sand/60 px-4 py-3">
              <Sparkles className="h-4 w-4 text-wine" />
              <p className="text-[12.5px] font-semibold text-foreground">Ask Sakhi's AI Advisor</p>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
              {historyLoading ? (
                <div className="flex h-full items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : !hasStarted ? (
                <div className="flex h-full flex-col items-center justify-center gap-3 px-4 text-center">
                  <p className="text-[13px] text-muted-foreground">
                    Ask about your revenue, brand, content ideas, or what to do next.
                  </p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {SUGGESTIONS.map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => send(s)}
                        className="rounded-full border border-clay/25 bg-card px-3 py-1.5 text-[11.5px] text-foreground/75 transition-colors hover:border-wine/30 hover:text-wine"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                historyMessages.map((message, i) => (
                  <ChatBubble key={`${message.created_at}-${i}`} message={message} />
                ))
              )}
              {sendMessage.isPending && (
                <>
                  <ChatBubble
                    message={{
                      role: "user",
                      content: (sendMessage.variables as string) ?? "",
                      created_at: "",
                    }}
                  />
                  <ChatThinkingBubble />
                </>
              )}
              <div ref={chatEndRef} />
            </div>
            <ChatComposer
              value={input}
              onChange={setInput}
              onSubmit={() => send(input)}
              disabled={sendMessage.isPending}
              placeholder="Ask Sakhi anything about your business…"
            />
          </div>
        </Reveal>

        <Reveal delay={100}>
          <Craft tone="lilac" texture="weave" className="h-full">
            <Eyebrow>Grounded in</Eyebrow>
            <h3 className="mt-2 font-display text-xl font-semibold">Not generic advice</h3>
            <ul className="mt-4 space-y-2.5 text-[12.5px] text-foreground/75">
              <li className="flex items-start gap-2">
                <BadgeCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-wine" />
                Your business profile and brand kit
              </li>
              <li className="flex items-start gap-2">
                <BadgeCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-wine" />
                Your real logged revenue and stock levels
              </li>
              <li className="flex items-start gap-2">
                <BadgeCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-wine" />
                Past memories from your voice notes
              </li>
            </ul>
            {lastServices.length > 0 && (
              <>
                <Eyebrow>Last answer used</Eyebrow>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {lastServices.map((s) => (
                    <Pill key={s} tone="indigo">
                      {SERVICE_LABELS[s] ?? s}
                    </Pill>
                  ))}
                </div>
              </>
            )}
          </Craft>
        </Reveal>
      </section>
    </Page>
  );
}
