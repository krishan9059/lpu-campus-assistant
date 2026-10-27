"""Render evaluation results as Markdown."""

from __future__ import annotations

from datetime import datetime

from app.evaluation.metrics import Metrics
from app.evaluation.runner import CaseResult


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_report(
    sections: dict[str, tuple[Metrics, list[CaseResult]]],
    *,
    mode: str,
    embedding_model: str,
    llm_model: str | None,
    threshold: float,
    k: int,
) -> str:
    lines = [
        "# Evaluation report",
        "",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- Answer mode: {mode}" + (f" ({llm_model})" if llm_model else ""),
        f"- Embedding model: {embedding_model}",
        f"- Retrieval threshold: {threshold}",
        f"- Passages retrieved per question (k): {k}",
        "",
        "| Assistant | Questions | Hit@1 | Hit@k | MRR | Answer accuracy | Escalation accuracy | "
        "Escalation precision | Escalation recall | False escalations |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, (m, _) in sections.items():
        lines.append(
            f"| {name} | {m.evaluated} | {_pct(m.hit_at_1)} | {_pct(m.hit_at_k)} | {m.mrr:.3f} | "
            f"{_pct(m.answer_accuracy)} | {_pct(m.escalation_accuracy)} | "
            f"{_pct(m.escalation_precision)} | {_pct(m.escalation_recall)} | "
            f"{_pct(m.false_escalation_rate)} |"
        )
    skipped = sum(m.skipped for m, _ in sections.values())
    if skipped:
        lines += ["", f"{skipped} question(s) that need a language model were skipped."]

    for name, (_, results) in sections.items():
        failures = [
            r
            for r in results
            if not r.skipped
            and (
                r.escalated != r.case.should_escalate
                or r.correct is False
                or (r.case.expected_docs and r.hit_rank is None)
            )
        ]
        lines += ["", f"## {name}: cases to review ({len(failures)})", ""]
        if not failures:
            lines.append("None.")
            continue
        lines += [
            "| Id | Question | Expected | Got | Retrieval score | Doc rank |",
            "|---|---|---|---|---|---|",
        ]
        for r in failures:
            expected = "escalate" if r.case.should_escalate else "answer"
            rank = str(r.hit_rank) if r.hit_rank else "-"
            lines.append(
                f"| {r.case.id} | {r.case.question} | {expected} | {r.status} | "
                f"{r.best_score:.3f} | {rank} |"
            )
    return "\n".join(lines) + "\n"
