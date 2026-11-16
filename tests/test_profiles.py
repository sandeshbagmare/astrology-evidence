from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import select

from astrology_evidence.config import Settings
from astrology_evidence.db import create_db
from astrology_evidence.identity import issue_login
from astrology_evidence.identity import router as identity_router
from astrology_evidence.models import Chart, Profile, ProfileRevision, User

BIRTH = {
    "birth_date": "2000-01-01",
    "local_time": "12:00",
    "time_precision": "exact",
    "latitude": 28.6,
    "longitude": 77.2,
    "timezone": "Asia/Kolkata",
    "timezone_history": "confirmed",
}


@pytest.fixture
def client():
    from astrology_evidence.profiles import router

    app = FastAPI()
    app.state.db = create_db("sqlite://")
    app.state.db.initialize()
    app.state.settings = Settings(
        _env_file=None,
        app_env="test",
        authentication_enabled=True,
        dev_login_enabled=True,
        app_public_origin="http://testserver",
    )
    app.include_router(identity_router)
    app.include_router(router)
    with TestClient(app) as client:
        bootstrap = client.get("/auth/dev/start").json()
        client.post(
            "/auth/dev",
            headers={"Origin": "http://testserver", "X-CSRF-Token": bootstrap["csrf_token"]},
        )
        yield client


def headers(client):
    return {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.get("/api/me").json()["csrf_token"],
    }


def create(client, **changes):
    payload = {
        "alias": "Synthetic",
        "birth_input": BIRTH,
        "storage_consent": True,
        "notice_version": "privacy-1",
    } | changes
    return client.post("/api/profiles", json=payload, headers=headers(client))


@pytest.mark.parametrize(
    "birth",
    [
        BIRTH | {"latitude": 100},
        BIRTH | {"time_precision": "unknown"},
        BIRTH | {"birth_date": "1899-01-01"},
        BIRTH | {"timezone": "Not/AZone"},
        BIRTH | {"latitude": "28.6"},
    ],
)
def test_invalid_birth_data_never_saved(client, birth):
    assert create(client, birth_input=birth).status_code == 422
    assert client.get("/api/profiles").json() == []


def test_storage_consent_and_csrf_required(client):
    assert create(client, storage_consent=False).status_code == 400
    assert (
        client.post(
            "/api/profiles",
            json={"birth_input": BIRTH, "storage_consent": True, "notice_version": "privacy-1"},
        ).status_code
        == 403
    )


def test_server_rejects_supplied_owner(client):
    assert create(client, owner_id="someone-else").status_code == 422


def test_revisions_immutable_and_stale_write_conflicts(client):
    original = create(client).json()
    patch = {
        "expected_version": 1,
        "alias": "Changed",
        "birth_input": BIRTH | {"local_time": "13:00"},
        "storage_consent": True,
        "notice_version": "privacy-1",
    }
    response = client.patch(f"/api/profiles/{original['id']}", json=patch, headers=headers(client))
    assert response.status_code == 200
    assert response.json()["version"] == 2
    assert (
        client.patch(
            f"/api/profiles/{original['id']}", json=patch, headers=headers(client)
        ).status_code
        == 409
    )
    with client.app.state.db.session() as db:
        revisions = db.scalars(select(ProfileRevision).order_by(ProfileRevision.revision)).all()
        assert len(revisions) == 2
        assert revisions[0].birth_input["local_time"] == "12:00:00"
        assert revisions[1].birth_input["local_time"] == "13:00:00"


def test_other_user_cannot_see_profile_or_revision(client):
    profile = create(client).json()
    app = client.app
    with app.state.db.session() as db:
        other = User(issuer="test", subject="other")
        db.add(other)
        db.flush()
        other_id = other.id
    response = JSONResponse({})
    issue_login(app.state.db, app.state.settings, other_id, response)
    with TestClient(app) as other:
        for cookie in response.headers.getlist("set-cookie"):
            key, value = cookie.split(";", 1)[0].split("=", 1)
            other.cookies.set(key, value)
        assert other.get("/api/profiles").json() == []
        assert other.get(f"/api/profiles/{profile['id']}").status_code == 404
        assert (
            other.post(
                "/api/charts",
                json={"profile_revision_id": profile["profile_revision_id"]},
                headers=headers(other),
            ).status_code
            == 404
        )


def test_deleted_profile_revision_cannot_create_chart(client):
    profile = create(client).json()
    from astrology_evidence.models import utcnow

    with client.app.state.db.session() as db:
        db.get(Profile, profile["id"]).deleted_at = utcnow()
    assert (
        client.post(
            "/api/charts",
            json={"profile_revision_id": profile["profile_revision_id"]},
            headers=headers(client),
        ).status_code
        == 404
    )


def test_chart_rejects_client_engine_paths(client):
    profile = create(client).json()
    assert (
        client.post(
            "/api/charts",
            json={
                "profile_revision_id": profile["profile_revision_id"],
                "settings": {"ephemeris_path": "C:/private"},
            },
            headers=headers(client),
        ).status_code
        == 422
    )


def test_chart_cache_tracks_runtime_without_rewriting_saved_snapshots(client):
    profile = create(client).json()
    snapshot = {
        "manifest": {
            "input_hash": "a" * 64,
            "settings_hash": "b" * 64,
            "reproducibility_hash": "c" * 64,
            "engine_version": "original-runtime",
            "computed_at": "2000-01-01T00:00:00Z",
        },
        "settings": {},
        "facts": [{"fact_id": "original:sun:longitude", "value": 100.0}],
        "unavailable_facts": {},
    }
    client.app.state.calculator = lambda birth, settings: SimpleNamespace(
        model_dump=lambda **kwargs: snapshot
    )

    def calculate():
        response = client.post(
            "/api/charts",
            json={"profile_revision_id": profile["profile_revision_id"]},
            headers=headers(client),
        )
        assert response.status_code == 201
        return response.json()

    first = calculate()
    snapshot["manifest"]["computed_at"] = "2000-01-02T00:00:00Z"
    assert calculate()["id"] == first["id"]
    snapshot["manifest"].update(
        reproducibility_hash="d" * 64, engine_version="updated-runtime"
    )
    snapshot["facts"] = [{"fact_id": "updated:sun:longitude", "value": 101.0}]
    updated = calculate()
    assert updated["id"] != first["id"]
    assert updated["facts"][0]["value"] == 101.0
    assert updated["manifest"]["engine_version"] == "updated-runtime"
    assert updated["manifest"]["settings_hash"] == first["manifest"]["settings_hash"]
    assert client.get("/api/charts/" + first["id"]).json() == first
    assert calculate()["id"] == updated["id"]


def test_legacy_chart_cache_row_remains_readable_after_runtime_cache_upgrade(client):
    profile = create(client).json()
    with client.app.state.db.session() as db:
        legacy = Chart(
            owner_id=profile["owner_id"],
            profile_revision_id=profile["profile_revision_id"],
            input_hash="a" * 64,
            settings_hash="b" * 64,
            settings={},
            manifest={"input_hash": "a" * 64, "settings_hash": "b" * 64},
            facts=[{"fact_id": "old", "value": 100.0}],
            unavailable_facts={},
        )
        db.add(legacy)
        db.flush()
        legacy_id = legacy.id
    client.app.state.calculator = lambda birth, settings: SimpleNamespace(
        model_dump=lambda **kwargs: {
            "manifest": {
                "input_hash": "a" * 64,
                "settings_hash": "b" * 64,
                "reproducibility_hash": "c" * 64,
            },
            "settings": {},
            "facts": [{"fact_id": "new", "value": 101.0}],
            "unavailable_facts": {},
        }
    )
    response = client.post(
        "/api/charts",
        json={"profile_revision_id": profile["profile_revision_id"]},
        headers=headers(client),
    )
    assert response.status_code == 201
    assert response.json()["id"] != legacy_id
    assert client.get("/api/charts/" + legacy_id).json()["facts"][0]["value"] == 100.0
