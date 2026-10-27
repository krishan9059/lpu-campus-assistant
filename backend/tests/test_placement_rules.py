from datetime import date

import pytest

from app.db.models import PlacementDrive, StudentProfile
from app.services.placement import evaluate_eligibility


def _student(**kw) -> StudentProfile:
    base = dict(program="B.Tech", branch="CSE", batch=2027, cgpa=8.0, active_backlogs=0, highest_offer_lpa=None)
    base.update(kw)
    return StudentProfile(**base)


def _drive(**kw) -> PlacementDrive:
    base = dict(
        company="Acme", role_title="SDE", ctc_lpa=10.0, category="regular", min_cgpa=7.0,
        max_active_backlogs=0, allowed_branches=["CSE", "IT"], mode="On campus", location="Hall",
        drive_date=date(2026, 12, 1), registration_deadline=date(2026, 11, 20), description="",
    )
    base.update(kw)
    return PlacementDrive(**base)


def test_eligible_student_passes_all_checks():
    result = evaluate_eligibility(_student(), _drive(), today=date(2026, 11, 1), offer_multiplier=1.5)
    assert result.eligible
    assert all(c.passed for c in result.checks)


def test_low_cgpa_fails():
    result = evaluate_eligibility(_student(cgpa=6.0), _drive(min_cgpa=7.0), today=date(2026, 11, 1), offer_multiplier=1.5)
    assert not result.eligible
    assert next(c for c in result.checks if c.code == "cgpa").passed is False


def test_too_many_backlogs_fails():
    result = evaluate_eligibility(
        _student(active_backlogs=2), _drive(max_active_backlogs=1), today=date(2026, 11, 1), offer_multiplier=1.5
    )
    assert not result.eligible


def test_branch_not_allowed_fails():
    result = evaluate_eligibility(
        _student(branch="ECE"), _drive(allowed_branches=["CSE", "IT"]), today=date(2026, 11, 1), offer_multiplier=1.5
    )
    assert not result.eligible


def test_branch_all_wildcard_allows_everyone():
    result = evaluate_eligibility(
        _student(branch="ME"), _drive(allowed_branches=["ALL"]), today=date(2026, 11, 1), offer_multiplier=1.5
    )
    assert next(c for c in result.checks if c.code == "branch").passed is True


@pytest.mark.parametrize(
    ("existing_offer", "new_ctc", "expected"),
    [(6.0, 9.0, True), (6.0, 9.1, True), (6.0, 8.9, False), (10.0, 15.0, True), (10.0, 14.9, False)],
)
def test_one_offer_multiplier_boundary(existing_offer, new_ctc, expected):
    result = evaluate_eligibility(
        _student(highest_offer_lpa=existing_offer), _drive(ctc_lpa=new_ctc),
        today=date(2026, 11, 1), offer_multiplier=1.5,
    )
    assert next(c for c in result.checks if c.code == "offer_rule").passed is expected


def test_no_existing_offer_skips_offer_rule():
    result = evaluate_eligibility(_student(highest_offer_lpa=None), _drive(), today=date(2026, 11, 1), offer_multiplier=1.5)
    assert not any(c.code == "offer_rule" for c in result.checks)


def test_registration_closed_after_deadline():
    result = evaluate_eligibility(
        _student(), _drive(registration_deadline=date(2026, 10, 1)), today=date(2026, 10, 2), offer_multiplier=1.5
    )
    assert result.registration_open is False


def test_registration_open_on_deadline_day():
    result = evaluate_eligibility(
        _student(), _drive(registration_deadline=date(2026, 10, 1)), today=date(2026, 10, 1), offer_multiplier=1.5
    )
    assert result.registration_open is True
