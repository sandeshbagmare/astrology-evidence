"""Bootstrap an opaque, per-browser workspace without a sign-in interaction."""

import secrets
from datetime import timedelta
from typing import Any, cast
from uuid import UUID

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import CursorResult, select, update
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from astrology_evidence.identity import (
    GUEST_ISSUER,
    cookie_name,
    digest,
    get_db,
    get_settings,
    set_cookie,
)
from astrology_evidence.models import QuotaBucket, Session, User, new_id, utcnow


class GuestWorkspaceRateLimited(RuntimeError):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(1, retry_after)
        super().__init__("Guest workspace issuance limit reached")


class GuestWorkspaceChanged(RuntimeError):
    """Another request has rotated this session; do not create a second workspace."""


def _session_hint(token: str) -> str | None:
    identifier, separator, _secret = token.partition(".")
    if not separator:
        return None
    try:
        return str(UUID(identifier))
    except ValueError:
        return None


def _valid_guest(row, user, now) -> bool:
    return (
        row is not None
        and row.revoked_at is None
        and row.expires_at > now
        and row.last_seen_at > now - timedelta(hours=24)
        and user is not None
        and user.deleted_at is None
        and user.issuer == GUEST_ISSUER
    )


def _reserve_guest_issuance(session, settings, now) -> None:
    statement: Any
    if session.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        statement = pg_insert(QuotaBucket)
    else:
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        statement = sqlite_insert(QuotaBucket)
    reset = now + timedelta(minutes=1)
    session.execute(
        statement.values(
            id="guest-workspace-issuance",
            used=0,
            capacity=settings.guest_workspace_global_limit_per_minute,
            resets_at=reset,
        ).on_conflict_do_nothing(index_elements=["id"])
    )
    bucket = session.scalar(
        select(QuotaBucket).where(QuotaBucket.id == "guest-workspace-issuance").with_for_update()
    )
    assert bucket is not None
    if bucket.resets_at <= now:
        bucket.used = 0
        bucket.capacity = settings.guest_workspace_global_limit_per_minute
        bucket.resets_at = reset
    if bucket.used >= settings.guest_workspace_global_limit_per_minute:
        raise GuestWorkspaceRateLimited(int((bucket.resets_at - now).total_seconds()) + 1)
    bucket.used += 1


def prepare_workspace(request: Request) -> tuple[str, str, list[tuple[bytes, bytes]]] | None:
    """Keep valid guest ownership; never inherit a previous authenticated account."""
    settings = get_settings(request)
    database = get_db(request)
    token = request.cookies.get(settings.session_cookie, "")
    csrf = request.cookies.get(cookie_name(settings, "csrf"), "")
    now = utcnow()
    csrf_token = secrets.token_urlsafe(32)
    with database.session() as db:
        row = (
            db.scalar(select(Session).where(Session.token_hash == digest(token))) if token else None
        )
        session_hint = _session_hint(token)
        if row is None and session_hint:
            hinted = db.get(Session, session_hint)
            hinted_user = db.get(User, hinted.user_id) if hinted is not None else None
            if _valid_guest(hinted, hinted_user, now):
                # The opaque ID is a concurrency hint only; it never authorizes access.
                raise GuestWorkspaceChanged
        user = db.get(User, row.user_id) if row else None
        valid = _valid_guest(row, user, now)
        if valid:
            assert user is not None and row is not None
            if csrf and secrets.compare_digest(row.csrf_hash, digest(csrf)):
                return None
            session_token = f"{row.id}.{secrets.token_urlsafe(32)}"
            changed = db.execute(
                update(Session)
                .where(
                    Session.id == row.id,
                    Session.token_hash == digest(token),
                    Session.revoked_at.is_(None),
                    Session.expires_at > now,
                    Session.last_seen_at > now - timedelta(hours=24),
                )
                .values(token_hash=digest(session_token), csrf_hash=digest(csrf_token))
                .execution_options(synchronize_session=False)
            )
            if cast(CursorResult, changed).rowcount != 1:
                raise GuestWorkspaceChanged
            expires_at = row.expires_at
        else:
            _reserve_guest_issuance(db, settings, now)
            user = User(
                issuer=GUEST_ISSUER,
                subject=secrets.token_urlsafe(32),
                display_name="Your workspace",
            )
            db.add(user)
            db.flush()
            owner_id = user.id
            identifier = new_id()
            session_token = f"{identifier}.{secrets.token_urlsafe(32)}"
            if row is not None:
                row.revoked_at = now
            expires_at = now + timedelta(days=7)
            db.add(
                Session(
                    id=identifier,
                    user_id=owner_id,
                    token_hash=digest(session_token),
                    csrf_hash=digest(csrf_token),
                    expires_at=expires_at,
                    last_seen_at=now,
                )
            )

    response = Response()
    max_age = max(0, int((expires_at - utcnow()).total_seconds()))
    set_cookie(
        response, settings, settings.session_cookie, session_token, max_age=max_age, samesite="lax"
    )
    set_cookie(
        response,
        settings,
        cookie_name(settings, "csrf"),
        csrf_token,
        httponly=False,
        max_age=max_age,
    )
    cookies = [(key, value) for key, value in response.raw_headers if key == b"set-cookie"]
    return session_token, csrf_token, cookies


class GuestWorkspaceMiddleware:
    """Create a separate workspace for interactive requests, preserving CSRF/ownership."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        settings = get_settings(request)
        path = scope["path"]
        workspace = path in {"/", "/dashboard", "/settings", "/api/me"} or any(
            path == root or path.startswith(root + "/")
            for root in (
                "/profiles", "/charts", "/readings", "/exports",
                "/api/profiles", "/api/charts", "/api/readings", "/api/reading-requests",
                "/api/jobs", "/api/exports",
            )
        )
        workspace = workspace or (
            path.startswith("/library/sources/") and "reading_id" in request.query_params
        )
        if (
            settings.authentication_enabled
            or not workspace
            or scope["method"] not in {"GET", "HEAD"}
        ):
            await self.app(scope, receive, send)
            return
        try:
            bootstrap = await run_in_threadpool(prepare_workspace, request)
        except GuestWorkspaceChanged:
            response = JSONResponse(
                {"detail": "Workspace changed in another request. Reopen this page."},
                status_code=409,
            )
            await response(scope, receive, send)
            return
        except GuestWorkspaceRateLimited as exc:
            response = JSONResponse(
                {"detail": "Guest workspace issuance limit reached"}, status_code=429
            )
            response.headers["Retry-After"] = str(exc.retry_after)
            await response(scope, receive, send)
            return
        if bootstrap is None:
            await self.app(scope, receive, send)
            return
        session_token, csrf_token, cookies = bootstrap
        scope = dict(scope)
        cookie = request.headers.get("cookie", "")
        cookie += (
            f"; {settings.session_cookie}={session_token}; "
            f"{cookie_name(settings, 'csrf')}={csrf_token}"
        )
        scope["headers"] = [
            (key, value) for key, value in scope["headers"] if key.lower() != b"cookie"
        ] + [(b"cookie", cookie.lstrip("; ").encode("latin-1"))]

        async def with_cookies(message: Message) -> None:
            if message["type"] == "http.response.start":
                message = dict(message)
                message["headers"] = list(message.get("headers", [])) + cookies
            await send(message)

        await self.app(scope, receive, with_cookies)
