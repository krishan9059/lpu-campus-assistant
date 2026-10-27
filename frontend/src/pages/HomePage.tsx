import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Briefcase, GraduationCap } from "lucide-react";

import { endpoints } from "@/api/endpoints";
import { ApiError } from "@/api/client";
import { PageShell } from "@/components/layout/PageShell";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/context/AuthContext";
import type { Assistant, AnswerLanguage } from "@/types/api";

import "./HomePage.css";

const ICONS: Record<string, typeof GraduationCap> = {
  university: GraduationCap,
  placement: Briefcase,
};

function pickLanguage(record: Record<AnswerLanguage, string[]>): AnswerLanguage {
  const browser = navigator.language.slice(0, 2);
  if ((browser === "hi" || browser === "pa") && record[browser]?.length) return browser;
  return "en";
}

export function HomePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [assistants, setAssistants] = useState<Assistant[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    endpoints
      .assistants()
      .then((data) => {
        if (!cancelled) setAssistants(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load the assistants.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <PageShell>
      <section className="home-intro">
        <h1>What do you need help with?</h1>
        <p>
          Ask about attendance, fees, hostels and exams, or check placement policy and your own
          eligibility. Every answer points to the official document it came from.
        </p>
      </section>

      {error && <p className="home-error">{error}</p>}
      {!assistants && !error && (
        <div className="home-loading">
          <Spinner label="Loading assistants" />
        </div>
      )}

      <div className="home-grid">
        {assistants?.map((assistant) => {
          const Icon = ICONS[assistant.domain] ?? GraduationCap;
          const lang = pickLanguage(assistant.suggested_questions);
          const questions = assistant.suggested_questions[lang]?.slice(0, 3) ?? [];
          return (
            <button
              key={assistant.id}
              type="button"
              className="assistant-card"
              onClick={() => navigate(`/chat/${assistant.id}`)}
            >
              <span className="assistant-card-icon">
                <Icon size={22} aria-hidden="true" />
              </span>
              <h2>{assistant.name[lang]}</h2>
              <p className="assistant-card-tagline">{assistant.tagline[lang]}</p>
              {assistant.personalised && !user && (
                <p className="assistant-card-note">Sign in for answers based on your own record</p>
              )}
              <ul className="assistant-card-questions">
                {questions.map((question) => (
                  <li key={question}>{question}</li>
                ))}
              </ul>
              <span className="assistant-card-cta">
                Start chatting <ArrowRight size={15} aria-hidden="true" />
              </span>
            </button>
          );
        })}
      </div>
    </PageShell>
  );
}
