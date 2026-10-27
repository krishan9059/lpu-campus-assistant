import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import type { UiLanguage } from "@/types/api";

const STORAGE_KEY = "campus_assistant_language";

interface LanguageState {
  language: UiLanguage;
  setLanguage: (language: UiLanguage) => void;
}

const LanguageContext = createContext<LanguageState | null>(null);

function readStored(): UiLanguage {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === "en" || raw === "hi" || raw === "pa" || raw === "auto") return raw;
  } catch {
    // ignore
  }
  return "auto";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<UiLanguage>(readStored);

  const setLanguage = (next: UiLanguage) => {
    setLanguageState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore
    }
  };

  const value = useMemo(() => ({ language, setLanguage }), [language]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageState {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used within a LanguageProvider");
  return context;
}
