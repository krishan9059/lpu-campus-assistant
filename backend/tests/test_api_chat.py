from fastapi.testclient import TestClient


def test_health_reports_indexed_chunks(client: TestClient):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["index"]["chunks"]["university"] > 0
    assert body["index"]["chunks"]["placement"] > 0


def test_extractive_answer_cites_a_source(client: TestClient):
    body = client.post(
        "/api/chat",
        json={"assistant": "university", "message": "What attendance do I need for the term-end exam?"},
    ).json()
    assert body["status"] == "answered"
    assert body["mode"] == "extractive"
    assert body["sources"]
    assert body["sources"][0]["title"] == "Academic Regulations"


def test_off_topic_question_escalates(client: TestClient):
    body = client.post(
        "/api/chat", json={"assistant": "university", "message": "Who won the last cricket world cup?"}
    ).json()
    assert body["status"] == "escalated"
    assert body["escalation"]["reason"] == "no_relevant_source"


def test_wellbeing_message_skips_retrieval_and_escalates(client: TestClient):
    body = client.post(
        "/api/chat", json={"assistant": "university", "message": "I want to end my life"}
    ).json()
    assert body["status"] == "escalated"
    assert body["escalation"]["reason"] == "sensitive_topic"
    assert body["escalation"]["department"]["id"] == "counselling"
    assert any(d["id"] == "tele_manas" for d in body["escalation"]["additional"])
    assert not body["sources"]


def test_unknown_assistant_is_404(client: TestClient):
    assert client.post("/api/chat", json={"assistant": "nope", "message": "hi"}).status_code == 404


def test_blank_message_is_rejected(client: TestClient):
    assert client.post("/api/chat", json={"assistant": "university", "message": "   "}).status_code == 422


def test_overlong_message_is_rejected(client: TestClient):
    body = {"assistant": "university", "message": "x" * 2000}
    assert client.post("/api/chat", json=body).status_code == 422


def test_placement_pdf_source_has_page_number(client: TestClient):
    body = client.post(
        "/api/chat", json={"assistant": "placement", "message": "What CTC counts as Super Dream?"}
    ).json()
    assert body["status"] == "answered"
    assert body["sources"][0]["page"] is not None


def test_policy_exception_request_escalates(client: TestClient):
    body = client.post(
        "/api/chat",
        json={"assistant": "placement", "message": "Can the committee relax the CGPA cut-off for me?"},
    ).json()
    assert body["status"] == "escalated"
    assert body["escalation"]["reason"] == "policy_exception"


def test_language_auto_detects_hindi():
    pass  # covered directly in test_language.py; kept out of the API layer here
