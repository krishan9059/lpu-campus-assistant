"""Exercise the OpenAI-compatible client against a mocked transport, with no real network call."""

from __future__ import annotations

import json

import httpx
import pytest

from app.llm.base import ChatMessage, LLMError, ToolSpec
from app.llm.openai_compat import OpenAICompatibleClient


def _client(handler, **kw) -> OpenAICompatibleClient:
    transport = httpx.MockTransport(handler)
    return OpenAICompatibleClient(
        base_url="https://example.test/v1",
        model="test-model",
        api_key="secret-key",
        transport=transport,
        sleep=lambda _seconds: None,
        **kw,
    )


def _completion(text: str = "Hello there") -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


def test_sends_bearer_auth_and_model():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers["authorization"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_completion())

    client = _client(handler)
    reply = client.complete([ChatMessage("user", "hi")])
    assert captured["auth"] == "Bearer secret-key"
    assert captured["body"]["model"] == "test-model"
    assert reply.content == "Hello there"


def test_parses_tool_calls():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "function": {
                                        "name": "check_eligibility",
                                        "arguments": '{"company": "Acme"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    client = _client(handler)
    reply = client.complete(
        [ChatMessage("user", "am I eligible for Acme?")],
        tools=[ToolSpec("check_eligibility", "check", {"type": "object", "properties": {}})],
    )
    assert len(reply.tool_calls) == 1
    assert reply.tool_calls[0].name == "check_eligibility"
    assert reply.tool_calls[0].arguments == {"company": "Acme"}


def test_retries_on_503_then_succeeds():
    attempts = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] < 3:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, json=_completion("recovered"))

    client = _client(handler, max_retries=3)
    reply = client.complete([ChatMessage("user", "hi")])
    assert reply.content == "recovered"
    assert attempts["n"] == 3


def test_gives_up_after_max_retries():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="down")

    client = _client(handler, max_retries=1)
    with pytest.raises(LLMError):
        client.complete([ChatMessage("user", "hi")])


def test_non_retryable_error_raises_immediately():
    calls = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, text="bad key")

    client = _client(handler, max_retries=3)
    with pytest.raises(LLMError):
        client.complete([ChatMessage("user", "hi")])
    assert calls["n"] == 1


def test_malformed_json_response_raises_llm_error():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    client = _client(handler)
    with pytest.raises(LLMError):
        client.complete([ChatMessage("user", "hi")])


def test_unexpected_shape_raises_llm_error():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    client = _client(handler)
    with pytest.raises(LLMError):
        client.complete([ChatMessage("user", "hi")])
