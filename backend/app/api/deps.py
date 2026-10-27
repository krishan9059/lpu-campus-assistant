"""FastAPI dependencies: container access, database sessions, authentication, rate limits."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.container import Container
from app.core.errors import ForbiddenError, RateLimitedError, UnauthorizedError
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import InvalidTokenError, decode_access_token
from app.db.models import User

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_db(container: ContainerDep) -> Iterator[Session]:
    with container.session_factory() as session:
        yield session


DbDep = Annotated[Session, Depends(get_db)]


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    container: ContainerDep,
    db: DbDep,
) -> User | None:
    """No token means anonymous. A token that is present but invalid is rejected, so the
    client knows to sign in again instead of silently losing personalised answers."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(
            credentials.credentials, secret=container.settings.secret_key.get_secret_value()
        )
    except InvalidTokenError:
        raise UnauthorizedError("Your session has expired. Please sign in again.") from None
    user = db.scalar(select(User).where(User.reg_no == payload.subject))
    if user is None or not user.is_active:
        raise UnauthorizedError("Your session is no longer valid. Please sign in again.")
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_user(user: OptionalUser) -> User:
    if user is None:
        raise UnauthorizedError("Sign in to continue.")
    return user


CurrentUser = Annotated[User, Depends(require_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise ForbiddenError("Administrator access is required.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def _client_key(request: Request, container: Container) -> str:
    if container.settings.trust_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce(limiter: SlidingWindowLimiter, request: Request, container: Container) -> None:
    retry_after = limiter.check(_client_key(request, container))
    if retry_after:
        raise RateLimitedError(retry_after)


def limit_chat(request: Request, container: ContainerDep) -> None:
    _enforce(container.chat_limiter, request, container)


def limit_login(request: Request, container: ContainerDep) -> None:
    _enforce(container.login_limiter, request, container)
