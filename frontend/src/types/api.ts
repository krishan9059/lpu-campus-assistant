// Mirrors the Pydantic schemas in backend/app/schemas/. Kept as one file since both
// sides are small; if this grows, generate it from /api/openapi.json instead.

export type UiLanguage = "auto" | "en" | "hi" | "pa";
export type AnswerLanguage = "en" | "hi" | "pa";

export interface LocalizedText {
  en: string;
  hi: string;
  pa: string;
}

export interface Assistant {
  id: string;
  domain: string;
  name: LocalizedText;
  tagline: LocalizedText;
  suggested_questions: Record<AnswerLanguage, string[]>;
  personalised: boolean;
}

export interface Department {
  id: string;
  name: string;
  description: string;
  email: string;
  phone: string;
  hours: string;
  url: string | null;
}

export type EscalationReason =
  | "no_relevant_source"
  | "model_not_found"
  | "ungrounded"
  | "sensitive_topic"
  | "policy_exception";

export interface Escalation {
  reason: EscalationReason;
  department: Department;
  additional: Department[];
}

export interface Source {
  id: number;
  title: string;
  section: string;
  page: number | null;
  effective_date: string | null;
  snippet: string;
  sample: boolean;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  assistant: string;
  message: string;
  language: UiLanguage;
  history: ChatTurn[];
}

export interface ChatResponse {
  answer: string;
  status: "answered" | "escalated" | "needs_sign_in";
  language: AnswerLanguage;
  mode: "generative" | "extractive";
  degraded: boolean;
  sources: Source[];
  escalation: Escalation | null;
  tools_used: string[];
  meta: { best_score: number; latency_ms: number; model: string | null };
}

export interface UserOut {
  reg_no: string;
  full_name: string;
  role: "student" | "admin";
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  user: UserOut;
}

export interface EligibilityCheck {
  code: string;
  passed: boolean;
  required: string;
  actual: string;
}

export interface Eligibility {
  eligible: boolean;
  registration_open: boolean;
  checks: EligibilityCheck[];
}

export interface Drive {
  id: number;
  company: string;
  role_title: string;
  ctc_lpa: number;
  category: "regular" | "dream" | "super_dream";
  min_cgpa: number;
  max_active_backlogs: number;
  allowed_branches: string[];
  mode: string;
  location: string;
  drive_date: string;
  registration_deadline: string;
  description: string;
  eligibility: Eligibility | null;
}

export interface StudentOut {
  reg_no: string;
  full_name: string;
  program: string;
  branch: string;
  batch: number;
  cgpa: number;
  active_backlogs: number;
  highest_offer_lpa: number | null;
}

export interface DrivesResponse {
  student: StudentOut | null;
  drives: Drive[];
}

export interface HealthOut {
  status: "ok" | "degraded";
  version: string;
  environment: string;
  llm: { enabled: boolean; model: string | null };
  index: { embedding_model: string; chunks: Record<string, number> };
}

export interface EscalationLogOut {
  id: number;
  created_at: string;
  assistant: string;
  reason: string;
  department_id: string;
  language: string;
  question: string;
}

export interface ReindexResponse {
  added: string[];
  updated: string[];
  removed: string[];
  unchanged: string[];
  errors: Record<string, string>;
  chunks: number;
}
