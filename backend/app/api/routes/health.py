from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.api.deps import ContainerDep, DbDep
from app.schemas.system import HealthOut, IndexStatus, LLMStatus

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthOut)
def health(container: ContainerDep, db: DbDep) -> HealthOut:
    db.execute(text("SELECT 1"))
    chunks = {a.domain: container.store.count(a.domain) for a in container.assistants.all()}
    return HealthOut(
        status="ok" if all(chunks.values()) else "degraded",
        version=__version__,
        environment=container.settings.environment,
        llm=LLMStatus(
            enabled=container.llm is not None, model=container.llm.model if container.llm else None
        ),
        index=IndexStatus(embedding_model=container.embedder.name, chunks=chunks),
    )
