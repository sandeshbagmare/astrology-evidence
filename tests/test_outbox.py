from unittest.mock import Mock

import pytest
from qdrant_client import QdrantClient
from sqlalchemy import select
from test_corpus import payload
from test_retrieval import DeterministicTestEncoder

from astrology_evidence.corpus import CorpusService
from astrology_evidence.db import create_db
from astrology_evidence.jobs.outbox import process_withdrawal
from astrology_evidence.models import Edition, OutboxOperation, Passage
from astrology_evidence.retrieval import QdrantIndex


@pytest.fixture
def state():
    db = create_db("sqlite://")
    db.initialize()
    client = QdrantClient(":memory:")
    corpus = CorpusService(db)
    edition_id = corpus.import_edition(payload())
    generation = corpus.publish(QdrantIndex(client), DeterministicTestEncoder())
    corpus.withdraw(edition_id)
    yield db, client, edition_id, generation
    client.close()
    db.engine.dispose()


def test_withdrawal_purges_actual_local_index_and_text(state):
    db, client, edition_id, generation = state
    assert process_withdrawal(db, client)
    with db.session() as session:
        passage = session.scalar(select(Passage))
        assert passage.exact_text == passage.normalized_text == ""
        assert session.scalar(select(OutboxOperation)).status == "succeeded"
        assert session.get(Edition, edition_id).title
        from astrology_evidence.models import CorpusGeneration

        collection = session.get(CorpusGeneration, generation).physical_collection_name
    assert client.count(collection, exact=True).count == 0
    assert process_withdrawal(db, client) is False


def test_index_failure_remains_pending_and_can_retry(state):
    db, client, _, _ = state
    failing = Mock()
    failing.collection_exists.side_effect = RuntimeError("offline")
    assert process_withdrawal(db, failing) is False
    with db.session() as session:
        assert session.scalar(select(OutboxOperation)).status == "pending"
        assert session.scalar(select(Passage)).exact_text == ""
    assert process_withdrawal(db, client)


def test_never_purges_active_edition(state):
    db, client, edition_id, _ = state
    with db.session() as session:
        session.get(Edition, edition_id).withdrawn_at = None
    assert process_withdrawal(db, client) is False
    with db.session() as session:
        assert session.scalar(select(Passage)).exact_text
        assert session.scalar(select(OutboxOperation)).status == "pending"


def test_withdrawal_redacts_saved_narrative_and_worker_consumes(state):
    from datetime import timedelta

    from astrology_evidence.jobs.worker import run_once
    from astrology_evidence.models import (
        Chart,
        Profile,
        ProfileRevision,
        Reading,
        ReadingRequest,
        User,
        utcnow,
    )

    db, client, _, _ = state
    with db.session() as session:
        passage = session.scalar(select(Passage))
        user = User(issuer="test", subject="withdrawal")
        session.add(user)
        session.flush()
        profile = Profile(owner_id=user.id)
        session.add(profile)
        session.flush()
        revision = ProfileRevision(
            profile_id=profile.id, owner_id=user.id, revision=1, birth_input={}
        )
        session.add(revision)
        session.flush()
        chart = Chart(
            owner_id=user.id,
            profile_revision_id=revision.id,
            input_hash="input",
            settings_hash="settings",
            settings={},
            manifest={},
            facts=[],
        )
        request = ReadingRequest(
            owner_id=user.id,
            profile_revision_id=revision.id,
            question="private",
            idempotency_key="key",
            request_hash="hash",
            deadline=utcnow() + timedelta(minutes=1),
        )
        session.add_all([chart, request])
        session.flush()
        reading = Reading(
            owner_id=user.id,
            chart_id=chart.id,
            request_id=request.id,
            answer={"summary": "withdrawn source quote"},
            evidence_manifest={"passages": [{"id": passage.id, "text": "withdrawn source quote"}]},
        )
        session.add(reading)
    assert run_once(db, "outbox-worker", qdrant_client=client)
    with db.session() as session:
        stored = session.scalar(select(Reading))
        assert "withdrawn source quote" not in str(stored.answer)
        assert "withdrawn source quote" not in str(stored.evidence_manifest)
        assert session.scalar(select(OutboxOperation)).status == "succeeded"
