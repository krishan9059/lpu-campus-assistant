from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Language = Literal["en", "hi", "pa"]
EscalationReason = Literal[
    "no_relevant_source", "model_not_found", "ungrounded", "sensitive_topic", "policy_exception"
]


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    assistant: str = Field(min_length=1, max_length=32)
    message: str = Field(min_length=1, max_length=1000)
    language: Literal["auto", "en", "hi", "pa"] = "auto"
    history: list[Turn] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be blank")
        return value


class SourceOut(BaseModel):
    id: int
    title: str
    section: str
    page: int | None
    effective_date: date | None
    snippet: str
    sample: bool


class DepartmentOut(BaseModel):
    id: str
    name: str
    description: str
    email: str
    phone: str
    hours: str
    url: str | None = None


class EscalationOut(BaseModel):
    reason: EscalationReason
    department: DepartmentOut
    additional: list[DepartmentOut] = Field(default_factory=list)


class ResponseMeta(BaseModel):
    best_score: float
    latency_ms: int
    model: str | None


class ChatResponse(BaseModel):
    answer: str
    status: Literal["answered", "escalated", "needs_sign_in"]
    language: Language
    mode: Literal["generative", "extractive"]
    degraded: bool = False
    sources: list[SourceOut]
    escalation: EscalationOut | None
    tools_used: list[str]
    meta: ResponseMeta


class AssistantOut(BaseModel):
    id: str
    domain: str
    name: dict[str, str]
    tagline: dict[str, str]
    suggested_questions: dict[str, list[str]]
    personalised: bool
