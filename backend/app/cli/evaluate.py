"""Measure retrieval and answer quality on the question sets in data/eval/.

    python -m app.cli.evaluate                      # both assistants
    python -m app.cli.evaluate --assistant placement --no-llm

Without a language model the run measures the passages the assistant would show, and
questions that need tool calls are skipped. The report states which mode produced it.
"""

from __future__ import annotations

import argparse
from datetime import datetime

from app.bootstrap import prepare
from app.config import BACKEND_DIR, get_settings
from app.container import build_container
from app.evaluation.dataset import load_cases
from app.evaluation.metrics import compute_metrics
from app.evaluation.report import render_report
from app.evaluation.runner import run_cases
from app.logging import configure_logging

EVAL_DIR = BACKEND_DIR / "data" / "eval"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--assistant", choices=["all", "university", "placement"], default="all")
    parser.add_argument(
        "--no-llm", action="store_true", help="ignore the configured language model"
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging("WARNING")
    container = build_container(settings, llm=None) if args.no_llm else build_container(settings)
    try:
        prepare(container)
        use_llm = container.llm is not None
        names = (
            [a.id for a in container.assistants.all()]
            if args.assistant == "all"
            else [args.assistant]
        )
        sections = {}
        for name in names:
            path = EVAL_DIR / f"{name}.jsonl"
            if not path.exists():
                print(f"No question set for '{name}' at {path}")
                continue
            results = run_cases(container, name, load_cases(path), use_llm=use_llm)
            sections[name] = (compute_metrics(results), results)

        report = render_report(
            sections,
            mode="generative" if use_llm else "extractive (no language model)",
            embedding_model=container.embedder.name,
            llm_model=container.llm.model if container.llm else None,
            threshold=settings.effective_min_retrieval_score,
            k=settings.retrieval_top_k,
        )
    finally:
        container.close()

    out_dir = BACKEND_DIR / "var" / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
