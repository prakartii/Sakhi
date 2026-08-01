import { Link } from "@tanstack/react-router";
import { Globe, Mic, ChevronDown, Sparkles } from "lucide-react";
import type { ReactNode } from "react";

const NAV = [
  { to: "/", label: "Companion" },
  { to: "/memory", label: "Memory" },
  { to: "/noticed", label: "Sakhi noticed" },
  { to: "/cashflow", label: "Cashflow" },
  { to: "/schemes", label: "Schemes" },
  { to: "/mentors", label: "Mentors" },
  { to: "/inventory", label: "Inventory" },
  { to: "/opportunities", label: "Opportunity Engine" },
] as const;

const GROW_NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/business-setup", label: "Business Setup" },
  { to: "/brand-studio", label: "Brand Studio" },
  { to: "/website-studio", label: "Website Studio" },
  { to: "/social-studio", label: "Social Studio" },
  { to: "/content-calendar", label: "Content Calendar" },
  { to: "/analytics", label: "Analytics" },
  { to: "/advisor", label: "AI Advisor" },
] as const;

export function SiteHeader() {
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
              by Yuukke Catalyst
            </span>
          </span>
        </Link>

        <nav className="col-span-2 flex flex-nowrap items-center gap-x-1 overflow-x-auto text-[13px] lg:col-span-1 lg:order-2">
          <span className="mr-1 flex shrink-0 items-center gap-1 text-[10px] font-semibold tracking-[0.18em] text-wine uppercase">
            <Sparkles className="h-3 w-3" /> Grow
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
          <button className="hidden items-center gap-1.5 rounded-full border border-clay/30 bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-wine/30 hover:text-wine sm:flex">
            <Globe className="h-3.5 w-3.5" /> English <ChevronDown className="h-3 w-3" />
          </button>
          <Link
            to="/login"
            className="rounded-full border border-clay/30 bg-card px-3.5 py-2 text-xs font-medium text-foreground transition-colors hover:border-wine/30 hover:text-wine"
          >
            Login
          </Link>
          <button className="flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-xs font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5">
            <Mic className="h-3.5 w-3.5" /> Talk to Sakhi
          </button>
        </div>
      </div>
      <div className="thread opacity-40" />
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-20">
      <div className="thread opacity-50" />
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-8">
        <p className="text-xs text-muted-foreground">Sakhi — remembers, predicts, acts.</p>
        <p className="hand">built for the women who build India</p>
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
