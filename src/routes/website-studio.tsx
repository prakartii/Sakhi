import { useEffect, useRef, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { Copy, Link as LinkIcon, Loader2, Mail, Sparkles } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { usePrimaryWebsite, usePublishWebsite } from "@/hooks/use-websites";
import { useSendWebsiteMessage, useWebsiteChatHistory } from "@/hooks/use-website-chat";
import { Reveal } from "@/components/sakhi/Reveal";
import { Craft, Eyebrow, Hero } from "@/components/sakhi/Cards";
import { BotanicalMark } from "@/components/sakhi/CompanionAssets";
import { BrowserFrame, PublishStepper } from "@/components/sakhi/WebsiteStudioAssets";
import { ChatBubble, ChatComposer, ChatThinkingBubble } from "@/components/sakhi/WebsiteChatAssets";
import type {
  WebsiteChatResponse,
  WebsiteGenerateFAQ,
  WebsiteGenerateHero,
  WebsiteGenerateProduct,
  WebsiteGenerateSection,
  WebsiteImages,
} from "@/lib/types";
import { ApiError } from "@/lib/api-client";

export const Route = createFileRoute("/website-studio")({
  head: () => ({
    meta: [
      { title: "Website Studio — Sakhi" },
      {
        name: "description",
        content:
          "Chat with Sakhi to build a real website for your business — landing page, products, about and contact — then publish it with a live link.",
      },
    ],
  }),
  component: WebsiteStudioRoute,
});

function WebsiteStudioRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <WebsiteStudio />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

interface DisplaySite {
  hero: WebsiteGenerateHero;
  sections: WebsiteGenerateSection[];
  about: string;
  products: WebsiteGenerateProduct[];
  contact: string;
  faq: WebsiteGenerateFAQ[];
  seo_keywords: string[];
  images: WebsiteImages;
}

function WebsiteStudio() {
  const { website, isLoading: websiteLoading } = usePrimaryWebsite();
  const { messages: historyMessages, isLoading: historyLoading } = useWebsiteChatHistory();
  const sendMessage = useSendWebsiteMessage();
  const publish = usePublishWebsite(website?.id);

  const [input, setInput] = useState("");
  const [latestReply, setLatestReply] = useState<WebsiteChatResponse | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [historyMessages.length, sendMessage.isPending]);

  // website.published/preview_slug/website_name come from the live query
  // (kept fresh by publish's own invalidation); latestReply.website is
  // only a fallback for the brief gap right after the first chat turn,
  // before that query has refetched — it must never override fresher data.
  const effectiveWebsite = website ?? latestReply?.website;

  const displaySite: DisplaySite | null = latestReply
    ? {
        hero: latestReply.hero,
        sections: latestReply.sections,
        about: latestReply.about,
        products: latestReply.products,
        contact: latestReply.contact,
        faq: latestReply.faq,
        seo_keywords: latestReply.seo_keywords,
        images: latestReply.images,
      }
    : website?.content
      ? {
          hero: website.content.pages.landing.hero,
          sections: website.content.pages.landing.sections,
          about: website.content.pages.about.body,
          products: website.content.pages.products,
          contact: website.content.pages.contact.body,
          faq: website.content.pages.faq,
          seo_keywords: website.content.seo.keywords,
          images: website.images ?? {},
        }
      : null;

  function handleSend() {
    const message = input.trim();
    if (!message) return;
    setInput("");
    sendMessage.mutate(message, {
      onSuccess: (data) => setLatestReply(data),
      onError: (error) =>
        toast.error(
          error instanceof ApiError ? error.message : "Sakhi couldn't respond — try again",
        ),
    });
  }

  function handlePublish() {
    publish.mutate(undefined, {
      onSuccess: () => toast.success(`${effectiveWebsite?.website_name ?? "Your site"} is live!`),
      onError: () => toast.error("Couldn't publish — try again"),
    });
  }

  const previewPath =
    latestReply?.preview_path ??
    (effectiveWebsite?.published && effectiveWebsite.preview_slug
      ? `/site/${effectiveWebsite.preview_slug}`
      : null);
  const previewUrl =
    previewPath && typeof window !== "undefined" ? `${window.location.origin}${previewPath}` : null;

  const loading = websiteLoading || historyLoading;
  const hasStarted = historyMessages.length > 0 || !!latestReply;

  return (
    <Page>
      <section className="relative overflow-hidden py-14 lg:py-16">
        <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />
        <Reveal>
          <Hero
            eyebrow="Website studio"
            title="A website,"
            accent="built by talking to her."
            copy="Tell Sakhi about your business, ask for changes as you go, and publish a live link — no forms, no build."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-6 py-10 lg:grid-cols-[0.85fr_1.15fr]">
        <Reveal>
          <div className="card-soft flex h-[34rem] flex-col overflow-hidden rounded-3xl">
            <div className="flex items-center gap-2 border-b border-clay/15 bg-sand/60 px-4 py-3">
              <Sparkles className="h-4 w-4 text-wine" />
              <p className="text-[12.5px] font-semibold text-foreground">Chat with Sakhi</p>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
              {loading ? (
                <div className="flex h-full items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : !hasStarted ? (
                <div className="flex h-full flex-col items-center justify-center gap-2 px-4 text-center">
                  <p className="text-[13px] text-muted-foreground">
                    Tell Sakhi what you want on your website — she'll build it as you talk.
                  </p>
                  <p className="hand text-[13px]">
                    &ldquo;Build me a site for my crochet bags&rdquo;
                  </p>
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
              onSubmit={handleSend}
              disabled={sendMessage.isPending}
              placeholder={hasStarted ? "Ask for a change…" : "Describe your business…"}
            />
          </div>
        </Reveal>

        <Reveal delay={90}>
          <div className="space-y-5">
            {!displaySite ? (
              <div className="card-soft flex min-h-[20rem] flex-col items-center justify-center gap-3 rounded-3xl px-6 text-center">
                <p className="text-sm text-muted-foreground">
                  Your live preview will appear here once you start chatting.
                </p>
              </div>
            ) : (
              <>
                <BrowserFrame
                  url={
                    previewUrl?.replace(/^https?:\/\//, "") ??
                    `${effectiveWebsite?.website_name ?? "your-site"}.sakhi.site`
                  }
                >
                  <div
                    className="relative flex min-h-[16rem] flex-col items-start justify-center gap-3 px-8 py-10"
                    style={
                      displaySite.images.hero_url
                        ? {
                            backgroundImage: `linear-gradient(0deg, color-mix(in oklab, var(--sand) 60%, transparent), color-mix(in oklab, var(--sand) 78%, transparent)), url(${displaySite.images.hero_url})`,
                            backgroundSize: "cover",
                            backgroundPosition: "center",
                          }
                        : {
                            background:
                              "radial-gradient(80% 100% at 10% 10%, color-mix(in oklab, var(--rose) 65%, transparent), transparent 70%), var(--sand)",
                          }
                    }
                  >
                    <span className="rounded-full bg-card px-3 py-1 text-[9.5px] font-semibold tracking-[0.16em] text-muted-foreground uppercase">
                      {effectiveWebsite?.website_name}
                    </span>
                    <p className="font-display max-w-sm text-2xl leading-tight font-semibold text-foreground">
                      {displaySite.hero.headline}
                    </p>
                    <p className="max-w-sm text-[12px] text-foreground/70">
                      {displaySite.hero.subhead}
                    </p>
                    <button className="mt-1 rounded-full bg-primary px-4 py-2 text-[11.5px] font-semibold text-primary-foreground">
                      {displaySite.hero.cta}
                    </button>
                  </div>
                  <div className="grid grid-cols-3 gap-3 border-t border-clay/15 p-4">
                    {displaySite.products.slice(0, 3).map((p) => (
                      <div key={p.name} className="rounded-lg bg-sand/70 px-2.5 py-3 text-center">
                        <p className="truncate text-[10.5px] font-medium text-foreground/80">
                          {p.name}
                        </p>
                        {p.price && <p className="text-[10px] text-muted-foreground">{p.price}</p>}
                      </div>
                    ))}
                  </div>
                </BrowserFrame>

                <div className="card-soft rounded-2xl px-6 py-6">
                  <Eyebrow>Publish</Eyebrow>
                  <PublishStepper current={effectiveWebsite?.published ? 2 : 1} className="mt-3" />
                  {previewUrl ? (
                    <div className="mt-4 flex items-center gap-2 rounded-xl bg-sand/70 px-3.5 py-2.5">
                      <LinkIcon className="h-3.5 w-3.5 shrink-0 text-wine" />
                      <a
                        href={previewUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="min-w-0 flex-1 truncate text-[12px] font-medium text-wine underline-offset-2 hover:underline"
                      >
                        {previewUrl}
                      </a>
                      <button
                        type="button"
                        onClick={() => {
                          void navigator.clipboard.writeText(previewUrl);
                          toast.success("Link copied");
                        }}
                        className="shrink-0 rounded-full border border-clay/25 p-1.5 text-muted-foreground transition-colors hover:border-wine/30 hover:text-wine"
                        aria-label="Copy link"
                      >
                        <Copy className="h-3 w-3" />
                      </button>
                    </div>
                  ) : (
                    <p className="mt-4 text-[12.5px] text-muted-foreground">
                      Publish to get a shareable link for your site.
                    </p>
                  )}
                  <button
                    type="button"
                    onClick={handlePublish}
                    disabled={publish.isPending || !!effectiveWebsite?.published}
                    className="mt-4 w-full rounded-xl bg-primary px-5 py-2.5 text-[13.5px] font-semibold text-primary-foreground shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5 disabled:pointer-events-none disabled:opacity-70"
                  >
                    {effectiveWebsite?.published
                      ? "Published"
                      : publish.isPending
                        ? "Publishing…"
                        : "Publish website"}
                  </button>
                </div>
              </>
            )}
          </div>
        </Reveal>
      </section>

      {displaySite && (
        <>
          <div className="thread opacity-50" />

          <section className="grid gap-8 py-10 lg:grid-cols-2">
            <Reveal>
              <Eyebrow>About section</Eyebrow>
              <h2 className="font-display mt-1.5 text-xl font-semibold text-foreground">
                Your story, told
              </h2>
              <div className="card-soft mt-4 rounded-2xl px-5 py-5">
                <p className="text-[12.5px] leading-relaxed text-foreground/75">
                  {displaySite.about}
                </p>
              </div>
            </Reveal>

            <Reveal delay={70}>
              <Eyebrow>Contact section</Eyebrow>
              <h2 className="font-display mt-1.5 text-xl font-semibold text-foreground">
                Easy to reach
              </h2>
              <div className="card-soft mt-4 space-y-2.5 rounded-2xl px-5 py-5">
                <p className="flex items-center gap-2 text-[12.5px] text-foreground/75">
                  <Mail className="h-3.5 w-3.5 shrink-0 text-wine" /> {displaySite.contact}
                </p>
              </div>
            </Reveal>
          </section>

          <div className="thread opacity-50" />

          <section className="py-10">
            <Reveal>
              <Eyebrow>Frequently asked</Eyebrow>
              <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
                From your FAQ
              </h2>
            </Reveal>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {displaySite.faq.slice(0, 4).map((f, i) => (
                <Reveal key={f.q} delay={i * 60}>
                  <Craft tone="indigo" texture="weave">
                    <h3 className="font-display text-base font-semibold">{f.q}</h3>
                    <p className="mt-2 text-[12.5px] text-foreground/75">{f.a}</p>
                  </Craft>
                </Reveal>
              ))}
            </div>
          </section>
        </>
      )}
    </Page>
  );
}
