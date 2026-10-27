"""Client for any OpenAI-compatible ``/chat/completions`` endpoint.

Gemini, Groq, OpenRouter and Ollama all expose this interface, so switching provider is a
matter of changing three environment variables.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Sequence
from typing import Any

import httpx

from app.llm.base import ChatMessage, LLMError, LLMResponse, ToolCall, ToolSpec

logger = logging.getLogger(__name__)

_RETRYABLE = {429, 500, 502, 503, 504}


def _encode_message(message: ChatMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.tool_calls:
        payload["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in message.tool_calls
        ]
    if message.role == "tool":
        payload["tool_call_id"] = message.tool_call_id
        if message.name:
            payload["name"] = message.name
    return payload


def _parse_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # some providers return content parts
        return "".join(p.get("text", "") for p in content if isinstance(p, dict))
    return ""


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        reasoning_effort: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._model = model
        self._max_retries = max_retries
        self._reasoning_effort = reasoning_effort
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=base_url.rstrip("/") + "/",
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    @property
    def model(self) -> str:
        return self._model

    def close(self) -> None:
        self._client.close()

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [_encode_message(m) for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self._reasoning_effort:
            payload["reasoning_effort"] = self._reasoning_effort
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
            payload["tool_choice"] = "auto"
        return self._parse(self._post(payload))

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(self._max_retries + 1):
            last_attempt = attempt == self._max_retries
            try:
                response = self._client.post("chat/completions", json=payload)
            except httpx.TimeoutException as exc:
                if last_attempt:
                    raise LLMError("The language model timed out.") from exc
            except httpx.HTTPError as exc:
                raise LLMError(
                    f"Could not reach the language model: {exc.__class__.__name__}"
                ) from exc
            else:
                if response.status_code < 400:
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise LLMError("The language model returned invalid JSON.") from exc
                if response.status_code not in _RETRYABLE or last_attempt:
                    detail = response.text[:200].replace("\n", " ")
                    raise LLMError(
                        f"Language model request failed (HTTP {response.status_code}): {detail}"
                    )
                logger.warning("LLM returned HTTP %s, retrying", response.status_code)
            self._sleep(min(2.0**attempt, 8.0))
        raise LLMError("Language model request failed.")  # pragma: no cover

    @staticmethod
    def _parse(data: dict[str, Any]) -> LLMResponse:
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("Unexpected response shape from the language model.") from exc
        calls = [
            ToolCall(
                id=raw.get("id") or f"call_{index}",
                name=raw["function"]["name"],
                arguments=_parse_arguments(raw["function"].get("arguments")),
            )
            for index, raw in enumerate(message.get("tool_calls") or [])
        ]
        return LLMResponse(content=_text_content(message.get("content")).strip(), tool_calls=calls)
