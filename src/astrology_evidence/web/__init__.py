"""Server-rendered browser application routes."""

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select

from astrology_evidence import identity, privacy, profiles
from astrology_evidence.answers import routes as answers
from astrology_evidence.corpus import CorpusService, EditionImport
from astrology_evidence.corpus import routes as corpus_routes
from astrology_evidence.identity import get_db, get_settings, require_user
from astrology_evidence.models import (
    ActiveCorpus,
    Chart,
    CorpusGeneration,
    Edition,
    Profile,
    ProfileRevision,
)

BASE = Path(__file__).parent
router = APIRouter()
templates = Jinja2Templates(directory=str(BASE / "templates"))


def render(request: Request, name: str, **context: Any):
    context.setdefault("settings", get_settings(request))
    context.setdefault("request", request)
    context.setdefault(
        "csrf", request.cookies.get(identity.cookie_name(get_settings(request), "csrf"), "")
    )
    context.setdefault("request_key", str(uuid4()))
    return templates.TemplateResponse(request=request, name=name, context=context)


def page_user(request: Request):
    try:
        return require_user(request)
    except HTTPException as exc:
        if exc.status_code == 401:
            raise HTTPException(303, headers={"Location": "/login"}) from exc
        raise


def common(request: Request, user=None):
    return {
        "user": user,
        "ai_enabled": bool(
            get_settings(request).ai_enabled and get_settings(request).provider_reviewed
        ),
    }


@router.get("/", response_class=HTMLResponse, name="home")
def home(request: Request):
    return render(request, "home.html", **common(request))


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    response = Response()
    state = ""
    try:
        state = identity.dev_start(request, response)["csrf_token"]
    except HTTPException:
        pass
    page = render(request, "login.html", **common(request), dev_state=state)
    for key, value in response.raw_headers:
        if key == b"set-cookie":
            page.raw_headers.append((key, value))
    return page


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = page_user(request)
    with get_db(request).session() as db:
        profiles = db.scalars(
            select(Profile).where(Profile.owner_id == user.user_id, Profile.deleted_at.is_(None))
        ).all()
        charts = db.scalars(
            select(Chart).where(Chart.owner_id == user.user_id).order_by(Chart.created_at.desc())
        ).all()
    return render(
        request, "dashboard.html", **common(request, user), profiles=profiles, charts=charts
    )


@router.get("/profiles/new", response_class=HTMLResponse)
def profile_new(request: Request):
    user = page_user(request)
    return render(request, "profile_form.html", **common(request, user), profile=None)


@router.get("/profiles/{profile_id}/edit", response_class=HTMLResponse)
def profile_edit(request: Request, profile_id: str):
    user = page_user(request)
    with get_db(request).session() as db:
        profile = db.scalar(
            select(Profile).where(
                Profile.id == profile_id,
                Profile.owner_id == user.user_id,
                Profile.deleted_at.is_(None),
            )
        )
        if profile is None:
            raise HTTPException(404, "Profile not found")
        revision = db.scalar(
            select(ProfileRevision).where(
                ProfileRevision.profile_id == profile.id,
                ProfileRevision.revision == profile.version,
            )
        )
    return render(
        request, "profile_form.html", **common(request, user), profile=profile, revision=revision
    )


@router.get("/charts/{chart_id}", response_class=HTMLResponse)
def chart_page(request: Request, chart_id: str):
    user = page_user(request)
    chart = profiles.get_chart(request, chart_id)
    return render(request, "chart.html", **common(request, user), chart=chart)


@router.get("/readings/new", response_class=HTMLResponse)
def reading_new(request: Request):
    user = page_user(request)
    from astrology_evidence.profiles import list_profiles

    profiles = list_profiles(request)
    return render(request, "reading_new.html", **common(request, user), profiles=profiles)


@router.get("/readings", response_class=HTMLResponse)
def readings(request: Request):
    user = page_user(request)
    rows = answers.list_readings(request)
    return render(request, "readings.html", **common(request, user), readings=rows)


@router.get("/readings/{reading_id}", response_class=HTMLResponse)
def reading_page(request: Request, reading_id: str):
    user = page_user(request)
    reading = answers.read(request, reading_id)
    return render(request, "reading.html", **common(request, user), reading=reading)


@router.get("/library", response_class=HTMLResponse)
def library(request: Request):
    sources = []
    service = CorpusService(get_db(request))
    with get_db(request).session() as db:
        active = db.get(ActiveCorpus, 1)
        generation = db.get(CorpusGeneration, active.generation_id) if active else None
        identifiers = list(generation.manifest.get("passage_hashes", {})) if generation else []
    for identifier in identifiers:
        passage = service.source(identifier)
        if passage:
            sources.append(passage.model_dump())
    return render(request, "library.html", **common(request), sources=sources)


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    user = page_user(request)
    return render(request, "settings.html", **common(request, user))


@router.get("/admin/corpus", response_class=HTMLResponse)
def admin_corpus(request: Request):
    user = page_user(request)
    if not user.is_admin:
        raise HTTPException(403, "Curator access required")
    with get_db(request).session() as db:
        editions = db.scalars(select(Edition)).all()
    return render(request, "admin_corpus.html", **common(request, user), editions=editions)


@router.post("/web/action", response_class=HTMLResponse)
async def form_action(request: Request):
    """Translate ordinary forms to the same validated, CSRF-protected API handlers."""
    form = dict(await request.form())
    scope = dict(request.scope)
    scope["headers"] = [
        (k, v)
        for k, v in request.scope["headers"]
        if k.lower() not in (b"x-csrf-token", b"idempotency-key")
    ]
    scope["headers"] += [
        (b"x-csrf-token", str(form.get("csrf_token", "")).encode()),
        (b"idempotency-key", str(form.get("request_key", "")).encode()),
    ]
    adapted = Request(scope)
    action = form.get("action", "")
    target = "/dashboard"
    try:
        if action == "dev_login":
            response = RedirectResponse("/dashboard", status_code=303)
            identity.dev_login(adapted, response)
            return response
        if action == "logout":
            response = identity.logout(adapted)
            response.status_code = 303
            response.headers["location"] = "/login"
            return response
        if action == "profile":
            precision = form.get("time_precision", "unknown")
            birth = {
                "birth_date": form.get("birth_date"),
                "time_precision": precision,
                "latitude": float(str(form.get("latitude", ""))),
                "longitude": float(str(form.get("longitude", ""))),
                "timezone": form.get("timezone"),
                "timezone_history": form.get("timezone_history", "uncertain"),
            }
            if precision == "exact":
                birth["local_time"] = form.get("local_time")
            elif precision == "approximate":
                birth.update(
                    earliest_local=form.get("earliest_local"), latest_local=form.get("latest_local")
                )
            payload: dict[str, Any] = {
                "alias": form.get("alias", ""),
                "birth_input": birth,
                "storage_consent": form.get("storage_consent") == "true",
                "notice_version": "privacy-1",
            }
            if form.get("profile_id"):
                payload["expected_version"] = int(str(form.get("expected_version")))
                profiles.update_profile(
                    adapted, str(form["profile_id"]), profiles.ProfilePatch.model_validate(payload)
                )
            else:
                profiles.create_profile(adapted, profiles.ProfileCreate.model_validate(payload))
        elif action == "chart":
            profile = profiles.get_profile(adapted, str(form["profile_id"]))
            chart = profiles.create_chart(
                adapted, profiles.ChartCreate(profile_revision_id=profile["profile_revision_id"])
            )
            target = "/charts/" + chart["id"]
        elif action == "reading":
            result = answers.create(
                adapted,
                answers.ReadingCreate(
                    profile_revision_id=str(form.get("profile_revision_id", "")),
                    question=str(form.get("question", "")),
                ),
                Response(),
            )
            target = (
                "/readings/" + result["reading_id"] if result.get("reading_id") else "/readings"
            )
        elif action == "delete_reading":
            answers.delete(adapted, str(form["reading_id"]))
            target = "/readings"
        elif action == "delete_profile":
            privacy.delete_profile(adapted, str(form["profile_id"]))
        elif action == "consent":
            answers.consent(
                adapted,
                answers.ConsentInput(
                    granted=form.get("granted") == "true", notice_version="privacy-1"
                ),
            )
            target = "/settings"
        elif action == "export":
            result = privacy.export_account(adapted)
            return render(request, "operation.html", title="Export queued", result=result)
        elif action == "delete_account":
            if form.get("confirm") != "DELETE":
                raise HTTPException(422, "Type DELETE to confirm account deletion")
            result = privacy.delete_account(adapted)
            return render(
                request,
                "operation.html",
                title="Account access revoked; deletion queued",
                result=result,
            )
        elif action == "import":
            corpus_routes.import_edition(
                adapted, EditionImport.model_validate(json.loads(str(form.get("metadata", ""))))
            )
            target = "/admin/corpus"
        elif action in ("publish", "withdraw"):
            getattr(corpus_routes, action)(adapted, str(form["edition_id"]))
            target = "/admin/corpus"
        else:
            raise HTTPException(400, "Unknown form action")
    except (HTTPException, ValidationError, ValueError, KeyError) as exc:
        message = (
            str(exc.detail)
            if isinstance(exc, HTTPException)
            else "Invalid input. Check all required fields and birth-time uncertainty."
        )
        response = render(
            request,
            "operation.html",
            title="Request could not be completed",
            error=message,
            result={},
            values={k: v for k, v in form.items() if k not in ("csrf_token", "request_key")},
        )
        response.status_code = exc.status_code if isinstance(exc, HTTPException) else 422
        return response
    return RedirectResponse(target, status_code=303)


@router.get("/exports/{export_id}", response_class=HTMLResponse)
def export_page(request: Request, export_id: str, job_id: str):
    user = page_user(request)
    result = privacy.job_status(request, job_id)
    return render(
        request,
        "operation.html",
        **common(request, user),
        title="Export status",
        result={**result, "export_id": export_id, "job_id": job_id},
    )
