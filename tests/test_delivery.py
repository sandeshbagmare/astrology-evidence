"""Optional real-service delivery checks; CI supplies disposable service URLs."""

import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from qdrant_client import QdrantClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from astrology_evidence.models import Base, User
from astrology_evidence.retrieval import QdrantIndex


def test_postgresql_migration_and_roundtrip():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set; real PostgreSQL check requires a test server")
    engine = create_engine(url)
    schema = "delivery_" + uuid4().hex
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        scoped_url = engine.url.update_query_dict({"options": f"-csearch_path={schema}"})
        config = Config("alembic.ini")
        config.attributes["ignore_environment"] = True
        config.set_main_option(
            "sqlalchemy.url", scoped_url.render_as_string(hide_password=False).replace("%", "%%")
        )
        command.upgrade(config, "head")
        scoped = create_engine(scoped_url)
        try:
            with scoped.connect() as connection:
                assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
            with Session(scoped) as session, session.begin():
                session.add(User(issuer="delivery-test", subject=schema))
            with Session(scoped) as session:
                user = session.scalar(select(User).where(User.subject == schema))
                assert user is not None
                assert user.created_at.tzinfo is not None
            command.downgrade(config, "base")
        finally:
            scoped.dispose()
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()


def test_remote_qdrant_index_and_query():
    url = os.environ.get("TEST_QDRANT_URL")
    if not url:
        pytest.skip("TEST_QDRANT_URL is not set; real Qdrant check requires a test server")
    client = QdrantClient(url=url, timeout=15)
    collection = "delivery_" + uuid4().hex
    passage = SimpleNamespace(id=str(uuid4()), exact_text="synthetic Jupiter", text_hash="test")
    edition = SimpleNamespace(id=str(uuid4()), title="Test", tradition="jyotish", language="en")

    class SyntheticEncoder:
        def encode(self, text):
            return [1.0] + [0.0] * 383

        def count_tokens(self, text):
            return len(text.split())

    index = QdrantIndex(client)
    try:
        index.build(collection, [(passage, edition)], SyntheticEncoder())
        index.verify(collection, {passage.id: passage.text_hash})
        assert index.search(collection, "Jupiter", SyntheticEncoder(), [passage.id], "jyotish") == [
            passage.id
        ]
        assert index.search(collection, "Jupiter", SyntheticEncoder(), [], "jyotish") == []
    finally:
        if client.collection_exists(collection):
            client.delete_collection(collection)
        client.close()
