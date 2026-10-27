import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AlertTriangle, Wrench } from "lucide-react";

import { EscalationCard } from "@/components/chat/EscalationCard";
import { SourceList } from "@/components/chat/SourceList";
import type { ChatResponse } from "@/types/api";

import "./MessageBubble.css";

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
  pending?: boolean;
  failed?: boolean;
}

const TOOL_LABELS: Record<string, string> = {
  get_my_profile: "Checked your profile",
  list_upcoming_drives: "Checked upcoming drives",
  check_eligibility: "Checked eligibility criteria",
};

export function MessageBubble({ message }: { message: DisplayMessage }) {
  if (message.role === "user") {
    return (
      <div className="message-row message-row-user">
        <div className="bubble bubble-user">{message.content}</div>
      </div>
    );
  }

  const response = message.response;
  const degraded = response?.degraded;

  return (
    <div className="message-row message-row-assistant">
      <div className="bubble bubble-assistant">
        {message.pending ? (
          <span className="bubble-typing" aria-label="Assistant is typing">
            <span />
            <span />
            <span />
          </span>
        ) : (
          <>
            {message.failed ? (
              <p className="bubble-error">
                <AlertTriangle size={15} aria-hidden="true" /> {message.content}
              </p>
            ) : (
              <>
                {degraded && (
                  <p className="bubble-notice">
                    <AlertTriangle size={13} aria-hidden="true" />
                    The assistant's language model is temporarily unavailable.
                  </p>
                )}
                <div className="bubble-markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                </div>
                {!!response?.tools_used.length && (
                  <p className="bubble-tools">
                    <Wrench size={12} aria-hidden="true" />
                    {response.tools_used.map((t) => TOOL_LABELS[t] ?? t).join(" · ")}
                  </p>
                )}
                {response?.escalation && <EscalationCard escalation={response.escalation} />}
                {response?.sources && <SourceList sources={response.sources} />}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
