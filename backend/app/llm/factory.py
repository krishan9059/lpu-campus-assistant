"""Build the configured language model client, if any."""

from __future__ import annotations

from app.config import Settings
from app.llm.base import LLMClient
from app.llm.openai_compat import OpenAICompatibleClient


def build_llm(settings: Settings) -> LLMClient | None:
    if not settings.llm_enabled:
        return None
    assert settings.llm_base_url is not None
    assert settings.llm_model is not None
    key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else None
    return OpenAICompatibleClient(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=key,
        timeout=settings.llm_timeout_seconds,
        reasoning_effort=settings.llm_reasoning_effort,
    )
