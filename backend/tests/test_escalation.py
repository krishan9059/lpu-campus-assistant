from pathlib import Path

import pytest

from app.services.escalation import DepartmentDirectory, EscalationRouter

CONFIG = Path(__file__).resolve().parents[1] / "data" / "config" / "departments.yaml"


@pytest.fixture
def router() -> EscalationRouter:
    return EscalationRouter(DepartmentDirectory.load(CONFIG))


def test_keyword_routes_to_matching_department(router: EscalationRouter):
    dept = router.route("When is the library open?", domain="university")
    assert dept.id == "library"


def test_no_keyword_match_falls_back_to_default(router: EscalationRouter):
    dept = router.route("Something completely unrelated to campus life", domain="university")
    assert dept.id == "student_services"


def test_more_specific_keyword_wins_over_generic(router: EscalationRouter):
    dept = router.route("I need a bonafide certificate and my transcript", domain="university")
    assert dept.id == "academic_affairs"


def test_sensitive_wellbeing_detected(router: EscalationRouter):
    match = router.detect_sensitive("I want to end my life", domain="university")
    assert match is not None
    assert match.reason == "sensitive_topic"
    assert match.department.id == "counselling"
    assert any(d.id == "tele_manas" for d in match.additional)


def test_sensitive_grievance_detected(router: EscalationRouter):
    match = router.detect_sensitive("my roommate is ragging me every day", domain="university")
    assert match is not None
    assert match.department.id == "student_welfare"


def test_ordinary_message_is_not_sensitive(router: EscalationRouter):
    assert router.detect_sensitive("what time does the library close?", domain="university") is None


def test_sensitive_rule_is_domain_scoped(router: EscalationRouter):
    assert router.detect_sensitive("relaxation of the cut-off please", domain="university") is None
    match = router.detect_sensitive("can I get a relaxation of the cut-off?", domain="placement")
    assert match is not None and match.department.id == "placement_cell"


def test_hindi_keyword_is_detected(router: EscalationRouter):
    assert router.detect_sensitive("मैं मरना चाहता हूं", domain="university") is not None
