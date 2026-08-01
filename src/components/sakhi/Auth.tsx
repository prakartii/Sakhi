import { useState, type ComponentType } from "react";
import { Eye, EyeOff, Globe, Lock, Phone } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
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

export function LabeledInput({
  label,
  icon: Icon,
  ...props
}: {
  label: string;
  icon: ComponentType<{ className?: string }>;
} & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[13px] font-medium text-foreground/85">{label}</span>
      <span className="relative flex items-center">
        <Icon className="pointer-events-none absolute left-3.5 h-4 w-4 text-muted-foreground" />
        <Input
          {...props}
          className="h-11 rounded-xl border-clay/25 bg-card pl-10 text-[14px] shadow-sm placeholder:text-muted-foreground/70 focus-visible:ring-wine/30"
        />
      </span>
    </label>
  );
}

export function PasswordField({
  label = "Password",
  placeholder = "Enter your password",
  value,
  onChange,
}: {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <label className="block">
      <span className="mb-1.5 block text-[13px] font-medium text-foreground/85">{label}</span>
      <span className="relative flex items-center">
        <Lock className="pointer-events-none absolute left-3.5 h-4 w-4 text-muted-foreground" />
        <Input
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="h-11 rounded-xl border-clay/25 bg-card pr-10 pl-10 text-[14px] shadow-sm placeholder:text-muted-foreground/70 focus-visible:ring-wine/30"
        />
        <button
          type="button"
          aria-label={visible ? "Hide password" : "Show password"}
          onClick={() => setVisible((v) => !v)}
          className="absolute right-3.5 text-muted-foreground transition-colors hover:text-wine"
        >
          {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </span>
    </label>
  );
}

export function MobileField({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <LabeledInput
      label="Mobile Number"
      icon={Phone}
      type="tel"
      inputMode="numeric"
      placeholder="Enter your mobile number"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
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
          "grid h-11 w-11 shrink-0 place-items-center rounded-full",
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
