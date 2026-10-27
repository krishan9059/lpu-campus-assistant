"""Tools the placement assistant may call.

Every tool is bound to the signed-in student when the toolbox is created. The model never
supplies a student identifier, so it cannot request anyone else's record.
"""

from __future__ import annotations

import logging
from typing import Any

from app.db.models import PlacementDrive, StudentProfile, User
from app.llm.base import ToolSpec
from app.services.placement import Eligibility, PlacementService

logger = logging.getLogger(__name__)

_NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}


def _drive_payload(drive: PlacementDrive) -> dict[str, Any]:
    return {
        "company": drive.company,
        "role": drive.role_title,
        "ctc_lpa": drive.ctc_lpa,
        "category": drive.category,
        "drive_date": drive.drive_date.isoformat(),
        "registration_deadline": drive.registration_deadline.isoformat(),
        "mode": drive.mode,
        "location": drive.location,
        "criteria": {
            "min_cgpa": drive.min_cgpa,
            "max_active_backlogs": drive.max_active_backlogs,
            "branches": drive.allowed_branches,
        },
    }


def _eligibility_payload(result: Eligibility) -> dict[str, Any]:
    return {
        "meets_criteria": result.eligible,
        "registration_open": result.registration_open,
        "checks": [
            {
                "criterion": c.code,
                "passed": c.passed,
                "required": c.required,
                "student_has": c.actual,
            }
            for c in result.checks
        ],
    }


class PlacementToolbox:
    def __init__(self, service: PlacementService, user: User, student: StudentProfile) -> None:
        self._service = service
        self._user = user
        self._student = student
        self._handlers = {
            "get_my_profile": self._get_my_profile,
            "list_upcoming_drives": self._list_upcoming_drives,
            "check_eligibility": self._check_eligibility,
        }

    def specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                "get_my_profile",
                "Return the signed-in student's own CGPA, active backlogs, branch and "
                "highest offer.",
                _NO_ARGS,
            ),
            ToolSpec(
                "list_upcoming_drives",
                "List upcoming placement drives with dates, packages and criteria. "
                "Set only_eligible to true to keep drives the student qualifies for.",
                {
                    "type": "object",
                    "properties": {"only_eligible": {"type": "boolean"}},
                    "additionalProperties": False,
                },
            ),
            ToolSpec(
                "check_eligibility",
                "Check whether the signed-in student meets the criteria of the drive for "
                "a company.",
                {
                    "type": "object",
                    "properties": {"company": {"type": "string", "description": "Company name"}},
                    "required": ["company"],
                    "additionalProperties": False,
                },
            ),
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers.get(name)
        if handler is None:
            return {"error": f"Unknown tool '{name}'."}
        try:
            return handler(arguments)
        except Exception:
            logger.exception("Tool %s failed", name)
            return {"error": "The tool failed. Ask the student to contact the Placement Cell."}

    def _get_my_profile(self, _: dict[str, Any]) -> dict[str, Any]:
        s = self._student
        return {
            "name": self._user.full_name,
            "registration_number": self._user.reg_no,
            "program": s.program,
            "branch": s.branch,
            "batch": s.batch,
            "cgpa": s.cgpa,
            "active_backlogs": s.active_backlogs,
            "highest_offer_lpa": s.highest_offer_lpa,
        }

    def _list_upcoming_drives(self, arguments: dict[str, Any]) -> dict[str, Any]:
        only_eligible = bool(arguments.get("only_eligible", False))
        drives = []
        for drive in self._service.list_drives():
            result = self._service.evaluate(self._student, drive)
            if only_eligible and not result.eligible:
                continue
            drives.append({**_drive_payload(drive), **_eligibility_payload(result)})
        return {"drives": drives}

    def _check_eligibility(self, arguments: dict[str, Any]) -> dict[str, Any]:
        company = str(arguments.get("company", "")).strip()
        matches = self._service.find_drives(company)
        if not matches:
            return {"error": f"No drive found for '{company}'."}
        return {
            "results": [
                {
                    **_drive_payload(d),
                    **_eligibility_payload(self._service.evaluate(self._student, d)),
                }
                for d in matches
            ]
        }
