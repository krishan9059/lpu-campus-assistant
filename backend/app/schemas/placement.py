from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class CheckOut(BaseModel):
    code: str
    passed: bool
    required: str
    actual: str


class EligibilityOut(BaseModel):
    eligible: bool
    registration_open: bool
    checks: list[CheckOut]


class DriveOut(BaseModel):
    id: int
    company: str
    role_title: str
    ctc_lpa: float
    category: str
    min_cgpa: float
    max_active_backlogs: int
    allowed_branches: list[str]
    mode: str
    location: str
    drive_date: date
    registration_deadline: date
    description: str
    eligibility: EligibilityOut | None = None


class StudentOut(BaseModel):
    reg_no: str
    full_name: str
    program: str
    branch: str
    batch: int
    cgpa: float
    active_backlogs: int
    highest_offer_lpa: float | None


class DrivesResponse(BaseModel):
    student: StudentOut | None
    drives: list[DriveOut]
