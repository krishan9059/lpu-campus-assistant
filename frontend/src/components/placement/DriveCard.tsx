import { useState } from "react";
import { ChevronDown, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { EligibilityBadge } from "@/components/placement/EligibilityBadge";
import { formatCategory, formatCtc, formatDate, formatDeadline } from "@/utils/format";
import type { Drive } from "@/types/api";

import "./DriveCard.css";

const CATEGORY_TONE: Record<string, "neutral" | "orange" | "info"> = {
  regular: "neutral",
  dream: "orange",
  super_dream: "info",
};

export function DriveCard({ drive }: { drive: Drive }) {
  const [open, setOpen] = useState(false);
  const failedChecks = drive.eligibility?.checks.filter((c) => !c.passed) ?? [];

  return (
    <article className="drive-card">
      <div className="drive-card-main">
        <div className="drive-card-heading">
          <h3>{drive.company}</h3>
          <Badge tone={CATEGORY_TONE[drive.category] ?? "neutral"}>
            {formatCategory(drive.category)}
          </Badge>
        </div>
        <p className="drive-role">{drive.role_title}</p>
        <div className="drive-meta">
          <span className="drive-ctc">{formatCtc(drive.ctc_lpa)}</span>
          <span className="drive-dot" aria-hidden="true">
            ·
          </span>
          <span>{formatDate(drive.drive_date)}</span>
          <span className="drive-dot" aria-hidden="true">
            ·
          </span>
          <span className="drive-location">
            <MapPin size={13} aria-hidden="true" />
            {drive.location || drive.mode}
          </span>
        </div>
      </div>

      <div className="drive-card-side">
        <EligibilityBadge eligibility={drive.eligibility} />
        <span className="drive-deadline">{formatDeadline(drive.registration_deadline)}</span>
        {drive.eligibility && (
          <button
            type="button"
            className="drive-details-toggle"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            Criteria
            <ChevronDown size={14} aria-hidden="true" className={open ? "is-open" : ""} />
          </button>
        )}
      </div>

      {open && drive.eligibility && (
        <div className="drive-details">
          <ul>
            {drive.eligibility.checks.map((check) => (
              <li key={check.code} className={check.passed ? "is-passed" : "is-failed"}>
                <span className="drive-check-code">{check.code.replace("_", " ")}</span>
                <span>
                  required {check.required} · you have {check.actual}
                </span>
              </li>
            ))}
          </ul>
          {failedChecks.length === 0 && drive.eligibility.eligible && (
            <p className="drive-details-note">You meet every criterion for this drive.</p>
          )}
        </div>
      )}
    </article>
  );
}
