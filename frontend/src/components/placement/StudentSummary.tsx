import type { StudentOut } from "@/types/api";

import "./StudentSummary.css";

export function StudentSummary({ student }: { student: StudentOut }) {
  return (
    <div className="student-summary">
      <div>
        <p className="student-summary-name">{student.full_name}</p>
        <p className="student-summary-sub">
          {student.program} · {student.branch} · Batch {student.batch}
        </p>
      </div>
      <dl className="student-summary-stats">
        <div>
          <dt>CGPA</dt>
          <dd>{student.cgpa}</dd>
        </div>
        <div>
          <dt>Active backlogs</dt>
          <dd>{student.active_backlogs}</dd>
        </div>
        <div>
          <dt>Highest offer</dt>
          <dd>{student.highest_offer_lpa ? `${student.highest_offer_lpa} LPA` : "None yet"}</dd>
        </div>
      </dl>
    </div>
  );
}
