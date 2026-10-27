"""Seed demo users and placement drives from CSV files.

Drive dates are stored as day offsets from the seeding date so the demo data never goes stale.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import PlacementDrive, StudentProfile, User

ADMIN_REG_NO = "admin"


@dataclass(frozen=True)
class SeedReport:
    students: int
    drives: int


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if any(row.values())]


def is_seeded(session: Session) -> bool:
    return (session.scalar(select(func.count()).select_from(User)) or 0) > 0


def seed_database(
    session: Session,
    seed_dir: Path,
    *,
    today: date,
    demo_password: str,
    bcrypt_rounds: int = 12,
    reset: bool = False,
) -> SeedReport:
    if reset:
        session.execute(delete(StudentProfile))
        session.execute(delete(PlacementDrive))
        session.execute(delete(User))
        session.commit()

    # All demo accounts share one password, so hash it once.
    hashed = hash_password(demo_password, rounds=bcrypt_rounds)

    session.add(
        User(reg_no=ADMIN_REG_NO, full_name="Placement Admin", hashed_password=hashed, role="admin")
    )
    students = _rows(seed_dir / "students.csv")
    for row in students:
        user = User(
            reg_no=row["reg_no"].strip(),
            full_name=row["full_name"].strip(),
            hashed_password=hashed,
            role="student",
        )
        offer = row.get("highest_offer_lpa", "").strip()
        user.profile = StudentProfile(
            program=row["program"].strip(),
            branch=row["branch"].strip(),
            batch=int(row["batch"]),
            cgpa=float(row["cgpa"]),
            active_backlogs=int(row["active_backlogs"]),
            highest_offer_lpa=float(offer) if offer else None,
        )
        session.add(user)

    drives = _rows(seed_dir / "drives.csv")
    for row in drives:
        session.add(
            PlacementDrive(
                company=row["company"].strip(),
                role_title=row["role_title"].strip(),
                ctc_lpa=float(row["ctc_lpa"]),
                category=row["category"].strip(),
                min_cgpa=float(row["min_cgpa"]),
                max_active_backlogs=int(row["max_active_backlogs"]),
                allowed_branches=[
                    b.strip() for b in row["allowed_branches"].split("|") if b.strip()
                ],
                mode=row["mode"].strip(),
                location=row["location"].strip(),
                drive_date=today + timedelta(days=int(row["drive_offset_days"])),
                registration_deadline=today + timedelta(days=int(row["deadline_offset_days"])),
                description=row["description"].strip(),
            )
        )
    session.commit()
    return SeedReport(students=len(students), drives=len(drives))
