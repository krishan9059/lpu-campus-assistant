"""One chat turn: safety routing, retrieval, grounded generation and escalation."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.config import Settings
from app.core.clock import today_in
from app.core.errors import IndexNotReadyError
from app.db.models import EscalationLog, User
from app.llm.base import ChatMessage, LLMClient, LLMError
from app.prompts import load_prompt
from app.rag.retriever import HybridRetriever
from app.rag.types import RetrievedChunk, SearchResult
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    DepartmentOut,
    EscalationOut,
    ResponseMeta,
    SourceOut,
    Turn,
)
from app.services.assistants import AssistantRegistry, AssistantSpec
from app.services.escalation import Department, EscalationRouter
from app.services.language import Language, instruction_for, resolve_language
from app.services.messages import MessageCatalog
from app.services.placement import PlacementService
from app.services.tools import PlacementToolbox

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 6
MAX_TOOL_ROUNDS = 3
EXTRACTIVE_PASSAGES = 2

_NOT_FOUND = re.compile(r"^\W*NOT_FOUND\b", re.IGNORECASE)
_NEEDS_SIGN_IN = re.compile(r"^\W*NEEDS_SIGN_IN\b", re.IGNORECASE)
_CITATION_GROUP = re.compile(r"\[(\d{1,2}(?:\s*[,;]\s*\d{1,2})*)\]")
_ANY_CITATION = re.compile(r"\s*\[\d{1,2}\]")

_SIGNED_IN_NOTE = "The user is signed in as a student, so you may call the tools."
_ANONYMOUS_NOTE = (
    "The user is not signed in and tools are unavailable. If the question depends on their own "
    "CGPA, backlogs, offers or eligibility, reply with exactly NEEDS_SIGN_IN and nothing else."
)


@dataclass
class _Turn:
    request: ChatRequest
    assistant: AssistantSpec
    language: Language
    user: User | None
    db: Session
    started: float


def normalise_citations(text: str, max_id: int) -> tuple[str, set[int]]:
    """Rewrite ``[1, 2]`` as ``[1][2]`` and drop markers that point at no passage."""
    cited: set[int] = set()

    def replace(match: re.Match[str]) -> str:
        ids = [int(n) for n in re.split(r"[,;]", match.group(1))]
        valid = [i for i in ids if 1 <= i <= max_id]
        cited.update(valid)
        return "".join(f"[{i}]" for i in valid)

    return _CITATION_GROUP.sub(replace, text), cited


def build_retrieval_query(message: str, history: list[Turn]) -> str:
    """Very short follow-ups ("and for ECE?") borrow the previous question for retrieval."""
    if len(message.split()) <= 6:
        previous = next((t.content for t in reversed(history) if t.role == "user"), None)
        if previous:
            return f"{previous}\n{message}"
    return message


def format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no passages were retrieved)"
    blocks = []
    for index, retrieved in enumerate(chunks, start=1):
        chunk = retrieved.chunk
        header = f"[{index}] {chunk.title}" + (f" / {chunk.section}" if chunk.section else "")
        details = []
        if chunk.effective_date:
            details.append(f"effective {chunk.effective_date}")
        if chunk.page:
            details.append(f"page {chunk.page}")
        if details:
            header += f" ({', '.join(details)})"
        blocks.append(f"{header}\n{chunk.text}")
    return "\n\n".join(blocks)


def excerpt(text: str, limit: int = 600) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    window = text[:limit]
    boundary = max(window.rfind(". "), window.rfind("\n"))
    return (window[: boundary + 1] if boundary > limit // 2 else window.rstrip()) + " ..."


def _department_out(department: Department) -> DepartmentOut:
    return DepartmentOut(
        id=department.id,
        name=department.name,
        description=department.description,
        email=department.email,
        phone=department.phone,
        hours=department.hours,
        url=department.url,
    )


class ChatService:
    def __init__(
        self,
        *,
        settings: Settings,
        assistants: AssistantRegistry,
        retriever: HybridRetriever,
        llm: LLMClient | None,
        router: EscalationRouter,
        messages: MessageCatalog,
    ) -> None:
        self._settings = settings
        self._assistants = assistants
        self._retriever = retriever
        self._llm = llm
        self._router = router
        self._messages = messages

    @property
    def mode(self) -> str:
        return "generative" if self._llm else "extractive"

    def answer(self, request: ChatRequest, *, user: User | None, db: Session) -> ChatResponse:
        assistant = self._assistants.require(request.assistant)
        turn = _Turn(
            request=request,
            assistant=assistant,
            language=resolve_language(request.language, request.message),
            user=user,
            db=db,
            started=time.perf_counter(),
        )
        response = self._respond(turn)
        logger.info(
            "chat assistant=%s status=%s mode=%s lang=%s score=%.3f tools=%s ms=%d",
            assistant.id,
            response.status,
            response.mode,
            response.language,
            response.meta.best_score,
            ",".join(response.tools_used) or "-",
            response.meta.latency_ms,
        )
        return response

    def _respond(self, turn: _Turn) -> ChatResponse:
        sensitive = self._router.detect_sensitive(
            turn.request.message, domain=turn.assistant.domain
        )
        if sensitive:
            return self._escalate(
                turn,
                reason=sensitive.reason,
                message_key=sensitive.message_key,
                department=sensitive.department,
                additional=sensitive.additional,
            )

        query = build_retrieval_query(turn.request.message, turn.request.history)
        try:
            search = self._retriever.search(query, turn.assistant.domain)
        except Exception as exc:
            logger.exception("Retrieval failed")
            raise IndexNotReadyError(
                "The search index is not ready yet. Try again shortly."
            ) from exc

        # Assistants with tools can answer from live data even when no passage matches,
        # so the model decides instead of the retrieval score.
        model_decides = turn.assistant.tools_enabled and self._llm is not None
        if (
            not model_decides
            and search.best_dense_score < self._settings.effective_min_retrieval_score
        ):
            return self._escalate_unanswerable(turn, "no_relevant_source", search)

        if self._llm is None:
            return self._extractive(turn, search, degraded=False)

        toolbox = self._toolbox(turn)
        try:
            text, tools_used = self._generate(turn, search.chunks, toolbox)
        except LLMError as exc:
            logger.warning("Language model unavailable, falling back to passages: %s", exc)
            return self._extractive(turn, search, degraded=True)

        if _NEEDS_SIGN_IN.match(text):
            if toolbox is None:
                return self._build(
                    turn,
                    search,
                    status="needs_sign_in",
                    answer=self._messages.get("sign_in_required", turn.language),
                )
            return self._escalate_unanswerable(turn, "model_not_found", search)
        if not text or _NOT_FOUND.match(text):
            return self._escalate_unanswerable(turn, "model_not_found", search)

        answer, cited = normalise_citations(text, len(search.chunks))
        if self._settings.require_citations and not cited and not tools_used:
            return self._escalate_unanswerable(turn, "ungrounded", search)
        return self._build(
            turn, search, status="answered", answer=answer, cited=cited, tools_used=tools_used
        )

    def _toolbox(self, turn: _Turn) -> PlacementToolbox | None:
        user = turn.user
        if not turn.assistant.tools_enabled or user is None or user.profile is None:
            return None
        service = PlacementService(
            turn.db,
            today=today_in(self._settings.timezone),
            offer_multiplier=self._settings.placement_offer_multiplier,
        )
        return PlacementToolbox(service, user, user.profile)

    def _generate(
        self, turn: _Turn, chunks: list[RetrievedChunk], toolbox: PlacementToolbox | None
    ) -> tuple[str, list[str]]:
        assert self._llm is not None
        system = load_prompt(turn.assistant.prompt).format(
            language_instruction=instruction_for(turn.request.language),
            auth_note=_SIGNED_IN_NOTE if toolbox else _ANONYMOUS_NOTE,
            context=format_context(chunks),
        )
        messages = [ChatMessage("system", system)]
        for past in turn.request.history[-MAX_HISTORY_MESSAGES:]:
            content = (
                _ANY_CITATION.sub("", past.content) if past.role == "assistant" else past.content
            )
            messages.append(ChatMessage(past.role, content))
        messages.append(ChatMessage("user", turn.request.message))

        specs = toolbox.specs() if toolbox else None
        used: list[str] = []
        options = {
            "temperature": self._settings.llm_temperature,
            "max_tokens": self._settings.llm_max_tokens,
        }
        for _ in range(MAX_TOOL_ROUNDS):
            reply = self._llm.complete(messages, tools=specs, **options)
            if not reply.tool_calls:
                return reply.content, list(dict.fromkeys(used))
            messages.append(
                ChatMessage("assistant", reply.content or None, tool_calls=reply.tool_calls)
            )
            for call in reply.tool_calls:
                result = (
                    toolbox.execute(call.name, call.arguments)
                    if toolbox
                    else {"error": "Tools are unavailable."}
                )
                used.append(call.name)
                messages.append(
                    ChatMessage(
                        "tool",
                        json.dumps(result, default=str),
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )
        final = self._llm.complete(messages, tools=None, **options)
        return final.content, list(dict.fromkeys(used))

    def _extractive(self, turn: _Turn, search: SearchResult, *, degraded: bool) -> ChatResponse:
        header = self._messages.get(
            "degraded_notice" if degraded else "extractive_notice", turn.language
        )
        shown = search.chunks[:EXTRACTIVE_PASSAGES]
        parts = [header]
        for index, retrieved in enumerate(shown, start=1):
            chunk = retrieved.chunk
            label = chunk.title + (f" - {chunk.section}" if chunk.section else "")
            parts.append(f"**{label}** [{index}]\n{excerpt(chunk.text)}")
        return self._build(
            turn,
            search,
            status="answered",
            answer="\n\n".join(parts),
            cited=set(range(1, len(shown) + 1)),
            degraded=degraded,
            mode="extractive",
        )

    def _build(
        self,
        turn: _Turn,
        search: SearchResult,
        *,
        status: str,
        answer: str,
        cited: set[int] | None = None,
        tools_used: list[str] | None = None,
        degraded: bool = False,
        mode: str | None = None,
    ) -> ChatResponse:
        sources = []
        for index, retrieved in enumerate(search.chunks, start=1):
            if index not in (cited or set()):
                continue
            chunk = retrieved.chunk
            sources.append(
                SourceOut(
                    id=index,
                    title=chunk.title,
                    section=chunk.section,
                    page=chunk.page,
                    effective_date=date.fromisoformat(chunk.effective_date)
                    if chunk.effective_date
                    else None,
                    snippet=excerpt(chunk.text, 280),
                    sample=chunk.sample,
                )
            )
        return ChatResponse(
            answer=answer,
            status=status,  # type: ignore[arg-type]
            language=turn.language,
            mode=mode or self.mode,  # type: ignore[arg-type]
            degraded=degraded,
            sources=sources,
            escalation=None,
            tools_used=tools_used or [],
            meta=self._meta(turn, search.best_dense_score),
        )

    def _escalate_unanswerable(
        self, turn: _Turn, reason: str, search: SearchResult
    ) -> ChatResponse:
        department = self._router.route(turn.request.message, domain=turn.assistant.domain)
        return self._escalate(
            turn,
            reason=reason,
            message_key="no_answer",
            department=department,
            best_score=search.best_dense_score,
        )

    def _escalate(
        self,
        turn: _Turn,
        *,
        reason: str,
        message_key: str,
        department: Department,
        additional: tuple[Department, ...] = (),
        best_score: float = 0.0,
    ) -> ChatResponse:
        helpline = additional[0].phone if additional else ""
        text = self._messages.get(
            message_key, turn.language, department=department.name, helpline=helpline
        )
        self._log_escalation(turn, reason, department)
        return ChatResponse(
            answer=text,
            status="escalated",
            language=turn.language,
            mode=self.mode,  # type: ignore[arg-type]
            sources=[],
            escalation=EscalationOut(
                reason=reason,  # type: ignore[arg-type]
                department=_department_out(department),
                additional=[_department_out(d) for d in additional],
            ),
            tools_used=[],
            meta=self._meta(turn, best_score),
        )

    def _meta(self, turn: _Turn, best_score: float) -> ResponseMeta:
        return ResponseMeta(
            best_score=round(best_score, 4),
            latency_ms=int((time.perf_counter() - turn.started) * 1000),
            model=self._llm.model if self._llm else None,
        )

    def _log_escalation(self, turn: _Turn, reason: str, department: Department) -> None:
        try:
            turn.db.add(
                EscalationLog(
                    assistant=turn.assistant.id,
                    reason=reason,
                    department_id=department.id,
                    language=turn.language,
                    question=turn.request.message[:500],
                    user_id=turn.user.id if turn.user else None,
                )
            )
            turn.db.commit()
        except Exception:
            turn.db.rollback()
            logger.exception("Could not record escalation")
