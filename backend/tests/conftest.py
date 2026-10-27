"""Shared fixtures. Everything runs against the hash embedder and an in-memory vector
store, so the suite needs no model download and no network access."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.container import Container, build_container
from app.core.clock import today_in
from app.db.seed import seed_database
from app.db.session import init_db
from app.llm.base import ChatMessage, LLMResponse, ToolSpec
from app.main import create_app
from app.rag.embeddings import HashingEmbedder
from app.rag.vectorstore import InMemoryVectorStore

BACKEND_DIR = Path(__file__).resolve().parents[1]


class FakeLLM:
    """A stand-in language model. ``script`` maps a substring of the user's latest
    message to a canned reply, so tests can target one turn without a real model."""

    def __init__(self, script: dict[str, str] | None = None, default: str = "NOT_FOUND") -> None:
        self.script = script or {}
        self.default = default
        self.calls: list[list[ChatMessage]] = []

    @property
    def model(self) -> str:
        return "fake-llm"

    def complete(
        self, messages, *, tools=None, temperature: float = 0.1, max_tokens: int = 1024
    ) -> LLMResponse:
        self.calls.append(list(messages))
        latest = next((m.content for m in reversed(messages) if m.role == "user"), "") or ""
        for needle, reply in self.script.items():
            if needle in latest:
                return LLMResponse(content=reply)
        return LLMResponse(content=self.default)

    def close(self) -> None:
        pass


def make_settings(tmp_path: Path, **overrides: object) -> Settings:
    defaults = dict(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        vector_dir=tmp_path / "chroma",
        docs_dir=BACKEND_DIR / "data" / "docs",
        config_dir=BACKEND_DIR / "data" / "config",
        seed_dir=BACKEND_DIR / "data" / "seed",
        static_dir=tmp_path / "no-static",
        vector_store="memory",
        embedding_provider="hash",
        bcrypt_rounds=4,
        secret_key="test-secret",
        demo_password="campus@123",
        chat_rate_limit_per_minute=1000,
        login_rate_limit_per_minute=1000,
        auto_seed=False,
        auto_ingest=False,
    )
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def _seed(container: Container) -> None:
    init_db(container.engine)
    with container.session_factory() as session:
        seed_database(
            session,
            container.settings.seed_dir,
            today=today_in(container.settings.timezone),
            demo_password=container.settings.demo_password.get_secret_value(),
            bcrypt_rounds=container.settings.bcrypt_rounds,
        )
    container.ingestor.sync()
    container.retriever.refresh()


@pytest.fixture
def container(tmp_path: Path) -> Iterator[Container]:
    c = build_container(
        make_settings(tmp_path), embedder=HashingEmbedder(), store=InMemoryVectorStore(), llm=None
    )
    _seed(c)
    yield c
    c.close()


@pytest.fixture
def container_with_llm(tmp_path: Path) -> Iterator[tuple[Container, FakeLLM]]:
    llm = FakeLLM()
    c = build_container(
        make_settings(tmp_path), embedder=HashingEmbedder(), store=InMemoryVectorStore(), llm=llm
    )
    _seed(c)
    yield c, llm
    c.close()


@pytest.fixture
def db(container: Container) -> Iterator[Session]:
    with container.session_factory() as session:
        yield session


@pytest.fixture
def client(container: Container) -> Iterator[TestClient]:
    app = create_app(container.settings, container=container)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_with_llm(container_with_llm: tuple[Container, FakeLLM]) -> Iterator[tuple[TestClient, FakeLLM]]:
    c, llm = container_with_llm
    app = create_app(c.settings, container=c)
    with TestClient(app) as test_client:
        yield test_client, llm


@pytest.fixture
def today() -> date:
    return today_in("Asia/Kolkata")
