import json
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from astrology_evidence.answers.contracts import GenerationResult, ProviderError
from astrology_evidence.answers.reading import ReadingService
from astrology_evidence.answers.validation import SCOPE, SUMMARY
from astrology_evidence.config import Settings
from astrology_evidence.corpus import CorpusService, text_hash
from astrology_evidence.db import create_db
from astrology_evidence.models import (
    ActiveCorpus,
    Chart,
    Consent,
    CorpusGeneration,
    Edition,
    Passage,
    Profile,
    ProfileRevision,
    QuotaBucket,
    Reading,
    ReadingRequest,
    RightsRecord,
    User,
    utcnow,
)


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.effect = None
        self.invalid = False

    def generate(self, request):
        self.calls.append(request)
        if self.effect:
            self.effect()
        if self.invalid:
            return GenerationResult("not JSON")
        evidence = json.loads(request.prompt.split("\nDATA\n")[1])["evidence"][0]
        return GenerationResult(
            json.dumps(
                {
                    "status": "partial",
                    "concise_summary": SUMMARY,
                    "traditional_claims": [
                        {
                            "claim_id": "c1",
                            "text": evidence["text"],
                            "citation_ids": ["q1"],
                            "chart_fact_ids": [],
                            "applicability_status": "not_established",
                            "scope_note": SCOPE,
                        }
                    ],
                    "evidence_manifest": [
                        {
                            "citation_id": "q1",
                            "passage_id": evidence["id"],
                            "passage_hash": evidence["text_hash"],
                            "quoted_text": evidence["text"],
                            "start": 0,
                            "end": len(evidence["text"]),
                            "locators": evidence["locators"],
                        }
                    ],
                }
            )
        )


@pytest.fixture
def env():
    db = create_db("sqlite://")
    db.initialize()
    with db.session() as session:
        u = User(issuer="test", subject="a")
        v = User(issuer="test", subject="b")
        session.add_all([u, v])
        session.flush()
        p = Profile(owner_id=u.id)
        session.add(p)
        session.flush()
        rev = ProfileRevision(
            profile_id=p.id,
            owner_id=u.id,
            revision=1,
            birth_input={"private_birth": "do not transmit"},
        )
        session.add(rev)
        session.flush()
        c = Chart(
            owner_id=u.id,
            profile_revision_id=rev.id,
            input_hash="a" * 64,
            settings_hash="b" * 64,
            settings={"tradition": "jyotish"},
            manifest={"private_birth": "do not transmit"},
            facts=[{"fact_id": "sun", "kind": "sign", "value": "aries"}],
        )
        session.add(c)
        session.add(Consent(user_id=u.id, purpose="model_processing", notice_version="v1"))
        rights = RightsRecord(
            evidence_reference="synthetic",
            reviewer="reviewer",
            status="approved",
            jurisdictions=["test"],
            permissions={"display": True, "model_transmit": True, "index": True},
            excerpt_policy={"max_chars": 200, "attribution": "Synthetic"},
        )
        session.add(rights)
        session.flush()
        edition = Edition(
            title="Synthetic", author="Test", rights_id=rights.id, review_state="approved"
        )
        session.add(edition)
        session.flush()
        text = "A calm practice supports reflection."
        passage = Passage(
            edition_id=edition.id,
            exact_text=text,
            text_hash=text_hash(text),
            locators={"verse": "1"},
            layer_type="original",
            review_state="approved",
        )
        session.add(passage)
        session.flush()
        gen = CorpusGeneration(
            physical_collection_name="test",
            manifest_hash="c" * 64,
            manifest={"passage_hashes": {passage.id: passage.text_hash}},
            status="published",
        )
        session.add(gen)
        session.flush()
        session.add(ActiveCorpus(id=1, generation_id=gen.id))
        session.flush()
        ids = SimpleNamespace(
            user=u.id,
            other=v.id,
            profile=p.id,
            revision=rev.id,
            chart=c.id,
            passage=passage.id,
            rights=rights.id,
        )
    corpus = CorpusService(db)
    retriever = SimpleNamespace(search=lambda *a, **k: [corpus.source(ids.passage)])
    provider = FakeProvider()
    settings = Settings(
        app_env="test",
        authentication_enabled=True,
        ai_enabled=True,
        provider_reviewed=True,
        openai_api_key="synthetic",
    )
    service = ReadingService(db, retriever, provider, settings)
    yield SimpleNamespace(
        db=db, ids=ids, provider=provider, service=service, retriever=retriever, settings=settings
    )
    db.engine.dispose()


def create(env, key="one", question="reflection"):
    return env.service.create(env.ids.user, env.ids.revision, question, key)


def test_real_graph_publishes_exact_source_and_minimizes_input(env):
    result = create(env)
    assert result["status"] == "succeeded"
    reading = env.service.get_reading(env.ids.user, result["reading_id"])
    assert reading["answer"]["status"] == "partial"
    assert "private_birth" not in env.provider.calls[0].prompt
    assert env.provider.calls[0].timeout_seconds <= 120


def test_empty_evidence_never_calls_provider(env):
    env.retriever.search = lambda *a, **k: []
    result = create(env)
    assert result["status"] == "succeeded"
    assert not env.provider.calls
    assert (
        env.service.get_reading(env.ids.user, result["reading_id"])["answer"]["status"]
        == "insufficient_evidence"
    )


def test_disabled_ai_never_calls_provider(env):
    env.settings.ai_enabled = False
    result = create(env)
    assert result["status"] == "succeeded" and not env.provider.calls


def test_identical_idempotency_replay_never_calls_again(env):
    assert create(env) == create(env)
    assert len(env.provider.calls) == 1


def test_changed_idempotency_content_conflicts(env):
    create(env)
    with pytest.raises(HTTPException) as e:
        create(env, question="different")
    assert e.value.status_code == 409


def test_other_owner_revision_denied(env):
    with pytest.raises(HTTPException) as e:
        env.service.create(env.ids.other, env.ids.revision, "q", "one")
    assert e.value.status_code == 404


def test_missing_chart_requires_clarification(env):
    with pytest.raises(HTTPException) as e:
        env.service.create(env.ids.user, env.ids.revision, "q", "one", "missing")
    assert e.value.status_code == 422


def test_consent_needed_before_provider(env):
    env.service.set_consent(env.ids.user, False, "v1")
    result = create(env)
    assert result["failure_code"] == "consent_required" and not env.provider.calls


def test_invalid_output_has_only_one_repair(env):
    env.provider.invalid = True
    assert create(env)["status"] == "failed"
    assert len(env.provider.calls) == 2


def test_unknown_transport_is_not_retried(env):
    def fail():
        raise ProviderError("provider_unknown", unknown=True)

    env.provider.effect = fail
    result = create(env)
    assert result["status"] == "unknown" and len(env.provider.calls) == 1
    assert create(env) == result


def test_cancel_during_generation_fences_publication(env):
    def cancel():
        with env.db.session() as db:
            req = db.scalar(select(ReadingRequest))
        env.service.cancel(env.ids.user, req.id)

    env.provider.effect = cancel
    assert create(env)["status"] == "cancelled"
    with env.db.session() as db:
        assert db.scalar(select(Reading)) is None


def test_consent_revoked_during_generation_fences_publication(env):
    env.provider.effect = lambda: env.service.set_consent(env.ids.user, False, "v1")
    assert create(env)["status"] == "cancelled"


def test_withdrawal_during_generation_fails_closed(env):
    def withdraw():
        with env.db.session() as db:
            db.get(RightsRecord, env.ids.rights).withdrawn_at = utcnow()

    env.provider.effect = withdraw
    assert create(env)["status"] == "failed"


def test_saved_reading_rights_rechecked(env):
    result = create(env)
    with env.db.session() as db:
        db.get(RightsRecord, env.ids.rights).withdrawn_at = utcnow()
    with pytest.raises(HTTPException) as e:
        env.service.get_reading(env.ids.user, result["reading_id"])
    assert e.value.status_code == 410


def test_saved_reading_owner_rechecked(env):
    result = create(env)
    with pytest.raises(HTTPException) as e:
        env.service.get_reading(env.ids.other, result["reading_id"])
    assert e.value.status_code == 404


def test_delete_removes_narrative(env):
    result = create(env)
    env.service.delete(env.ids.user, result["reading_id"])
    with env.db.session() as db:
        assert db.get(Reading, result["reading_id"]).answer == {}
    with pytest.raises(HTTPException):
        env.service.get_reading(env.ids.user, result["reading_id"])


def test_daily_quota_is_atomic_admission_limit(env):
    env.settings.answer_daily_limit = 1
    create(env)
    with pytest.raises(HTTPException) as e:
        create(env, key="two")
    assert e.value.status_code == 429


def test_concurrent_request_same_user_rejected(env):
    def nested():
        with pytest.raises(HTTPException) as e:
            create(env, key="two")
        assert e.value.status_code == 429

    env.provider.effect = nested
    assert create(env)["status"] == "succeeded"


def test_deleted_profile_cannot_publish(env):
    def delete():
        with env.db.session() as db:
            db.get(Profile, env.ids.profile).deleted_at = utcnow()

    env.provider.effect = delete
    assert create(env)["status"] == "cancelled"


def test_expired_generation_cannot_publish(env):
    def expire():
        with env.db.session() as db:
            db.scalar(select(ReadingRequest)).deadline = utcnow() - timedelta(seconds=1)

    env.provider.effect = expire
    assert create(env)["status"] == "unknown"


def test_api_requires_authentication_and_csrf(env):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from astrology_evidence.answers.routes import router

    app = FastAPI()
    app.state.db = env.db
    app.state.settings = env.settings
    app.state.reading_service = env.service
    app.include_router(router)
    client = TestClient(app)
    assert client.get("/api/readings").status_code == 401
    assert client.post("/api/readings", json={}).status_code in (401, 422)


def api_client(env):
    from fastapi import FastAPI, Response
    from fastapi.testclient import TestClient

    from astrology_evidence.answers.routes import router
    from astrology_evidence.identity import issue_login

    app = FastAPI()
    app.state.db = env.db
    app.state.settings = env.settings
    app.state.reading_service = env.service
    app.include_router(router)
    client = TestClient(app)
    response = Response()
    issue_login(env.db, env.settings, env.ids.user, response)
    for cookie in response.headers.getlist("set-cookie"):
        key, value = cookie.split(";")[0].split("=", 1)
        client.cookies.set(key, value)
    client.headers.update(
        {"Origin": env.settings.app_public_origin, "X-CSRF-Token": client.cookies["ae_csrf"]}
    )
    return client


def test_api_create_status_read_delete_and_feedback(env):
    client = api_client(env)
    result = client.post(
        "/api/readings",
        json={"profile_revision_id": env.ids.revision, "question": "reflection"},
        headers={"Idempotency-Key": "api"},
    )
    assert result.status_code == 201, result.text
    data = result.json()
    assert client.get("/api/reading-requests/" + data["id"]).json()["status"] == "succeeded"
    assert client.get("/api/readings/" + data["reading_id"]).status_code == 200
    assert (
        client.post(
            "/api/feedback", json={"reading_id": data["reading_id"], "category": "citation_issue"}
        ).status_code
        == 201
    )
    assert len(client.get("/api/readings").json()) == 1
    assert client.delete("/api/readings/" + data["reading_id"]).status_code == 204


def test_api_rejects_missing_csrf_and_idempotency(env):
    client = api_client(env)
    payload = {"profile_revision_id": env.ids.revision, "question": "reflection"}
    assert client.post("/api/readings", json=payload).status_code == 422
    client.headers.pop("X-CSRF-Token")
    assert (
        client.post("/api/readings", json=payload, headers={"Idempotency-Key": "api"}).status_code
        == 403
    )


def test_api_opt_out_and_safe_failure(env):
    client = api_client(env)
    assert (
        client.post(
            "/api/consent",
            json={"purpose": "model_processing", "granted": False, "notice_version": "v1"},
        ).status_code
        == 200
    )
    response = client.post(
        "/api/readings",
        json={"profile_revision_id": env.ids.revision, "question": "reflection"},
        headers={"Idempotency-Key": "api"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "consent_required"


def test_api_model_injection_and_owner_fields_rejected(env):
    client = api_client(env)
    for extra in ({"owner_id": env.ids.other}, {"model": "anything"}, {"tools": ["shell"]}):
        response = client.post(
            "/api/readings",
            json={"profile_revision_id": env.ids.revision, "question": "reflection", **extra},
            headers={"Idempotency-Key": "api"},
        )
        assert response.status_code == 422


def test_api_cancel_does_not_change_terminal_state(env):
    result = create(env)
    client = api_client(env)
    response = client.post("/api/reading-requests/" + result["id"] + "/cancel")
    assert response.status_code == 200 and response.json()["status"] == "succeeded"


def test_question_over_2000_characters_is_rejected_before_provider(env):
    with pytest.raises(HTTPException) as exc:
        create(env, question="x" * 2001)
    assert exc.value.status_code == 422
    assert not env.provider.calls


@pytest.mark.parametrize("global_limit", [1, 5])
def test_cancelled_generation_holds_concurrency_until_provider_returns(env, global_limit):
    env.settings.answer_global_limit = global_limit

    def cancel_and_try_again():
        env.provider.effect = None
        with env.db.session() as db:
            request = db.scalar(select(ReadingRequest))
        assert env.service.cancel(env.ids.user, request.id)["status"] == "cancelled"
        with pytest.raises(HTTPException) as rejected:
            create(env, key="while-cancelled-call-runs")
        assert rejected.value.status_code == 429

    env.provider.effect = cancel_and_try_again
    assert create(env)["status"] == "cancelled"
    assert len(env.provider.calls) == 1
    assert create(env, key="after-call-returns")["status"] == "succeeded"
    assert len(env.provider.calls) == 2


def test_consent_revoke_and_regrant_does_not_free_running_call_slot(env):
    def revoke_and_try_again():
        env.provider.effect = None
        env.service.set_consent(env.ids.user, False, "v1")
        env.service.set_consent(env.ids.user, True, "v1")
        with pytest.raises(HTTPException) as rejected:
            create(env, key="while-revoked-call-runs")
        assert rejected.value.status_code == 429

    env.provider.effect = revoke_and_try_again
    assert create(env)["status"] == "cancelled"
    assert create(env, key="after-call-returns")["status"] == "succeeded"


@pytest.mark.parametrize("scope", ["profile", "account"])
def test_privacy_purge_does_not_free_inflight_global_slot(env, scope):
    from astrology_evidence.jobs.worker import run_once
    from astrology_evidence.privacy import PrivacyService

    env.settings.answer_global_limit = 1
    with env.db.session() as db:
        profile = Profile(owner_id=env.ids.other)
        db.add(profile)
        db.flush()
        revision = ProfileRevision(
            profile_id=profile.id, owner_id=env.ids.other, revision=1, birth_input={}
        )
        db.add(revision)
        db.flush()
        db.add(Chart(
            owner_id=env.ids.other, profile_revision_id=revision.id,
            input_hash="c" * 64, settings_hash="d" * 64,
            settings={}, manifest={}, facts=[],
        ))
        other_revision = revision.id
    second_service = ReadingService(env.db, None, None, env.settings)

    def purge_and_try_again():
        env.provider.effect = None
        privacy = PrivacyService(env.db)
        if scope == "profile":
            privacy.request_profile_deletion(env.ids.user, env.ids.profile)
        else:
            privacy.request_account_deletion(env.ids.user)
        assert run_once(env.db, "purge-review")
        with pytest.raises(HTTPException) as rejected:
            second_service.create(env.ids.other, other_revision, "question", "while-purged")
        assert rejected.value.status_code == 429

    env.provider.effect = purge_and_try_again
    with pytest.raises(HTTPException) as removed:
        create(env)
    assert removed.value.status_code == 404
    assert second_service.create(
        env.ids.other, other_revision, "question", "after-call-returns"
    )["status"] == "succeeded"


@pytest.mark.parametrize("failure", ["unknown", "unexpected"])
def test_failed_generation_releases_concurrency_after_return(env, failure):
    env.settings.answer_global_limit = 1

    def fail():
        if failure == "unknown":
            raise ProviderError("provider_unknown", unknown=True)
        raise RuntimeError("synthetic provider failure")

    env.provider.effect = fail
    assert create(env)["status"] == "unknown"
    env.provider.effect = None
    assert create(env, key="after-failure")["status"] == "succeeded"


def test_crashed_inflight_lease_expires_without_refunding_daily_budget(env, monkeypatch):
    import astrology_evidence.answers.reading as reading_module

    now = utcnow()
    env.settings.answer_global_limit = 1
    env.settings.answer_global_daily_limit = 3
    with env.db.session() as db:
        db.add(QuotaBucket(
            id=f"reading-inflight:{env.ids.other}:crashed-request",
            used=1, capacity=1, resets_at=now + timedelta(seconds=20),
        ))
        db.add(QuotaBucket(
            id="global-reading-day", used=1, capacity=3,
            resets_at=now + timedelta(days=1),
        ))
    restarted = ReadingService(env.db, env.retriever, env.provider, env.settings)
    with pytest.raises(HTTPException) as rejected:
        restarted.create(env.ids.user, env.ids.revision, "reflection", "before-expiry")
    assert rejected.value.status_code == 429
    monkeypatch.setattr(reading_module, "utcnow", lambda: now + timedelta(seconds=21))
    assert restarted.create(
        env.ids.user, env.ids.revision, "reflection", "after-expiry"
    )["status"] == "succeeded"
    with env.db.session() as db:
        assert db.scalar(select(QuotaBucket).where(
            QuotaBucket.id.startswith("reading-inflight:")
        )) is None
        assert db.get(QuotaBucket, "global-reading-day").used == 2


def test_legacy_active_request_without_permit_still_blocks_admission(env):
    result = create(env)
    with env.db.session() as db:
        request = db.get(ReadingRequest, result["id"])
        request.status = "generating"
        request.deadline = utcnow() + timedelta(seconds=30)
    with pytest.raises(HTTPException) as rejected:
        create(env, key="while-legacy-call-runs")
    assert rejected.value.status_code == 429
