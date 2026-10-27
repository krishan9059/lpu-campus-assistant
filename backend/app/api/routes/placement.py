from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ContainerDep, DbDep, OptionalUser
from app.core.clock import today_in
from app.db.models import PlacementDrive
from app.schemas.placement import CheckOut, DriveOut, DrivesResponse, EligibilityOut, StudentOut
from app.services.placement import Eligibility, PlacementService

router = APIRouter(prefix="/placement", tags=["placement"])


def _drive_out(drive: PlacementDrive, eligibility: Eligibility | None) -> DriveOut:
    return DriveOut(
        id=drive.id,
        company=drive.company,
        role_title=drive.role_title,
        ctc_lpa=drive.ctc_lpa,
        category=drive.category,
        min_cgpa=drive.min_cgpa,
        max_active_backlogs=drive.max_active_backlogs,
        allowed_branches=drive.allowed_branches,
        mode=drive.mode,
        location=drive.location,
        drive_date=drive.drive_date,
        registration_deadline=drive.registration_deadline,
        description=drive.description,
        eligibility=EligibilityOut(
            eligible=eligibility.eligible,
            registration_open=eligibility.registration_open,
            checks=[
                CheckOut(code=c.code, passed=c.passed, required=c.required, actual=c.actual)
                for c in eligibility.checks
            ],
        )
        if eligibility
        else None,
    )


@router.get("/drives", response_model=DrivesResponse)
def upcoming_drives(container: ContainerDep, db: DbDep, user: OptionalUser) -> DrivesResponse:
    """Upcoming drives. Signed-in students also get a per-drive eligibility breakdown."""
    settings = container.settings
    service = PlacementService(
        db, today=today_in(settings.timezone), offer_multiplier=settings.placement_offer_multiplier
    )
    profile = user.profile if user else None
    drives = [
        _drive_out(d, service.evaluate(profile, d) if profile else None)
        for d in service.list_drives()
    ]
    student = (
        StudentOut(
            reg_no=user.reg_no,
            full_name=user.full_name,
            program=profile.program,
            branch=profile.branch,
            batch=profile.batch,
            cgpa=profile.cgpa,
            active_backlogs=profile.active_backlogs,
            highest_offer_lpa=profile.highest_offer_lpa,
        )
        if user and profile
        else None
    )
    return DrivesResponse(student=student, drives=drives)
