import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, delete, func, select, text
from test_readings import env as env

from astrology_evidence.answers.reading import ReadingService
from astrology_evidence.config import Settings
from astrology_evidence.db import create_db
from astrology_evidence.identity import digest
from astrology_evidence.main import create_app
from astrology_evidence.models import (
    Chart,
    Profile,
    ProfileRevision,
    QuotaBucket,
    ReadingRequest,
    Session,
    User,
    utcnow,
)


@pytest.fixture(params=["sqlite", "postgresql"])
def quota_database_url(tmp_path, request):
    if request.param == "sqlite":
        yield f"sqlite:///{tmp_path}/atomic-quotas.db"
        return
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set; shared PostgreSQL quota race runs in CI")
    engine = create_engine(url)
    schema = "quotas_" + uuid4().hex
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        yield engine.url.update_query_dict({"options": f"-csearch_path={schema}"}).render_as_string(
            hide_password=False
        )
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()


def guest_app(tmp_path, limit=2, database_url=None):
    app = create_app(
        Settings(
            _env_file=None,
            app_env="test",
            database_url=database_url or f"sqlite:///{tmp_path}/guest-limit.db",
            app_public_origin="http://testserver",
            guest_workspace_global_limit_per_minute=limit,
        )
    )
    app.state.db.initialize()
    return app


def test_global_guest_issuance_limit_survives_new_clients_and_app_restart(tmp_path):
    app = guest_app(tmp_path)
    first = TestClient(app)
    assert first.get("/api/me").status_code == 200
    assert TestClient(app).get("/api/me").status_code == 200
    restarted = guest_app(tmp_path)
    response = TestClient(restarted).get("/api/me")
    assert response.status_code == 429
    assert 1 <= int(response.headers["Retry-After"]) <= 60
    assert "ae_session" not in response.cookies
    with app.state.db.session() as db:
        assert db.scalar(select(func.count(User.id))) == 2
        assert db.scalar(select(func.count(Session.id))) == 2
    assert first.get("/api/me").status_code == 200
    first.cookies.delete("ae_csrf")
    assert first.get("/api/me").status_code == 200
    with app.state.db.session() as db:
        assert db.scalar(select(func.count(User.id))) == 2


def test_guest_issuance_recovers_at_minute_boundary(tmp_path):
    app = guest_app(tmp_path, limit=1)
    assert TestClient(app).get("/api/me").status_code == 200
    assert TestClient(app).get("/api/me").status_code == 429
    with app.state.db.session() as db:
        bucket = db.get(QuotaBucket, "guest-workspace-issuance")
        bucket.resets_at = utcnow() - timedelta(seconds=1)
    assert TestClient(app).get("/api/me").status_code == 200


@pytest.mark.parametrize("csrf_state", ["missing", "wrong"])
def test_repeated_csrf_repair_reuses_one_session_at_full_workspace_limit(tmp_path, csrf_state):
    app = guest_app(tmp_path, limit=1)
    client = TestClient(app)
    owner = client.get("/api/me").json()["id"]
    with app.state.db.session() as db:
        original = db.scalar(select(Session))
        session_id, created_at, expires_at = original.id, original.created_at, original.expires_at
    previous = client.cookies["ae_session"]
    for _ in range(10):
        client.cookies.delete("ae_csrf")
        if csrf_state == "wrong":
            client.cookies.set("ae_csrf", "wrong")
        response = client.get("/api/me")
        assert response.status_code == 200
        assert response.json()["id"] == owner
        assert client.cookies["ae_session"] != previous
        previous = client.cookies["ae_session"]
    with app.state.db.session() as db:
        assert db.scalar(select(func.count(User.id))) == 1
        assert db.scalar(select(func.count(Session.id))) == 1
        row = db.get(Session, session_id)
        assert row.created_at == created_at
        assert row.expires_at == expires_at
        assert row.token_hash == digest(previous)
        assert row.revoked_at is None
        assert db.get(QuotaBucket, "guest-workspace-issuance").used == 1


def test_csrf_repair_preserves_absolute_expiry_and_caps_cookie_lifetime(tmp_path):
    app = guest_app(tmp_path, limit=1)
    client = TestClient(app)
    owner = client.get("/api/me").json()["id"]
    cutoff = utcnow() + timedelta(minutes=5)
    with app.state.db.session() as db:
        db.scalar(select(Session)).expires_at = cutoff
    client.cookies.delete("ae_csrf")
    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json()["id"] == owner
    for cookie in response.headers.get_list("set-cookie"):
        age = int(cookie.split("Max-Age=", 1)[1].split(";", 1)[0])
        assert 1 <= age <= 300
    with app.state.db.session() as db:
        assert db.scalar(select(Session)).expires_at == cutoff


def test_parallel_csrf_repair_has_one_winner_without_allocating_rows(tmp_path, quota_database_url):
    app = guest_app(tmp_path, limit=60, database_url=quota_database_url)
    original = TestClient(app)
    owner = original.get("/api/me").json()["id"]
    old_cookie = original.cookies["ae_session"]
    barrier = Barrier(8)

    def repair(_):
        client = TestClient(app)
        barrier.wait(timeout=10)
        response = client.get("/api/me", headers={"Cookie": f"ae_session={old_cookie}"})
        return response

    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(repair, range(8)))
    accepted = [response for response in responses if response.status_code == 200]
    denied = [response for response in responses if response.status_code != 200]
    assert len(accepted) == 1
    assert accepted[0].json()["id"] == owner
    assert all(response.status_code == 409 for response in denied)
    assert all(not response.headers.get_list("set-cookie") for response in denied)
    with app.state.db.session() as db:
        assert db.scalar(select(func.count(User.id))) == 1
        assert db.scalar(select(func.count(Session.id))) == 1
        assert db.get(QuotaBucket, "guest-workspace-issuance").used == 1
    winning = TestClient(app)
    winning.cookies.update(accepted[0].cookies)
    assert winning.get("/api/me").json()["id"] == owner
    app.state.db.engine.dispose()


@pytest.mark.parametrize("invalid", ["expired", "revoked", "deleted", "legacy"])
def test_historical_rotated_token_starts_new_guest_when_hint_is_no_longer_valid(tmp_path, invalid):
    app = guest_app(tmp_path, limit=2)
    original = TestClient(app)
    owner = original.get("/api/me").json()["id"]
    old_token = original.cookies["ae_session"]
    original.cookies.delete("ae_csrf")
    assert original.get("/api/me").status_code == 200
    with app.state.db.session() as db:
        row = db.scalar(select(Session).where(Session.user_id == owner))
        if invalid == "expired":
            row.expires_at = utcnow() - timedelta(seconds=1)
        elif invalid == "revoked":
            row.revoked_at = utcnow()
        elif invalid == "deleted":
            db.get(User, owner).deleted_at = utcnow()
        else:
            db.get(User, owner).issuer = "https://accounts.google.com"
    response = TestClient(app).get("/api/me", headers={"Cookie": f"ae_session={old_token}"})
    assert response.status_code == 200
    assert response.json()["id"] != owner
    with app.state.db.session() as db:
        assert db.scalar(select(func.count(User.id))) == 2
        assert db.scalar(select(func.count(Session.id))) == 2
        assert db.get(QuotaBucket, "guest-workspace-issuance").used == 2


def test_parallel_guest_bootstrap_cannot_overrun_shared_capacity(tmp_path, quota_database_url):
    app = guest_app(tmp_path, limit=3, database_url=quota_database_url)
    barrier = Barrier(8)

    def bootstrap(_):
        barrier.wait(timeout=10)
        return TestClient(app).get("/api/me").status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(bootstrap, range(8)))
    assert statuses.count(200) == 3
    assert statuses.count(429) == 5
    with app.state.db.session() as db:
        assert db.scalar(select(func.count(User.id))) == 3
        assert db.scalar(select(func.count(Session.id))) == 3
    app.state.db.engine.dispose()


@pytest.mark.parametrize("name", [
    "guest_workspace_global_limit_per_minute", "answer_global_daily_limit",
])
@pytest.mark.parametrize("value", [0, -1, 100001])
def test_shared_limits_require_positive_bounded_settings(name, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{name: value})


def test_global_reading_budget_blocks_before_provider_and_replay_is_free(env):
    env.settings.answer_global_daily_limit = 1
    result = env.service.create(env.ids.user, env.ids.revision, "reflection", "first")
    assert len(env.provider.calls) == 1
    assert env.service.create(env.ids.user, env.ids.revision, "reflection", "first") == result
    with pytest.raises(HTTPException) as rejected:
        env.service.create(env.ids.user, env.ids.revision, "reflection", "second")
    assert rejected.value.status_code == 429
    assert 1 <= int(rejected.value.headers["Retry-After"]) <= 86400
    assert len(env.provider.calls) == 1


def test_global_reading_budget_does_not_refund_after_deletion_or_restart(env):
    env.settings.answer_global_daily_limit = 1
    env.service.create(env.ids.user, env.ids.revision, "reflection", "first")
    with env.db.session() as db:
        db.execute(delete(ReadingRequest))
    service = ReadingService(env.db, env.retriever, env.provider, env.settings)
    with pytest.raises(HTTPException) as rejected:
        service.create(env.ids.user, env.ids.revision, "reflection", "next")
    assert rejected.value.status_code == 429
    assert len(env.provider.calls) == 1


def test_global_reading_budget_resets_after_utc_day(env):
    env.settings.answer_global_daily_limit = 1
    env.service.create(env.ids.user, env.ids.revision, "reflection", "first")
    with env.db.session() as db:
        db.get(QuotaBucket, "global-reading-day").resets_at = utcnow() - timedelta(seconds=1)
    result = env.service.create(env.ids.user, env.ids.revision, "reflection", "next-day")
    assert result["status"] == "succeeded"
    assert len(env.provider.calls) == 2


def test_failed_admission_does_not_consume_shared_reading_budget(env):
    env.settings.answer_global_daily_limit = 1
    with pytest.raises(HTTPException):
        env.service.create(env.ids.other, env.ids.revision, "reflection", "not-owner")
    assert env.service.create(env.ids.user, env.ids.revision, "reflection", "first")["status"] == (
        "succeeded"
    )


def test_failed_generation_keeps_its_shared_daily_reservation(env):
    env.settings.answer_global_daily_limit = 1
    env.provider.invalid = True
    result = env.service.create(env.ids.user, env.ids.revision, "reflection", "invalid")
    assert result["status"] == "failed"
    assert len(env.provider.calls) == 2
    with pytest.raises(HTTPException) as rejected:
        env.service.create(env.ids.user, env.ids.revision, "reflection", "next")
    assert rejected.value.status_code == 429
    assert len(env.provider.calls) == 2


def test_global_reading_budget_is_atomic_across_distinct_guest_owners(quota_database_url):
    db = create_db(quota_database_url)
    db.initialize()
    owners = []
    with db.session() as session:
        for index in range(6):
            user = User(issuer="anonymous-workspace", subject=str(index))
            session.add(user)
            session.flush()
            profile = Profile(owner_id=user.id)
            session.add(profile)
            session.flush()
            revision = ProfileRevision(
                owner_id=user.id, profile_id=profile.id, revision=1, birth_input={}
            )
            session.add(revision)
            session.flush()
            session.add(Chart(
                owner_id=user.id, profile_revision_id=revision.id,
                input_hash="a" * 64, settings_hash="b" * 64,
                settings={}, manifest={}, facts=[],
            ))
            owners.append((user.id, revision.id))
    settings = Settings(_env_file=None, answer_global_daily_limit=2)
    service = ReadingService(db, None, None, settings)
    barrier = Barrier(len(owners))

    def request(owner):
        barrier.wait(timeout=10)
        try:
            return service.create(*owner, "reflection", "new-key")["status"]
        except HTTPException as rejected:
            return rejected.status_code

    with ThreadPoolExecutor(max_workers=len(owners)) as pool:
        results = list(pool.map(request, owners))
    assert results.count("succeeded") == 2
    assert results.count(429) == 4
    with db.session() as session:
        assert session.get(QuotaBucket, "global-reading-day").used == 2
        assert session.scalar(select(func.count(ReadingRequest.id))) == 2
    db.engine.dispose()


def test_guest_mutation_with_expired_session_prompts_reopening_instead_of_sign_in(tmp_path):
    app = guest_app(tmp_path)
    client = TestClient(app)
    client.get("/api/me")
    with app.state.db.session() as db:
        db.scalar(select(Session)).expires_at = utcnow() - timedelta(seconds=1)
    response = client.post(
        "/api/consent", json={"granted": True, "notice_version": "test"},
        headers={"Origin": "http://testserver", "X-CSRF-Token": client.cookies["ae_csrf"]},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Reopen this workspace page to continue"
