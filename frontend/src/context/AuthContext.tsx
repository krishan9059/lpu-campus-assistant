import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { ApiError } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { getToken, setToken } from "@/api/client";
import type { UserOut } from "@/types/api";

interface AuthState {
  user: UserOut | null;
  isAuthenticating: boolean;
  error: string | null;
  login: (regNo: string, password: string) => Promise<boolean>;
  logout: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

// The backend does not expose a "who am I" check without a round trip we want to avoid
// on every load, so the signed-in name comes from the login response and is cached
// alongside the token. A stale or expired token still fails safely: any authenticated
// call returns 401 and the caller can react by logging out.
const USER_KEY = "campus_assistant_user";

function readCachedUser(): UserOut | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as UserOut) : null;
  } catch {
    return null;
  }
}

function writeCachedUser(user: UserOut | null): void {
  try {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
  } catch {
    // Non-fatal: the user just has to sign in again after a reload.
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(() => (getToken() ? readCachedUser() : null));
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (regNo: string, password: string) => {
    setIsAuthenticating(true);
    setError(null);
    try {
      const response = await endpoints.login(regNo, password);
      setToken(response.access_token);
      writeCachedUser(response.user);
      setUser(response.user);
      return true;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not sign in. Please try again.");
      return false;
    } finally {
      setIsAuthenticating(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    writeCachedUser(null);
    setUser(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const value = useMemo(
    () => ({ user, isAuthenticating, error, login, logout, clearError }),
    [user, isAuthenticating, error, login, logout, clearError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
