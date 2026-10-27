"""Suggest MIN_RETRIEVAL_SCORE for the current embedding model.

Similarity scores are not comparable between embedding models, so run this whenever the
model changes. It compares the best retrieval score of answerable questions with that of
questions that should not be answered, using the sets in data/eval/.
"""

from __future__ import annotations

import statistics

from app.bootstrap import prepare
from app.cli.evaluate import EVAL_DIR
from app.config import get_settings
from app.container import build_container
from app.evaluation.dataset import load_cases
from app.logging import configure_logging
from app.services.escalation import EscalationRouter

TARGET_RECALL = 0.95


def _describe(label: str, scores: list[float]) -> None:
    if not scores:
        print(f"  {label}: no questions")
        return
    print(
        f"  {label}: n={len(scores)} min={min(scores):.3f} "
        f"median={statistics.median(scores):.3f} max={max(scores):.3f}"
    )


def main() -> None:
    settings = get_settings()
    configure_logging("WARNING")
    container = build_container(settings, llm=None)
    try:
        prepare(container)
        router = EscalationRouter(container.directory)
        answerable: list[float] = []
        unanswerable: list[float] = []
        for spec in container.assistants.all():
            path = EVAL_DIR / f"{spec.id}.jsonl"
            if not path.exists():
                continue
            for case in load_cases(path):
                if case.requires_llm:
                    continue
                if case.should_escalate and router.detect_sensitive(
                    case.question, domain=spec.domain
                ):
                    continue  # handled before retrieval, so the score is irrelevant
                score = container.retriever.search(case.question, spec.domain).best_dense_score
                (unanswerable if case.should_escalate else answerable).append(score)
    finally:
        container.close()

    print(f"Embedding model: {container.embedder.name}")
    _describe("answerable  ", answerable)
    _describe("unanswerable", unanswerable)
    if not answerable:
        return

    ordered = sorted(answerable)
    cutoff = ordered[int((1 - TARGET_RECALL) * len(ordered))]
    rejected = sum(1 for s in unanswerable if s < cutoff)
    print(
        f"\nA threshold of {cutoff:.3f} lets {TARGET_RECALL:.0%} of answerable questions through "
        f"and stops {rejected} of {len(unanswerable)} unanswerable ones before the language model."
    )
    print(f"Current setting: {settings.effective_min_retrieval_score}")
    print(f"\nSuggested .env line:\nMIN_RETRIEVAL_SCORE={cutoff:.3f}")
    if unanswerable and max(unanswerable) >= min(answerable):
        print(
            "\nThe two groups overlap, so the language model has to make the final call for some "
            "questions. That is expected; keep the threshold low rather than high."
        )


if __name__ == "__main__":
    main()
