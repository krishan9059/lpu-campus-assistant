import { useEffect, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { PageShell } from "@/components/layout/PageShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/context/AuthContext";

import "./SignInPage.css";

export function SignInPage() {
  const { user, login, isAuthenticating, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [regNo, setRegNo] = useState("");
  const [password, setPassword] = useState("");

  const from = (location.state as { from?: string } | undefined)?.from || "/";

  useEffect(() => {
    if (user) {
      navigate(from, { replace: true });
    }
  }, [user, navigate, from]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    clearError();
    const ok = await login(regNo.trim(), password);
    if (ok) navigate(from, { replace: true });
  };

  return (
    <PageShell showLanguageSwitcher={false}>
      <div className="signin-wrap">
        <h1>Sign in</h1>
        <p className="signin-subtitle">
          Sign in with your student or staff registration number to access the assistant and placement features.
        </p>

        <form className="signin-form" onSubmit={handleSubmit}>
          <label className="signin-field">
            <span>Registration number</span>
            <input
              value={regNo}
              onChange={(e) => setRegNo(e.target.value)}
              placeholder="DEMO001"
              autoComplete="username"
              autoFocus
              required
            />
          </label>
          <label className="signin-field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error && <p className="signin-error">{error}</p>}

          <Button type="submit" isLoading={isAuthenticating} className="signin-submit">
            Sign in
          </Button>
        </form>

        <div className="signin-demo">
          <p>Demo accounts (all share the same password):</p>
          <ul>
            <li>
              <code>DEMO001</code> – <code>DEMO012</code> as students
            </li>
            <li>
              <code>admin</code> as the placement administrator
            </li>
          </ul>
          <p>
            Password: <code>campus@123</code>
          </p>
        </div>
      </div>
    </PageShell>
  );
}
