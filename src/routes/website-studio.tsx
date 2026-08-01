import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { Loader2, Mail, RefreshCw } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { useGenerateWebsite, usePrimaryWebsite, usePublishWebsite } from "@/hooks/use-websites";
import { Reveal } from "@/components/sakhi/Reveal";
import { Craft, Eyebrow, Hero } from "@/components/sakhi/Cards";
import { BotanicalMark } from "@/components/sakhi/CompanionAssets";
import { BrowserFrame, PhoneFrame, PublishStepper } from "@/components/sakhi/WebsiteStudioAssets";
import type { WebsiteGenerateResponse } from "@/lib/types";
import { ApiError } from "@/lib/api-client";

export const Route = createFileRoute("/website-studio")({
  head: () => ({
    meta: [
      { title: "Website Studio — Sakhi" },
      {
        name: "description",
        content:
          "A real website for your business — landing page, products, about and contact — generated and ready to publish.",
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

function WebsiteStudio() {
  const { website, isLoading: websiteLoading } = usePrimaryWebsite();
  const generate = useGenerateWebsite();
  const publish = usePublishWebsite(website?.id);
  const [content, setContent] = useState<WebsiteGenerateResponse | null>(null);
  const generateStatus = generate.status;

  // The full generated copy isn't persisted server-side (see
  // POST /websites/generate's docstring) — call it once per visit so
  // there's something to preview, same as a fresh generate/regenerate.
  useEffect(() => {
    if (!websiteLoading && !content && generateStatus === "idle") {
      generate.mutate(undefined, {
        onSuccess: (data) => setContent(data),
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't generate your website"),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [websiteLoading, content, generateStatus]);

  function handleRegenerate() {
    generate.mutate(undefined, {
      onSuccess: (data) => {
        setContent(data);
        toast.success("Website regenerated");
      },
      onError: (error) =>
        toast.error(error instanceof ApiError ? error.message : "Couldn't regenerate your website"),
    });
  }

  function handlePublish() {
    publish.mutate(undefined, {
      onSuccess: () => toast.success(`${website?.website_name ?? "Your site"} is live!`),
      onError: () => toast.error("Couldn't publish — try again"),
    });
  }

  const loading = websiteLoading || (generate.isPending && !content);

  return (
    <Page>
      <section className="relative overflow-hidden py-14 lg:py-16">
        <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />
        <Reveal>
          <Hero
            eyebrow="Website studio"
            title="A website,"
            accent="without the build."
            copy="Landing page, products, about and contact — generated from your brand, previewed live, ready to publish."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      {loading ? (
        <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 py-10 text-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Sakhi is writing your website…</p>
        </div>
      ) : !content ? (
        <div className="flex min-h-[30vh] flex-col items-center justify-center gap-3 py-10 text-center">
          <p className="text-sm text-muted-foreground">Couldn't generate a preview.</p>
          <button
            type="button"
            onClick={handleRegenerate}
            className="rounded-xl bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground"
          >
            Try again
          </button>
        </div>
      ) : (
        <>
          <section className="py-10">
            <div className="flex items-center justify-between">
              <Reveal>
                <Eyebrow>Live preview</Eyebrow>
                <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
                  Desktop &amp; mobile, side by side
                </h2>
              </Reveal>
              <button
                type="button"
                onClick={handleRegenerate}
                disabled={generate.isPending}
                className="flex items-center gap-1.5 rounded-full border border-clay/25 px-3.5 py-1.5 text-[12px] font-medium text-foreground/75 transition-colors hover:border-wine/30 hover:text-wine disabled:pointer-events-none disabled:opacity-60"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${generate.isPending ? "animate-spin" : ""}`} />
                Regenerate
              </button>
            </div>
            <div className="mt-7 grid gap-8 lg:grid-cols-[1fr_auto]">
              <Reveal delay={70}>
                <BrowserFrame
                  url={
                    website?.custom_domain ?? `${website?.website_name ?? "your-site"}.sakhi.site`
                  }
                >
                  <div
                    className="relative flex min-h-[16rem] flex-col items-start justify-center gap-3 px-8 py-10"
                    style={{
                      background:
                        "radial-gradient(80% 100% at 10% 10%, color-mix(in oklab, var(--rose) 65%, transparent), transparent 70%), var(--sand)",
                    }}
                  >
                    <span className="rounded-full bg-card px-3 py-1 text-[9.5px] font-semibold tracking-[0.16em] text-muted-foreground uppercase">
                      {website?.website_name}
                    </span>
                    <p className="font-display max-w-sm text-2xl leading-tight font-semibold text-foreground">
                      {content.hero.headline}
                    </p>
                    <p className="max-w-sm text-[12px] text-foreground/70">
                      {content.hero.subhead}
                    </p>
                    <button className="mt-1 rounded-full bg-primary px-4 py-2 text-[11.5px] font-semibold text-primary-foreground">
                      {content.hero.cta}
                    </button>
                  </div>
                  <div className="grid grid-cols-3 gap-3 border-t border-clay/15 p-4">
                    {content.products.slice(0, 3).map((p) => (
                      <div key={p.name} className="rounded-lg bg-sand/70 px-2.5 py-3 text-center">
                        <p className="truncate text-[10.5px] font-medium text-foreground/80">
                          {p.name}
                        </p>
                        {p.price && <p className="text-[10px] text-muted-foreground">{p.price}</p>}
                      </div>
                    ))}
                  </div>
                </BrowserFrame>
              </Reveal>

              <Reveal delay={140}>
                <PhoneFrame>
                  <div
                    className="flex min-h-[15rem] flex-col items-start justify-center gap-2 px-4 py-6"
                    style={{
                      background:
                        "radial-gradient(90% 100% at 20% 10%, color-mix(in oklab, var(--rose) 65%, transparent), transparent 70%), var(--sand)",
                    }}
                  >
                    <span className="rounded-full bg-card px-2 py-0.5 text-[7px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
                      {website?.website_name}
                    </span>
                    <p className="font-display max-w-[8rem] text-[13px] leading-tight font-semibold text-foreground">
                      {content.hero.headline}
                    </p>
                    <button className="rounded-full bg-primary px-3 py-1.5 text-[8.5px] font-semibold text-primary-foreground">
                      {content.hero.cta}
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 border-t border-clay/15 p-2">
                    {content.products.slice(0, 2).map((p) => (
                      <div key={p.name} className="rounded-md bg-sand/70 px-1.5 py-2 text-center">
                        <p className="truncate text-[8px] font-medium text-foreground/80">
                          {p.name}
                        </p>
                      </div>
                    ))}
                  </div>
                </PhoneFrame>
              </Reveal>
            </div>
          </section>

          <div className="thread opacity-50" />

          <section className="grid gap-8 py-10 lg:grid-cols-2">
            <Reveal>
              <Eyebrow>About section</Eyebrow>
              <h2 className="font-display mt-1.5 text-xl font-semibold text-foreground">
                Your story, told
              </h2>
              <div className="card-soft mt-4 rounded-2xl px-5 py-5">
                <p className="text-[12.5px] leading-relaxed text-foreground/75">{content.about}</p>
              </div>
            </Reveal>

            <Reveal delay={70}>
              <Eyebrow>Contact section</Eyebrow>
              <h2 className="font-display mt-1.5 text-xl font-semibold text-foreground">
                Easy to reach
              </h2>
              <div className="card-soft mt-4 space-y-2.5 rounded-2xl px-5 py-5">
                <p className="flex items-center gap-2 text-[12.5px] text-foreground/75">
                  <Mail className="h-3.5 w-3.5 shrink-0 text-wine" /> {content.contact}
                </p>
              </div>
            </Reveal>
          </section>

          <div className="thread opacity-50" />

          <section className="grid gap-8 py-10 lg:grid-cols-[0.9fr_1.1fr]">
            <Reveal>
              <Eyebrow>Publish</Eyebrow>
              <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
                Ready to go live
              </h2>
              <div className="card-soft mt-6 rounded-2xl px-6 py-6">
                <PublishStepper current={website?.published ? 2 : 1} />
                <p className="mt-5 text-[12.5px] text-muted-foreground">
                  Your site will publish to{" "}
                  <span className="font-medium text-foreground">
                    {website?.custom_domain ?? `${website?.website_name ?? "your-site"}.sakhi.site`}
                  </span>
                </p>
                <button
                  type="button"
                  onClick={handlePublish}
                  disabled={publish.isPending || website?.published}
                  className="mt-4 rounded-xl bg-primary px-5 py-2.5 text-[13.5px] font-semibold text-primary-foreground shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5 disabled:pointer-events-none disabled:opacity-70"
                >
                  {website?.published
                    ? "Published"
                    : publish.isPending
                      ? "Publishing…"
                      : "Publish website"}
                </button>
              </div>
            </Reveal>

            <Reveal delay={100}>
              <Eyebrow>Frequently asked</Eyebrow>
              <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
                From your FAQ
              </h2>
              <div className="mt-6 space-y-4">
                {content.faq.slice(0, 3).map((f) => (
                  <Craft key={f.q} tone="indigo" texture="weave">
                    <h3 className="font-display text-base font-semibold">{f.q}</h3>
                    <p className="mt-2 text-[12.5px] text-foreground/75">{f.a}</p>
                  </Craft>
                ))}
              </div>
            </Reveal>
          </section>
        </>
      )}
    </Page>
  );
}
