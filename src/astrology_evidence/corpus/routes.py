"""Authorization boundaries for reviewed corpus administration and lookup."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from astrology_evidence.corpus import CorpusService, EditionImport
from astrology_evidence.identity import get_db, require_csrf, require_user

router = APIRouter()


class SearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)


def curator(request: Request):
    user = require_csrf(request)
    if not user.is_admin:
        raise HTTPException(403, "Curator access required")
    return user


@router.post("/api/admin/editions", status_code=201)
def import_edition(request: Request, payload: EditionImport):
    curator(request)
    try:
        edition_id = CorpusService(get_db(request)).import_edition(payload.model_dump(mode="json"))
    except ValueError:
        raise HTTPException(422, "Edition metadata or permissions are invalid") from None
    return {"id": edition_id, "status": "imported"}


@router.post("/api/admin/editions/{edition_id}/publish")
def publish(request: Request, edition_id: str):
    curator(request)
    index = getattr(request.app.state, "index", None)
    encoder = getattr(request.app.state, "encoder", None)
    if index is None or encoder is None:
        raise HTTPException(503, "Reviewed embedding configuration is required")
    from astrology_evidence.models import Edition

    with get_db(request).session() as session:
        if session.get(Edition, edition_id) is None:
            raise HTTPException(404, "Edition not found")
    try:
        generation = CorpusService(get_db(request)).publish(index, encoder)
    except (ValueError, RuntimeError):
        raise HTTPException(422, "Corpus publication validation failed") from None
    return {"generation_id": generation, "status": "published"}


@router.post("/api/admin/editions/{edition_id}/withdraw", status_code=204)
def withdraw(request: Request, edition_id: str):
    curator(request)
    from fastapi import Response

    try:
        CorpusService(get_db(request)).withdraw(edition_id)
    except ValueError:
        raise HTTPException(404, "Edition not found") from None
    return Response(status_code=204)


@router.get("/api/sources/{passage_id}")
def source(request: Request, passage_id: str):
    require_user(request)
    passage = CorpusService(get_db(request)).source(passage_id, action="display")
    if passage is None:
        raise HTTPException(404, "Source unavailable")
    return passage.model_dump()


@router.post("/api/search")
def search(request: Request, payload: SearchInput):
    require_csrf(request)
    retriever = getattr(request.app.state, "retriever", None)
    if retriever is None:
        raise HTTPException(503, "Source search is not configured")
    return [item.model_dump() for item in retriever.search(payload.question, action="display")]
