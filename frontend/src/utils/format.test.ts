import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { daysUntil, formatCategory, formatCtc, formatDate, formatDeadline } from "@/utils/format";

describe("formatDate", () => {
  it("formats an ISO date in a readable form", () => {
    expect(formatDate("2026-10-15")).toBe("15 Oct 2026");
  });

  it("returns an empty string for null", () => {
    expect(formatDate(null)).toBe("");
  });

  it("returns the raw string when it cannot be parsed", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
});

describe("formatCtc", () => {
  it("drops the decimal for whole numbers", () => {
    expect(formatCtc(10)).toBe("10 LPA");
  });

  it("keeps one decimal for fractional values", () => {
    expect(formatCtc(7.2)).toBe("7.2 LPA");
  });
});

describe("formatCategory", () => {
  it("maps known categories to display labels", () => {
    expect(formatCategory("super_dream")).toBe("Super Dream");
    expect(formatCategory("regular")).toBe("Regular");
  });

  it("falls back to the raw value for unknown categories", () => {
    expect(formatCategory("mystery")).toBe("mystery");
  });
});

describe("daysUntil / formatDeadline", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-10T12:00:00"));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("counts whole days to a future date", () => {
    expect(daysUntil("2026-10-13")).toBe(3);
  });

  it("reports today as zero", () => {
    expect(daysUntil("2026-10-10")).toBe(0);
  });

  it("formats a closed deadline", () => {
    expect(formatDeadline("2026-10-09")).toBe("Registration closed");
  });

  it("formats today and tomorrow specially", () => {
    expect(formatDeadline("2026-10-10")).toBe("Closes today");
    expect(formatDeadline("2026-10-11")).toBe("Closes tomorrow");
  });

  it("formats further-out deadlines with a day count", () => {
    expect(formatDeadline("2026-10-15")).toBe("Closes in 5 days");
  });
});
