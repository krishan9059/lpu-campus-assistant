from fastapi.testclient import TestClient


def _token(client: TestClient, reg_no: str) -> str:
    response = client.post("/api/auth/login", json={"reg_no": reg_no, "password": "campus@123"})
    return response.json()["access_token"]


def test_anonymous_drives_have_no_eligibility(client: TestClient):
    body = client.get("/api/placement/drives").json()
    assert body["student"] is None
    assert all(d["eligibility"] is None for d in body["drives"])


def test_signed_in_drives_include_eligibility(client: TestClient):
    token = _token(client, "DEMO001")
    body = client.get("/api/placement/drives", headers={"Authorization": f"Bearer {token}"}).json()
    assert body["student"]["reg_no"] == "DEMO001"
    assert all(d["eligibility"] is not None for d in body["drives"])


def test_high_cgpa_student_is_eligible_for_regular_drive(client: TestClient):
    token = _token(client, "DEMO004")  # cgpa 9.1, IT, no backlogs, no existing offer
    body = client.get("/api/placement/drives", headers={"Authorization": f"Bearer {token}"}).json()
    drive = next(d for d in body["drives"] if d["company"] == "Northwind Technologies")
    assert drive["eligibility"]["eligible"] is True


def test_low_cgpa_student_fails_cgpa_check(client: TestClient):
    token = _token(client, "DEMO008")  # cgpa 5.9
    body = client.get("/api/placement/drives", headers={"Authorization": f"Bearer {token}"}).json()
    drive = next(d for d in body["drives"] if d["company"] == "Helio Motors")
    codes = [c["code"] for c in drive["eligibility"]["checks"] if not c["passed"]]
    assert "cgpa" in codes


def test_student_with_offer_needs_higher_ctc(client: TestClient):
    token = _token(client, "DEMO006")  # existing offer 6.5, needs >= 9.75
    body = client.get("/api/placement/drives", headers={"Authorization": f"Bearer {token}"}).json()
    by_company = {d["company"]: d["eligibility"] for d in body["drives"]}
    assert by_company["Aster Analytics"]["eligible"] is False  # 7.2 LPA, below threshold
    assert by_company["Kestrel Data"]["eligible"] is True  # 18.0 LPA, above threshold


def test_past_drive_is_not_listed(client: TestClient):
    body = client.get("/api/placement/drives").json()
    assert all(d["company"] != "Lumen Retail Systems" for d in body["drives"])
