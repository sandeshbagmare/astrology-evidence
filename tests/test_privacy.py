from datetime import timedelta

import pytest
from sqlalchemy import select

from astrology_evidence.db import create_db
from astrology_evidence.jobs import JobService, LeaseLost
from astrology_evidence.models import (
    Consent,
    DeletionTombstone,
    Edition,
    Export,
    Job,
    Profile,
    ProfileRevision,
    RightsRecord,
    Session,
    User,
    utcnow,
)
from astrology_evidence.privacy import PrivacyService, ResourceUnavailable


@pytest.fixture
def data():
    db = create_db("sqlite://")
    db.initialize()
    with db.session() as session:
        a, b = (
            User(issuer="test", subject="a", email="private@test"),
            User(issuer="test", subject="b"),
        )
        session.add_all([a, b])
        session.flush()
        p = Profile(owner_id=a.id, alias="private profile")
        session.add(p)
        session.flush()
        session.add_all(
            [
                ProfileRevision(
                    profile_id=p.id, owner_id=a.id, revision=1, birth_input={"year": 2000}
                ),
                Consent(user_id=a.id, purpose="storage", notice_version="1"),
                Session(
                    user_id=a.id,
                    token_hash="secret-hash",
                    csrf_hash="csrf-secret",
                    expires_at=utcnow() + timedelta(days=1),
                ),
            ]
        )
        rights = RightsRecord(evidence_reference="license")
        session.add(rights)
        session.flush()
        session.add(Edition(rights_id=rights.id, title="Shared source"))
    yield db, a.id, b.id, p.id
    db.engine.dispose()


def run_one(db):
    lease = JobService(db).claim("test-worker")
    assert lease is not None
    PrivacyService(db).process_job(lease)
    return lease


def test_account_delete_immediate_deny_and_durable_purge(data):
    db, a, b, profile = data
    privacy = PrivacyService(db)
    job = privacy.request_account_deletion(a)
    with db.session() as session:
        assert session.get(User, a).deleted_at
        assert session.scalar(select(Session)).revoked_at
        assert session.get(Profile, profile).deleted_at
        assert session.scalar(select(DeletionTombstone)) is not None
    with pytest.raises(ResourceUnavailable):
        privacy.request_export(a)
    run_one(db)
    with db.session() as session:
        assert session.get(User, a) is None
        assert session.get(User, b) is not None
        assert session.scalar(select(ProfileRevision)) is None
        assert session.scalar(select(Edition)) is not None
        assert session.get(Job, job.id).payload == {}
        assert session.scalar(select(DeletionTombstone)).completed_at is not None


def test_profile_delete_ownership_and_purge(data):
    db, a, b, profile = data
    privacy = PrivacyService(db)
    with pytest.raises(ResourceUnavailable):
        privacy.request_profile_deletion(b, profile)
    privacy.request_profile_deletion(a, profile)
    run_one(db)
    with db.session() as session:
        assert session.get(Profile, profile) is None
        assert session.get(User, a) is not None


def test_export_owned_sanitized_and_expires(data):
    db, a, b, _ = data
    privacy = PrivacyService(db)
    export = privacy.request_export(a)
    run_one(db)
    payload = privacy.download_export(a, export.id)
    assert payload["account"]["email"] == "private@test"
    assert payload["profiles"][0]["revisions"][0]["birth_input"] == {"year": 2000}
    assert "secret-hash" not in str(payload) and "csrf-secret" not in str(payload)
    with pytest.raises(ResourceUnavailable):
        privacy.download_export(b, export.id)
    with db.session() as session:
        session.get(Export, export.id).expires_at = utcnow() - timedelta(seconds=1)
    with pytest.raises(ResourceUnavailable):
        privacy.download_export(a, export.id)
    assert privacy.purge_expired_exports() == 1


def test_deletion_wins_late_export(data):
    db, a, _, _ = data
    privacy = PrivacyService(db)
    export = privacy.request_export(a)
    lease = JobService(db).claim("slow")
    privacy.request_account_deletion(a)
    with pytest.raises((ResourceUnavailable, LeaseLost)):
        privacy.process_job(lease)
    with pytest.raises(ResourceUnavailable):
        privacy.download_export(a, export.id)
    run_one(db)
    with db.session() as session:
        assert session.scalar(select(Export)) is None


def test_deletion_idempotent(data):
    db, a, _, _ = data
    privacy = PrivacyService(db)
    assert privacy.request_account_deletion(a).id == privacy.request_account_deletion(a).id


def test_restore_tombstone_replay_denies_restored_account(data):
    db, a, _, _ = data
    privacy = PrivacyService(db)
    privacy.request_account_deletion(a)
    with db.session() as session:
        tombstone = session.scalar(select(DeletionTombstone))
        journal = [{"scope": tombstone.scope, "subject_hash": tombstone.subject_hash}]
        session.get(User, a).deleted_at = None
        session.scalar(select(Session)).revoked_at = None
    privacy.replay_tombstones(journal)
    with db.session() as session:
        assert session.get(User, a).deleted_at
        assert session.scalar(select(Session)).revoked_at


def test_worker_processes_purge(data):
    from astrology_evidence.jobs.worker import run_once

    db, a, _, _ = data
    PrivacyService(db).request_account_deletion(a)
    assert run_once(db, "independent-worker") is True
    assert run_once(db, "independent-worker") is False
    with db.session() as session:
        assert session.get(User, a) is None


def test_http_csrf_owner_and_download_no_store():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from astrology_evidence.config import Settings
    from astrology_evidence.identity import router as identity_router
    from astrology_evidence.privacy import router

    app = FastAPI()
    app.state.db = create_db("sqlite://")
    app.state.db.initialize()
    app.state.settings = Settings(
        _env_file=None,
        app_env="test",
        dev_login_enabled=True,
        app_public_origin="http://testserver",
    )
    app.include_router(identity_router)
    app.include_router(router)
    with TestClient(app) as client:
        assert client.post("/api/me/export").status_code == 401
        csrf = client.get("/auth/dev/start").json()["csrf_token"]
        client.post("/auth/dev", headers={"Origin": "http://testserver", "X-CSRF-Token": csrf})
        assert client.post("/api/me/export").status_code == 403
        headers = {
            "Origin": "http://testserver",
            "X-CSRF-Token": client.get("/api/me").json()["csrf_token"],
        }
        response = client.post("/api/me/export", headers=headers)
        assert response.status_code == 202
        body = response.json()
        run_one(app.state.db)
        download = client.get("/api/exports/" + body["export_id"])
        assert download.status_code == 200
        assert download.headers["cache-control"] == "no-store"
        assert client.get("/api/jobs/" + body["job_id"]).json()["status"] == "succeeded"
        assert client.delete("/api/me", headers=headers).status_code == 202
        assert client.get("/api/exports/" + body["export_id"]).status_code == 401
    app.state.db.engine.dispose()


def test_reading_export_omits_unverified_narrative_and_raw_response():
    from astrology_evidence.models import Reading

    reading = Reading(
        id="reading",
        request_id="request",
        chart_id="chart",
        owner_id="owner",
        versions={"schema": "1"},
        created_at=utcnow(),
        answer={"concise_summary": "restricted source words", "raw_response": "raw"},
        evidence_manifest={"citations": [{"quote": "restricted source words"}]},
    )
    exported = PrivacyService.export_reading(reading)
    assert exported["id"] == "reading"
    assert exported["answer_omitted_reason"]
    assert "restricted source words" not in str(exported)
    assert "raw_response" not in str(exported)
