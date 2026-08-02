import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import {
  useGenerateLogo,
  usePrimaryBrandAsset,
  useUpdateBrandAsset,
} from "@/hooks/use-brand-assets";
import { Reveal } from "@/components/sakhi/Reveal";
import { Action, Basis, Craft, Eyebrow, Hero, HandNote, Pill, Why } from "@/components/sakhi/Cards";
import { BotanicalMark, DeckleCard, StitchDivider } from "@/components/sakhi/CompanionAssets";
import { InstagramPreviewMini } from "@/components/sakhi/ScrapbookAssets";
import {
  BusinessCardMockup,
  GuidelineRow,
  LabelMockup,
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
  component: BrandStudioRoute,
});

function BrandStudioRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <BrandStudio />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

/** Renders a hex colour as a circular swatch — the palette AI generates is
 * arbitrary hex, not one of the fixed design-system tones ColorSwatch (from
 * BusinessSetupAssets) is built around, so this is a small standalone. */
function HexSwatch({ hex, label }: { hex: string; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <span
        className="h-11 w-11 shrink-0 rounded-full ring-1 ring-clay/20"
        style={{ backgroundColor: hex }}
        aria-label={label}
      />
      <span className="text-[10px] tracking-[0.04em] text-muted-foreground uppercase">{hex}</span>
    </div>
  );
}

function BrandStudio() {
  const { brandAsset, isLoading } = usePrimaryBrandAsset();
  const updateBrandAsset = useUpdateBrandAsset(brandAsset?.id);
  const generateLogo = useGenerateLogo(brandAsset?.id);

  const [tagline, setTagline] = useState("");
  const [story, setStory] = useState("");

  useEffect(() => {
    if (brandAsset) {
      setTagline(brandAsset.tagline ?? "");
      setStory(brandAsset.brand_story ?? "");
    }
  }, [brandAsset]);

  if (isLoading) {
    return (
      <Page>
        <div className="flex min-h-[50vh] items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </Page>
    );
  }

  if (!brandAsset) {
    return (
      <Page>
        <div className="flex min-h-[50vh] flex-col items-center justify-center gap-2 text-center">
          <p className="font-display text-xl font-semibold text-foreground">No brand kit yet</p>
          <p className="max-w-sm text-sm text-muted-foreground">
            Sakhi builds your brand kit automatically during business setup — finish that first.
          </p>
        </div>
      </Page>
    );
  }

  const voiceWords = (brandAsset.brand_voice ?? "")
    .split(",")
    .map((w) => w.trim())
    .filter(Boolean);
  const packagingIdeas = (brandAsset.packaging_notes ?? "")
    .split(";")
    .map((w) => w.trim())
    .filter(Boolean);
  const [headingFont, bodyFont] = (brandAsset.typography ?? "").split("/").map((f) => f.trim());

  function handleGenerateLogo() {
    generateLogo.mutate(undefined, {
      onSuccess: () => toast.success("New logo recommendation ready"),
      onError: () => toast.error("Couldn't generate a logo — try again"),
    });
  }

  function handleSaveIdentity() {
    updateBrandAsset.mutate(
      { tagline: tagline || null, brand_story: story || null },
      {
        onSuccess: () => toast.success("Brand identity saved"),
        onError: () => toast.error("Couldn't save — try again"),
      },
    );
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
            copy="Everything Sakhi built for your identity during setup — colour, voice, typography and guidelines — kept in one workspace."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="py-10">
        <Reveal>
          <Craft tone="lilac" texture="weave">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-wine" />
              <Eyebrow>Recommended logo</Eyebrow>
            </div>
            <div className="mt-5 flex flex-col items-center gap-5 sm:flex-row sm:items-start">
              <div className="grid h-32 w-32 shrink-0 place-items-center overflow-hidden rounded-2xl bg-card ring-1 ring-clay/20">
                {generateLogo.isPending ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : brandAsset.logo_url ? (
                  <img
                    src={brandAsset.logo_url}
                    alt={`${brandAsset.brand_name} logo`}
                    className="h-full w-full object-contain"
                  />
                ) : (
                  <span className="px-3 text-center text-[11px] text-muted-foreground">
                    No logo generated yet
                  </span>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[13px] text-foreground/75">
                  Sakhi can recommend a logo mark from your business name, tagline, brand voice and
                  colour palette — a starting concept, not a final trademark-ready file.
                </p>
                <button
                  type="button"
                  onClick={handleGenerateLogo}
                  disabled={generateLogo.isPending}
                  className="mt-4 inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:pointer-events-none disabled:opacity-70"
                >
                  {generateLogo.isPending ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" /> Generating…
                    </>
                  ) : brandAsset.logo_url ? (
                    "Regenerate logo"
                  ) : (
                    "Generate a logo"
                  )}
                </button>
                <Basis>
                  Built from your brand name, tagline, voice and primary colour — regenerate for a
                  different concept.
                </Basis>
              </div>
            </div>
          </Craft>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-8 py-10 lg:grid-cols-2">
        <Reveal>
          <Eyebrow>Colour palette</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            Generated from your brand
          </h2>
          <div className="card-soft mt-6 rounded-2xl px-5 py-5">
            <div className="flex flex-wrap gap-5">
              {brandAsset.primary_color && (
                <HexSwatch hex={brandAsset.primary_color} label="Primary colour" />
              )}
              {brandAsset.secondary_color && (
                <HexSwatch hex={brandAsset.secondary_color} label="Secondary colour" />
              )}
              {!brandAsset.primary_color && !brandAsset.secondary_color && (
                <p className="text-[12.5px] text-muted-foreground">No palette generated yet.</p>
              )}
            </div>
          </div>
        </Reveal>

        <Reveal delay={90}>
          <Eyebrow>Typography</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            How your text reads
          </h2>
          {headingFont || bodyFont ? (
            <div className="card-soft mt-6 flex flex-col gap-1 rounded-2xl px-5 py-5">
              <span
                className="text-3xl font-semibold text-foreground"
                style={{ fontFamily: headingFont }}
              >
                Aa
              </span>
              <span className="text-[12px] text-foreground/70" style={{ fontFamily: bodyFont }}>
                The quick brown fox
              </span>
              <span className="mt-1.5 text-[10.5px] font-medium tracking-[0.08em] text-muted-foreground uppercase">
                {brandAsset.typography}
              </span>
            </div>
          ) : (
            <p className="mt-6 text-[12.5px] text-muted-foreground">
              No typography pairing generated yet.
            </p>
          )}
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-8 py-10 lg:grid-cols-2">
        <Reveal>
          <Eyebrow>Brand voice</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            How you sound
          </h2>
          <div className="mt-5 flex flex-wrap gap-2">
            {voiceWords.length > 0 ? (
              voiceWords.map((w) => <Pill key={w}>{w}</Pill>)
            ) : (
              <p className="text-[12.5px] text-muted-foreground">No brand voice generated yet.</p>
            )}
          </div>

          <label className="mt-6 block">
            <span className="mb-1.5 block text-[12.5px] font-medium text-foreground/80">
              Tagline
            </span>
            <input
              value={tagline}
              onChange={(e) => setTagline(e.target.value)}
              className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2.5 text-[14px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
            />
          </label>
        </Reveal>

        <Reveal delay={90}>
          <Eyebrow>Brand story</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            Where it began
          </h2>
          <textarea
            value={story}
            onChange={(e) => setStory(e.target.value)}
            rows={5}
            className="hand mt-5 w-full resize-none rounded-2xl border border-clay/25 bg-ivory px-4 py-3.5 text-[1rem] leading-relaxed text-wine-soft shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
          <button
            type="button"
            onClick={handleSaveIdentity}
            disabled={updateBrandAsset.isPending}
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:pointer-events-none disabled:opacity-70"
          >
            {updateBrandAsset.isPending ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Saving…
              </>
            ) : (
              "Save changes"
            )}
          </button>
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="py-10">
        <Reveal>
          <Eyebrow>Business card &amp; label previews</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            On paper, in hand
          </h2>
        </Reveal>
        <div className="mt-7 flex flex-wrap items-start gap-10">
          <Reveal delay={70}>
            <BusinessCardMockup name={brandAsset.brand_name} tagline={tagline} tone="rose" />
          </Reveal>
          <Reveal delay={140}>
            <LabelMockup name={brandAsset.brand_name} tone="rose" rotate={-3} />
          </Reveal>
          <Reveal delay={210}>
            <InstagramPreviewMini
              handle={brandAsset.brand_name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}
              tones={["rose", "sand", "rose"]}
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
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            Keep it consistent
          </h2>
          <DeckleCard
            paperClassName="bg-card border border-clay/25"
            className="mt-6 px-6 py-6"
            style={{ boxShadow: "var(--shadow-soft)" }}
          >
            <ul className="space-y-2.5">
              <GuidelineRow ok>Use your primary colour on light backgrounds only</GuidelineRow>
              <GuidelineRow ok>Keep at least 12px of clear space around any logo</GuidelineRow>
              <GuidelineRow ok={false}>Don't stretch or recolour your mark</GuidelineRow>
              <GuidelineRow ok={false}>
                Don't pair the tagline with more than one accent colour
              </GuidelineRow>
            </ul>
            <StitchDivider className="my-4" />
            <HandNote>When in doubt, choose warmth over polish.</HandNote>
          </DeckleCard>
        </Reveal>

        <Reveal delay={100}>
          <Eyebrow>From your brand kit</Eyebrow>
          <h2 className="font-display mt-1.5 text-2xl font-semibold text-foreground">
            Mission &amp; packaging
          </h2>
          <div className="mt-6 space-y-5">
            {brandAsset.mission && (
              <Craft tone="marigold" texture="blockprint">
                <Eyebrow>Mission</Eyebrow>
                <p className="mt-2 text-[13.5px] leading-relaxed text-foreground/80">
                  {brandAsset.mission}
                </p>
                <Basis>Generated from your business story during setup.</Basis>
              </Craft>
            )}
            {packagingIdeas.length > 0 && (
              <Craft tone="indigo" texture="weave">
                <Eyebrow>Packaging ideas</Eyebrow>
                <ul className="mt-2 space-y-1.5 text-[13px] text-foreground/80">
                  {packagingIdeas.map((idea) => (
                    <li key={idea}>• {idea}</li>
                  ))}
                </ul>
                <Why>
                  Packaging that matches your brand voice photographs better for social proof.
                </Why>
                <Action>Refresh packaging</Action>
              </Craft>
            )}
          </div>
        </Reveal>
      </section>
    </Page>
  );
}
