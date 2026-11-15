from contextlib import closing
from types import SimpleNamespace

import pytest
from sqlalchemy import delete
from test_profiles import client as client
from test_profiles import create

from astrology_evidence.models import ProfileRevision
from astrology_evidence.retrieval import QdrantIndex


@pytest.mark.parametrize(
    "vector",
    [
        None,
        [],
        [1.0] * 384,
        {"dense": [[1.0] * 384]},
        {"dense": ["1"] * 384},
        {"dense": [float("nan")] * 384},
    ],
)
def test_verify_rejects_invalid_dense_shapes(vector):
    record = SimpleNamespace(id="passage", vector=vector, payload={"text_hash": "hash"})
    client = SimpleNamespace(scroll=lambda *args, **kwargs: ([record], None))
    with pytest.raises(ValueError, match="dimension"):
        QdrantIndex(client).verify("collection", {"passage": "hash"})


def test_verify_rejects_missing_payload():
    record = SimpleNamespace(id="passage", vector={"dense": [1.0] * 384}, payload=None)
    client = SimpleNamespace(scroll=lambda *args, **kwargs: ([record], None))
    with pytest.raises(ValueError, match="hash"):
        QdrantIndex(client).verify("collection", {"passage": "hash"})


@pytest.mark.parametrize("path", ["/api/profiles", "/api/profiles/{id}"])
def test_missing_current_profile_revision_returns_not_found(client, path):
    profile = create(client).json()
    with client.app.state.db.session() as db:
        db.execute(
            delete(ProfileRevision).where(ProfileRevision.id == profile["profile_revision_id"])
        )
    response = client.get(path.format(id=profile["id"]))
    assert response.status_code == 404


@pytest.mark.parametrize("missing_model", ["Edition", "RightsRecord", "CorpusGeneration"])
def test_source_denies_missing_related_records(monkeypatch, missing_model):
    from qdrant_client import QdrantClient
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from test_corpus import payload
    from test_retrieval import DeterministicTestEncoder

    from astrology_evidence import models
    from astrology_evidence.corpus import CorpusService
    from astrology_evidence.db import create_db

    database = create_db("sqlite://")
    database.initialize()
    with closing(QdrantClient(":memory:")) as index_client:
        corpus = CorpusService(database)
        corpus.import_edition(payload())
        corpus.publish(QdrantIndex(index_client), DeterministicTestEncoder())
        with database.session() as session:
            passage_id = session.scalar(select(models.Passage.id))
        original_get = Session.get

        def get_with_missing_row(self, entity, ident, **kwargs):
            if entity is getattr(models, missing_model):
                return None
            return original_get(self, entity, ident, **kwargs)

        monkeypatch.setattr(Session, "get", get_with_missing_row)
        assert corpus.source(passage_id) is None
    database.engine.dispose()


def test_me_denies_user_removed_after_authentication(client, monkeypatch):
    from astrology_evidence import identity

    monkeypatch.setattr(
        identity, "require_user", lambda request: identity.UserContext("missing", False)
    )
    assert client.get("/api/me").status_code == 401
