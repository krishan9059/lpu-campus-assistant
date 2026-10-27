"""Placement rules: which drives a student can attend, and why not."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PlacementDrive, StudentProfile, User


@dataclass(frozen=True)
class Check:
    code: str  # cgpa | backlogs | branch | offer_rule
    passed: bool
    required: str
    actual: str

    @property
    def detail(self) -> str:
        verdict = "met" if self.passed else "not met"
        return f"{self.code}: required {self.required}, student has {self.actual} ({verdict})"


@dataclass(frozen=True)
class Eligibility:
    eligible: bool
    registration_open: bool
    checks: tuple[Check, ...]


def _fmt(value: float) -> str:
    return f"{value:g}"


def evaluate_eligibility(
    student: StudentProfile,
    drive: PlacementDrive,
    *,
    today: date,
    offer_multiplier: float,
) -> Eligibility:
    """Apply the drive criteria and the one-offer policy to a student's record."""
    allowed = {b.upper() for b in drive.allowed_branches}
    branch_ok = "ALL" in allowed or student.branch.upper() in allowed

    checks = [
        Check(
            "cgpa", student.cgpa >= drive.min_cgpa, f">= {_fmt(drive.min_cgpa)}", _fmt(student.cgpa)
        ),
        Check(
            "backlogs",
            student.active_backlogs <= drive.max_active_backlogs,
            f"<= {drive.max_active_backlogs}",
            str(student.active_backlogs),
        ),
        Check(
            "branch",
            branch_ok,
            ", ".join(drive.allowed_branches) or "any",
            student.branch,
        ),
    ]
    if student.highest_offer_lpa is not None:
        threshold = round(offer_multiplier * student.highest_offer_lpa, 2)
        checks.append(
            Check(
                "offer_rule",
                drive.ctc_lpa >= threshold,
                f"CTC >= {_fmt(threshold)} LPA",
                f"CTC {_fmt(drive.ctc_lpa)} LPA "
                f"(current offer {_fmt(student.highest_offer_lpa)} LPA)",
            )
        )
    return Eligibility(
        eligible=all(c.passed for c in checks),
        registration_open=drive.registration_deadline >= today,
        checks=tuple(checks),
    )


class PlacementService:
    def __init__(self, session: Session, *, today: date, offer_multiplier: float) -> None:
        self._session = session
        self._today = today
        self._offer_multiplier = offer_multiplier

    def list_drives(self, *, include_past: bool = False) -> list[PlacementDrive]:
        query = select(PlacementDrive).order_by(PlacementDrive.drive_date, PlacementDrive.company)
        if not include_past:
            query = query.where(PlacementDrive.drive_date >= self._today)
        return list(self._session.scalars(query))

    def find_drives(self, company: str) -> list[PlacementDrive]:
        needle = company.strip().casefold()
        if not needle:
            return []
        drives = self.list_drives(include_past=True)
        direct = [d for d in drives if needle in d.company.casefold()]
        if direct:
            return direct
        by_name = {d.company.casefold(): d for d in drives}
        return [
            by_name[n] for n in difflib.get_close_matches(needle, list(by_name), n=3, cutoff=0.6)
        ]

    def evaluate(self, student: StudentProfile, drive: PlacementDrive) -> Eligibility:
        return evaluate_eligibility(
            student, drive, today=self._today, offer_multiplier=self._offer_multiplier
        )

    @staticmethod
    def student_of(user: User) -> StudentProfile | None:
        return user.profile
