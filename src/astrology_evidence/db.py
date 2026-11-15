"""Explicit database construction; importing this module never connects."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from astrology_evidence.models import Base


@dataclass
class Database:
    engine: Engine
    sessions: sessionmaker[Session]

    def initialize(self) -> None:
        """Create tables for local development/tests. Deployments use Alembic."""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.sessions.begin() as session:
            yield session


def create_db(database_url: str) -> Database:
    options: dict[str, Any] = {}
    if database_url.startswith("sqlite:"):
        options["connect_args"] = {"check_same_thread": False}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            options["poolclass"] = StaticPool
    engine = create_engine(database_url, pool_pre_ping=True, **options)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")

    return Database(engine, sessionmaker(engine, expire_on_commit=False))
