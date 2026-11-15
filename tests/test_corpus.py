"""Synthetic corpus integration tests: no books or real licensing claims."""

import copy
from datetime import timedelta

import pytest
from sqlalchemy import select

from astrology_evidence.corpus import CorpusService
from astrology_evidence.db import create_db
from astrology_evidence.models import Edition, OutboxOperation, Passage, RightsRecord, utcnow


def payload():
    return {
        "title": "Synthetic qualification fixture",
        "author": "Test author",
        "tradition": "jyotish",
        "language": "en",
        "review_state": "approved",
        "bibliographic_metadata": {"edition": "synthetic-1", "synthetic": True},
        "rights": {
            "evidence_reference": "Original test fixture; no real book",
            "reviewer": "test-admin",
            "status": "approved",
            "jurisdictions": ["test"],
            "permissions": {
                "store_original": True,
                "index": True,
                "display": True,
                "model_transmit": True,
            },
            "excerpt_policy": {"max_chars": 10000, "attribution": "Synthetic test author"},
        },
        "passages": [
            {
                "text": "Jupiter gives a synthetic result unless combust.",
                "locators": {
                    "chapter": "1",
                    "verse": "1",
                    "printed_page": "3",
                    "pdf_page_index": 5,
                },
                "layer_type": "commentary",
                "attributed_author": "Test author",
                "attribution_evidence": "Synthetic title page",
                "review_state": "approved",
            }
        ],
    }


@pytest.fixture
def db():
    database = create_db("sqlite://")
    database.initialize()
    yield database
    database.engine.dispose()


def test_import_preserves_exact_unicode_and_locators(db):
    data = payload()
    data["passages"][0]["text"] = "Śukra\u0301  गुरु — unless combust.\n"
    identifier = CorpusService(db).import_edition(data)
    with db.session() as session:
        passage = session.scalar(select(Passage).where(Passage.edition_id == identifier))
        assert passage.exact_text == data["passages"][0]["text"]
        assert passage.locators["pdf_page_index"] == 5
        assert passage.locators["printed_page"] == "3"
        assert passage.attributed_author == "Test author"
        assert len(passage.text_hash) == 64


@pytest.mark.parametrize("permission", ["store_original", "index", "display", "model_transmit"])
def test_rights_are_independent(db, permission):
    data = payload()
    data["rights"]["permissions"][permission] = False
    if permission == "store_original":
        with pytest.raises(ValueError):
            CorpusService(db).import_edition(data)
    else:
        identifier = CorpusService(db).import_edition(data)
        with db.session() as session:
            edition = session.get(Edition, identifier)
            assert session.get(RightsRecord, edition.rights_id).permissions[permission] is False


@pytest.mark.parametrize(
    "field,value", [("status", "pending"), ("reviewer", ""), ("evidence_reference", "")]
)
def test_import_requires_evidence_and_review(db, field, value):
    data = payload()
    data["rights"][field] = value
    with pytest.raises(ValueError):
        CorpusService(db).import_edition(data)


def test_expired_rights_rejected(db):
    data = payload()
    data["rights"]["expires_at"] = utcnow() - timedelta(seconds=1)
    with pytest.raises(ValueError):
        CorpusService(db).import_edition(data)


def test_chunking_preserves_parent_and_exact_spans(db):
    data = payload()
    original = "Śukra gives results. " * 10 + "Unless combust, this synthetic exception applies."
    data["passages"][0]["text"] = original
    identifier = CorpusService(db, max_tokens=100).import_edition(data)
    with db.session() as session:
        passages = session.scalars(select(Passage).where(Passage.edition_id == identifier)).all()
        parent = next(p for p in passages if p.parent_id is None)
        children = [p for p in passages if p.parent_id]
        assert parent.exact_text == original
        assert len(children) > 1
        assert "".join(p.exact_text for p in children) == original
        for child in children:
            start, end = child.locators["char_start"], child.locators["char_end"]
            assert original[start:end] == child.exact_text


def test_withdrawal_denies_before_outbox_cleanup(db):
    service = CorpusService(db)
    identifier = service.import_edition(payload())
    service.withdraw(identifier)
    service.withdraw(identifier)
    with db.session() as session:
        assert session.get(Edition, identifier).withdrawn_at is not None
        assert len(session.scalars(select(OutboxOperation)).all()) == 1


def test_missing_locator_or_authorship_rejected(db):
    for field in ("locators", "attributed_author"):
        data = copy.deepcopy(payload())
        data["passages"][0][field] = {} if field == "locators" else ""
        with pytest.raises(ValueError):
            CorpusService(db).import_edition(data)
