import { Link, useNavigate } from "react-router-dom";
import { LogOut, ShieldCheck } from "lucide-react";

import lpuLogo from "@/assets/brand/lpu-logo.png";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { LanguageSwitcher } from "@/components/ui/LanguageSwitcher";

import "./TopBar.css";

export function TopBar({ showLanguageSwitcher = true }: { showLanguageSwitcher?: boolean }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="top-bar">
      <Link to="/" className="top-bar-brand" aria-label="LPU Campus Assistant home">
        <img src={lpuLogo} alt="Lovely Professional University" height={28} />
        <span className="top-bar-divider" aria-hidden="true" />
        <span className="top-bar-title">Campus Assistant</span>
      </Link>

      <div className="top-bar-actions">
        {showLanguageSwitcher && <LanguageSwitcher />}
        {user ? (
          <>
            {user.role === "admin" && (
              <Button variant="ghost" size="sm" onClick={() => navigate("/admin")}>
                <ShieldCheck size={16} aria-hidden="true" />
                Admin
              </Button>
            )}
            <span className="top-bar-user" title={user.reg_no}>
              {user.full_name}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                logout();
                navigate("/sign-in");
              }}
            >
              <LogOut size={16} aria-hidden="true" />
              Sign out
            </Button>
          </>
        ) : (
          <Button variant="secondary" size="sm" onClick={() => navigate("/sign-in")}>
            Sign in
          </Button>
        )}
      </div>
    </header>
  );
}
