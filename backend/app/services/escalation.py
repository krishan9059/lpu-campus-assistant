"""Department directory and rules for routing questions the assistant should not answer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


def _pattern(keyword: str) -> re.Pattern[str]:
    # Match at the start of a word so "attend" also matches "attendance".
    return re.compile(r"(?<!\w)" + re.escape(keyword.casefold()))


@dataclass(frozen=True)
class Department:
    id: str
    name: str
    description: str
    email: str
    phone: str
    hours: str
    url: str | None
    domains: tuple[str, ...]
    patterns: tuple[re.Pattern[str], ...] = field(default=(), repr=False, compare=False)


@dataclass(frozen=True)
class SensitiveRule:
    id: str
    reason: str
    message_key: str
    department_id: str
    additional_ids: tuple[str, ...]
    domains: tuple[str, ...]
    patterns: tuple[re.Pattern[str], ...] = field(repr=False, compare=False)


@dataclass(frozen=True)
class SensitiveMatch:
    reason: str
    message_key: str
    department: Department
    additional: tuple[Department, ...]


class DepartmentDirectory:
    def __init__(
        self,
        departments: list[Department],
        defaults: dict[str, str],
        rules: list[SensitiveRule],
    ) -> None:
        self._by_id = {d.id: d for d in departments}
        self._defaults = defaults
        self.rules = rules

    @classmethod
    def load(cls, path: Path) -> DepartmentDirectory:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        departments = [
            Department(
                id=item["id"],
                name=item["name"],
                description=item.get("description", ""),
                email=item.get("email", ""),
                phone=item.get("phone", ""),
                hours=item.get("hours", ""),
                url=item.get("url"),
                domains=tuple(item.get("domains", [])),
                patterns=tuple(_pattern(k) for k in item.get("keywords", [])),
            )
            for item in raw["departments"]
        ]
        rules = [
            SensitiveRule(
                id=item["id"],
                reason=item["reason"],
                message_key=item["message_key"],
                department_id=item["department"],
                additional_ids=tuple(item.get("additional", [])),
                domains=tuple(item.get("domains", [])),
                patterns=tuple(_pattern(k) for k in item["keywords"]),
            )
            for item in raw.get("sensitive", [])
        ]
        return cls(departments, raw["default_department"], rules)

    def get(self, department_id: str) -> Department:
        return self._by_id[department_id]

    def all(self) -> list[Department]:
        return list(self._by_id.values())

    def for_domain(self, domain: str) -> list[Department]:
        return [d for d in self._by_id.values() if domain in d.domains]

    def default_for(self, domain: str) -> Department:
        return self._by_id[self._defaults[domain]]


class EscalationRouter:
    def __init__(self, directory: DepartmentDirectory) -> None:
        self._directory = directory

    def route(self, message: str, *, domain: str) -> Department:
        """Pick the department whose keywords best match, else the domain's default desk."""
        text = message.casefold()
        best, best_hits = None, 0
        for department in self._directory.for_domain(domain):
            hits = sum(1 for pattern in department.patterns if pattern.search(text))
            if hits > best_hits:
                best, best_hits = department, hits
        return best or self._directory.default_for(domain)

    def detect_sensitive(self, message: str, *, domain: str) -> SensitiveMatch | None:
        text = message.casefold()
        for rule in self._directory.rules:
            if domain not in rule.domains:
                continue
            if any(pattern.search(text) for pattern in rule.patterns):
                return SensitiveMatch(
                    reason=rule.reason,
                    message_key=rule.message_key,
                    department=self._directory.get(rule.department_id),
                    additional=tuple(self._directory.get(i) for i in rule.additional_ids),
                )
        return None
