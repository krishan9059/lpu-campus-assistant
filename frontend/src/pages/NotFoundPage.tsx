import { Link } from "react-router-dom";

import { PageShell } from "@/components/layout/PageShell";

export function NotFoundPage() {
  return (
    <PageShell>
      <h1>Page not found</h1>
      <p style={{ color: "var(--color-ink-muted)", marginTop: "var(--space-3)" }}>
        <Link to="/">Go back to the assistants</Link>
      </p>
    </PageShell>
  );
}
