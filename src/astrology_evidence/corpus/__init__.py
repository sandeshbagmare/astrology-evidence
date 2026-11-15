"""Rights-controlled import of administrator-reviewed, edition-specific text."""

import json
from collections.abc import Callable
from datetime import datetime
from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select

from astrology_evidence.db import Database
from astrology_evidence.models import (
    ActiveCorpus,
    CorpusGeneration,
    Edition,
    OutboxOperation,
    Passage,
    RightsRecord,
    new_id,
    utcnow,
)


def text_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RightsImport(StrictModel):
    evidence_reference: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    status: Literal["approved"]
    permissions: dict[str, bool]
    jurisdictions: list[str] = Field(min_length=1)
    excerpt_policy: dict
    expires_at: datetime | None = None

    @field_validator("reviewer", "evidence_reference")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("rights evidence and reviewer cannot be blank")
        return value


class PassageImport(StrictModel):
    text: str = Field(min_length=1, max_length=100000)
    locators: dict
    layer_type: Literal["original", "translation", "commentary", "modern_synthesis"]
    attributed_author: str = Field(min_length=1)
    attribution_evidence: str = Field(min_length=1)
    review_state: Literal["approved"]

    @field_validator("locators")
    @classmethod
    def located(cls, value: dict) -> dict:
        if not any(value.get(key) is not None for key in ("verse", "printed_page", "chapter")):
            raise ValueError("a stable edition locator is required")
        return value


class EditionImport(StrictModel):
    title: str = Field(min_length=1, max_length=500)
    author: str = Field(min_length=1)
    tradition: str = Field(default="jyotish", min_length=1)
    language: str = Field(default="en", min_length=1)
    bibliographic_metadata: dict
    review_state: Literal["approved"]
    rights: RightsImport
    passages: list[PassageImport] = Field(min_length=1, max_length=10000)


class EvidencePassage(BaseModel):
    id: str
    edition_id: str
    text: str
    title: str
    locators: dict
    text_hash: str
    attributed_author: str | None = None
    layer_type: str
    parent_id: str | None = None
    permission: dict
    attribution: str
    max_chars: int
    generation_id: str | None = None


def permitted(edition: Edition, rights: RightsRecord, action: str) -> bool:
    return bool(
        edition.withdrawn_at is None
        and edition.review_state == "approved"
        and rights.withdrawn_at is None
        and rights.status == "approved"
        and rights.reviewer
        and rights.evidence_reference
        and rights.jurisdictions
        and (rights.expires_at is None or rights.expires_at > utcnow())
        and rights.permissions.get(action) is True
    )


def embedding_text(title: str, text: str) -> str:
    return f"passage: {title}\n{text}"


class CorpusService:
    def __init__(
        self, db: Database, tokenizer: Callable[[str], int] | None = None, max_tokens: int = 448
    ):
        self.db = db
        # Conservative byte budgeting is an import fallback, never a model tokenizer claim.
        self.tokenizer = tokenizer or (lambda value: len(value.encode("utf-8")))
        self.max_tokens = max_tokens
        if not 32 <= max_tokens <= 448:
            raise ValueError("chunk cap must be between 32 and 448")

    def import_edition(self, payload: dict | EditionImport) -> str:
        data = EditionImport.model_validate(payload)
        rights_data = data.rights
        if rights_data.permissions.get("store_original") is not True:
            raise ValueError("storing text requires explicit permission")
        if rights_data.expires_at is not None:
            if rights_data.expires_at.tzinfo is None or rights_data.expires_at <= utcnow():
                raise ValueError("rights expiry must be a future aware timestamp")
        policy = rights_data.excerpt_policy
        if (
            type(policy.get("max_chars")) is not int
            or policy["max_chars"] <= 0
            or not str(policy.get("attribution", "")).strip()
        ):
            raise ValueError("an explicit excerpt limit and attribution are required")
        artifact = json.dumps(data.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
        with self.db.session() as session:
            rights = RightsRecord(**rights_data.model_dump())
            session.add(rights)
            session.flush()
            edition = Edition(
                **data.model_dump(exclude={"rights", "passages"}),
                rights_id=rights.id,
                artifact_checksum=text_hash(artifact),
            )
            session.add(edition)
            session.flush()
            for entry in data.passages:
                shared = dict(
                    edition_id=edition.id,
                    layer_type=entry.layer_type,
                    attributed_author=entry.attributed_author,
                    attribution_evidence=entry.attribution_evidence,
                    language=data.language,
                    review_state="approved",
                )
                parent = Passage(
                    **shared,
                    exact_text=entry.text,
                    text_hash=text_hash(entry.text),
                    normalized_text=entry.text.casefold(),
                    locators=entry.locators,
                )
                session.add(parent)
                session.flush()
                if self.tokenizer(embedding_text(data.title, entry.text)) <= self.max_tokens:
                    continue
                start = 0
                while start < len(entry.text):
                    low, high = start, len(entry.text)
                    while low < high:
                        middle = (low + high + 1) // 2
                        count = self.tokenizer(embedding_text(data.title, entry.text[start:middle]))
                        if count <= self.max_tokens:
                            low = middle
                        else:
                            high = middle - 1
                    if low == start:
                        raise ValueError("metadata exceeds the tokenizer budget")
                    end = low
                    # Prefer sentence/word boundaries, preserving every original character.
                    if end < len(entry.text):
                        boundary = entry.text.rfind(" ", start + (end - start) // 2, end)
                        if boundary > start:
                            end = boundary + 1
                    excerpt = entry.text[start:end]
                    session.add(
                        Passage(
                            **shared,
                            parent_id=parent.id,
                            exact_text=excerpt,
                            text_hash=text_hash(excerpt),
                            normalized_text=excerpt.casefold(),
                            locators={**entry.locators, "char_start": start, "char_end": end},
                        )
                    )
                    start = end
            return edition.id

    def withdraw(self, edition_id: str) -> None:
        with self.db.session() as session:
            edition = session.get(Edition, edition_id)
            if edition is None:
                raise ValueError("edition not found")
            if edition.withdrawn_at is not None:
                return
            edition.withdrawn_at = utcnow()
            session.add(
                OutboxOperation(
                    kind="purge_edition",
                    idempotency_key=f"purge:{edition_id}",
                    payload={"edition_id": edition_id},
                )
            )

    def source(
        self, passage_id: str, action: str = "display", generation_id: str | None = None
    ) -> EvidencePassage | None:
        with self.db.session() as session:
            passage = session.get(Passage, passage_id)
            if passage is None or passage.review_state != "approved":
                return None
            edition = session.get(Edition, passage.edition_id)
            rights = session.get(RightsRecord, edition.rights_id)
            if not permitted(edition, rights, action):
                return None
            active = session.get(ActiveCorpus, 1)
            generation = session.get(
                CorpusGeneration, generation_id or (active.generation_id if active else "")
            )
            if generation is None or generation.status != "published":
                return None
            expected = generation.manifest["passage_hashes"].get(passage_id)
            if expected != passage.text_hash or text_hash(passage.exact_text) != expected:
                return None
            limit = rights.excerpt_policy.get("max_chars", 0)
            if type(limit) is not int or len(passage.exact_text) > limit:
                return None
            return EvidencePassage(
                id=passage.id,
                edition_id=edition.id,
                text=passage.exact_text,
                title=edition.title,
                locators=passage.locators,
                text_hash=passage.text_hash,
                attributed_author=passage.attributed_author,
                layer_type=passage.layer_type,
                parent_id=passage.parent_id,
                permission=rights.permissions,
                attribution=rights.excerpt_policy["attribution"],
                max_chars=limit,
                generation_id=generation.id,
            )

    def publish(self, index, encoder) -> str:
        generation_id = new_id()
        collection = f"corpus_{generation_id.replace('-', '')}"
        with self.db.session() as session:
            rows = session.execute(
                select(Passage, Edition, RightsRecord)
                .join(Edition, Passage.edition_id == Edition.id)
                .join(RightsRecord, Edition.rights_id == RightsRecord.id)
            ).all()
            eligible = [
                (p, e, r)
                for p, e, r in rows
                if p.review_state == "approved"
                and all(permitted(e, r, action) for action in ("index", "display"))
            ]
            parent_ids = {p.parent_id for p, _, _ in eligible if p.parent_id}
            indexed = [(p, e) for p, e, _ in eligible if p.id not in parent_ids]
            if not indexed:
                raise ValueError("no rights-approved reviewed passages to publish")
            manifest = {
                "passage_hashes": {p.id: p.text_hash for p, _, _ in eligible},
                "indexed_ids": [p.id for p, _ in indexed],
                "encoder_revision": encoder.revision,
                "dimensions": 384,
                "sparse_revision": "unicode-casefold-blake2b32-tf-v1",
                "rrf_k": 60,
            }
            generation = CorpusGeneration(
                id=generation_id,
                physical_collection_name=collection,
                manifest=manifest,
                manifest_hash=text_hash(json.dumps(manifest, sort_keys=True)),
                expected_count=len(indexed),
                status="indexing",
            )
            session.add(generation)
        try:
            index.build(collection, indexed, encoder)
            index.verify(collection, {p.id: p.text_hash for p, _ in indexed})
            with self.db.session() as session:
                generation = session.get(CorpusGeneration, generation_id)
                for passage, edition in indexed:
                    current = session.get(Edition, edition.id)
                    rights = session.get(RightsRecord, current.rights_id)
                    current_passage = session.get(Passage, passage.id)
                    if (
                        not all(
                            permitted(current, rights, action) for action in ("index", "display")
                        )
                        or current_passage.text_hash != passage.text_hash
                        or text_hash(current_passage.exact_text) != passage.text_hash
                    ):
                        raise ValueError("edition permissions or text changed during index build")
                generation.status = "published"
                generation.indexed_count = len(indexed)
                generation.published_at = utcnow()
                active = session.get(ActiveCorpus, 1)
                if active:
                    active.generation_id = generation_id
                else:
                    session.add(ActiveCorpus(id=1, generation_id=generation_id))
        except Exception:
            with self.db.session() as session:
                session.get(CorpusGeneration, generation_id).status = "failed"
            raise
        return generation_id
