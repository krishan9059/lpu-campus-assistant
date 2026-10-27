import { useState } from "react";
import { ChevronDown, FileText } from "lucide-react";

import { formatDate } from "@/utils/format";
import type { Source } from "@/types/api";

import "./SourceList.css";

export function SourceList({ sources }: { sources: Source[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);
  if (sources.length === 0) return null;

  return (
    <div className="source-list">
      <p className="source-list-label">Sources</p>
      <ul>
        {sources.map((source) => {
          const isOpen = expanded === source.id;
          return (
            <li key={source.id} className="source-item">
              <button
                type="button"
                className="source-toggle"
                aria-expanded={isOpen}
                onClick={() => setExpanded(isOpen ? null : source.id)}
              >
                <span className="source-marker">{source.id}</span>
                <FileText size={14} aria-hidden="true" className="source-icon" />
                <span className="source-title">
                  {source.title}
                  {source.section ? ` — ${source.section}` : ""}
                </span>
                {source.sample && <span className="source-sample-tag">sample</span>}
                <ChevronDown
                  size={15}
                  aria-hidden="true"
                  className={`source-chevron ${isOpen ? "is-open" : ""}`}
                />
              </button>
              {isOpen && (
                <div className="source-detail">
                  <p>{source.snippet}</p>
                  <p className="source-meta">
                    {source.effective_date && (
                      <span>Effective {formatDate(source.effective_date)}</span>
                    )}
                    {source.page && <span>Page {source.page}</span>}
                  </p>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
