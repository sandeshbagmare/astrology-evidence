"""Session-authenticated reading endpoints reuse the fenced service."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from astrology_evidence.answers.reading import ReadingService
from astrology_evidence.identity import get_db, require_csrf, require_user
from astrology_evidence.models import Feedback, Reading

router = APIRouter()


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ReadingCreate(InputModel):
    profile_revision_id: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=2000)
    chart_id: str | None = Field(default=None, min_length=1, max_length=80)


class ConsentInput(InputModel):
    purpose: Literal["model_processing"] = "model_processing"
    granted: bool
    notice_version: str = Field(min_length=1, max_length=80)


class FeedbackInput(InputModel):
    reading_id: str = Field(min_length=1, max_length=80)
    category: Literal["citation_issue", "incorrect_fact", "unclear", "helpful", "other"]
    comment: str | None = Field(default=None, max_length=2000)


def get_service(request: Request) -> ReadingService:
    existing = getattr(request.app.state, "reading_service", None)
    if existing is not None:
        return existing
    return ReadingService(
        get_db(request),
        getattr(request.app.state, "retriever", None),
        getattr(request.app.state, "provider", None),
        request.app.state.settings,
    )


@router.post("/api/readings", status_code=201)
def create(request: Request, payload: ReadingCreate, response: Response):
    user = require_csrf(request)
    result = get_service(request).create(
        user.user_id,
        payload.profile_revision_id,
        payload.question,
        request.headers.get("Idempotency-Key", ""),
        payload.chart_id,
    )
    if result["status"] in ("admitted", "generating"):
        response.status_code = 202
    elif result["status"] in ("failed", "unknown", "cancelled"):
        code = result["failure_code"] or "generation_failed"
        status = (
            422
            if code in ("consent_required", "clarification_required")
            else (504 if code == "deadline_exceeded" else 503)
        )
        if result["status"] == "cancelled":
            status = 409
        raise HTTPException(
            status,
            {
                "code": code,
                "request_id": result["id"],
                "message": "The request did not produce a reading.",
                "retryable": False,
            },
        )
    return result


@router.get("/api/readings")
def list_readings(request: Request):
    return get_service(request).list_readings(require_user(request).user_id)


@router.get("/api/readings/{reading_id}")
def read(request: Request, reading_id: str):
    return get_service(request).get_reading(require_user(request).user_id, reading_id)


@router.delete("/api/readings/{reading_id}", status_code=204)
def delete(request: Request, reading_id: str):
    get_service(request).delete(require_csrf(request).user_id, reading_id)
    return Response(status_code=204)


@router.get("/api/reading-requests/{request_id}")
def request_status(request: Request, request_id: str):
    return get_service(request).request_status(require_user(request).user_id, request_id)


@router.post("/api/reading-requests/{request_id}/cancel")
def cancel(request: Request, request_id: str):
    return get_service(request).cancel(require_csrf(request).user_id, request_id)


@router.post("/api/consent")
@router.post("/api/consent/model-processing")
def consent(request: Request, payload: ConsentInput):
    return get_service(request).set_consent(
        require_csrf(request).user_id, payload.granted, payload.notice_version
    )


@router.post("/api/feedback", status_code=201)
def feedback(request: Request, payload: FeedbackInput):
    user = require_csrf(request)
    with get_db(request).session() as session:
        reading = session.scalar(
            select(Reading).where(
                Reading.id == payload.reading_id,
                Reading.owner_id == user.user_id,
                Reading.deleted_at.is_(None),
            )
        )
        if reading is None:
            raise HTTPException(404, "Not found")
        row = Feedback(
            owner_id=user.user_id,
            reading_id=reading.id,
            category=payload.category,
            comment=payload.comment,
        )
        session.add(row)
        session.flush()
        return {"id": row.id}
