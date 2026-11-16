from datetime import timedelta
from hashlib import sha256
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from astrology_evidence.config import Settings
from astrology_evidence.db import create_db
from astrology_evidence.models import OAuthTransaction, Session, User, utcnow


@pytest.fixture
def client():
    from astrology_evidence.identity import router

    app = FastAPI()
    app.state.db = create_db("sqlite://")
    app.state.db.initialize()
    app.state.settings = Settings(
        _env_file=None,
        authentication_enabled=True,
        app_env="test",
        dev_login_enabled=True,
        app_public_origin="http://testserver",
    )
    app.include_router(router)
    with TestClient(app) as value:
        yield value


def login(client):
    bootstrap = client.get("/auth/dev/start")
    assert bootstrap.status_code == 200
    return client.post(
        "/auth/dev",
        headers={"Origin": "http://testserver", "X-CSRF-Token": bootstrap.json()["csrf_token"]},
    )


def headers(client):
    return {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.get("/api/me").json()["csrf_token"],
    }


def test_unauthenticated_is_401(client):
    assert client.get("/api/me").status_code == 401


def test_login_opaque_session_csrf_and_no_identity_from_client(client):
    assert login(client).status_code == 200
    me = client.get("/api/me").json()
    assert me["is_admin"] is False
    assert me["csrf_token"]
    with client.app.state.db.session() as db:
        session = db.scalar(select(Session))
        assert session.token_hash != client.cookies["ae_session"]
        assert session.token_hash == sha256(client.cookies["ae_session"].encode()).hexdigest()
    assert "HttpOnly" in login(client).headers.get_list("set-cookie")[0]


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Origin": "https://evil.example"},
        {"Origin": "http://testserver", "X-CSRF-Token": "bad"},
    ],
)
def test_development_login_requires_browser_csrf(client, headers):
    assert client.post("/auth/dev", headers=headers).status_code == 403


def test_development_login_disabled(client):
    client.app.state.settings.dev_login_enabled = False
    assert client.get("/auth/dev/start").status_code == 404


def test_bootstrap_single_use(client):
    token = client.get("/auth/dev/start").json()["csrf_token"]
    auth_headers = {"Origin": "http://testserver", "X-CSRF-Token": token}
    assert client.post("/auth/dev", headers=auth_headers).status_code == 200
    assert client.post("/auth/dev", headers=auth_headers).status_code == 403


@pytest.mark.parametrize("field", ["expires_at", "last_seen_at", "revoked_at"])
def test_expired_idle_or_revoked_session_denied(client, field):
    login(client)
    with client.app.state.db.session() as db:
        session = db.scalar(select(Session))
        setattr(session, field, utcnow() - timedelta(days=2))
    assert client.get("/api/me").status_code == 401


def test_deleted_user_denied(client):
    login(client)
    with client.app.state.db.session() as db:
        db.scalar(select(User)).deleted_at = utcnow()
    assert client.get("/api/me").status_code == 401


@pytest.mark.parametrize("bad", ["csrf", "origin"])
def test_logout_rejects_csrf_and_origin(client, bad):
    login(client)
    values = headers(client)
    values["X-CSRF-Token" if bad == "csrf" else "Origin"] = "bad"
    assert client.post("/auth/logout", headers=values).status_code == 403
    assert client.get("/api/me").status_code == 200


def test_logout_revokes_replayed_cookie(client):
    login(client)
    cookie = client.cookies["ae_session"]
    assert client.post("/auth/logout", headers=headers(client)).status_code == 204
    client.cookies.set("ae_session", cookie)
    assert client.get("/api/me").status_code == 401


def test_google_missing_configuration_is_503(client):
    assert client.get("/auth/google/start", follow_redirects=False).status_code == 503


def test_oauth_state_is_bound_and_consumed_on_rejection(client):
    client.app.state.settings.google_client_id = "test-client"
    from pydantic import SecretStr

    client.app.state.settings.google_client_secret = SecretStr("synthetic-test-secret")
    start = client.get("/auth/google/start", follow_redirects=False)
    assert start.status_code == 302
    query = parse_qs(urlparse(start.headers["location"]).query)
    assert query["code_challenge_method"] == ["S256"]
    state = query["state"][0]
    callback = f"/auth/google/callback?state={state}&error=access_denied"
    assert client.get(callback).status_code == 400
    with client.app.state.db.session() as db:
        assert db.scalar(select(OAuthTransaction)).consumed_at is not None
    assert client.get(callback).status_code == 400
    assert client.get("/api/me").status_code == 401


@pytest.mark.parametrize(
    "mutation", ["valid", "signature", "issuer", "audience", "expired", "nonce"]
)
def test_google_verifies_signed_tokens_before_creating_user(client, monkeypatch, mutation):
    import time

    import httpx
    from authlib.jose import JsonWebKey, JsonWebToken
    from pydantic import SecretStr

    from astrology_evidence import identity

    settings = client.app.state.settings
    settings.google_client_id = "test-client"
    settings.google_client_secret = SecretStr("synthetic-secret")
    start = client.get("/auth/google/start", follow_redirects=False)
    query = parse_qs(urlparse(start.headers["location"]).query)
    state, nonce = query["state"][0], query["nonce"][0]
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    other = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "sub": "signed-subject",
        "aud": "test-client",
        "iat": now,
        "exp": now + 600,
        "nonce": nonce,
        "email": "test@example.invalid",
        "email_verified": True,
    }
    if mutation == "issuer":
        claims["iss"] = "https://attacker.example"
    elif mutation == "audience":
        claims["aud"] = "other-client"
    elif mutation == "expired":
        claims["exp"] = now - 120
    elif mutation == "nonce":
        claims["nonce"] = "wrong-nonce"
    token = (
        JsonWebToken(["RS256"])
        .encode({"alg": "RS256"}, claims, other if mutation == "signature" else key)
        .decode()
    )
    monkeypatch.setattr(
        identity.OAuth2Client, "fetch_token", lambda *args, **kwargs: {"id_token": token}
    )
    original_get = httpx.Client.get

    def get_keys(self, url, *args, **kwargs):
        if url == "https://www.googleapis.com/oauth2/v3/certs":
            return httpx.Response(
                200,
                json={"keys": [key.as_dict(is_private=False)]},
                request=httpx.Request("GET", url),
            )
        return original_get(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "get", get_keys)
    callback = f"/auth/google/callback?state={state}&code=synthetic-code"
    response = client.get(callback, follow_redirects=False)
    assert response.status_code == (303 if mutation == "valid" else 400)
    assert client.get("/api/me").status_code == (200 if mutation == "valid" else 401)
    assert client.get(callback, follow_redirects=False).status_code == 400


def test_oauth_cross_browser_and_expired_state_rejected(client):
    from pydantic import SecretStr

    client.app.state.settings.google_client_id = "test-client"
    client.app.state.settings.google_client_secret = SecretStr("synthetic-secret")
    start = client.get("/auth/google/start", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    with TestClient(client.app) as stranger:
        assert stranger.get(f"/auth/google/callback?state={state}&code=x").status_code == 400
    with client.app.state.db.session() as db:
        db.scalar(select(OAuthTransaction)).expires_at = utcnow() - timedelta(seconds=1)
    assert client.get(f"/auth/google/callback?state={state}&code=x").status_code == 400
