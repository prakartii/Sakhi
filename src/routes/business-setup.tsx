import { useState, type SyntheticEvent } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { useInvalidateBusinessProfiles } from "@/hooks/use-business-profile";
import { api, ApiError } from "@/lib/api-client";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Gem,
  GraduationCap,
  Globe2,
  LayoutTemplate,
  MapPin,
  Mic,
  Package,
  Palette,
  Rocket,
  Ship,
  Shirt,
  Store,
  TrendingUp,
} from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { Reveal } from "@/components/sakhi/Reveal";
import { Hero } from "@/components/sakhi/Cards";
import { BotanicalMark, DeckleCard } from "@/components/sakhi/CompanionAssets";
import {
  ColorSwatch,
  MarginNote,
  ProductCard,
  PromptChip,
  SelectableCard,
  StepRail,
  type JournalTone,
} from "@/components/sakhi/BusinessSetupAssets";

export const Route = createFileRoute("/business-setup")({
  head: () => ({
    meta: [
      { title: "Business Setup — Sakhi" },
      {
        name: "description",
        content:
          "Tell Sakhi about your business once — products, customers, goals and identity — and she remembers it everywhere.",
      },
    ],
  }),
  component: BusinessSetupRoute,
});

function BusinessSetupRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="present" redirectTo="/dashboard">
        <BusinessSetup />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

const STORY_PROMPTS = [
  "I crochet bags.",
  "I make handloom sarees.",
  "I sell via WhatsApp.",
  "I want more customers.",
];

type Product = {
  icon: typeof Package;
  tone: JournalTone;
  name: string;
  category: string;
  price: string;
  materials: string;
  note: string;
};

const SAMPLE_PRODUCTS: Product[] = [
  {
    icon: Package,
    tone: "rose",
    name: "Crochet handbag",
    category: "Bags",
    price: "₹899",
    materials: "Cotton yarn",
    note: "✎ best-seller since March",
  },
  {
    icon: Shirt,
    tone: "marigold",
    name: "Block-print dupatta",
    category: "Textiles",
    price: "₹640",
    materials: "Cotton, natural dye",
    note: "✎ raised price in June",
  },
  {
    icon: Gem,
    tone: "indigo",
    name: "Beaded earrings",
    category: "Accessories",
    price: "₹350",
    materials: "Glass beads",
    note: "✎ pairs well with dupattas",
  },
];

const CUSTOMERS = [
  { icon: MapPin, tone: "rose" as const, label: "Local buyers", note: "Neighbours and word of mouth" },
  { icon: Package, tone: "marigold" as const, label: "Instagram buyers", note: "DMs and story replies" },
  { icon: Building2, tone: "indigo" as const, label: "Wholesale", note: "Boutiques and shops" },
  { icon: GraduationCap, tone: "leaf" as const, label: "College students", note: "Affordable, trend-led" },
  { icon: Globe2, tone: "lilac" as const, label: "Export", note: "Buyers outside India" },
];

const GOALS = [
  { icon: TrendingUp, tone: "rose" as const, label: "Increase sales", note: "Sell more of what already works" },
  { icon: LayoutTemplate, tone: "marigold" as const, label: "Create a website", note: "A home beyond social media" },
  { icon: Rocket, tone: "indigo" as const, label: "Launch online", note: "Start selling on marketplaces" },
  { icon: Palette, tone: "leaf" as const, label: "Build a brand", note: "Look consistent everywhere" },
  { icon: Ship, tone: "lilac" as const, label: "Export products", note: "Reach buyers abroad" },
  { icon: Store, tone: "sand" as const, label: "Open a studio", note: "A physical space of your own" },
];

const PERSONALITIES = ["Warm", "Earthy", "Playful", "Minimal", "Festive", "Artisan"];
const PALETTE: JournalTone[] = ["rose", "leaf", "marigold", "indigo", "lilac", "sand"];

function BusinessSetup() {
  const navigate = useNavigate();
  const invalidateBusinessProfiles = useInvalidateBusinessProfiles();
  const [step, setStep] = useState(0);
  const [story, setStory] = useState("");
  const [products, setProducts] = useState(SAMPLE_PRODUCTS);
  const [customers, setCustomers] = useState<string[]>(["Local buyers", "Instagram buyers"]);
  const [goals, setGoals] = useState<string[]>(["Increase sales", "Build a brand"]);
  const [businessName, setBusinessName] = useState("Kavita's Loom");
  const [tagline, setTagline] = useState("");
  const [personality, setPersonality] = useState<string[]>(["Warm", "Earthy"]);
  const [palette, setPalette] = useState<JournalTone>("rose");
  const [newProduct, setNewProduct] = useState("");
  const [creating, setCreating] = useState(false);

  function toggle(list: string[], setList: (v: string[]) => void, value: string) {
    setList(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  }

  function handleAddProduct(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!newProduct.trim()) return;
    setProducts((p) => [
      ...p,
      {
        icon: Package,
        tone: "leaf",
        name: newProduct.trim(),
        category: "New",
        price: "—",
        materials: "Add details later",
        note: "✎ just added",
      },
    ]);
    setNewProduct("");
    toast.success("Product pinned to your board");
  }

  async function handleFinish() {
    const parts = [
      story.trim(),
      businessName.trim() && `The business is called ${businessName.trim()}.`,
      tagline.trim() && `Tagline: ${tagline.trim()}.`,
      products.length > 0 &&
        `Products: ${products.map((p) => `${p.name} (${p.category})`).join(", ")}.`,
      customers.length > 0 && `Sells mainly to: ${customers.join(", ")}.`,
      goals.length > 0 && `Goals: ${goals.join(", ")}.`,
      personality.length > 0 && `Brand personality: ${personality.join(", ")}.`,
    ].filter(Boolean);
    const text = parts.join(" ");

    if (!text.trim()) {
      toast.error("Tell Sakhi a little about your business first.");
      setStep(0);
      return;
    }

    setCreating(true);
    try {
      await api.post("/onboarding", { text });
      await invalidateBusinessProfiles();
      toast.success(`${businessName || "Your business"} is set up — welcome to Sakhi!`);
      navigate({ to: "/dashboard" });
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Couldn't set up your business — try again.";
      toast.error(message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <Page>
      <section className="relative overflow-hidden py-14 lg:py-16">
        <BotanicalMark className="pointer-events-none absolute -top-10 -left-14 hidden h-52 w-40 opacity-[0.1] lg:block" />
        <Reveal>
          <Hero
            eyebrow="Business setup"
            title="Let's build your business"
            accent="together."
            copy="This isn't a form — it's a conversation. Tell Sakhi your story, and she'll remember it everywhere else in the app."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <Reveal className="py-8">
        <StepRail current={step} />
      </Reveal>

      <section className="grid gap-6 pb-16 lg:grid-cols-[1fr_18rem]">
        <Reveal key={step} className="min-w-0">
          <DeckleCard
            paperClassName="bg-card border-2 border-dashed border-wine/20"
            className="relative overflow-hidden px-7 py-9 sm:px-10 sm:py-10"
            style={{ boxShadow: "var(--shadow-lift)" }}
          >
            {step === 0 && (
              <>
                <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                  Step 1 · Business story
                </p>
                <h2 className="font-display mt-2 text-2xl font-semibold text-foreground sm:text-3xl">
                  Tell us about your business
                </h2>
                <p className="mt-2 max-w-lg text-[13.5px] text-muted-foreground">
                  Speak it or write it — whatever feels natural. A sentence is enough to start.
                </p>

                <div className="relative mt-6">
                  <textarea
                    value={story}
                    onChange={(e) => setStory(e.target.value)}
                    placeholder="I crochet bags and sell them to friends and family..."
                    rows={4}
                    className="hand w-full resize-none rounded-2xl border border-clay/25 bg-ivory px-4 py-3.5 text-[1.05rem] leading-relaxed text-wine-soft shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
                  />
                  <button
                    type="button"
                    onClick={() => toast.info("Voice capture isn't wired up yet")}
                    aria-label="Speak instead"
                    className="absolute right-3 bottom-3 grid h-9 w-9 place-items-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-105"
                  >
                    <Mic className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {STORY_PROMPTS.map((p) => (
                    <PromptChip key={p} onClick={() => setStory((s) => (s ? `${s} ${p}` : p))}>
                      {p}
                    </PromptChip>
                  ))}
                </div>
              </>
            )}

            {step === 1 && (
              <>
                <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                  Step 2 · Products
                </p>
                <h2 className="font-display mt-2 text-2xl font-semibold text-foreground sm:text-3xl">
                  Pin what you make
                </h2>
                <p className="mt-2 max-w-lg text-[13.5px] text-muted-foreground">
                  A few pieces to start — you can always add more later.
                </p>

                <div className="mt-7 grid gap-x-6 gap-y-9 sm:grid-cols-2 lg:grid-cols-3">
                  {products.map((p, i) => (
                    <ProductCard key={p.name} {...p} rotate={i % 2 === 0 ? -2 : 2} />
                  ))}
                </div>

                <form onSubmit={handleAddProduct} className="mt-8 flex flex-wrap gap-2">
                  <input
                    value={newProduct}
                    onChange={(e) => setNewProduct(e.target.value)}
                    placeholder="Add another product..."
                    className="min-w-0 flex-1 rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13.5px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
                  />
                  <button
                    type="submit"
                    className="rounded-xl bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5"
                  >
                    Pin it
                  </button>
                </form>
              </>
            )}

            {step === 2 && (
              <>
                <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                  Step 3 · Customers
                </p>
                <h2 className="font-display mt-2 text-2xl font-semibold text-foreground sm:text-3xl">
                  Who do you sell to?
                </h2>
                <p className="mt-2 max-w-lg text-[13.5px] text-muted-foreground">
                  Pick as many as fit — Sakhi tailors suggestions to each one.
                </p>

                <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {CUSTOMERS.map((c) => (
                    <SelectableCard
                      key={c.label}
                      {...c}
                      selected={customers.includes(c.label)}
                      onClick={() => toggle(customers, setCustomers, c.label)}
                    />
                  ))}
                </div>
              </>
            )}

            {step === 3 && (
              <>
                <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                  Step 4 · Goals
                </p>
                <h2 className="font-display mt-2 text-2xl font-semibold text-foreground sm:text-3xl">
                  What are you working toward?
                </h2>
                <p className="mt-2 max-w-lg text-[13.5px] text-muted-foreground">
                  Choose what matters most right now — this shapes what Sakhi suggests first.
                </p>

                <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {GOALS.map((g) => (
                    <SelectableCard
                      key={g.label}
                      {...g}
                      selected={goals.includes(g.label)}
                      onClick={() => toggle(goals, setGoals, g.label)}
                    />
                  ))}
                </div>
              </>
            )}

            {step === 4 && (
              <>
                <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                  Step 5 · Business identity
                </p>
                <h2 className="font-display mt-2 text-2xl font-semibold text-foreground sm:text-3xl">
                  How should your business feel?
                </h2>
                <p className="mt-2 max-w-lg text-[13.5px] text-muted-foreground">
                  A few artisan paper samples — Sakhi uses these to shape everything she makes for
                  you.
                </p>

                <div className="mt-7 grid gap-6 sm:grid-cols-2">
                  <label className="block">
                    <span className="mb-1.5 block text-[12.5px] font-medium text-foreground/80">
                      Business name
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="font-display grid h-11 w-11 shrink-0 place-items-center rounded-full bg-rose text-base text-wine ring-1 ring-wine/20">
                        {businessName.trim().charAt(0).toUpperCase() || "S"}
                      </span>
                      <input
                        value={businessName}
                        onChange={(e) => setBusinessName(e.target.value)}
                        className="min-w-0 flex-1 rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[14px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
                      />
                    </div>
                  </label>

                  <label className="block">
                    <span className="mb-1.5 block text-[12.5px] font-medium text-foreground/80">
                      Tagline
                    </span>
                    <input
                      value={tagline}
                      onChange={(e) => setTagline(e.target.value)}
                      placeholder="Handwoven, one piece at a time"
                      className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[14px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
                    />
                  </label>
                </div>

                <div className="mt-6">
                  <span className="mb-2 block text-[12.5px] font-medium text-foreground/80">
                    Brand personality
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {PERSONALITIES.map((p) => (
                      <PromptChip
                        key={p}
                        selected={personality.includes(p)}
                        onClick={() => toggle(personality, setPersonality, p)}
                      >
                        {p}
                      </PromptChip>
                    ))}
                  </div>
                </div>

                <div className="mt-6">
                  <span className="mb-2 block text-[12.5px] font-medium text-foreground/80">
                    Colour palette
                  </span>
                  <div className="flex flex-wrap gap-3">
                    {PALETTE.map((tone) => (
                      <ColorSwatch
                        key={tone}
                        tone={tone}
                        selected={palette === tone}
                        onClick={() => setPalette(tone)}
                      />
                    ))}
                  </div>
                </div>
              </>
            )}

            <div className="mt-9 flex items-center justify-between border-t border-clay/15 pt-6">
              <button
                type="button"
                onClick={() => setStep((s) => Math.max(0, s - 1))}
                disabled={step === 0}
                className="flex items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:text-wine disabled:pointer-events-none disabled:opacity-0"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> Back
              </button>

              {step < 4 ? (
                <button
                  type="button"
                  onClick={() => setStep((s) => Math.min(4, s + 1))}
                  className="group flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-[13.5px] font-semibold text-primary-foreground shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5"
                >
                  Continue
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleFinish}
                  disabled={creating}
                  className="group flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-[13.5px] font-semibold text-primary-foreground shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5 disabled:pointer-events-none disabled:opacity-70"
                >
                  {creating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Setting up your business…
                    </>
                  ) : (
                    <>
                      Create my business
                      <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                    </>
                  )}
                </button>
              )}
            </div>
          </DeckleCard>
        </Reveal>

        <div className="space-y-4 lg:pt-2">
          {step === 0 && (
            <MarginNote>The more specific you are, the better Sakhi's suggestions get.</MarginNote>
          )}
          {step === 1 && <MarginNote>Adding gift packaging could increase festival sales.</MarginNote>}
          {step === 2 && (
            <MarginNote>Your products would appeal to urban college students.</MarginNote>
          )}
          {step === 3 && (
            <MarginNote>
              Businesses that combine 2–3 goals tend to grow faster than those chasing just one.
            </MarginNote>
          )}
          {step === 4 && <MarginNote>Natural, earthy colours match your craft.</MarginNote>}
        </div>
      </section>
    </Page>
  );
}
