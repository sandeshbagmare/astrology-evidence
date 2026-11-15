from datetime import timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from astrology_evidence.db import create_db
from astrology_evidence.models import Profile, ProfileRevision, ReadingRequest, User, utcnow


def test_transaction_rollback_and_utc():
    db = create_db("sqlite://")
    db.initialize()
    with pytest.raises(RuntimeError), db.session() as session:
        session.add(User(issuer="google", subject="rollback"))
        raise RuntimeError("abort")
    with db.session() as session:
        assert session.scalar(select(User)) is None
        user = User(issuer="google", subject="kept")
        session.add(user)
    with db.session() as session:
        assert session.scalar(select(User)).created_at.tzinfo is not None
    db.engine.dispose()


def test_owner_foreign_key_and_idempotency():
    db = create_db("sqlite://")
    db.initialize()
    with db.session() as session:
        alice, bob = User(issuer="google", subject="a"), User(issuer="google", subject="b")
        session.add_all([alice, bob])
        session.flush()
        alice_id, bob_id = alice.id, bob.id
        profile = Profile(owner_id=alice.id)
        session.add(profile)
        session.flush()
        profile_id = profile.id
    with pytest.raises(IntegrityError), db.session() as session:
        session.add(
            ProfileRevision(profile_id=profile_id, owner_id=bob_id, revision=1, birth_input={})
        )
    with db.session() as session:
        revision = ProfileRevision(
            profile_id=profile_id, owner_id=alice_id, revision=1, birth_input={}
        )
        session.add(revision)
        session.flush()
        revision_id = revision.id

    def request(owner=alice_id, key="once"):
        return ReadingRequest(
            owner_id=owner,
            profile_revision_id=revision_id,
            question="question",
            idempotency_key=key,
            request_hash="hash",
            deadline=utcnow() + timedelta(minutes=1),
        )

    with db.session() as session:
        session.add(request())
    with pytest.raises(IntegrityError), db.session() as session:
        session.add(request())
    with pytest.raises(IntegrityError), db.session() as session:
        session.add(request(bob_id, "other"))
    db.engine.dispose()


def test_migration_upgrade_and_downgrade(tmp_path):
    url = "sqlite:///" + str(tmp_path / "migration.db").replace("\\", "/")
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    db = create_db(url)
    assert {"users", "reading_requests", "jobs", "editions"} <= set(
        inspect(db.engine).get_table_names()
    )
    command.downgrade(config, "base")
    assert "users" not in inspect(db.engine).get_table_names()
    db.engine.dispose()


def test_profile_revisions_cannot_be_updated():
    db = create_db("sqlite://")
    db.initialize()
    with db.session() as session:
        user = User(issuer="google", subject="immutable")
        session.add(user)
        session.flush()
        profile = Profile(owner_id=user.id)
        session.add(profile)
        session.flush()
        revision = ProfileRevision(
            profile_id=profile.id, owner_id=user.id, revision=1, birth_input={"date": "2000-01-01"}
        )
        session.add(revision)
        session.flush()
        revision_id = revision.id
    with pytest.raises(ValueError, match="immutable"), db.session() as session:
        revision = session.get(ProfileRevision, revision_id)
        revision.birth_input = {"date": "2001-01-01"}
    db.engine.dispose()


def test_migration_matches_models_and_postgres_ddl(tmp_path):
    from io import StringIO

    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    from astrology_evidence.models import Base

    config = Config("alembic.ini")
    config.attributes["ignore_environment"] = True
    url = "sqlite:///" + str(tmp_path / "schema.db").replace("\\", "/")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    db = create_db(url)
    with db.engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert differences == []
    db.engine.dispose()
    output = StringIO()
    config.output_buffer = output
    config.set_main_option("sqlalchemy.url", "postgresql+psycopg://localhost/offline")
    command.upgrade(config, "head", sql=True)
    assert "TIMESTAMP WITH TIME ZONE" in output.getvalue()
    assert "FOREIGN KEY(profile_revision_id, owner_id)" in output.getvalue()
