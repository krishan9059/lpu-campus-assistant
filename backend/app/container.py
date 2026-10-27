"""Composition root: builds and owns the long-lived components."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.core.rate_limit import SlidingWindowLimiter
from app.db.session import create_db_engine, create_session_factory
from app.llm.base import LLMClient
from app.llm.factory import build_llm
from app.rag.embeddings import Embedder, build_embedder
from app.rag.ingest import Ingestor
from app.rag.retriever import HybridRetriever
from app.rag.vectorstore import VectorStore, build_vector_store
from app.services.assistants import AssistantRegistry
from app.services.chat import ChatService
from app.services.escalation import DepartmentDirectory, EscalationRouter
from app.services.messages import MessageCatalog


@dataclass
class Container:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    embedder: Embedder
    store: VectorStore
    retriever: HybridRetriever
    ingestor: Ingestor
    llm: LLMClient | None
    assistants: AssistantRegistry
    directory: DepartmentDirectory
    chat: ChatService
    chat_limiter: SlidingWindowLimiter
    login_limiter: SlidingWindowLimiter

    def close(self) -> None:
        if self.llm:
            self.llm.close()
        self.engine.dispose()


def build_container(
    settings: Settings,
    *,
    embedder: Embedder | None = None,
    store: VectorStore | None = None,
    llm: LLMClient | None = None,
) -> Container:
    """Assemble the app. Tests pass fakes for the embedder, store or language model."""
    engine = create_db_engine(settings.database_url)
    embedder = embedder or build_embedder(settings)
    store = store or build_vector_store(settings)
    llm = llm if llm is not None else build_llm(settings)

    retriever = HybridRetriever(
        store,
        embedder,
        top_k=settings.retrieval_top_k,
        candidates=settings.retrieval_candidates,
    )
    persistent = settings.vector_store == "chroma"
    ingestor = Ingestor(
        docs_dir=settings.docs_dir,
        store=store,
        embedder=embedder,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        manifest_path=settings.vector_dir / "manifest.json" if persistent else None,
    )
    assistants = AssistantRegistry.load(
        settings.config_dir / "assistants.yaml", settings.enabled_assistants
    )
    directory = DepartmentDirectory.load(settings.config_dir / "departments.yaml")
    chat = ChatService(
        settings=settings,
        assistants=assistants,
        retriever=retriever,
        llm=llm,
        router=EscalationRouter(directory),
        messages=MessageCatalog.load(settings.config_dir / "messages.yaml"),
    )
    return Container(
        settings=settings,
        engine=engine,
        session_factory=create_session_factory(engine),
        embedder=embedder,
        store=store,
        retriever=retriever,
        ingestor=ingestor,
        llm=llm,
        assistants=assistants,
        directory=directory,
        chat=chat,
        chat_limiter=SlidingWindowLimiter(settings.chat_rate_limit_per_minute),
        login_limiter=SlidingWindowLimiter(settings.login_rate_limit_per_minute),
    )
