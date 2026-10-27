import { useEffect, useState } from "react";
import { RefreshCcw } from "lucide-react";

import { ApiError } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { PageShell } from "@/components/layout/PageShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import type { EscalationLogOut, HealthOut, ReindexResponse } from "@/types/api";

import "./AdminPage.css";

const REASON_TONE: Record<string, "neutral" | "danger" | "orange" | "info"> = {
  no_relevant_source: "neutral",
  model_not_found: "neutral",
  ungrounded: "danger",
  sensitive_topic: "orange",
  policy_exception: "info",
};

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}

export function AdminPage() {
  const [health, setHealth] = useState<HealthOut | null>(null);
  const [escalations, setEscalations] = useState<EscalationLogOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reindexResult, setReindexResult] = useState<ReindexResponse | null>(null);
  const [isReindexing, setIsReindexing] = useState(false);

  const loadEscalations = () => {
    endpoints
      .adminEscalations()
      .then(setEscalations)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load escalations."),
      );
  };

  useEffect(() => {
    endpoints
      .health()
      .then(setHealth)
      .catch(() => undefined);
    loadEscalations();
  }, []);

  const handleReindex = async (rebuild: boolean) => {
    setIsReindexing(true);
    setError(null);
    try {
      const result = await endpoints.adminReindex(rebuild);
      setReindexResult(result);
      endpoints
        .health()
        .then(setHealth)
        .catch(() => undefined);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Reindex failed.");
    } finally {
      setIsReindexing(false);
    }
  };

  return (
    <PageShell showLanguageSwitcher={false}>
      <h1>Admin</h1>
      <p className="admin-subtitle">Document index health and questions handed to a department.</p>

      {error && <p className="admin-error">{error}</p>}

      <section className="admin-section">
        <h2>Index status</h2>
        {health ? (
          <div className="admin-health">
            <div>
              <span className="admin-health-label">Language model</span>
              <Badge tone={health.llm.enabled ? "success" : "neutral"}>
                {health.llm.enabled ? health.llm.model : "Off (extractive mode)"}
              </Badge>
            </div>
            <div>
              <span className="admin-health-label">Embedding model</span>
              <span>{health.index.embedding_model}</span>
            </div>
            {Object.entries(health.index.chunks).map(([domain, count]) => (
              <div key={domain}>
                <span className="admin-health-label">{domain} chunks</span>
                <span>{count}</span>
              </div>
            ))}
          </div>
        ) : (
          <Spinner label="Loading health" />
        )}

        <div className="admin-reindex-actions">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleReindex(false)}
            isLoading={isReindexing}
          >
            <RefreshCcw size={14} aria-hidden="true" />
            Sync changed documents
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleReindex(true)}
            isLoading={isReindexing}
          >
            Rebuild entire index
          </Button>
        </div>

        {reindexResult && (
          <p className="admin-reindex-result">
            {reindexResult.added.length} added, {reindexResult.updated.length} updated,{" "}
            {reindexResult.removed.length} removed, {reindexResult.unchanged.length} unchanged
            {Object.keys(reindexResult.errors).length > 0 &&
              ` — ${Object.keys(reindexResult.errors).length} failed`}
            . {reindexResult.chunks} chunks in the index.
          </p>
        )}
      </section>

      <section className="admin-section">
        <h2>Recent escalations</h2>
        <p className="admin-section-hint">
          Each row is a question the assistant would not answer on its own. Repeated topics point at
          a gap in the source documents.
        </p>
        {escalations === null ? (
          <Spinner label="Loading escalations" />
        ) : escalations.length === 0 ? (
          <p className="admin-empty">No escalations recorded yet.</p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Assistant</th>
                <th>Reason</th>
                <th>Routed to</th>
                <th>Question</th>
              </tr>
            </thead>
            <tbody>
              {escalations.map((row) => (
                <tr key={row.id}>
                  <td>{formatTimestamp(row.created_at)}</td>
                  <td>{row.assistant}</td>
                  <td>
                    <Badge tone={REASON_TONE[row.reason] ?? "neutral"}>
                      {row.reason.replaceAll("_", " ")}
                    </Badge>
                  </td>
                  <td>{row.department_id.replaceAll("_", " ")}</td>
                  <td className="admin-table-question">{row.question}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </PageShell>
  );
}
