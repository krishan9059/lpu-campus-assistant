"""Evaluation question sets (JSON Lines)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EvalCase:
    id: str
    question: str
    language: str = "auto"
    expected_docs: tuple[str, ...] = ()
    must_include: tuple[str, ...] = ()  # every item must appear; "a|b" accepts either
    should_escalate: bool = False
    as_user: str | None = None
    requires_llm: bool = False
    tags: tuple[str, ...] = field(default=())

    @property
    def answerable(self) -> bool:
        return not self.should_escalate


def load_cases(path: Path) -> list[EvalCase]:
    cases = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{number}: {exc}") from exc
            cases.append(
                EvalCase(
                    id=raw["id"],
                    question=raw["question"],
                    language=raw.get("language", "auto"),
                    expected_docs=tuple(raw.get("expected_docs", ())),
                    must_include=tuple(raw.get("must_include", ())),
                    should_escalate=bool(raw.get("should_escalate", False)),
                    as_user=raw.get("as_user"),
                    requires_llm=bool(raw.get("requires_llm", False)),
                )
            )
    return cases
