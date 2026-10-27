"""Password hashing and signed access tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

_ALGORITHM = "HS256"
_BCRYPT_MAX_BYTES = 72


class InvalidTokenError(Exception):
    """Raised when a token is malformed, expired or badly signed."""


@dataclass(frozen=True, slots=True)
class TokenPayload:
    subject: str
    role: str


def _password_bytes(password: str) -> bytes:
    # bcrypt only considers the first 72 bytes; truncate explicitly so newer
    # bcrypt releases do not raise for long passphrases.
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str, *, rounds: int = 12) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt(rounds=rounds)).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(password), hashed.encode("ascii"))
    except ValueError:
        return False


def create_access_token(
    subject: str, role: str, *, secret: str, expires_minutes: int, now: datetime | None = None
) -> str:
    issued = now or datetime.now(UTC)
    claims = {
        "sub": subject,
        "role": role,
        "iat": issued,
        "exp": issued + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(claims, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, *, secret: str) -> TokenPayload:
    try:
        claims = jwt.decode(
            token, secret, algorithms=[_ALGORITHM], options={"require": ["exp", "sub"]}
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    return TokenPayload(subject=str(claims["sub"]), role=str(claims.get("role", "student")))
