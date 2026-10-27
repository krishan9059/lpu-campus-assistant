"""Aggregate metrics for evaluation runs."""

from __future__ import annotations

from dataclasses import dataclass

from app.evaluation.runner import CaseResult


@dataclass(frozen=True)
class Metrics:
    evaluated: int
    skipped: int
    retrieval_cases: int
    hit_at_1: float
    hit_at_k: float
    mrr: float
    answerable: int
    answer_accuracy: float
    escalation_accuracy: float
    escalation_precision: float
    escalation_recall: float
    false_escalation_rate: float


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def compute_metrics(results: list[CaseResult]) -> Metrics:
    done = [r for r in results if not r.skipped]
    retrieval = [r for r in done if r.case.expected_docs]
    answerable = [r for r in done if r.case.answerable]

    true_positive = sum(1 for r in done if r.case.should_escalate and r.escalated)
    false_positive = sum(1 for r in done if not r.case.should_escalate and r.escalated)
    false_negative = sum(1 for r in done if r.case.should_escalate and not r.escalated)

    return Metrics(
        evaluated=len(done),
        skipped=len(results) - len(done),
        retrieval_cases=len(retrieval),
        hit_at_1=_ratio(sum(1 for r in retrieval if r.hit_rank == 1), len(retrieval)),
        hit_at_k=_ratio(sum(1 for r in retrieval if r.hit_rank is not None), len(retrieval)),
        mrr=_ratio(sum(1 / r.hit_rank for r in retrieval if r.hit_rank), len(retrieval)),
        answerable=len(answerable),
        answer_accuracy=_ratio(sum(1 for r in answerable if r.correct), len(answerable)),
        escalation_accuracy=_ratio(
            sum(1 for r in done if r.escalated == r.case.should_escalate), len(done)
        ),
        escalation_precision=_ratio(true_positive, true_positive + false_positive),
        escalation_recall=_ratio(true_positive, true_positive + false_negative),
        false_escalation_rate=_ratio(false_positive, len(answerable)),
    )
