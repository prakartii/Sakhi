import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { Mail, MapPin, Phone } from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, Hero, Pill, Why } from "@/components/sakhi/Cards";
import { BotanicalMark } from "@/components/sakhi/CompanionAssets";
import { ColorSwatch, PromptChip, type JournalTone as SetupTone } from "@/components/sakhi/BusinessSetupAssets";
import { BrandStamp } from "@/components/sakhi/ScrapbookAssets";
import { BrowserFrame, PhoneFrame, PublishStepper } from "@/components/sakhi/WebsiteStudioAssets";

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
  component: WebsiteStudio,
});

const PRODUCTS = [
  { name: "Crochet handbag", price: "₹899" },
  { name: "Block-print dupatta", price: "₹640" },
  { name: "Beaded earrings", price: "₹350" },
];

const SEO_SUGGESTIONS = [
  {
    title: "Add \"handloom sarees Jaipur\" to your title",
    why: "This exact phrase is searched 2,400 times a month, and none of your local competitors rank for it yet.",
    impact: { text: "+Search visibility", tone: "indigo" as const },
    action: "Update page title",
  },
  {
    title: "Add alt text to your product photos",
    why: "Google Images sends 30% of your competitors' traffic — your photos currently have none of the tags needed to appear there.",
    impact: { text: "+Image search traffic", tone: "leaf" as const },
    action: "Generate alt text",
  },
];

const LAYOUTS = ["Editorial", "Minimal", "Gallery", "Storefront"];

function WebsiteStudio() {
  const [tone, setTone] = useState<SetupTone>("rose");
  const [layout, setLayout] = useState("Editorial");
  const [stage, setStage] = useState(1);

  function handlePublish() {
    setStage(2);
    toast.success("threadsofjaipur.sakhi.site is live!");
  }

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

      <section className="py-10">
        <Reveal>
          <Eyebrow>Live preview</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            Desktop &amp; mobile, side by side
          </h2>
        </Reveal>
        <div className="mt-7 grid gap-8 lg:grid-cols-[1fr_auto]">
          <Reveal delay={70}>
            <BrowserFrame url="threadsofjaipur.sakhi.site">
              <div
                className="relative flex min-h-[16rem] flex-col items-start justify-center gap-3 px-8 py-10"
                style={{
                  background:
                    "radial-gradient(80% 100% at 10% 10%, color-mix(in oklab, var(--rose) 65%, transparent), transparent 70%), var(--sand)",
                }}
              >
                <span className="rounded-full bg-card px-3 py-1 text-[9.5px] font-semibold tracking-[0.16em] text-muted-foreground uppercase">
                  Threads of Jaipur
                </span>
                <p className="font-display max-w-sm text-2xl leading-tight font-semibold text-foreground">
                  Handwoven, one thread of love at a time.
                </p>
                <button className="mt-1 rounded-full bg-primary px-4 py-2 text-[11.5px] font-semibold text-primary-foreground">
                  Shop the collection
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3 border-t border-clay/15 p-4">
                {PRODUCTS.map((p) => (
                  <div key={p.name} className="rounded-lg bg-sand/70 px-2.5 py-3 text-center">
                    <p className="truncate text-[10.5px] font-medium text-foreground/80">{p.name}</p>
                    <p className="text-[10px] text-muted-foreground">{p.price}</p>
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
                  Threads of Jaipur
                </span>
                <p className="font-display max-w-[8rem] text-[13px] leading-tight font-semibold text-foreground">
                  Handwoven, one thread of love at a time.
                </p>
                <button className="rounded-full bg-primary px-3 py-1.5 text-[8.5px] font-semibold text-primary-foreground">
                  Shop the collection
                </button>
              </div>
              <div className="grid grid-cols-2 gap-1.5 border-t border-clay/15 p-2">
                {PRODUCTS.slice(0, 2).map((p) => (
                  <div key={p.name} className="rounded-md bg-sand/70 px-1.5 py-2 text-center">
                    <p className="truncate text-[8px] font-medium text-foreground/80">{p.name}</p>
                  </div>
                ))}
              </div>
            </PhoneFrame>
          </Reveal>
        </div>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-8 py-10 lg:grid-cols-3">
        <Reveal>
          <Eyebrow>About section</Eyebrow>
          <h2 className="font-display mt-1.5 text-xl font-semibold text-foreground">Your story, told</h2>
          <div className="card-soft mt-4 rounded-2xl px-5 py-5">
            <p className="text-[12.5px] leading-relaxed text-foreground/75">
              Threads of Jaipur began on my grandmother's loom — every dupatta still carries her
              patience, and every buyer becomes part of that thread.
            </p>
          </div>
        </Reveal>

        <Reveal delay={70}>
          <Eyebrow>Contact section</Eyebrow>
          <h2 className="font-display mt-1.5 text-xl font-semibold text-foreground">Easy to reach</h2>
          <div className="card-soft mt-4 space-y-2.5 rounded-2xl px-5 py-5">
            <p className="flex items-center gap-2 text-[12.5px] text-foreground/75">
              <MapPin className="h-3.5 w-3.5 shrink-0 text-wine" /> Bagru, Jaipur
            </p>
            <p className="flex items-center gap-2 text-[12.5px] text-foreground/75">
              <Phone className="h-3.5 w-3.5 shrink-0 text-wine" /> +91 98xxx xxxxx
            </p>
            <p className="flex items-center gap-2 text-[12.5px] text-foreground/75">
              <Mail className="h-3.5 w-3.5 shrink-0 text-wine" /> hello@threadsofjaipur.com
            </p>
          </div>
        </Reveal>

        <Reveal delay={140}>
          <Eyebrow>Customize</Eyebrow>
          <h2 className="font-display mt-1.5 text-xl font-semibold text-foreground">Make it yours</h2>
          <div className="card-soft mt-4 space-y-4 rounded-2xl px-5 py-5">
            <div>
              <p className="mb-2 text-[11px] font-medium text-foreground/70">Theme colour</p>
              <div className="flex flex-wrap gap-2">
                {(["rose", "leaf", "marigold", "indigo", "lilac", "sand"] as SetupTone[]).map((t) => (
                  <ColorSwatch key={t} tone={t} selected={tone === t} onClick={() => setTone(t)} />
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-[11px] font-medium text-foreground/70">Layout style</p>
              <div className="flex flex-wrap gap-2">
                {LAYOUTS.map((l) => (
                  <PromptChip key={l} selected={layout === l} onClick={() => setLayout(l)}>
                    {l}
                  </PromptChip>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-8 py-10 lg:grid-cols-[0.9fr_1.1fr]">
        <Reveal>
          <Eyebrow>Publish</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">Ready to go live</h2>
          <div className="card-soft mt-6 rounded-2xl px-6 py-6">
            <PublishStepper current={stage} />
            <p className="mt-5 text-[12.5px] text-muted-foreground">
              Your site will publish to{" "}
              <span className="font-medium text-foreground">threadsofjaipur.sakhi.site</span>
            </p>
            <button
              type="button"
              onClick={handlePublish}
              className="mt-4 rounded-xl bg-primary px-5 py-2.5 text-[13.5px] font-semibold text-primary-foreground shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5"
            >
              Publish website
            </button>
          </div>
        </Reveal>

        <Reveal delay={100}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <Eyebrow>AI recommendations</Eyebrow>
              <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
                For better conversions
              </h2>
            </div>
            <BrandStamp className="hidden sm:grid" />
          </div>
          <div className="mt-6 space-y-5">
            {SEO_SUGGESTIONS.map((s, i) => (
              <Craft key={s.title} tone={i === 0 ? "indigo" : "leaf"} texture={i === 0 ? "weave" : "blockprint"}>
                <Eyebrow>SEO suggestion</Eyebrow>
                <h3 className="font-display mt-2 text-lg font-semibold">{s.title}</h3>
                <div className="mt-2.5">
                  <Pill tone={s.impact.tone}>{s.impact.text}</Pill>
                </div>
                <Why>{s.why}</Why>
                <Basis />
                <Action>{s.action}</Action>
              </Craft>
            ))}
          </div>
        </Reveal>
      </section>
    </Page>
  );
}
