import { useEffect, type ReactNode } from "react";
import { I18nextProvider } from "react-i18next";
import i18n, { LANGUAGE_STORAGE_KEY } from "@/lib/i18n";

/** Re-syncs i18next to the visitor's persisted language after hydration —
 * the server always renders "en-IN" (no localStorage there), so a
 * returning visitor with a different preference sees one brief flash of
 * English before this effect switches it, same tradeoff RequireAuth
 * already makes for session state that only exists client-side. */
export function LanguageProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (saved && saved !== i18n.language) {
      void i18n.changeLanguage(saved);
    }
  }, []);

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

export function setAppLanguage(code: string) {
  localStorage.setItem(LANGUAGE_STORAGE_KEY, code);
  void i18n.changeLanguage(code);
}
