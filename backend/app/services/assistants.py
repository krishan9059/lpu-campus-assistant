"""Assistant definitions, loaded from ``data/config/assistants.yaml``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.core.errors import NotFoundError


@dataclass(frozen=True)
class AssistantSpec:
    id: str
    domain: str
    prompt: str
    tools_enabled: bool
    names: dict[str, str]
    taglines: dict[str, str]
    suggested_questions: dict[str, list[str]]


class AssistantRegistry:
    def __init__(self, specs: list[AssistantSpec]) -> None:
        self._specs = {s.id: s for s in specs}

    @classmethod
    def load(cls, path: Path, enabled: list[str]) -> AssistantRegistry:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        specs = [
            AssistantSpec(
                id=item["id"],
                domain=item["domain"],
                prompt=item["prompt"],
                tools_enabled=bool(item.get("tools", False)),
                names=item["name"],
                taglines=item["tagline"],
                suggested_questions=item["suggested_questions"],
            )
            for item in raw["assistants"]
            if item["id"] in enabled
        ]
        if not specs:
            raise ValueError(f"No assistants enabled. Known ids in {path.name}, enabled={enabled}")
        return cls(specs)

    def all(self) -> list[AssistantSpec]:
        return list(self._specs.values())

    def require(self, assistant_id: str) -> AssistantSpec:
        try:
            return self._specs[assistant_id]
        except KeyError:
            raise NotFoundError(f"Unknown assistant '{assistant_id}'") from None
