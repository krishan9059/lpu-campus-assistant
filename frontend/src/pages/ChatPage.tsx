import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import { endpoints } from "@/api/endpoints";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { Composer } from "@/components/chat/Composer";
import { SuggestedQuestions } from "@/components/chat/SuggestedQuestions";
import { PageShell } from "@/components/layout/PageShell";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { useChat } from "@/hooks/useChat";
import type { Assistant, AnswerLanguage } from "@/types/api";

import "./ChatPage.css";

function suggestedLanguage(uiLanguage: string): AnswerLanguage {
  return uiLanguage === "hi" || uiLanguage === "pa" ? uiLanguage : "en";
}

export function ChatPage() {
  const { assistantId = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { language } = useLanguage();
  const [assistant, setAssistant] = useState<Assistant | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const { messages, isSending, send } = useChat(assistantId, language);

  useEffect(() => {
    let cancelled = false;
    endpoints
      .assistants()
      .then((all) => {
        if (cancelled) return;
        const match = all.find((a) => a.id === assistantId);
        if (match) setAssistant(match);
        else setNotFound(true);
      })
      .catch(() => {
        if (!cancelled) setNotFound(true);
      });
    return () => {
      cancelled = true;
    };
  }, [assistantId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = (text?: string) => {
    const value = text ?? draft;
    setDraft("");
    void send(value);
  };

  if (notFound) {
    return (
      <PageShell>
        <p>That assistant does not exist.</p>
        <button type="button" onClick={() => navigate("/")}>
          Back to assistants
        </button>
      </PageShell>
    );
  }

  const lang = suggestedLanguage(language);
  const suggestions = assistant?.suggested_questions[lang] ?? [];
  const showSuggestions = messages.length === 0 && suggestions.length > 0;
  const showSignInNote = assistant?.personalised && !user;

  return (
    <PageShell fullBleed>
      <div className="chat-page">
        <div className="chat-header">
          <button type="button" className="chat-back" onClick={() => navigate("/")}>
            <ArrowLeft size={16} aria-hidden="true" />
            <span className="visually-hidden">Back to assistants</span>
          </button>
          <div>
            <h1>{assistant?.name[lang] ?? "Loading…"}</h1>
            {assistant && <p className="chat-tagline">{assistant.tagline[lang]}</p>}
          </div>
        </div>

        <div className="chat-scroll" ref={scrollRef}>
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-empty">
                <p>
                  {assistant
                    ? `Ask ${assistant.name[lang]} anything. Answers are grounded in the official documents and cite their source.`
                    : ""}
                </p>
                {showSignInNote && (
                  <button
                    type="button"
                    className="chat-signin-note"
                    onClick={() => navigate("/sign-in")}
                  >
                    Sign in to get answers based on your own placement record
                  </button>
                )}
              </div>
            )}
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
        </div>

        <div className="chat-footer">
          {showSuggestions && <SuggestedQuestions questions={suggestions} onSelect={handleSend} />}
          <Composer
            value={draft}
            onChange={setDraft}
            onSubmit={() => handleSend()}
            disabled={isSending}
            placeholder={assistant ? `Message ${assistant.name[lang]}…` : "Message the assistant…"}
          />
          <p className="chat-disclaimer">
            Answers are generated from official documents and may be incomplete. Verify anything
            important with the department shown.
          </p>
        </div>
      </div>
    </PageShell>
  );
}
