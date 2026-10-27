import { Mail, Phone, Clock } from "lucide-react";

import type { Escalation } from "@/types/api";

import "./EscalationCard.css";

export function EscalationCard({ escalation }: { escalation: Escalation }) {
  const departments = [escalation.department, ...escalation.additional];
  return (
    <div className="escalation-card">
      {departments.map((department) => (
        <div key={department.id} className="escalation-department">
          <p className="escalation-name">{department.name}</p>
          {department.description && (
            <p className="escalation-description">{department.description}</p>
          )}
          <div className="escalation-contacts">
            {department.phone && (
              <a href={`tel:${department.phone.replace(/[^\d+]/g, "")}`}>
                <Phone size={14} aria-hidden="true" /> {department.phone}
              </a>
            )}
            {department.email && (
              <a href={`mailto:${department.email}`}>
                <Mail size={14} aria-hidden="true" /> {department.email}
              </a>
            )}
            {department.hours && (
              <span>
                <Clock size={14} aria-hidden="true" /> {department.hours}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
