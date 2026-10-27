from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import ContainerDep, DbDep, OptionalUser, limit_chat
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(limit_chat)])
def chat(
    request: ChatRequest, container: ContainerDep, db: DbDep, user: OptionalUser
) -> ChatResponse:
    return container.chat.answer(request, user=user, db=db)
