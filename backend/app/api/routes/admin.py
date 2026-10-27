from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import AdminUser, ContainerDep, DbDep
from app.db.models import EscalationLog
from app.schemas.system import EscalationLogOut, ReindexResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reindex", response_model=ReindexResponse)
def reindex(_: AdminUser, container: ContainerDep, rebuild: bool = False) -> ReindexResponse:
    """Re-scan the documents folder. Only new, changed or removed files are re-embedded."""
    report = container.ingestor.sync(rebuild=rebuild)
    container.retriever.refresh()
    return ReindexResponse(
        added=report.added,
        updated=report.updated,
        removed=report.removed,
        unchanged=report.unchanged,
        errors=report.errors,
        chunks=report.chunks,
    )


@router.get("/escalations", response_model=list[EscalationLogOut])
def escalations(
    _: AdminUser, db: DbDep, limit: int = Query(default=50, ge=1, le=200)
) -> list[EscalationLogOut]:
    """Recent questions that were handed to a person. Each one points at a gap in the documents."""
    rows = db.scalars(select(EscalationLog).order_by(EscalationLog.id.desc()).limit(limit))
    return [
        EscalationLogOut(
            id=r.id,
            created_at=r.created_at,
            assistant=r.assistant,
            reason=r.reason,
            department_id=r.department_id,
            language=r.language,
            question=r.question,
        )
        for r in rows
    ]
