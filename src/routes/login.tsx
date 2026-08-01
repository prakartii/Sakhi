import { useState, type SyntheticEvent } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { ArrowRight, BarChart3, Brain, Globe, Mic, ShieldCheck, User, UserPlus } from "lucide-react";
import { BotanicalMark } from "@/components/sakhi/CompanionAssets";
import {
  FeatureItem,
  GoogleIcon,
  LabeledInput,
  LanguageSelect,
  MobileField,
  PasswordField,
} from "@/components/sakhi/Auth";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — Sakhi" },
      {
        name: "description",
        content: "Sign in to continue your journey with Sakhi — your voice, your business.",
      },
    ],
  }),
  component: LoginPage,
});

type Mode = "login" | "signup";

function LoginPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [language, setLanguage] = useState("en");
  const [name, setName] = useState("");
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  function handleSubmit(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    if (mode === "signup" && password !== confirm) {
      toast.error("Passwords don't match");
      return;
    }
    toast.success(mode === "login" ? "Welcome back to Sakhi!" : "Account created — welcome to Sakhi!");
  }

  return (
    <div className="paper-grain relative flex min-h-screen items-center justify-center bg-background px-4 py-10 sm:px-6">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-x-0 top-0 h-[520px]"
        style={{
          background:
            "radial-gradient(80% 60% at 18% 0%, color-mix(in oklab, var(--rose) 65%, transparent), transparent 70%), radial-gradient(60% 50% at 92% 10%, color-mix(in oklab, var(--marigold) 45%, transparent), transparent 70%)",
        }}
      />

      <BotanicalMark className="pointer-events-none absolute bottom-6 left-6 hidden h-44 w-36 -rotate-[8deg] text-wine/[0.16] sm:block" />

      <div className="relative z-10 grid w-full max-w-6xl overflow-hidden rounded-[2rem] bg-card ring-1 ring-clay/15 lg:grid-cols-2 lg:min-h-[640px]" style={{ boxShadow: "var(--shadow-lift)" }}>
        {/* ---------- Left : form ---------- */}
        <div className="relative px-7 py-10 sm:px-12 sm:py-12 lg:px-14 lg:py-14">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-[1.65rem]">
                Sakhi
              </p>
              <p className="mt-0.5 text-[10px] font-semibold tracking-[0.22em] text-wine uppercase">
                By Yuukke Catalyst
              </p>
            </div>
            <LanguageSelect value={language} onValueChange={setLanguage} className="mt-1" />
          </div>

          <h1 className="mt-8 font-display text-3xl font-bold tracking-tight text-foreground sm:mt-9 sm:text-4xl">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h1>
          <p className="mt-2 text-[14px] text-muted-foreground">
            {mode === "login"
              ? "Sign in to continue your journey with Sakhi"
              : "Join the women growing their business with Sakhi"}
          </p>

          <div className="mt-7 flex items-center gap-6 border-b border-clay/20">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`relative flex items-center gap-1.5 pb-3 text-[14px] font-semibold transition-colors ${
                mode === "login" ? "text-wine" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <User className="h-4 w-4" /> Login
              {mode === "login" && (
                <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-wine" />
              )}
            </button>
            <button
              type="button"
              onClick={() => setMode("signup")}
              className={`relative flex items-center gap-1.5 pb-3 text-[14px] font-semibold transition-colors ${
                mode === "signup" ? "text-wine" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <UserPlus className="h-4 w-4" /> Create Account
              {mode === "signup" && (
                <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-wine" />
              )}
            </button>
          </div>

          <form className="mt-7 space-y-5" onSubmit={handleSubmit}>
            {mode === "signup" && (
              <LabeledInput
                label="Full Name"
                icon={User}
                placeholder="Enter your full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            )}

            <MobileField value={mobile} onChange={setMobile} />

            <PasswordField value={password} onChange={setPassword} />

            {mode === "signup" && (
              <PasswordField
                label="Confirm Password"
                placeholder="Re-enter your password"
                value={confirm}
                onChange={setConfirm}
              />
            )}

            {mode === "login" && (
              <div className="flex justify-end">
                <a href="#" className="text-[13px] font-medium text-wine hover:underline">
                  Forgot password?
                </a>
              </div>
            )}

            <button
              type="submit"
              className="group flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-primary text-[15px] font-semibold text-primary-foreground shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5"
            >
              {mode === "login" ? "Login to Sakhi" : "Create My Account"}
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </button>
          </form>

          <div className="mt-6 flex items-center gap-3 text-[11px] tracking-wide text-muted-foreground uppercase">
            <span className="h-px flex-1 bg-clay/25" /> or <span className="h-px flex-1 bg-clay/25" />
          </div>

          <button
            type="button"
            onClick={() => toast.info("Google sign-in isn't wired up yet")}
            className="mt-6 flex h-12 w-full items-center justify-center gap-2.5 rounded-xl border border-clay/30 bg-card text-[14px] font-medium text-foreground shadow-sm transition-colors hover:border-wine/30"
          >
            <GoogleIcon className="h-[18px] w-[18px]" /> Continue with Google
          </button>

          <p className="mt-7 flex items-center gap-2 text-[12px] text-muted-foreground">
            <ShieldCheck className="h-4 w-4 shrink-0 text-leaf-ink" /> Your data is safe with us. We
            respect your privacy.
          </p>
        </div>

        {/* ---------- Right : illustration + pitch ---------- */}
        <div
          className="relative hidden flex-col overflow-hidden px-10 py-12 lg:flex xl:px-12"
          style={{
            background:
              "radial-gradient(120% 100% at 15% 15%, color-mix(in oklab, var(--rose) 75%, transparent), transparent 62%), radial-gradient(90% 70% at 88% -5%, color-mix(in oklab, var(--marigold) 50%, transparent), transparent 65%), var(--sand)",
          }}
        >
          <div className="relative mx-auto w-full max-w-[360px] xl:ml-auto xl:mr-0">
            <img
              src="/images/artisan-loom.png"
              alt="Woman weaving on a handloom"
              className="w-full object-contain"
            />
          </div>

          <div className="relative mt-6">
            <h2 className="font-display text-[1.85rem] leading-[1.18] font-semibold text-foreground xl:text-[2rem]">
              Your voice. Your business.
              <br />
              Our <span className="text-[oklch(0.58_0.15_75)] italic">technology.</span>
            </h2>
            <p className="mt-4 max-w-sm text-[14px] leading-relaxed text-foreground/70">
              Sakhi listens, remembers and helps you grow your business — simply by talking.
            </p>
          </div>

          <div className="relative mt-9 grid grid-cols-4 gap-4">
            <FeatureItem
              icon={Mic}
              tone="rose"
              title="Voice First"
              subtitle="Just speak in your language"
            />
            <FeatureItem
              icon={Brain}
              tone="indigo"
              title="Remembers Everything"
              subtitle="Never miss important details"
            />
            <FeatureItem icon={BarChart3} tone="leaf" title="Insights" subtitle="Understand and grow better" />
            <FeatureItem
              icon={Globe}
              tone="marigold"
              title="7 Indian Languages"
              subtitle="Made for every woman"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
