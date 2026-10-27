from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class IndexStatus(BaseModel):
    embedding_model: str
    chunks: dict[str, int]


class LLMStatus(BaseModel):
    enabled: bool
    model: str | None


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    environment: str
    llm: LLMStatus
    index: IndexStatus


class ReindexResponse(BaseModel):
    added: list[str]
    updated: list[str]
    removed: list[str]
    unchanged: list[str]
    errors: dict[str, str]
    chunks: int


class EscalationLogOut(BaseModel):
    id: int
    created_at: datetime
    assistant: str
    reason: str
    department_id: str
    language: str
    question: str
