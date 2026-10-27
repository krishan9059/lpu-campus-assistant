import { useLanguage } from "@/context/LanguageContext";
import type { UiLanguage } from "@/types/api";

import "./LanguageSwitcher.css";

const OPTIONS: { value: UiLanguage; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "en", label: "EN" },
  { value: "hi", label: "हिं" },
  { value: "pa", label: "ਪੰ" },
];

export function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();
  return (
    <div className="lang-switcher" role="radiogroup" aria-label="Reply language">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={language === option.value}
          className={`lang-option ${language === option.value ? "is-active" : ""}`}
          onClick={() => setLanguage(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
