import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/context/AuthContext";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/sign-in" state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
}

export function RequireRole({ role, children }: { role: "admin"; children: ReactNode }) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/sign-in" state={{ from: location.pathname }} replace />;
  }
  if (user.role !== role) return <Navigate to="/" replace />;
  return <>{children}</>;
}
