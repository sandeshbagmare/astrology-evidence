"""Opaque sessions, browser-bound OAuth and explicit local demo identity."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Literal, cast
from urllib.parse import urlparse

import httpx
from authlib.common.errors import AuthlibBaseError
from authlib.integrations.httpx_client import OAuth2Client
from authlib.jose import JsonWebToken
from authlib.oidc.core import CodeIDToken
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from joserfc.errors import JoseError
from sqlalchemy import CursorResult, select, update

from astrology_evidence.config import Settings
from astrology_evidence.db import Database
from astrology_evidence.models import OAuthTransaction, Session, User, utcnow

router = APIRouter()
GOOGLE_ISSUER = "https://accounts.google.com"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def cookie_name(settings: Settings, suffix: str) -> str:
    return ("__Host-" if settings.secure_cookies else "ae_") + suffix


def set_cookie(
    response: Response,
    settings: Settings,
    name: str,
    token: str,
    *,
    httponly: bool = True,
    max_age: int = 600,
    samesite: Literal["lax", "strict", "none"] = "strict",
) -> None:
    response.set_cookie(
        name,
        token,
        max_age=max_age,
        secure=settings.secure_cookies,
        httponly=httponly,
        samesite=samesite,
        path="/",
    )


@dataclass(frozen=True)
class UserContext:
    user_id: str
    is_admin: bool


def require_origin(request: Request) -> None:
    if request.headers.get("origin") != get_settings(request).app_public_origin:
        raise HTTPException(403, "Invalid request origin")


def require_user(request: Request) -> UserContext:
    token = request.cookies.get(get_settings(request).session_cookie, "")
    now = utcnow()
    with get_db(request).session() as db:
        row = db.scalar(select(Session).where(Session.token_hash == digest(token)))
        if (
            row is None
            or row.revoked_at
            or row.expires_at <= now
            or row.last_seen_at <= now - timedelta(hours=24)
        ):
            raise HTTPException(401, "Sign in required")
        user = db.get(User, row.user_id)
        if user is None or user.deleted_at:
            raise HTTPException(401, "Sign in required")
        row.last_seen_at = now
        return UserContext(user.id, user.is_admin)


def require_csrf(request: Request) -> UserContext:
    user = require_user(request)
    require_origin(request)
    token = request.cookies.get(get_settings(request).session_cookie, "")
    csrf = request.headers.get("x-csrf-token", "")
    with get_db(request).session() as db:
        row = db.scalar(select(Session).where(Session.token_hash == digest(token)))
        if not csrf or row is None or not secrets.compare_digest(row.csrf_hash, digest(csrf)):
            raise HTTPException(403, "Invalid CSRF token")
    return user


def issue_login(
    db: Database, settings: Settings, user_id: str, response: Response, old_token: str | None = None
) -> None:
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    now = utcnow()
    with db.session() as session:
        if old_token:
            session.execute(
                update(Session)
                .where(Session.token_hash == digest(old_token))
                .values(revoked_at=now)
            )
        session.add(
            Session(
                user_id=user_id,
                token_hash=digest(token),
                csrf_hash=digest(csrf),
                expires_at=now + timedelta(days=7),
                last_seen_at=now,
            )
        )
    set_cookie(response, settings, settings.session_cookie, token, max_age=604800, samesite="lax")
    set_cookie(
        response, settings, cookie_name(settings, "csrf"), csrf, httponly=False, max_age=604800
    )


@router.get("/api/me")
def me(request: Request):
    context = require_user(request)
    with get_db(request).session() as db:
        user = db.get(User, context.user_id)
        if user is None or user.deleted_at:
            raise HTTPException(401, "Sign in required")
        return {
            "id": user.id,
            "display_name": user.display_name,
            "is_admin": user.is_admin,
            "csrf_token": request.cookies.get(cookie_name(get_settings(request), "csrf"), ""),
        }


@router.post("/auth/logout", status_code=204)
def logout(request: Request):
    require_csrf(request)
    settings = get_settings(request)
    with get_db(request).session() as db:
        db.execute(
            update(Session)
            .where(Session.token_hash == digest(request.cookies.get(settings.session_cookie, "")))
            .values(revoked_at=utcnow())
        )
    response = Response(status_code=204)
    for name in (settings.session_cookie, cookie_name(settings, "csrf")):
        response.delete_cookie(name, path="/", secure=settings.secure_cookies)
    return response


def require_dev(request: Request) -> None:
    settings = get_settings(request)
    if (
        not settings.dev_login_enabled
        or settings.app_env == "production"
        or urlparse(settings.app_public_origin).hostname
        not in {"localhost", "127.0.0.1", "::1", "testserver"}
    ):
        raise HTTPException(404, "Not found")


def new_transaction(request: Request):
    state, browser = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    transaction = OAuthTransaction(
        state_hash=digest(state),
        browser_hash=digest(browser),
        nonce=secrets.token_urlsafe(32),
        code_verifier=secrets.token_urlsafe(48),
        expires_at=utcnow() + timedelta(minutes=10),
    )
    with get_db(request).session() as db:
        db.add(transaction)
    return state, browser, transaction


def consume_transaction(request: Request, state: str, cookie: str) -> OAuthTransaction:
    now = utcnow()
    with get_db(request).session() as db:
        transaction = db.scalar(
            select(OAuthTransaction).where(
                OAuthTransaction.state_hash == digest(state),
                OAuthTransaction.browser_hash == digest(request.cookies.get(cookie, "")),
                OAuthTransaction.consumed_at.is_(None),
                OAuthTransaction.expires_at > now,
            )
        )
        if transaction is None:
            raise HTTPException(400, "Invalid or expired sign-in transaction")
        result = db.execute(
            update(OAuthTransaction)
            .where(OAuthTransaction.id == transaction.id, OAuthTransaction.consumed_at.is_(None))
            .values(consumed_at=now)
        )
        if cast(CursorResult, result).rowcount != 1:
            raise HTTPException(400, "Sign-in transaction already used")
        return transaction


@router.get("/auth/dev/start")
def dev_start(request: Request, response: Response):
    require_dev(request)
    state, browser, _ = new_transaction(request)
    set_cookie(response, get_settings(request), cookie_name(get_settings(request), "dev"), browser)
    return {"csrf_token": state, "notice": "Local synthetic demo only; do not enter real data."}


@router.post("/auth/dev")
def dev_login(request: Request, response: Response):
    require_dev(request)
    require_origin(request)
    settings = get_settings(request)
    try:
        consume_transaction(
            request, request.headers.get("x-csrf-token", ""), cookie_name(settings, "dev")
        )
    except HTTPException as exc:
        raise HTTPException(403, "Invalid sign-in CSRF token") from exc
    with get_db(request).session() as db:
        user = db.scalar(select(User).where(User.issuer == "local-demo", User.subject == "demo"))
        if user is None:
            user = User(issuer="local-demo", subject="demo", display_name="Synthetic demo")
            db.add(user)
            db.flush()
        if user.deleted_at:
            raise HTTPException(403, "Demo account deleted")
        user_id = user.id
    issue_login(
        get_db(request), settings, user_id, response, request.cookies.get(settings.session_cookie)
    )
    return {"id": user_id, "demo": True}


def oauth_client(settings: Settings) -> OAuth2Client:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(503, "Google sign-in is not configured")
    return OAuth2Client(
        settings.google_client_id,
        settings.google_client_secret.get_secret_value(),
        scope="openid email profile",
        code_challenge_method="S256",
        redirect_uri=settings.app_public_origin + "/auth/google/callback",
        timeout=15,
    )


@router.get("/auth/google/start")
def google_start(request: Request):
    settings = get_settings(request)
    with oauth_client(settings) as client:
        state, browser, transaction = new_transaction(request)
        url, _ = client.create_authorization_url(
            "https://accounts.google.com/o/oauth2/v2/auth",
            state=state,
            nonce=transaction.nonce,
            code_verifier=transaction.code_verifier,
        )
    response = RedirectResponse(url, status_code=302)
    set_cookie(response, settings, cookie_name(settings, "oauth"), browser, samesite="lax")
    return response


def exchange_google(request: Request, code: str, transaction: OAuthTransaction) -> dict:
    settings = get_settings(request)
    with oauth_client(settings) as client:
        token = client.fetch_token(
            "https://oauth2.googleapis.com/token",
            code=code,
            code_verifier=transaction.code_verifier,
        )
    with httpx.Client(timeout=15) as client:
        response = client.get("https://www.googleapis.com/oauth2/v3/certs")
        response.raise_for_status()
        keys = response.json()
    claims = JsonWebToken(["RS256"]).decode(
        token["id_token"],
        keys,
        claims_cls=CodeIDToken,
        claims_options={
            "iss": {"essential": True, "values": [GOOGLE_ISSUER, "accounts.google.com"]},
            "aud": {"essential": True, "value": settings.google_client_id},
            "exp": {"essential": True},
            "sub": {"essential": True},
            "nonce": {"essential": True, "value": transaction.nonce},
        },
        claims_params={
            "nonce": transaction.nonce,
            "client_id": settings.google_client_id,
            "access_token": token.get("access_token"),
        },
    )
    claims.validate(leeway=30)
    return dict(claims)


@router.get("/auth/google/callback")
def google_callback(request: Request, state: str = "", code: str = "", error: str = ""):
    settings = get_settings(request)
    transaction = consume_transaction(request, state, cookie_name(settings, "oauth"))
    if error or not code:
        raise HTTPException(400, "Sign-in was cancelled or rejected")
    try:
        claims = exchange_google(request, code, transaction)
    except (httpx.HTTPError, AuthlibBaseError, JoseError, ValueError, KeyError) as exc:
        raise HTTPException(400, "Unable to verify Google sign-in") from exc
    # Token verification is completed before any user is created.
    with get_db(request).session() as db:
        user = db.scalar(
            select(User).where(User.issuer == GOOGLE_ISSUER, User.subject == claims["sub"])
        )
        if user is None:
            user = User(issuer=GOOGLE_ISSUER, subject=claims["sub"])
            db.add(user)
        if user.deleted_at:
            raise HTTPException(403, "Account unavailable")
        user.display_name = str(claims.get("name", ""))[:255]
        user.email = claims.get("email") if claims.get("email_verified") is True else None
        db.flush()
        user_id = user.id
    response = RedirectResponse("/", status_code=303)
    issue_login(
        get_db(request), settings, user_id, response, request.cookies.get(settings.session_cookie)
    )
    response.delete_cookie(cookie_name(settings, "oauth"), path="/", secure=settings.secure_cookies)
    return response
