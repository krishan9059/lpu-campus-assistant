from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import ContainerDep
from app.schemas.chat import AssistantOut, DepartmentOut

router = APIRouter(tags=["assistants"])


@router.get("/assistants", response_model=list[AssistantOut])
def list_assistants(container: ContainerDep) -> list[AssistantOut]:
    return [
        AssistantOut(
            id=a.id,
            domain=a.domain,
            name=a.names,
            tagline=a.taglines,
            suggested_questions=a.suggested_questions,
            personalised=a.tools_enabled,
        )
        for a in container.assistants.all()
    ]


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(
    container: ContainerDep, assistant: str = Query(min_length=1, max_length=32)
) -> list[DepartmentOut]:
    spec = container.assistants.require(assistant)
    return [
        DepartmentOut(
            id=d.id,
            name=d.name,
            description=d.description,
            email=d.email,
            phone=d.phone,
            hours=d.hours,
            url=d.url,
        )
        for d in container.directory.for_domain(spec.domain)
    ]
