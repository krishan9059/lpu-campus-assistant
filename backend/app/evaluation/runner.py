"""Run evaluation cases against the live retrieval and chat pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.container import Container
from app.db.models import User
from app.evaluation.dataset import EvalCase
from app.schemas.chat import ChatRequest


@dataclass
class CaseResult:
    case: EvalCase
    skipped: bool = False
    best_score: float = 0.0
    hit_rank: int | None = None  # 1-based rank of the first expected document in the top-k
    escalated: bool = False
    status: str = ""
    correct: bool | None = None  # answerable cases only
    answer: str = ""


def contains_all(answer: str, must_include: tuple[str, ...]) -> bool:
    text = answer.casefold()
    return all(
        any(option.strip().casefold() in text for option in item.split("|"))
        for item in must_include
    )


def run_cases(
    container: Container, assistant_id: str, cases: list[EvalCase], *, use_llm: bool
) -> list[CaseResult]:
    spec = container.assistants.require(assistant_id)
    results: list[CaseResult] = []
    with container.session_factory() as db:
        for case in cases:
            if case.requires_llm and not use_llm:
                results.append(CaseResult(case=case, skipped=True))
                continue

            search = container.retriever.search(case.question, spec.domain)
            hit_rank = next(
                (i for i, r in enumerate(search.chunks, 1) if r.chunk.doc_id in case.expected_docs),
                None,
            )
            user = (
                db.scalar(select(User).where(User.reg_no == case.as_user)) if case.as_user else None
            )
            response = container.chat.answer(
                ChatRequest(assistant=assistant_id, message=case.question, language=case.language),
                user=user,
                db=db,
            )
            escalated = response.status == "escalated"
            results.append(
                CaseResult(
                    case=case,
                    best_score=search.best_dense_score,
                    hit_rank=hit_rank,
                    escalated=escalated,
                    status=response.status,
                    correct=(
                        None
                        if case.should_escalate
                        else (not escalated and contains_all(response.answer, case.must_include))
                    ),
                    answer=response.answer,
                )
            )
    return results
