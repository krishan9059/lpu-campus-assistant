import type { ReactNode } from "react";

import "./Badge.css";

type Tone = "neutral" | "success" | "danger" | "orange" | "info";

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
