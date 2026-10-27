"""ORM models."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    reg_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(16), default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped[StudentProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    program: Mapped[str] = mapped_column(String(40))
    branch: Mapped[str] = mapped_column(String(20))
    batch: Mapped[int] = mapped_column(Integer)
    cgpa: Mapped[float] = mapped_column(Float)
    active_backlogs: Mapped[int] = mapped_column(Integer, default=0)
    highest_offer_lpa: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")


class PlacementDrive(Base):
    __tablename__ = "placement_drives"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(80), index=True)
    role_title: Mapped[str] = mapped_column(String(80))
    ctc_lpa: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(16))
    min_cgpa: Mapped[float] = mapped_column(Float)
    max_active_backlogs: Mapped[int] = mapped_column(Integer, default=0)
    allowed_branches: Mapped[list[str]] = mapped_column(JSON, default=list)
    mode: Mapped[str] = mapped_column(String(20), default="On campus")
    location: Mapped[str] = mapped_column(String(80), default="")
    drive_date: Mapped[date] = mapped_column(Date)
    registration_deadline: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(400), default="")


class EscalationLog(Base):
    """Questions the assistants could not answer. Useful for finding gaps in the documents."""

    __tablename__ = "escalation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    assistant: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(String(32))
    department_id: Mapped[str] = mapped_column(String(48))
    language: Mapped[str] = mapped_column(String(8))
    question: Mapped[str] = mapped_column(String(500))
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
