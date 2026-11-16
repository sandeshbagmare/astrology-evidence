"""Server-rendered browser application routes."""

import hashlib
import hmac
import json
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from astrology_evidence import identity, privacy, profiles
from astrology_evidence.answers import routes as answers
from astrology_evidence.corpus import CorpusService, EditionImport
from astrology_evidence.corpus import routes as corpus_routes
from astrology_evidence.identity import get_db, get_settings, require_csrf, require_user
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


class TimeOptionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    birth_date: date
    local_time: time
    timezone: str


def local_time_choices(birth: profiles.BirthInput) -> list[dict[str, Any]]:
    unresolved = birth.model_copy(update={"fold": None})
    resolved = profiles.resolve_birth_time(unresolved)
    assert birth.local_time is not None
    local = datetime.combine(birth.birth_date, birth.local_time)
    options = []
    for fold, instant in enumerate(resolved.candidates):
        # Resolved candidates use the pinned tzdata package, independent of the host.
        offset = local - instant.replace(tzinfo=None)
        seconds = int(offset.total_seconds())
        sign = "+" if seconds >= 0 else "-"
        hours, remainder = divmod(abs(seconds), 3600)
        minutes, extra_seconds = divmod(remainder, 60)
        label_offset = f"UTC{sign}{hours:02d}:{minutes:02d}"
        if extra_seconds:
            label_offset += f":{extra_seconds:02d}"
        occurrence = "First" if fold == 0 else "Second"
        options.append(
            {
                "fold": fold,
                "offset": label_offset,
                "label": f"{occurrence} occurrence ({label_offset})",
            }
        )
    return options


def time_signature(request: Request, birth: profiles.BirthInput) -> str:
    fields = birth.model_dump(
        mode="json", include={"birth_date", "local_time", "timezone", "time_precision"}
    )
    key = request.cookies.get(get_settings(request).session_cookie, "").encode()
    message = json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(key, b"profile-time-review:" + message, hashlib.sha256).hexdigest()


def render(request: Request, name: str, **context: Any):
    context.setdefault("settings", get_settings(request))
    context.setdefault("request", request)
    context.setdefault("path", request.url.path)
    context.setdefault("guest_mode", not get_settings(request).authentication_enabled)
    context.setdefault("user", None)
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
        "guest_mode": not get_settings(request).authentication_enabled,
        "path": request.url.path,
        "ai_enabled": bool(
            get_settings(request).ai_enabled and get_settings(request).provider_reviewed
        ),
    }


@router.get("/", response_class=HTMLResponse, name="home")
def home(request: Request):
    if not get_settings(request).authentication_enabled:
        return dashboard(request)
    return render(request, "home.html", **common(request))


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    if not get_settings(request).authentication_enabled:
        return RedirectResponse("/", status_code=303)
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
    saved_profiles = profiles.list_profiles(request)
    charts = owned_charts(request, user.user_id)
    readings = answers.list_readings(request)
    return render(
        request, "dashboard.html", **common(request, user), profiles=saved_profiles,
        charts=charts, readings=readings,
    )


def owned_charts(request: Request, user_id: str):
    with get_db(request).session() as db:
        rows = db.execute(
            select(Chart, Profile.alias)
            .join(ProfileRevision, Chart.profile_revision_id == ProfileRevision.id)
            .join(Profile, ProfileRevision.profile_id == Profile.id)
            .where(Chart.owner_id == user_id, Profile.owner_id == user_id,
                   Profile.deleted_at.is_(None))
            .order_by(Chart.created_at.desc())
        ).all()
    return [{"id": chart.id, "created_at": chart.created_at, "alias": alias,
             "settings": chart.settings, "fact_count": len(chart.facts)}
            for chart, alias in rows]


@router.get("/profiles", response_class=HTMLResponse)
def profile_index(request: Request):
    user = page_user(request)
    return render(
        request, "profiles.html", **common(request, user), profiles=profiles.list_profiles(request)
    )


@router.get("/charts", response_class=HTMLResponse)
def chart_index(request: Request):
    user = page_user(request)
    return render(request, "charts.html", **common(request, user),
                  charts=owned_charts(request, user.user_id))


@router.get("/profiles/new", response_class=HTMLResponse)
def profile_new(request: Request):
    user = page_user(request)
    return render(request, "profile_form.html", **common(request, user), profile=None)


@router.post("/api/time-options")
def time_options(request: Request, payload: TimeOptionsInput):
    require_csrf(request)
    try:
        birth = profiles.BirthInput(
            birth_date=payload.birth_date,
            local_time=payload.local_time,
            time_precision="exact",
            latitude=0,
            longitude=0,
            timezone=payload.timezone,
            timezone_history="confirmed",
        )
        options = local_time_choices(birth)
    except ValueError as exc:
        raise HTTPException(422, "Local time is invalid for the selected timezone") from exc
    return {"ambiguous": len(options) > 1, "candidates": options}


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
        if revision is None:
            raise HTTPException(404, "Profile revision not found")
    birth = profiles.BirthInput.model_validate(revision.birth_input)
    options = local_time_choices(birth) if birth.time_precision == "exact" else []
    return render(
        request,
        "profile_form.html",
        **common(request, user),
        profile=profile,
        revision=revision,
        fold_options=options,
        time_signature=time_signature(request, birth),
    )


@router.get("/charts/{chart_id}", response_class=HTMLResponse)
def chart_page(request: Request, chart_id: str):
    user = page_user(request)
    chart = profiles.get_chart(request, chart_id)
    return render(request, "chart.html", **common(request, user), chart=chart)


@router.get("/readings/new", response_class=HTMLResponse)
def reading_new(request: Request, profile_id: str | None = None, chart_id: str | None = None):
    user = page_user(request)
    from astrology_evidence.profiles import list_profiles

    saved_profiles = list_profiles(request)
    snapshot = None
    if chart_id is not None:
        if profile_id is not None:
            raise HTTPException(422, "Choose a chart snapshot or a profile, not both")
        chart = profiles.get_chart(request, chart_id)
        revision = profiles.owned_revision(request, user, chart["profile_revision_id"])
        with get_db(request).session() as db:
            profile = db.get(Profile, revision.profile_id)
            if profile is None:
                raise HTTPException(404, "Profile not found")
            snapshot = {"chart_id": chart_id, "profile_revision_id": revision.id,
                        "revision": revision.revision, "birth_input": revision.birth_input,
                        "alias": profile.alias}
    selected = next((p for p in saved_profiles if p["id"] == profile_id), None)
    if profile_id is not None and selected is None:
        raise HTTPException(404, "Profile not found")
    with get_db(request).session() as db:
        charted_revisions = set(db.scalars(
            select(Chart.profile_revision_id).where(Chart.owner_id == user.user_id)
        ))
    candidates = [selected] if selected else saved_profiles
    ready_profiles = [p for p in candidates if p["profile_revision_id"] in charted_revisions]
    needs_chart = [p for p in candidates if p["profile_revision_id"] not in charted_revisions]
    return render(request, "reading_new.html", **common(request, user),
                  profiles=ready_profiles, selected_profile=selected, snapshot=snapshot,
                  needs_chart=[] if snapshot else needs_chart)


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
    return render(
        request,
        "library.html",
        **common(request),
        sources=sources,
        query="",
        search_performed=False,
    )


@router.post("/library/search", response_class=HTMLResponse)
def library_search(request: Request, question: str = Form(...)):
    query = question.strip()
    if not query or len(query) > 2000:
        return render(
            request,
            "library.html",
            **common(request),
            sources=[],
            query=question,
            search_performed=True,
            search_error="Enter a search between 1 and 2,000 characters.",
        )
    retriever = getattr(request.app.state, "retriever", None)
    if retriever is None:
        return render(
            request,
            "library.html",
            **common(request),
            sources=[],
            query=question,
            search_performed=True,
            search_error="Source search is not configured.",
        )
    try:
        sources = [item.model_dump() for item in retriever.search(query, action="display")]
    except (ValueError, RuntimeError):
        return render(
            request,
            "library.html",
            **common(request),
            sources=[],
            query=question,
            search_performed=True,
            search_error="Source search is temporarily unavailable.",
        )
    return render(
        request,
        "library.html",
        **common(request),
        sources=sources,
        query=question,
        search_performed=True,
    )


@router.get("/library/sources/{passage_id}", response_class=HTMLResponse)
def source_page(request: Request, passage_id: str, reading_id: str | None = None):
    service = CorpusService(get_db(request))
    back_url = "/library"
    generation_id = None
    expected_hash = None
    if reading_id is not None:
        user = page_user(request)
        reading = answers.read(request, reading_id)
        evidence = next(
            (
                item
                for item in reading.get("evidence_manifest", {}).get("passages", [])
                if item.get("id") == passage_id
            ),
            None,
        )
        if evidence is None:
            raise HTTPException(404, "Source not found")
        generation_id = evidence["generation_id"]
        expected_hash = evidence["text_hash"]
        back_url = f"/readings/{reading_id}"
        user_context = user
    else:
        user_context = None
    source = service.source(passage_id, action="display", generation_id=generation_id)
    if source is None:
        raise HTTPException(404 if reading_id is None else 410, "Source unavailable")
    if expected_hash is not None and source.text_hash != expected_hash:
        raise HTTPException(410, "Source evidence is no longer available")
    return render(
        request,
        "source.html",
        **common(request, user_context),
        source=source,
        back_url=back_url,
    )


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
    return await run_in_threadpool(dispatch_form, request, form)


def dispatch_form(request: Request, form: dict[str, Any]):
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
            user = require_csrf(adapted)
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
                fold = form.get("fold")
                birth["fold"] = int(str(fold)) if fold in ("0", "1") else None
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
            birth_input = profiles.BirthInput.model_validate(birth)
            if precision == "exact":
                options = local_time_choices(birth_input)
                signature = time_signature(adapted, birth_input)
                if len(options) > 1 and (
                    birth_input.fold is None
                    or not hmac.compare_digest(str(form.get("time_signature", "")), signature)
                ):
                    profile = None
                    if form.get("profile_id"):
                        profile = profiles.get_profile(adapted, str(form["profile_id"]))
                        profile["alias"] = str(form.get("alias", ""))
                        profile["version"] = int(str(form.get("expected_version")))
                    draft = birth_input.model_copy(update={"fold": None}).model_dump(mode="json")
                    response = render(
                        request,
                        "profile_form.html",
                        **common(request, user),
                        profile=profile,
                        revision={"birth_input": draft},
                        draft_alias=str(form.get("alias", "")),
                        storage_consent=form.get("storage_consent") == "true",
                        fold_options=options,
                        time_signature=signature,
                        time_error=(
                            "Review the offsets and choose the first or second occurrence "
                            "for this local time before saving."
                        ),
                    )
                    response.status_code = 422
                    return response
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
                    chart_id=str(form["chart_id"]) if form.get("chart_id") else None,
                ),
                Response(),
            )
            target = (
                "/readings/" + result["reading_id"] if result.get("reading_id") else "/readings"
            )
        elif action == "delete_reading":
            if form.get("confirm_delete") != "DELETE":
                raise HTTPException(422, "Type DELETE to confirm removal of this reading")
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
