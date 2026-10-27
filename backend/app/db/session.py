"""Engine and session factory."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base


def create_db_engine(url: str) -> Engine:
    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        prefix = "sqlite:///"
        if url.startswith(prefix) and not url.startswith("sqlite:///:memory:"):
            Path(url.removeprefix(prefix)).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def init_db(engine: Engine) -> None:
    # The schema is small and seeded from files, so create_all is sufficient here.
    # Introduce Alembic migrations once the schema starts to change in production.
    from app.db import models  # noqa: F401  (register tables)

    Base.metadata.create_all(engine)
