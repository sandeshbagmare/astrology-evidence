"""Owned birth profiles, append-only revisions and chart snapshots."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update

from astrology_evidence.calculations import (
    BirthInput,
    ChartSettings,
    calculate_chart,
    resolve_birth_time,
)
from astrology_evidence.identity import UserContext, get_db, require_csrf, require_user
from astrology_evidence.models import Chart, Consent, Profile, ProfileRevision

router = APIRouter()


class ProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alias: str = Field(default="", max_length=80)
    birth_input: BirthInput
    storage_consent: bool
    notice_version: str = Field(min_length=1, max_length=80)


class ProfilePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1)
    alias: str | None = Field(default=None, max_length=80)
    birth_input: BirthInput
    storage_consent: bool
    notice_version: str = Field(min_length=1, max_length=80)


class PublicChartSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tradition: Literal["jyotish"] = "jyotish"
    zodiac: Literal["sidereal"] = "sidereal"
    ayanamsha: Literal["lahiri"] = "lahiri"
    house_system: Literal["whole_sign"] = "whole_sign"
    node_mode: Literal["mean"] = "mean"


class ChartCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_revision_id: str
    settings: PublicChartSettings = Field(default_factory=PublicChartSettings)


def validate_birth(birth: BirthInput) -> None:
    try:
        resolve_birth_time(birth)
    except ValueError as exc:
        raise HTTPException(422, "Birth time does not exist in the selected timezone") from exc


def profile_json(profile: Profile, revision: ProfileRevision) -> dict[str, Any]:
    return {
        "id": profile.id,
        "owner_id": profile.owner_id,
        "alias": profile.alias,
        "version": profile.version,
        "revision": revision.revision,
        "profile_revision_id": revision.id,
        "birth_input": revision.birth_input,
    }


def owned_revision(request: Request, user: UserContext, revision_id: str):
    with get_db(request).session() as db:
        revision = db.scalar(
            select(ProfileRevision).where(
                ProfileRevision.id == revision_id, ProfileRevision.owner_id == user.user_id
            )
        )
        if revision is None:
            raise HTTPException(404, "Profile not found")
        profile = db.scalar(
            select(Profile).where(
                Profile.id == revision.profile_id,
                Profile.owner_id == user.user_id,
                Profile.deleted_at.is_(None),
            )
        )
        if profile is None:
            raise HTTPException(404, "Profile not found")
        return revision


@router.post("/api/profiles", status_code=201)
def create_profile(request: Request, payload: ProfileCreate):
    user = require_csrf(request)
    if not payload.storage_consent:
        raise HTTPException(400, "Storage consent is required")
    validate_birth(payload.birth_input)
    with get_db(request).session() as db:
        profile = Profile(owner_id=user.user_id, alias=payload.alias)
        db.add(profile)
        db.flush()
        revision = ProfileRevision(
            profile_id=profile.id,
            owner_id=user.user_id,
            revision=1,
            birth_input=payload.birth_input.model_dump(mode="json"),
        )
        db.add(revision)
        db.add(
            Consent(
                user_id=user.user_id,
                purpose="profile_storage",
                notice_version=payload.notice_version,
            )
        )
        db.flush()
        return profile_json(profile, revision)


@router.get("/api/profiles")
def list_profiles(request: Request):
    user = require_user(request)
    with get_db(request).session() as db:
        profiles = db.scalars(
            select(Profile).where(Profile.owner_id == user.user_id, Profile.deleted_at.is_(None))
        ).all()
        return [
            profile_json(
                p,
                db.scalar(
                    select(ProfileRevision).where(
                        ProfileRevision.profile_id == p.id, ProfileRevision.revision == p.version
                    )
                ),
            )
            for p in profiles
        ]


@router.get("/api/profiles/{profile_id}")
def get_profile(request: Request, profile_id: str):
    user = require_user(request)
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
        return profile_json(profile, revision)


@router.patch("/api/profiles/{profile_id}")
def update_profile(request: Request, profile_id: str, payload: ProfilePatch):
    user = require_csrf(request)
    if not payload.storage_consent:
        raise HTTPException(400, "Storage consent is required")
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
        if profile.version != payload.expected_version:
            raise HTTPException(409, "Profile revision conflict")
        validate_birth(payload.birth_input)
        result = db.execute(
            update(Profile)
            .where(
                Profile.id == profile.id,
                Profile.owner_id == user.user_id,
                Profile.version == payload.expected_version,
                Profile.deleted_at.is_(None),
            )
            .values(version=payload.expected_version + 1)
        )
        if result.rowcount != 1:
            raise HTTPException(409, "Profile revision conflict")
        if payload.alias is not None:
            profile.alias = payload.alias
        revision = ProfileRevision(
            profile_id=profile.id,
            owner_id=user.user_id,
            revision=profile.version,
            birth_input=payload.birth_input.model_dump(mode="json"),
        )
        db.add(revision)
        db.add(
            Consent(
                user_id=user.user_id,
                purpose="profile_storage",
                notice_version=payload.notice_version,
            )
        )
        db.flush()
        return profile_json(profile, revision)


@router.post("/api/charts", status_code=201)
def create_chart(request: Request, payload: ChartCreate):
    user = require_csrf(request)
    revision = owned_revision(request, user, payload.profile_revision_id)
    config = request.app.state.settings
    settings = ChartSettings(
        **payload.settings.model_dump(),
        engine_mode=config.ephemeris_mode,
        ephemeris_path=config.ephemeris_path,
    )
    try:
        calculator = getattr(request.app.state, "calculator", calculate_chart)
        snapshot = calculator(BirthInput.model_validate(revision.birth_input), settings)
    except ValueError as exc:
        raise HTTPException(422, "Invalid chart input") from exc
    except RuntimeError as exc:
        raise HTTPException(503, "Calculation engine unavailable") from exc
    result = snapshot.model_dump(mode="json")
    manifest = result["manifest"]
    input_hash = manifest["input_hash"]
    settings_hash = manifest["settings_hash"]
    with get_db(request).session() as db:
        existing = db.scalar(
            select(Chart).where(
                Chart.owner_id == user.user_id,
                Chart.input_hash == input_hash,
                Chart.settings_hash == settings_hash,
            )
        )
        if existing:
            return chart_json(existing)
        chart = Chart(
            owner_id=user.user_id,
            profile_revision_id=revision.id,
            input_hash=input_hash,
            settings_hash=settings_hash,
            settings=result["settings"],
            manifest=manifest,
            facts=result.get("facts", []),
            unavailable_facts=result.get("unavailable_facts", []),
        )
        db.add(chart)
        db.flush()
        owned_revision(request, user, chart.profile_revision_id)
        return chart_json(chart)


def chart_json(chart: Chart) -> dict[str, Any]:
    return {
        "id": chart.id,
        "owner_id": chart.owner_id,
        "profile_revision_id": chart.profile_revision_id,
        "settings": chart.settings,
        "manifest": chart.manifest,
        "facts": chart.facts,
        "unavailable_facts": chart.unavailable_facts,
    }


@router.get("/api/charts/{chart_id}")
def get_chart(request: Request, chart_id: str):
    user = require_user(request)
    with get_db(request).session() as db:
        chart = db.scalar(select(Chart).where(Chart.id == chart_id, Chart.owner_id == user.user_id))
        if chart is None:
            raise HTTPException(404, "Chart not found")
        owned_revision(request, user, chart.profile_revision_id)
        return chart_json(chart)
