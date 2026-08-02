import type { CSSProperties } from "react";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Loader2, Mail } from "lucide-react";
import { api } from "@/lib/api-client";
import type { PublicWebsiteResponse } from "@/lib/types";

/**
 * Public, unauthenticated preview of a business's generated website
 * (GET /public/websites/{slug}) — deliberately standalone, no Sakhi nav or
 * chrome, since this represents the BUSINESS's own site in its own brand
 * colors/typography, not a page inside the Sakhi dashboard. Only reachable
 * once a site has been published from Website Studio.
 */
export const Route = createFileRoute("/site/$slug")({
  component: PublicWebsitePage,
});

function usePublicWebsite(slug: string) {
  return useQuery({
    queryKey: ["public-website", slug],
    queryFn: () => api.get<PublicWebsiteResponse>(`/public/websites/${slug}`),
    retry: false,
  });
}

function PublicWebsitePage() {
  const { slug } = Route.useParams();
  const { data, isLoading, isError } = usePublicWebsite(slug);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#faf7f2]">
        <Loader2 className="h-6 w-6 animate-spin text-[#8a8478]" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-2 bg-[#faf7f2] px-4 text-center">
        <h1 className="text-xl font-semibold text-[#2a261f]">This site isn't available</h1>
        <p className="text-sm text-[#6b6558]">
          It may not be published yet, or the link is incorrect.
        </p>
      </div>
    );
  }

  const primary = data.brand?.primary_color || "#8F2F56";
  const secondary = data.brand?.secondary_color || "#2a261f";
  const typographyParts = (data.brand?.typography || "Fraunces / Inter")
    .split("/")
    .map((s) => s.trim());
  const headingFont = typographyParts[0] || "Fraunces";
  const bodyFont = typographyParts[1] || "Inter";
  const fontHref = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(headingFont)}:wght@600;700&family=${encodeURIComponent(bodyFont)}:wght@400;500&display=swap`;
  const { pages, seo } = data.content;

  return (
    <div
      style={
        {
          "--brand-primary": primary,
          "--brand-secondary": secondary,
          "--font-heading": `"${headingFont}", Georgia, serif`,
          "--font-body": `"${bodyFont}", system-ui, sans-serif`,
        } as CSSProperties
      }
      className="min-h-screen bg-[#faf7f2] font-[var(--font-body)] text-[#2a261f]"
    >
      <title>{seo.title || data.website_name}</title>
      <meta name="description" content={seo.description} />
      <link rel="stylesheet" href={fontHref} />

      <header className="border-b border-black/5 px-6 py-5">
        <p className="text-sm font-semibold tracking-wide uppercase" style={{ color: primary }}>
          {data.website_name}
        </p>
      </header>

      <section
        className="relative flex min-h-[26rem] flex-col items-center justify-center gap-4 px-6 py-16 text-center"
        style={{
          backgroundImage: data.images.hero_url
            ? `linear-gradient(0deg, color-mix(in srgb, #faf7f2 55%, transparent), color-mix(in srgb, #faf7f2 78%, transparent)), url(${data.images.hero_url})`
            : `radial-gradient(70% 90% at 50% 0%, color-mix(in srgb, ${primary} 14%, transparent), transparent 70%)`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <h1
          className="max-w-2xl text-4xl leading-tight font-semibold sm:text-5xl"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          {pages.landing.hero.headline}
        </h1>
        <p className="max-w-xl text-base text-[#4a453b]">{pages.landing.hero.subhead}</p>
        <button
          className="mt-2 rounded-full px-6 py-3 text-sm font-semibold text-white shadow-sm"
          style={{ backgroundColor: primary }}
        >
          {pages.landing.hero.cta}
        </button>
      </section>

      {pages.landing.sections.length > 0 && (
        <section className="mx-auto grid max-w-5xl gap-8 px-6 py-16 sm:grid-cols-2 lg:grid-cols-3">
          {pages.landing.sections.map((s) => (
            <div key={s.heading} className="rounded-2xl bg-white/70 p-6 shadow-sm">
              <p
                className="text-[11px] font-semibold tracking-[0.14em] uppercase"
                style={{ color: primary }}
              >
                {s.type}
              </p>
              <h3
                className="mt-2 text-lg font-semibold"
                style={{ fontFamily: "var(--font-heading)" }}
              >
                {s.heading}
              </h3>
              <p className="mt-2 text-[13.5px] leading-relaxed text-[#4a453b]">{s.body}</p>
            </div>
          ))}
        </section>
      )}

      <section className="mx-auto max-w-3xl px-6 py-16 text-center">
        <h2
          className="text-2xl font-semibold"
          style={{ fontFamily: "var(--font-heading)", color: secondary }}
        >
          Our story
        </h2>
        <p className="mt-4 text-[14.5px] leading-relaxed text-[#4a453b]">{pages.about.body}</p>
      </section>

      {pages.products.length > 0 && (
        <section className="mx-auto max-w-5xl px-6 py-16">
          <h2
            className="text-center text-2xl font-semibold"
            style={{ fontFamily: "var(--font-heading)", color: secondary }}
          >
            What we offer
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {pages.products.map((p) => (
              <div key={p.name} className="rounded-2xl bg-white/70 p-5 shadow-sm">
                <h3 className="font-semibold" style={{ fontFamily: "var(--font-heading)" }}>
                  {p.name}
                </h3>
                <p className="mt-1.5 text-[13px] leading-relaxed text-[#4a453b]">{p.description}</p>
                {p.price != null && (
                  <p className="mt-2 text-sm font-semibold" style={{ color: primary }}>
                    ₹{p.price}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {pages.faq.length > 0 && (
        <section className="mx-auto max-w-3xl px-6 py-16">
          <h2
            className="text-center text-2xl font-semibold"
            style={{ fontFamily: "var(--font-heading)", color: secondary }}
          >
            Frequently asked
          </h2>
          <div className="mt-8 space-y-5">
            {pages.faq.map((f) => (
              <div key={f.q} className="rounded-xl bg-white/70 p-5 shadow-sm">
                <p className="font-semibold">{f.q}</p>
                <p className="mt-1.5 text-[13px] leading-relaxed text-[#4a453b]">{f.a}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <footer className="border-t border-black/5 px-6 py-10 text-center">
        <p className="flex items-center justify-center gap-2 text-[13px] text-[#6b6558]">
          <Mail className="h-3.5 w-3.5" /> {pages.contact.body}
        </p>
        <p className="mt-4 text-[11px] text-[#a09a8c]">Built with Sakhi</p>
      </footer>
    </div>
  );
}
