from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import ContainerDep, CurrentUser, DbDep, limit_login
from app.core.errors import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.db.models import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when the account does not exist, so response time does not reveal
# which registration numbers are valid.
_DUMMY_HASH = "$2b$12$C6UzMDM.H6dfI/f/IKcEeO5ZQ3vJm9oX6yQ0m8Vj2vQ1e5Yb3nq4y"


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_login)])
def login(payload: LoginRequest, container: ContainerDep, db: DbDep) -> TokenResponse:
    settings = container.settings
    user = db.scalar(select(User).where(User.reg_no == payload.reg_no.strip()))
    stored = user.hashed_password if user else _DUMMY_HASH
    valid = verify_password(payload.password, stored)
    if not (user and valid and user.is_active):
        raise UnauthorizedError("Registration number or password is incorrect.")
    token = create_access_token(
        user.reg_no,
        user.role,
        secret=settings.secret_key.get_secret_value(),
        expires_minutes=settings.access_token_expire_minutes,
    )
    return TokenResponse(
        access_token=token,
        user=UserOut(reg_no=user.reg_no, full_name=user.full_name, role=user.role),  # type: ignore[arg-type]
    )


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut(reg_no=user.reg_no, full_name=user.full_name, role=user.role)  # type: ignore[arg-type]
