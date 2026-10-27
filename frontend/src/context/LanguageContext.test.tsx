import { renderHook, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ReactNode } from "react";

import { LanguageProvider, useLanguage } from "@/context/LanguageContext";

function wrapper({ children }: { children: ReactNode }) {
  return <LanguageProvider>{children}</LanguageProvider>;
}

describe("useLanguage", () => {
  it("defaults to auto", () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(result.current.language).toBe("auto");
  });

  it("persists a language change", () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    act(() => result.current.setLanguage("hi"));
    expect(result.current.language).toBe("hi");
    expect(localStorage.getItem("campus_assistant_language")).toBe("hi");
  });

  it("throws when used outside the provider", () => {
    expect(() => renderHook(() => useLanguage())).toThrow();
  });
});
