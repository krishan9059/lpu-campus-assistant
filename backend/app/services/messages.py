"""Localised, system-generated messages (escalations, notices), kept in YAML."""

from __future__ import annotations

from pathlib import Path

import yaml


class MessageCatalog:
    def __init__(self, catalog: dict[str, dict[str, str]]) -> None:
        self._catalog = catalog

    @classmethod
    def load(cls, path: Path) -> MessageCatalog:
        return cls(yaml.safe_load(path.read_text(encoding="utf-8")) or {})

    def get(self, key: str, language: str, **values: str) -> str:
        entry = self._catalog[key]
        template = entry.get(language) or entry["en"]
        return template.format(**values) if values else template
