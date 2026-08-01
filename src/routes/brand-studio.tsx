import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/sakhi/Layout";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, Hero, HandNote, Pill, Why } from "@/components/sakhi/Cards";
import { BotanicalMark, DeckleCard, StitchDivider } from "@/components/sakhi/CompanionAssets";
import { ColorSwatch, PromptChip, type JournalTone as SetupTone } from "@/components/sakhi/BusinessSetupAssets";
import { BrandStamp, InstagramPreviewMini, LogoOption } from "@/components/sakhi/ScrapbookAssets";
import {
  BusinessCardMockup,
  FontSampleCard,
  GuidelineRow,
  LabelMockup,
  PinnedPhoto,
} from "@/components/sakhi/BrandStudioAssets";

export const Route = createFileRoute("/brand-studio")({
  head: () => ({
    meta: [
      { title: "Brand Studio — Sakhi" },
      {
        name: "description",
        content:
          "A complete AI branding workspace — logo concepts, palette, voice, packaging and guidelines, all in one place.",
      },
    ],
  }),
  component: BrandStudio,
});

const LOGO_OPTIONS: { label: string; tone: SetupTone }[] = [
  { label: "Option 1 · Mark", tone: "rose" },
  { label: "Option 2 · Badge", tone: "marigold" },
  { label: "Option 3 · Wreath", tone: "leaf" },
];

const PALETTE: SetupTone[] = ["rose", "leaf", "marigold", "indigo", "lilac", "sand"];
const PALETTE_MOOD: Record<SetupTone, string> = {
  rose: "Heritage · Warmth · Elegance",
  leaf: "Fresh · Grounded · Honest",
  marigold: "Festive · Joyful · Abundant",
  indigo: "Calm · Trustworthy · Timeless",
  lilac: "Gentle · Creative · Feminine",
  sand: "Natural · Earthy · Quiet",
};

const PERSONALITIES = ["Warm", "Authentic", "Handcrafted", "Feminine", "Timeless", "Festive"];

const FONT_PAIRS = [
  { label: "Fraunces + Karla", displayFont: "'Fraunces', Georgia, serif", bodyFont: "'Karla', sans-serif" },
  { label: "Georgia + Verdana", displayFont: "Georgia, serif", bodyFont: "Verdana, sans-serif" },
  { label: "Playfair + Inter", displayFont: "'Playfair Display', Georgia, serif", bodyFont: "Inter, sans-serif" },
];

const RECOMMENDATIONS = [
  {
    title: "Add gold foil accents to packaging",
    why: "Buyers photographing your festival orders keep the box in frame — a metallic accent reads as premium in that shot.",
    impact: { text: "Higher perceived value", tone: "marigold" as const },
    action: "Refresh packaging",
  },
  {
    title: "Simplify the tagline to 5 words",
    why: "Your current tagline runs long on mobile Instagram bios, where 68% of your profile visits happen.",
    impact: { text: "Cleaner bio & cards", tone: "indigo" as const },
    action: "Rewrite tagline",
  },
];

function BrandStudio() {
  const [logo, setLogo] = useState(0);
  const [palette, setPalette] = useState<SetupTone>("rose");
  const [personality, setPersonality] = useState<string[]>(["Warm", "Authentic", "Handcrafted"]);
  const [font, setFont] = useState(0);
  const [tagline, setTagline] = useState("Handwoven, one thread of love at a time.");
  const [story, setStory] = useState(
    "Threads of Jaipur began on my grandmother's loom — every dupatta still carries her patience, and every buyer becomes part of that thread.",
  );

  function togglePersonality(word: string) {
    setPersonality((p) => (p.includes(word) ? p.filter((w) => w !== word) : [...p, word]));
  }

  return (
    <Page>
      <section className="relative overflow-hidden py-14 lg:py-16">
        <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />
        <Reveal>
          <Hero
            eyebrow="Brand studio"
            title="A brand that"
            accent="looks like you."
            copy="Everything Sakhi has built for your identity — logo, colour, voice and guidelines — kept in one workspace."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="py-10">
        <Reveal>
          <Eyebrow>Logo concepts</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">Pick a mark</h2>
        </Reveal>
        <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_18rem]">
          <div className="grid gap-4 sm:grid-cols-3">
            {LOGO_OPTIONS.map((opt, i) => (
              <Reveal key={opt.label} delay={i * 80}>
                <LogoOption label={opt.label} tone={opt.tone} selected={logo === i} onClick={() => setLogo(i)} />
              </Reveal>
            ))}
          </div>
          <Reveal delay={120}>
            <PinnedPhoto src="/images/packaging-mockup.png" alt="Packaging mockup for Threads of Jaipur" rotate={2} />
          </Reveal>
        </div>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-8 py-10 lg:grid-cols-2">
        <Reveal>
          <Eyebrow>Colour palette</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">Set the mood</h2>
          <div className="card-soft mt-6 rounded-2xl px-5 py-5">
            <div className="flex flex-wrap gap-3">
              {PALETTE.map((tone) => (
                <ColorSwatch key={tone} tone={tone} selected={palette === tone} onClick={() => setPalette(tone)} />
              ))}
            </div>
            <p className="mt-3 text-[11.5px] tracking-[0.04em] text-muted-foreground uppercase">
              {PALETTE_MOOD[palette]}
            </p>
          </div>
        </Reveal>

        <Reveal delay={90}>
          <Eyebrow>Typography</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">Pick a voice for text</h2>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            {FONT_PAIRS.map((f, i) => (
              <FontSampleCard key={f.label} {...f} selected={font === i} onClick={() => setFont(i)} />
            ))}
          </div>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-8 py-10 lg:grid-cols-2">
        <Reveal>
          <Eyebrow>Brand personality &amp; voice</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">How you sound</h2>
          <div className="mt-5 flex flex-wrap gap-2">
            {PERSONALITIES.map((p) => (
              <PromptChip key={p} selected={personality.includes(p)} onClick={() => togglePersonality(p)}>
                {p}
              </PromptChip>
            ))}
          </div>

          <label className="mt-6 block">
            <span className="mb-1.5 block text-[12.5px] font-medium text-foreground/80">Tagline</span>
            <input
              value={tagline}
              onChange={(e) => setTagline(e.target.value)}
              className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2.5 text-[14px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
            />
          </label>
        </Reveal>

        <Reveal delay={90}>
          <Eyebrow>Brand story</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">Where it began</h2>
          <textarea
            value={story}
            onChange={(e) => setStory(e.target.value)}
            rows={5}
            className="hand mt-5 w-full resize-none rounded-2xl border border-clay/25 bg-ivory px-4 py-3.5 text-[1rem] leading-relaxed text-wine-soft shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="py-10">
        <Reveal>
          <Eyebrow>Business card &amp; label previews</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">On paper, in hand</h2>
        </Reveal>
        <div className="mt-7 flex flex-wrap items-start gap-10">
          <Reveal delay={70}>
            <BusinessCardMockup name="Threads of Jaipur" tagline={tagline} tone={palette} />
          </Reveal>
          <Reveal delay={140}>
            <LabelMockup name="Threads of Jaipur" tone={palette} rotate={-3} />
          </Reveal>
          <Reveal delay={210}>
            <InstagramPreviewMini
              handle="threads_of_jaipur"
              tones={[palette, "sand", palette]}
              rotate={2}
              className="mt-2"
            />
          </Reveal>
        </div>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-8 py-10 lg:grid-cols-[0.9fr_1.1fr]">
        <Reveal>
          <Eyebrow>Brand guidelines</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">Keep it consistent</h2>
          <DeckleCard
            paperClassName="bg-card border border-clay/25"
            className="mt-6 px-6 py-6"
            style={{ boxShadow: "var(--shadow-soft)" }}
          >
            <ul className="space-y-2.5">
              <GuidelineRow ok>Use the wine mark on light backgrounds only</GuidelineRow>
              <GuidelineRow ok>Keep at least 12px of clear space around the logo</GuidelineRow>
              <GuidelineRow ok={false}>Don't stretch or recolour the botanical mark</GuidelineRow>
              <GuidelineRow ok={false}>Don't pair the tagline with more than one accent colour</GuidelineRow>
            </ul>
            <StitchDivider className="my-4" />
            <HandNote>When in doubt, choose warmth over polish.</HandNote>
          </DeckleCard>
        </Reveal>

        <Reveal delay={100}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <Eyebrow>AI recommendations</Eyebrow>
              <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">Notes from Sakhi</h2>
            </div>
            <BrandStamp className="hidden sm:grid" />
          </div>
          <div className="mt-6 space-y-5">
            {RECOMMENDATIONS.map((r, i) => (
              <Craft key={r.title} tone={i === 0 ? "marigold" : "indigo"} texture={i === 0 ? "blockprint" : "weave"}>
                <Eyebrow>Suggestion</Eyebrow>
                <h3 className="font-display mt-2 text-lg font-semibold">{r.title}</h3>
                <div className="mt-2.5">
                  <Pill tone={r.impact.tone}>{r.impact.text}</Pill>
                </div>
                <Why>{r.why}</Why>
                <Basis />
                <Action>{r.action}</Action>
              </Craft>
            ))}
          </div>
        </Reveal>
      </section>
    </Page>
  );
}
