from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_round_trip():
    hashed = hash_password("correct horse battery staple", rounds=4)
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_hash_is_salted():
    a = hash_password("same password", rounds=4)
    b = hash_password("same password", rounds=4)
    assert a != b


def test_very_long_password_does_not_raise():
    long_password = "x" * 200
    hashed = hash_password(long_password, rounds=4)
    assert verify_password(long_password, hashed)


def test_verify_password_rejects_garbage_hash():
    assert verify_password("anything", "not-a-real-hash") is False


def test_token_round_trip():
    token = create_access_token("DEMO001", "student", secret="s3cret", expires_minutes=10)
    payload = decode_access_token(token, secret="s3cret")
    assert payload.subject == "DEMO001"
    assert payload.role == "student"


def test_token_rejects_wrong_secret():
    token = create_access_token("DEMO001", "student", secret="s3cret", expires_minutes=10)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret="different")


def test_expired_token_is_rejected():
    issued = datetime.now(UTC) - timedelta(minutes=20)
    token = create_access_token("DEMO001", "student", secret="s3cret", expires_minutes=10, now=issued)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret="s3cret")
