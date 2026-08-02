import { Link, useNavigate } from "@tanstack/react-router";
import { Globe, LogOut, Mic, ChevronDown, Sparkles } from "lucide-react";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/hooks/use-auth";
import { SUPPORTED_LANGUAGES } from "@/lib/i18n";
import { setAppLanguage } from "@/components/sakhi/LanguageProvider";

function useNav() {
  const { t } = useTranslation();
  const NAV = [
    { to: "/", label: t("nav.companion") },
    { to: "/memory", label: t("nav.memory") },
    { to: "/noticed", label: t("nav.noticed") },
    { to: "/cashflow", label: t("nav.cashflow") },
    { to: "/schemes", label: t("nav.schemes") },
    { to: "/mentors", label: t("nav.mentors") },
    { to: "/inventory", label: t("nav.inventory") },
    { to: "/opportunities", label: t("nav.opportunities") },
  ] as const;

  const GROW_NAV = [
    { to: "/dashboard", label: t("nav.dashboard") },
    { to: "/business-setup", label: t("nav.businessSetup") },
    { to: "/brand-studio", label: t("nav.brandStudio") },
    { to: "/website-studio", label: t("nav.websiteStudio") },
    { to: "/social-studio", label: t("nav.socialStudio") },
    { to: "/content-calendar", label: t("nav.contentCalendar") },
    { to: "/analytics", label: t("nav.analytics") },
    { to: "/advisor", label: t("nav.advisor") },
  ] as const;

  return { NAV, GROW_NAV };
}

function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const current =
    SUPPORTED_LANGUAGES.find((l) => l.code === i18n.language) ?? SUPPORTED_LANGUAGES[0]!;

  return (
    <div className="relative hidden sm:block">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 rounded-full border border-clay/30 bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-wine/30 hover:text-wine"
      >
        <Globe className="h-3.5 w-3.5" /> {current.label} <ChevronDown className="h-3 w-3" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} aria-hidden />
          <div className="absolute top-full right-0 z-50 mt-2 max-h-72 w-40 overflow-y-auto rounded-2xl border border-clay/20 bg-card py-1.5 shadow-[var(--shadow-lift)]">
            {SUPPORTED_LANGUAGES.map((l) => (
              <button
                key={l.code}
                type="button"
                onClick={() => {
                  setAppLanguage(l.code);
                  setOpen(false);
                }}
                className={`block w-full px-3.5 py-1.5 text-left text-[12.5px] transition-colors hover:bg-sand/60 ${
                  l.code === current.code ? "font-semibold text-wine" : "text-foreground/75"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export function SiteHeader() {
  const { user, loading, signOut } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { NAV, GROW_NAV } = useNav();

  async function handleSignOut() {
    await signOut();
    navigate({ to: "/login" });
  }

  return (
    <header className="sticky top-0 z-40 border-b border-clay/20 bg-ivory/85 backdrop-blur-md">
      <div className="mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-5 py-3 lg:grid-cols-[auto_minmax(0,1fr)_auto]">
        <Link to="/" className="flex min-w-0 items-center gap-2.5">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-rose font-display text-sm text-wine ring-1 ring-wine/20">
            S
          </span>
          <span className="min-w-0 leading-tight">
            <span className="block truncate font-display text-lg font-semibold text-foreground">
              Sakhi
            </span>
            <span className="block truncate text-[9px] tracking-[0.18em] text-muted-foreground uppercase">
              {t("nav.by")}
            </span>
          </span>
        </Link>

        <nav className="col-span-2 flex flex-nowrap items-center gap-x-1 overflow-x-auto text-[13px] lg:col-span-1 lg:order-2">
          <span className="mr-1 flex shrink-0 items-center gap-1 text-[10px] font-semibold tracking-[0.18em] text-wine uppercase">
            <Sparkles className="h-3 w-3" /> {t("nav.grow")}
          </span>
          {GROW_NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="shrink-0 rounded-full px-2.5 py-1 text-foreground/70 transition-colors hover:bg-rose hover:text-wine data-[status=active]:bg-rose data-[status=active]:text-wine"
            >
              {item.label}
            </Link>
          ))}
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              activeOptions={{ exact: item.to === "/" }}
              className="shrink-0 rounded-full px-3 py-1.5 text-muted-foreground transition-colors hover:text-wine data-[status=active]:bg-rose data-[status=active]:text-wine"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-2 lg:order-3">
          <LanguageSwitcher />
          {!loading && user ? (
            <button
              type="button"
              onClick={handleSignOut}
              className="flex items-center gap-1.5 rounded-full border border-clay/30 bg-card px-3.5 py-2 text-xs font-medium text-foreground transition-colors hover:border-wine/30 hover:text-wine"
            >
              <LogOut className="h-3.5 w-3.5" /> {t("nav.logout")}
            </button>
          ) : (
            <Link
              to="/login"
              className="rounded-full border border-clay/30 bg-card px-3.5 py-2 text-xs font-medium text-foreground transition-colors hover:border-wine/30 hover:text-wine"
            >
              {t("nav.login")}
            </Link>
          )}
          <Link
            to="/"
            className="flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-xs font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5"
          >
            <Mic className="h-3.5 w-3.5" /> {t("nav.talkToSakhi")}
          </Link>
        </div>
      </div>
      <div className="thread opacity-40" />
    </header>
  );
}

export function SiteFooter() {
  const { t } = useTranslation();
  return (
    <footer className="mt-20">
      <div className="thread opacity-50" />
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-8">
        <p className="text-xs text-muted-foreground">{t("nav.footerTagline")}</p>
        <p className="hand">{t("nav.footerHand")}</p>
      </div>
    </footer>
  );
}

export function Page({ children }: { children: ReactNode }) {
  return (
    <div className="paper-grain min-h-screen bg-background">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-x-0 top-0 h-[520px] bg-[radial-gradient(80%_60%_at_18%_0%,color-mix(in_oklab,var(--rose)_75%,transparent),transparent_70%),radial-gradient(60%_50%_at_92%_10%,color-mix(in_oklab,var(--marigold)_55%,transparent),transparent_70%)]"
      />
      <div className="relative z-10">
        <SiteHeader />
        <main className="mx-auto max-w-7xl px-5 pb-10">{children}</main>
        <SiteFooter />
      </div>
    </div>
  );
}
