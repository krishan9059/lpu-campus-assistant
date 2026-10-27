import { api } from "@/api/client";
import type {
  Assistant,
  ChatRequest,
  ChatResponse,
  Department,
  DrivesResponse,
  EscalationLogOut,
  HealthOut,
  ReindexResponse,
  TokenResponse,
} from "@/types/api";

export const endpoints = {
  health: () => api.get<HealthOut>("/health", { auth: false }),
  assistants: () => api.get<Assistant[]>("/assistants", { auth: false }),
  departments: (assistant: string) =>
    api.get<Department[]>(`/departments?assistant=${encodeURIComponent(assistant)}`, {
      auth: false,
    }),
  login: (regNo: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { reg_no: regNo, password }, { auth: false }),
  chat: (request: ChatRequest, signal?: AbortSignal) =>
    api.post<ChatResponse>("/chat", request, { signal }),
  drives: () => api.get<DrivesResponse>("/placement/drives"),
  adminEscalations: () => api.get<EscalationLogOut[]>("/admin/escalations"),
  adminReindex: (rebuild: boolean) =>
    api.post<ReindexResponse>(`/admin/reindex?rebuild=${rebuild}`),
};
