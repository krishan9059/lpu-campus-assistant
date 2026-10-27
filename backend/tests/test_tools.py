from fastapi.testclient import TestClient


def test_needs_sign_in_without_a_token(client_with_llm):
    client, llm = client_with_llm
    llm.script["cgpa"] = "NEEDS_SIGN_IN"
    body = client.post(
        "/api/chat", json={"assistant": "placement", "message": "What is my current cgpa?"}
    ).json()
    assert body["status"] == "needs_sign_in"


def test_tool_call_reaches_the_students_own_profile(client_with_llm, container_with_llm):
    client, llm = client_with_llm
    container, _ = container_with_llm

    def fake_complete(messages, *, tools=None, temperature=0.1, max_tokens=1024):
        from app.llm.base import LLMResponse, ToolCall

        if tools and not any(m.role == "tool" for m in messages):
            return LLMResponse(content="", tool_calls=[ToolCall(id="1", name="get_my_profile", arguments={})])
        tool_message = next(m for m in messages if m.role == "tool")
        return LLMResponse(content=f"Your CGPA is on record: {tool_message.content}. [1]")

    llm.complete = fake_complete  # type: ignore[method-assign]

    token = client.post("/api/auth/login", json={"reg_no": "DEMO001", "password": "campus@123"}).json()[
        "access_token"
    ]
    body = client.post(
        "/api/chat",
        json={"assistant": "placement", "message": "What is my current CGPA?"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert body["status"] == "answered"
    assert "get_my_profile" in body["tools_used"]
    assert "8.4" in body["answer"]  # DEMO001's cgpa from seed/students.csv


def test_model_cannot_request_another_students_data(client_with_llm):
    """The tool schema exposes no student identifier, so the model has no way to ask for
    anyone else's record; this asserts that invariant at the tool-spec level."""
    client, llm = client_with_llm
    from app.services.tools import PlacementToolbox

    toolbox = PlacementToolbox.__new__(PlacementToolbox)  # inspect the schema only
    specs = PlacementToolbox.specs.__get__(toolbox)()
    for spec in specs:
        properties = spec.parameters.get("properties", {})
        assert "reg_no" not in properties
        assert "student_id" not in properties


def test_ungrounded_llm_answer_is_escalated(client_with_llm):
    client, llm = client_with_llm
    llm.default = "The answer is definitely 42, trust me."
    body = client.post(
        "/api/chat", json={"assistant": "university", "message": "What is the minimum attendance?"}
    ).json()
    assert body["status"] == "escalated"
    assert body["escalation"]["reason"] == "ungrounded"


def test_llm_not_found_reply_escalates(client_with_llm):
    client, llm = client_with_llm
    llm.default = "NOT_FOUND"
    body = client.post(
        "/api/chat", json={"assistant": "university", "message": "What is the minimum attendance?"}
    ).json()
    assert body["status"] == "escalated"
    assert body["escalation"]["reason"] == "model_not_found"


def test_grounded_llm_answer_with_citation_is_returned(client_with_llm):
    client, llm = client_with_llm
    llm.script["minimum attendance"] = "You need at least 75% attendance [1]."
    body = client.post(
        "/api/chat", json={"assistant": "university", "message": "What is the minimum attendance?"}
    ).json()
    assert body["status"] == "answered"
    assert body["sources"]
    assert "[1]" in body["answer"]
