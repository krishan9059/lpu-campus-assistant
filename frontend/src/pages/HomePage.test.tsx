import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/context/AuthContext";
import { LanguageProvider } from "@/context/LanguageContext";
import { HomePage } from "@/pages/HomePage";

function renderHome() {
  return render(
    <MemoryRouter>
      <LanguageProvider>
        <AuthProvider>
          <HomePage />
        </AuthProvider>
      </LanguageProvider>
    </MemoryRouter>,
  );
}

describe("HomePage", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn(
      async () =>
        new Response(
          JSON.stringify([
            {
              id: "university",
              domain: "university",
              name: { en: "University Help Desk", hi: "", pa: "" },
              tagline: { en: "Academics and campus services", hi: "", pa: "" },
              suggested_questions: { en: ["What is the fee deadline?"], hi: [], pa: [] },
              personalised: false,
            },
          ]),
          { status: 200 },
        ),
    ) as typeof fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("renders assistant cards once loaded", async () => {
    renderHome();
    await waitFor(() => expect(screen.getByText("University Help Desk")).toBeInTheDocument());
    expect(screen.getByText("What is the fee deadline?")).toBeInTheDocument();
  });
});
