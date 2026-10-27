import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { SourceList } from "@/components/chat/SourceList";
import type { Source } from "@/types/api";

const sources: Source[] = [
  {
    id: 1,
    title: "Academic Regulations",
    section: "Minimum attendance",
    page: null,
    effective_date: "2025-07-01",
    snippet: "Students must maintain at least 75% attendance.",
    sample: true,
  },
];

describe("SourceList", () => {
  it("renders nothing for an empty list", () => {
    const { container } = render(<SourceList sources={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the source title collapsed by default", () => {
    render(<SourceList sources={sources} />);
    expect(screen.getByText(/Academic Regulations/)).toBeInTheDocument();
    expect(screen.queryByText(/at least 75% attendance/)).not.toBeInTheDocument();
  });

  it("expands to show the snippet on click", async () => {
    render(<SourceList sources={sources} />);
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByText(/at least 75% attendance/)).toBeInTheDocument();
  });
});
