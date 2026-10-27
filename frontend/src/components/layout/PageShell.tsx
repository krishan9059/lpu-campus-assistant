import type { ReactNode } from "react";

import { TopBar } from "@/components/layout/TopBar";

import "./PageShell.css";

export function PageShell({
  children,
  showLanguageSwitcher = true,
  fullBleed = false,
}: {
  children: ReactNode;
  showLanguageSwitcher?: boolean;
  fullBleed?: boolean;
}) {
  return (
    <div className="page-shell">
      <TopBar showLanguageSwitcher={showLanguageSwitcher} />
      <main className={fullBleed ? "page-main page-main-full" : "page-main"}>{children}</main>
    </div>
  );
}
