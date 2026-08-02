// App-wide i18n setup. Language codes deliberately match Sarvam's BCP-47
// voice codes exactly (en-IN, hi-IN, ta-IN, ...) — see
// app.ai.orchestrator.prompts.LANGUAGE_NAMES on the backend — so the same
// selected language drives both the UI text below and the voice
// STT/TTS/reply language in use-voice-companion.ts, with no code-mapping
// layer needed between the two.
//
// SSR note: this always initializes to "en-IN" on the server (no
// localStorage there). The client re-syncs to the persisted language after
// hydration — see LanguageProvider in components/sakhi/I18nProvider.tsx —
// so a returning visitor with a non-English preference sees one brief
// flash of English before it switches, the same tradeoff RequireAuth
// already makes for session state that only exists client-side.
import i18next from "i18next";
import { initReactI18next } from "react-i18next";

import en from "@/locales/en-IN.json";
import hi from "@/locales/hi-IN.json";
import ta from "@/locales/ta-IN.json";
import te from "@/locales/te-IN.json";
import mr from "@/locales/mr-IN.json";
import pa from "@/locales/pa-IN.json";
import as from "@/locales/as-IN.json";
import ml from "@/locales/ml-IN.json";
import bn from "@/locales/bn-IN.json";
import gu from "@/locales/gu-IN.json";
import kn from "@/locales/kn-IN.json";

export const SUPPORTED_LANGUAGES: { code: string; label: string }[] = [
  { code: "en-IN", label: "English" },
  { code: "hi-IN", label: "हिंदी" },
  { code: "mr-IN", label: "मराठी" },
  { code: "ta-IN", label: "தமிழ்" },
  { code: "te-IN", label: "తెలుగు" },
  { code: "pa-IN", label: "ਪੰਜਾਬੀ" },
  { code: "ml-IN", label: "മലയാളം" },
  { code: "as-IN", label: "অসমীয়া" },
  { code: "bn-IN", label: "বাংলা" },
  { code: "gu-IN", label: "ગુજરાતી" },
  { code: "kn-IN", label: "ಕನ್ನಡ" },
];

export const LANGUAGE_STORAGE_KEY = "sakhi-language";

if (!i18next.isInitialized) {
  void i18next.use(initReactI18next).init({
    lng: "en-IN",
    fallbackLng: "en-IN",
    resources: {
      "en-IN": { translation: en },
      "hi-IN": { translation: hi },
      "ta-IN": { translation: ta },
      "te-IN": { translation: te },
      "mr-IN": { translation: mr },
      "pa-IN": { translation: pa },
      "as-IN": { translation: as },
      "ml-IN": { translation: ml },
      "bn-IN": { translation: bn },
      "gu-IN": { translation: gu },
      "kn-IN": { translation: kn },
    },
    interpolation: { escapeValue: false },
    returnNull: false,
  });
}

export default i18next;
