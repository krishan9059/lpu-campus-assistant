import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import type { DisplayMessage } from "@/components/chat/MessageBubble";
import type { ChatTurn, UiLanguage } from "@/types/api";

const MAX_HISTORY_TURNS = 20;

function makeId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Chat state for one assistant: sending a message appends the user turn immediately, then
 * replaces a pending placeholder with the real response (or an inline error) once it lands. */
export function useChat(assistantId: string, language: UiLanguage) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setMessages([]);
    abortRef.current?.abort();
    setIsSending(false);
  }, [assistantId]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isSending) return;

      const history: ChatTurn[] = messages
        .filter((m) => !m.pending && !m.failed)
        .slice(-MAX_HISTORY_TURNS)
        .map((m) => ({ role: m.role, content: m.content }));

      const userMessage: DisplayMessage = { id: makeId(), role: "user", content: trimmed };
      const pendingId = makeId();
      setMessages((prev) => [
        ...prev,
        userMessage,
        { id: pendingId, role: "assistant", content: "", pending: true },
      ]);
      setIsSending(true);

      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const response = await endpoints.chat(
          { assistant: assistantId, message: trimmed, language, history },
          controller.signal,
        );
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingId
              ? { id: pendingId, role: "assistant", content: response.answer, response }
              : m,
          ),
        );
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        const detail =
          err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingId
              ? { id: pendingId, role: "assistant", content: detail, failed: true }
              : m,
          ),
        );
      } finally {
        setIsSending(false);
      }
    },
    [assistantId, language, messages, isSending],
  );

  return { messages, isSending, send };
}
