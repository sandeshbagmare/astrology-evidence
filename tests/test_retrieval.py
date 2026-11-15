"""Hybrid tests use actual Qdrant local mode and explicitly synthetic embeddings."""

import math
from hashlib import sha256

import pytest
from qdrant_client import QdrantClient
from sqlalchemy import select
from test_corpus import payload

from astrology_evidence.corpus import CorpusService
from astrology_evidence.db import create_db
from astrology_evidence.models import ActiveCorpus, CorpusGeneration, Edition, Passage, RightsRecord
from astrology_evidence.retrieval import E5Encoder, QdrantIndex, RetrievalService


class DeterministicTestEncoder:
    revision = "synthetic-test-only-v1"

    def count_tokens(self, text):
        return len(text.encode("utf-8"))

    def encode(self, text):
        vector = [0.0] * 384
        for word in text.casefold().split():
            vector[int.from_bytes(sha256(word.encode()).digest()[:4]) % 384] += 1
        norm = math.sqrt(sum(v * v for v in vector))
        return [v / norm for v in vector]


@pytest.fixture
def db():
    database = create_db("sqlite://")
    database.initialize()
    yield database
    database.engine.dispose()


@pytest.fixture
def components(db):
    client = QdrantClient(":memory:")
    index = QdrantIndex(client)
    encoder = DeterministicTestEncoder()
    corpus = CorpusService(db)
    corpus.import_edition(payload())
    generation = corpus.publish(index, encoder)
    yield corpus, index, encoder, generation
    client.close()


def test_real_qdrant_hybrid_and_authoritative_source(db, components):
    corpus, index, encoder, generation = components
    hits = RetrievalService(db, index, encoder).search("Jupiter")
    assert len(hits) == 1
    assert hits[0].text == "Jupiter gives a synthetic result unless combust."
    assert hits[0].generation_id == generation
    assert corpus.source(hits[0].id).text == hits[0].text
    with db.session() as session:
        collection = session.get(CorpusGeneration, generation).physical_collection_name
    points, _ = index.client.scroll(collection, with_payload=True)
    assert "text" not in points[0].payload


@pytest.mark.parametrize("permission", ["index", "display", "model_transmit"])
def test_revocation_filtered_from_both_branches(db, components, permission):
    corpus, index, encoder, _ = components
    with db.session() as session:
        rights = session.scalar(select(RightsRecord))
        rights.permissions = {**rights.permissions, permission: False}
    assert RetrievalService(db, index, encoder).search("Jupiter") == []


def test_withdrawn_edition_excluded_while_stale_vectors_remain(db, components):
    corpus, index, encoder, _ = components
    with db.session() as session:
        identifier = session.scalar(select(Edition.id))
    corpus.withdraw(identifier)
    assert RetrievalService(db, index, encoder).search("Jupiter") == []


def test_tradition_filter(db, components):
    _, index, encoder, _ = components
    assert RetrievalService(db, index, encoder).search("Jupiter", tradition="western") == []


def test_text_mutation_cannot_be_cited(db, components):
    corpus, index, encoder, _ = components
    with db.session() as session:
        passage = session.scalar(select(Passage))
        passage.exact_text = "Tampered text"
        identifier = passage.id
    assert corpus.source(identifier) is None
    assert RetrievalService(db, index, encoder).search("Jupiter") == []


def test_failed_publication_preserves_active_generation(db, components):
    corpus, index, encoder, original = components

    class WrongDimensionEncoder(DeterministicTestEncoder):
        def encode(self, text):
            return [1.0]

    with pytest.raises(ValueError):
        corpus.publish(index, WrongDimensionEncoder())
    with db.session() as session:
        assert session.get(ActiveCorpus, 1).generation_id == original
        assert "failed" in session.scalars(select(CorpusGeneration.status)).all()


def test_parent_expansion_preserves_qualification(db):
    client = QdrantClient(":memory:")
    index = QdrantIndex(client)
    encoder = DeterministicTestEncoder()
    data = payload()
    data["passages"][0]["text"] = "Jupiter gives synthetic results. " * 12 + "Unless combust."
    corpus = CorpusService(db, max_tokens=100)
    corpus.import_edition(data)
    corpus.publish(index, encoder)
    hits = RetrievalService(db, index, encoder).search("Jupiter", limit=1)
    assert len(hits) == 1
    assert hits[0].text.endswith("Unless combust.")
    client.close()


def test_missing_encoder_fails_closed(db):
    with pytest.raises(ValueError, match="encoder"):
        RetrievalService(db, None, None)
    with pytest.raises(ValueError, match="revision"):
        E5Encoder(revision="")


def test_sparse_unicode_normalization_and_stability():
    from astrology_evidence.retrieval import sparse_vector

    assert sparse_vector("ŚUKRA गुरु") == sparse_vector("śukra गुरु")
    assert sparse_vector("moon").indices != sparse_vector("sun").indices


def test_revocation_during_build_prevents_publication(db, components):
    corpus, index, encoder, original = components

    class RevokingIndex(QdrantIndex):
        def verify(self, collection, expected):
            super().verify(collection, expected)
            with db.session() as session:
                identifier = session.scalar(select(Edition.id))
            corpus.withdraw(identifier)

    with pytest.raises(ValueError, match="changed"):
        corpus.publish(RevokingIndex(index.client), encoder)
    with db.session() as session:
        assert session.get(ActiveCorpus, 1).generation_id == original


def test_aggregate_edition_excerpt_limit(db):
    client = QdrantClient(":memory:")
    index = QdrantIndex(client)
    encoder = DeterministicTestEncoder()
    data = payload()
    data["rights"]["excerpt_policy"]["max_chars"] = 70
    data["passages"].append(
        {**data["passages"][0], "text": "Jupiter has another synthetic result."}
    )
    corpus = CorpusService(db)
    corpus.import_edition(data)
    corpus.publish(index, encoder)
    hits = RetrievalService(db, index, encoder).search("Jupiter")
    assert len(hits) == 1
    assert sum(len(p.text) for p in hits) <= 70
    client.close()
