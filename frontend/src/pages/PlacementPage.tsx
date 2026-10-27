import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { DriveCard } from "@/components/placement/DriveCard";
import { StudentSummary } from "@/components/placement/StudentSummary";
import { PageShell } from "@/components/layout/PageShell";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/context/AuthContext";
import type { DrivesResponse } from "@/types/api";

import "./PlacementPage.css";

type Filter = "all" | "eligible";

export function PlacementPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<DrivesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    let cancelled = false;
    endpoints
      .drives()
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Could not load drives.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const drives = useMemo(() => {
    if (!data) return [];
    if (filter === "eligible") return data.drives.filter((d) => d.eligibility?.eligible);
    return data.drives;
  }, [data, filter]);

  return (
    <PageShell showLanguageSwitcher={false}>
      <div className="placement-header">
        <h1>Upcoming placement drives</h1>
        <p>Registration windows, packages and criteria for each drive.</p>
      </div>

      {!user && (
        <button
          type="button"
          className="placement-signin-banner"
          onClick={() => navigate("/sign-in")}
        >
          Sign in to see which drives you are eligible for, based on your own CGPA and branch.
        </button>
      )}

      {error && <p className="placement-error">{error}</p>}
      {!data && !error && (
        <div className="placement-loading">
          <Spinner label="Loading drives" />
        </div>
      )}

      {data?.student && <StudentSummary student={data.student} />}

      {data && data.drives.length > 0 && data.student && (
        <div className="placement-filter" role="radiogroup" aria-label="Filter drives">
          <button
            type="button"
            role="radio"
            aria-checked={filter === "all"}
            className={filter === "all" ? "is-active" : ""}
            onClick={() => setFilter("all")}
          >
            All drives ({data.drives.length})
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={filter === "eligible"}
            className={filter === "eligible" ? "is-active" : ""}
            onClick={() => setFilter("eligible")}
          >
            Eligible for me ({data.drives.filter((d) => d.eligibility?.eligible).length})
          </button>
        </div>
      )}

      <div className="placement-list">
        {drives.map((drive) => (
          <DriveCard key={drive.id} drive={drive} />
        ))}
        {data && drives.length === 0 && (
          <p className="placement-empty">No drives match this filter right now.</p>
        )}
      </div>
    </PageShell>
  );
}
