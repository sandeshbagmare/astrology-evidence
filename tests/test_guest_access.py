from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from astrology_evidence.config import Settings
from astrology_evidence.main import create_app
from astrology_evidence.models import Session, User, utcnow


@pytest.fixture
def app(tmp_path):
    app = create_app(
        Settings(
            _env_file=None,
            app_env="test",
            database_url=f"sqlite:///{tmp_path}/workspace.db",
            app_public_origin="http://testserver",
        )
    )
    app.state.db.initialize()
    return app


def headers(client):
    return {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.get("/api/me").json()["csrf_token"],
    }


def profile_payload():
    return {
        "alias": "Synthetic guest profile",
        "birth_input": {
            "birth_date": "2000-01-01",
            "time_precision": "unknown",
            "latitude": 28.6,
            "longitude": 77.2,
            "timezone": "Asia/Kolkata",
            "timezone_history": "confirmed",
        },
        "storage_consent": True,
        "notice_version": "privacy-1",
    }


def test_default_mode_opens_a_workspace_without_sign_in(app):
    with TestClient(app) as client:
        response = client.get("/api/me")
        assert response.status_code == 200
        assert response.json()["guest"] is True
        assert response.json()["authentication_enabled"] is False
        assert response.json()["csrf_token"]
        assert response.json()["is_admin"] is False
        assert "HttpOnly" in response.headers.get_list("set-cookie")[0]
        assert client.get("/dashboard").status_code == 200


def test_distinct_browsers_never_share_profiles_or_guest_identity(app):
    with TestClient(app) as owner, TestClient(app) as stranger:
        owner_id = owner.get("/api/me").json()["id"]
        stranger_id = stranger.get("/api/me").json()["id"]
        assert owner_id != stranger_id
        response = owner.post("/api/profiles", json=profile_payload(), headers=headers(owner))
        assert response.status_code == 201
        profile_id = response.json()["id"]
        assert owner.get("/api/me").json()["id"] == owner_id
        assert stranger.get("/api/profiles").json() == []
        assert stranger.get(f"/api/profiles/{profile_id}").status_code == 404


@pytest.mark.parametrize("mutation", ["missing_csrf", "wrong_csrf", "wrong_origin"])
def test_guest_writes_still_require_csrf_and_same_origin(app, mutation):
    with TestClient(app) as client:
        values = headers(client)
        if mutation == "missing_csrf":
            del values["X-CSRF-Token"]
        else:
            values["Origin" if mutation == "wrong_origin" else "X-CSRF-Token"] = "wrong"
        response = client.post("/api/profiles", json=profile_payload(), headers=values)
        assert response.status_code == 403
        assert client.get("/api/profiles").json() == []


@pytest.mark.parametrize(
    "path,method",
    [("/auth/google/start", "get"), ("/auth/google/callback", "get"),
     ("/auth/dev/start", "get"), ("/auth/dev", "post"), ("/auth/logout", "post")],
)
def test_sign_in_and_sign_out_endpoints_are_disabled_in_guest_mode(app, path, method):
    with TestClient(app) as client:
        client.get("/api/me")
        response = getattr(client, method)(path, follow_redirects=False)
        assert response.status_code == 404


def test_public_health_static_and_library_views_do_not_create_guests(app):
    with TestClient(app) as client:
        for path in ("/health/live", "/health/ready", "/static/app.js", "/library"):
            assert client.get(path).status_code == 200
        with app.state.db.session() as db:
            assert db.scalar(select(func.count(User.id))) == 0
        assert "ae_session" not in client.cookies


@pytest.mark.parametrize("path", ["/missing-page", "/admin/corpus", "/robots.txt"])
def test_unknown_and_administrative_navigation_do_not_allocate_guests(app, path):
    with TestClient(app) as client:
        client.get(path, follow_redirects=False)
        with app.state.db.session() as db:
            assert db.scalar(select(func.count(User.id))) == 0
        assert "ae_session" not in client.cookies


def test_bare_cross_origin_mutation_cannot_allocate_a_workspace(app):
    with TestClient(app) as client:
        response = client.post(
            "/api/profiles", json=profile_payload(), headers={"Origin": "https://other.example"}
        )
        assert response.status_code in {401, 403}
        with app.state.db.session() as db:
            assert db.scalar(select(func.count(User.id))) == 0
        assert "ae_session" not in client.cookies


@pytest.mark.parametrize("invalid", ["expires_at", "last_seen_at", "revoked_at", "deleted_user"])
def test_invalid_guest_workspace_gets_a_new_identity_without_reviving_it(app, invalid):
    with TestClient(app) as client:
        previous_id = client.get("/api/me").json()["id"]
        with app.state.db.session() as db:
            if invalid == "deleted_user":
                db.get(User, previous_id).deleted_at = utcnow()
            else:
                row = db.scalar(select(Session).where(Session.user_id == previous_id))
                setattr(row, invalid, utcnow() - timedelta(days=8))
        response = client.get("/api/me")
        assert response.status_code == 200
        assert response.json()["id"] != previous_id
        assert response.json()["guest"] is True


def test_missing_csrf_cookie_rotates_session_without_losing_the_workspace(app):
    with TestClient(app) as client:
        previous_id = client.get("/api/me").json()["id"]
        old_session = client.cookies["ae_session"]
        client.cookies.delete("ae_csrf")
        response = client.get("/api/me")
        assert response.status_code == 200
        assert response.json()["id"] == previous_id
        assert response.json()["csrf_token"]
        assert client.cookies["ae_session"] != old_session


def test_guest_mode_does_not_expose_a_previous_authenticated_account(app):
    with TestClient(app) as client:
        previous_id = client.get("/api/me").json()["id"]
        with app.state.db.session() as db:
            db.get(User, previous_id).issuer = "https://accounts.google.com"
        assert client.get("/api/me").json()["id"] != previous_id


def test_turning_authentication_on_does_not_promote_a_guest_session(app):
    with TestClient(app) as client:
        client.get("/api/me")
        app.state.settings.authentication_enabled = True
        assert client.get("/api/me").status_code == 401


def test_guest_account_delete_keeps_the_old_owner_deleted_and_denies_old_resources(app):
    with TestClient(app) as client:
        previous_id = client.get("/api/me").json()["id"]
        created = client.post("/api/profiles", json=profile_payload(), headers=headers(client))
        assert created.status_code == 201
        profile_id = created.json()["id"]
        response = client.delete("/api/me", headers=headers(client))
        assert response.status_code == 202
        fresh = client.get("/api/me").json()
        assert fresh["id"] != previous_id
        assert client.get(f"/api/profiles/{profile_id}").status_code == 404
        with app.state.db.session() as db:
            assert db.get(User, previous_id).deleted_at is not None


def test_invalid_and_duplicate_cookie_values_do_not_share_or_duplicate_a_workspace(app):
    with TestClient(app) as client:
        response = client.get(
            "/api/me", headers={"Cookie": 'unknown="x;y"; ae_session=bad; ae_csrf=bad'}
        )
        assert response.status_code == 200
        owner = response.json()["id"]
        session = client.cookies["ae_session"]
        csrf = client.cookies["ae_csrf"]
        response = client.get(
            "/api/me",
            headers={"Cookie": f"ae_session=bad; ae_session={session}; ae_csrf={csrf}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == owner
        with app.state.db.session() as db:
            assert db.scalar(select(func.count(User.id))) == 1
