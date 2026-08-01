import { useState, type ComponentType } from "react";
import { Eye, EyeOff, Globe, Lock, Phone } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/** Login/signup-only pieces. Kept separate from the shared Cards/Layout system. */

export const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "hi", label: "हिंदी" },
  { value: "bn", label: "বাংলা" },
  { value: "ta", label: "தமிழ்" },
  { value: "te", label: "తెలుగు" },
  { value: "mr", label: "मराठी" },
  { value: "gu", label: "ગુજરાતી" },
  { value: "kn", label: "ಕನ್ನಡ" },
] as const;

export function LanguageSelect({
  value,
  onValueChange,
  className,
}: {
  value: string;
  onValueChange: (v: string) => void;
  className?: string;
}) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger
        className={cn(
          "h-8 w-auto gap-1.5 rounded-full border-clay/30 bg-card px-3 text-xs text-muted-foreground shadow-none hover:border-wine/30 hover:text-wine [&>svg]:opacity-60",
          className,
        )}
      >
        <Globe className="h-3.5 w-3.5 shrink-0" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent align="end">
        {LANGUAGES.map((lang) => (
          <SelectItem key={lang.value} value={lang.value}>
            {lang.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function FieldError({ id, message }: { id: string; message?: string | undefined }) {
  if (!message) return null;
  return (
    <p id={id} role="alert" className="mt-1.5 text-[12px] font-medium text-destructive">
      {message}
    </p>
  );
}

export function LabeledInput({
  label,
  icon: Icon,
  error,
  id,
  ...props
}: {
  label: string;
  icon: ComponentType<{ className?: string }>;
  error?: string | undefined;
} & React.InputHTMLAttributes<HTMLInputElement>) {
  const inputId = id ?? `field-${label.toLowerCase().replace(/\s+/g, "-")}`;
  const errorId = `${inputId}-error`;
  return (
    <label className="block" htmlFor={inputId}>
      <span className="mb-1.5 block text-[13px] font-medium text-foreground/85">{label}</span>
      <span className="relative flex items-center">
        <Icon className="pointer-events-none absolute left-3.5 h-4 w-4 text-muted-foreground" />
        <Input
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
          {...props}
          className={cn(
            "h-11 rounded-xl border-clay/25 bg-card pl-10 text-[14px] shadow-sm placeholder:text-muted-foreground/70 focus-visible:ring-wine/30",
            error && "border-destructive/60 focus-visible:ring-destructive/30",
          )}
        />
      </span>
      <FieldError id={errorId} message={error} />
    </label>
  );
}

export function PasswordField({
  label = "Password",
  placeholder = "Enter your password",
  value,
  onChange,
  error,
  autoComplete,
  id,
}: {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
  error?: string | undefined;
  autoComplete?: string;
  id?: string;
}) {
  const [visible, setVisible] = useState(false);
  const inputId = id ?? `field-${label.toLowerCase().replace(/\s+/g, "-")}`;
  const errorId = `${inputId}-error`;
  return (
    <label className="block" htmlFor={inputId}>
      <span className="mb-1.5 block text-[13px] font-medium text-foreground/85">{label}</span>
      <span className="relative flex items-center">
        <Lock className="pointer-events-none absolute left-3.5 h-4 w-4 text-muted-foreground" />
        <Input
          id={inputId}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
          className={cn(
            "h-11 rounded-xl border-clay/25 bg-card pr-10 pl-10 text-[14px] shadow-sm placeholder:text-muted-foreground/70 focus-visible:ring-wine/30",
            error && "border-destructive/60 focus-visible:ring-destructive/30",
          )}
        />
        <button
          type="button"
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
          onClick={() => setVisible((v) => !v)}
          className="absolute right-3.5 text-muted-foreground transition-colors hover:text-wine"
        >
          {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </span>
      <FieldError id={errorId} message={error} />
    </label>
  );
}

export const COUNTRY_CODES = [
  { value: "IN", flag: "🇮🇳", dial: "+91" },
  { value: "US", flag: "🇺🇸", dial: "+1" },
  { value: "GB", flag: "🇬🇧", dial: "+44" },
  { value: "AE", flag: "🇦🇪", dial: "+971" },
  { value: "BD", flag: "🇧🇩", dial: "+880" },
  { value: "NP", flag: "🇳🇵", dial: "+977" },
  { value: "PK", flag: "🇵🇰", dial: "+92" },
  { value: "LK", flag: "🇱🇰", dial: "+94" },
] as const;

export function CountryCodeSelect({
  value,
  onValueChange,
}: {
  value: string;
  onValueChange: (v: string) => void;
}) {
  const current = COUNTRY_CODES.find((c) => c.value === value) ?? COUNTRY_CODES[0];
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="h-11 w-[5.25rem] shrink-0 gap-1 rounded-none border-0 border-r border-clay/20 bg-transparent px-3 text-[13.5px] shadow-none focus:ring-0 [&>svg]:opacity-50">
        <span className="flex items-center gap-1">
          <span aria-hidden>{current.flag}</span>
          <span>{current.dial}</span>
        </span>
      </SelectTrigger>
      <SelectContent>
        {COUNTRY_CODES.map((c) => (
          <SelectItem key={c.value} value={c.value}>
            <span className="flex items-center gap-2">
              <span aria-hidden>{c.flag}</span> {c.dial}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function MobileField({
  value,
  onChange,
  countryCode,
  onCountryCodeChange,
  error,
}: {
  value: string;
  onChange: (v: string) => void;
  countryCode: string;
  onCountryCodeChange: (v: string) => void;
  error?: string | undefined;
}) {
  const errorId = "field-mobile-number-error";
  return (
    <label className="block" htmlFor="field-mobile-number">
      <span className="mb-1.5 block text-[13px] font-medium text-foreground/85">
        Mobile Number
      </span>
      <span
        className={cn(
          "flex items-center overflow-hidden rounded-xl border border-clay/25 bg-card shadow-sm focus-within:ring-1 focus-within:ring-wine/30",
          error && "border-destructive/60 focus-within:ring-destructive/30",
        )}
      >
        <CountryCodeSelect value={countryCode} onValueChange={onCountryCodeChange} />
        <span className="relative flex flex-1 items-center">
          <Phone className="pointer-events-none absolute left-3.5 h-4 w-4 text-muted-foreground" />
          <Input
            id="field-mobile-number"
            type="tel"
            inputMode="numeric"
            autoComplete="tel-national"
            placeholder="Enter your mobile number"
            value={value}
            onChange={(e) => onChange(e.target.value.replace(/[^\d]/g, "").slice(0, 12))}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : undefined}
            className="h-11 rounded-none border-0 bg-transparent pl-10 text-[14px] shadow-none placeholder:text-muted-foreground/70 focus-visible:ring-0"
          />
        </span>
      </span>
      <FieldError id={errorId} message={error} />
    </label>
  );
}

export function RememberMe({
  checked,
  onCheckedChange,
}: {
  checked: boolean;
  onCheckedChange: (v: boolean) => void;
}) {
  return (
    <label className="flex select-none items-center gap-2 text-[13px] text-foreground/80">
      <Checkbox checked={checked} onCheckedChange={(v) => onCheckedChange(v === true)} />
      Remember me
    </label>
  );
}

export function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden>
      <path
        fill="#FFC107"
        d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.6 6 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.5z"
      />
      <path
        fill="#FF3D00"
        d="M6.3 14.7l6.6 4.8C14.6 15.9 18.9 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.6 6 29.6 4 24 4c-7.5 0-14 4.2-17.3 10.4z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.5 0 10.4-1.9 14.2-5.1l-6.6-5.4C29.6 35.4 26.9 36.5 24 36.5c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.9 39.7 16.4 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.2 4.2-4.1 5.5l6.6 5.4C41.5 36.4 44 30.8 44 24c0-1.3-.1-2.7-.4-3.5z"
      />
    </svg>
  );
}

const FEATURE_TONE = {
  rose: "bg-rose text-wine",
  leaf: "bg-leaf text-leaf-ink",
  marigold: "bg-marigold text-[oklch(0.42_0.09_70)]",
  indigo: "bg-indigo-tint text-[oklch(0.42_0.09_255)]",
} as const;

export function FeatureItem({
  icon: Icon,
  tone,
  title,
  subtitle,
}: {
  icon: ComponentType<{ className?: string }>;
  tone: keyof typeof FEATURE_TONE;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="flex flex-col items-center text-center sm:items-start sm:text-left">
      <span
        className={cn(
          "grid h-11 w-11 shrink-0 place-items-center rounded-full transition-transform duration-300 hover:scale-110",
          FEATURE_TONE[tone],
        )}
      >
        <Icon className="h-[18px] w-[18px]" />
      </span>
      <p className="mt-2.5 text-[13px] leading-snug font-semibold text-foreground">{title}</p>
      <p className="mt-0.5 text-[11.5px] leading-snug text-muted-foreground">{subtitle}</p>
    </div>
  );
}
