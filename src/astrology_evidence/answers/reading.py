"""Transactional request admission, publication fences, and rights-aware history."""

from __future__ import annotations

import json
import secrets
import time
from datetime import timedelta
from hashlib import sha256
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select, update

from astrology_evidence.answers.contracts import ProviderError
from astrology_evidence.answers.workflow import run_workflow
from astrology_evidence.corpus import CorpusService, permitted, text_hash
from astrology_evidence.models import (
    Chart,
    Consent,
    CorpusGeneration,
    Edition,
    Passage,
    Profile,
    ProfileRevision,
    QuotaBucket,
    Reading,
    ReadingRequest,
    RightsRecord,
    User,
    utcnow,
)

ACTIVE = ("admitted", "generating")


class ReadingService:
    def __init__(self, db, retriever, provider, settings):
        self.db, self.retriever, self.provider, self.settings = db, retriever, provider, settings
        self.corpus = CorpusService(db)

    def _lock(self, session):
        """One SQL row serializes admission across processes; SQLite insert takes a write lock."""
        statement: Any
        if self.db.engine.dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            statement = pg_insert(QuotaBucket)
        else:
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert

            statement = sqlite_insert(QuotaBucket)
        session.execute(
            statement.values(
                id="reading-admission",
                used=0,
                capacity=5,
                resets_at=utcnow() + timedelta(days=3650),
            ).on_conflict_do_nothing(index_elements=["id"])
        )
        session.scalar(
            select(QuotaBucket).where(QuotaBucket.id == "reading-admission").with_for_update()
        )

    def _owned_chart(self, session, user_id, revision_id, chart_id=None):
        user = session.get(User, user_id)
        revision = session.scalar(
            select(ProfileRevision).where(
                ProfileRevision.id == revision_id, ProfileRevision.owner_id == user_id
            )
        )
        profile = session.get(Profile, revision.profile_id) if revision else None
        if user is None or user.deleted_at or profile is None or profile.deleted_at:
            raise HTTPException(404, "Not found")
        query = select(Chart).where(
            Chart.owner_id == user_id, Chart.profile_revision_id == revision_id
        )
        if chart_id:
            query = query.where(Chart.id == chart_id)
        chart = session.scalar(query.order_by(Chart.created_at.desc()))
        if chart is None:
            raise HTTPException(422, "clarification_required")
        return chart

    def _reserve_global_daily(self, session, now):
        """Count accepted requests independently of owners and deleted reading rows."""
        # The admission row is already locked, including SQLite's transaction write lock.
        bucket = session.get(QuotaBucket, "global-reading-day")
        reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        capacity = self.settings.answer_global_daily_limit
        if bucket is None:
            bucket = QuotaBucket(
                id="global-reading-day", used=0, capacity=capacity, resets_at=reset
            )
            session.add(bucket)
        elif bucket.resets_at <= now:
            bucket.used = 0
            bucket.capacity = capacity
            bucket.resets_at = reset
        if bucket.used >= capacity:
            retry_after = max(1, int((bucket.resets_at - now).total_seconds()) + 1)
            raise HTTPException(
                429,
                "Global daily reading limit reached",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.used += 1

    def _evidence_live(self, session, evidence, model=False):
        for item in evidence:
            p = session.get(Passage, item["id"])
            e = session.get(Edition, p.edition_id) if p else None
            r = session.get(RightsRecord, e.rights_id) if e else None
            g = session.get(CorpusGeneration, item["generation_id"])
            if (
                p is None
                or e is None
                or r is None
                or g is None
                or g.status != "published"
                or p.review_state != "approved"
                or g.manifest.get("passage_hashes", {}).get(p.id) != item["text_hash"]
                or p.text_hash != item["text_hash"]
                or text_hash(p.exact_text) != item["text_hash"]
                or not permitted(e, r, "display")
                or (model and not permitted(e, r, "model_transmit"))
            ):
                raise ProviderError("evidence_unavailable")
            limit = r.excerpt_policy.get("max_chars", 0)
            if type(limit) is not int or len(p.exact_text) > limit:
                raise ProviderError("evidence_unavailable")

    def _status(self, session, row):
        if row.status in ACTIVE and row.deadline <= utcnow():
            row.status = "unknown" if row.status == "generating" else "failed"
            row.failure_code = "deadline_exceeded"
            row.execution_token = None
            session.flush()
        reading = session.scalar(
            select(Reading).where(Reading.request_id == row.id, Reading.deleted_at.is_(None))
        )
        return {
            "id": row.id,
            "request_id": row.id,
            "status": row.status,
            "reading_id": reading.id if reading else None,
            "failure_code": row.failure_code,
        }

    def create(self, user_id, profile_revision_id, question, idempotency_key, chart_id=None):
        if (
            not isinstance(question, str)
            or not question.strip()
            or len(question) > 2000
            or not isinstance(idempotency_key, str)
            or not idempotency_key.strip()
            or len(idempotency_key) > 255
        ):
            raise HTTPException(422, "Invalid request")
        digest = sha256(
            json.dumps(
                {"revision": profile_revision_id, "question": question, "chart_id": chart_id},
                sort_keys=True,
            ).encode()
        ).hexdigest()
        now = utcnow()
        with self.db.session() as session:
            self._lock(session)
            self._owned_chart(session, user_id, profile_revision_id, chart_id)
            previous = session.scalar(
                select(ReadingRequest).where(
                    ReadingRequest.owner_id == user_id,
                    ReadingRequest.idempotency_key == idempotency_key,
                )
            )
            if previous:
                if previous.request_hash != digest:
                    raise HTTPException(409, "Idempotency key conflict")
                return self._status(session, previous)
            # Restart recovery fences overdue work without ever resending it.
            for expired in session.scalars(
                select(ReadingRequest).where(
                    ReadingRequest.status.in_(ACTIVE), ReadingRequest.deadline <= now
                )
            ):
                expired.status = "unknown" if expired.status == "generating" else "failed"
                expired.failure_code = "deadline_exceeded"
                expired.execution_token = None
            session.flush()
            active = (
                select(func.count())
                .select_from(ReadingRequest)
                .where(ReadingRequest.status.in_(ACTIVE))
            )
            if session.scalar(active) >= min(5, self.settings.answer_global_limit):
                raise HTTPException(429, "Global request limit reached")
            if session.scalar(active.where(ReadingRequest.owner_id == user_id)) >= 1:
                raise HTTPException(429, "An active request already exists")
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            daily = session.scalar(
                select(func.count())
                .select_from(ReadingRequest)
                .where(ReadingRequest.owner_id == user_id, ReadingRequest.created_at >= day_start)
            )
            if daily >= min(10, self.settings.answer_daily_limit):
                raise HTTPException(429, "Daily request limit reached")
            self._reserve_global_daily(session, now)
            chart = self._owned_chart(session, user_id, profile_revision_id, chart_id)
            token = secrets.token_hex(32)
            row = ReadingRequest(
                owner_id=user_id,
                profile_revision_id=profile_revision_id,
                question=question,
                idempotency_key=idempotency_key,
                request_hash=digest,
                status="admitted",
                execution_token=token,
                stage="retrieve",
                deadline=now + timedelta(seconds=self.settings.answer_deadline_seconds),
            )
            session.add(row)
            session.flush()
            request_id = row.id
        monotonic_deadline = time.monotonic() + self.settings.answer_deadline_seconds
        transmitted = False

        def guard(model, passages):
            nonlocal transmitted
            items = [
                {"id": p.id, "text_hash": p.text_hash, "generation_id": p.generation_id}
                for p in passages
            ]
            with self.db.session() as session:
                self._lock(session)
                current = session.get(ReadingRequest, request_id)
                if (
                    current is None
                    or current.status not in ACTIVE
                    or current.execution_token != token
                ):
                    raise ProviderError("request_cancelled")
                try:
                    self._owned_chart(session, user_id, profile_revision_id, chart.id)
                except HTTPException:
                    raise ProviderError("request_cancelled") from None
                remaining = min(
                    (current.deadline - utcnow()).total_seconds(),
                    monotonic_deadline - time.monotonic(),
                )
                if remaining <= 0:
                    raise ProviderError("deadline_exceeded", unknown=transmitted)
                self._evidence_live(session, items, model)
                if model:
                    consent = session.scalar(
                        select(Consent.id).where(
                            Consent.user_id == user_id,
                            Consent.purpose == "model_processing",
                            Consent.revoked_at.is_(None),
                        )
                    )
                    if consent is None:
                        raise ProviderError(
                            "request_cancelled" if transmitted else "consent_required"
                        )
                    if self.provider is None:
                        raise ProviderError("provider_unavailable")
                    current.status = "generating"
                    current.stage = "generate"
                    transmitted = True
                return remaining

        try:
            state = run_workflow(
                question=question,
                chart=chart,
                retriever=self.retriever,
                provider=self.provider,
                ai_enabled=self.settings.ai_enabled,
                guard=guard,
            )
            evidence = [
                {"id": p.id, "text_hash": p.text_hash, "generation_id": p.generation_id}
                for p in state["passages"]
            ]
            with self.db.session() as session:
                self._lock(session)
                current = session.get(ReadingRequest, request_id)
                if (
                    current is None
                    or current.status not in ACTIVE
                    or current.execution_token != token
                ):
                    raise ProviderError("request_cancelled")
                try:
                    self._owned_chart(session, user_id, profile_revision_id, chart.id)
                except HTTPException:
                    raise ProviderError("request_cancelled") from None
                if utcnow() >= current.deadline or time.monotonic() >= monotonic_deadline:
                    raise ProviderError("deadline_exceeded", unknown=transmitted)
                if transmitted and not session.scalar(
                    select(Consent.id).where(
                        Consent.user_id == user_id,
                        Consent.purpose == "model_processing",
                        Consent.revoked_at.is_(None),
                    )
                ):
                    raise ProviderError("request_cancelled")
                self._evidence_live(session, evidence, transmitted)
                session.add(
                    Reading(
                        owner_id=user_id,
                        request_id=request_id,
                        chart_id=chart.id,
                        answer=state["answer"].model_dump(mode="json"),
                        evidence_manifest={"passages": evidence},
                        versions={
                            "workflow": "bounded-extractive-v1",
                            "prompt": "extractive-v1",
                            "model": self.settings.ai_model if transmitted else "none",
                        },
                    )
                )
                current.status = "succeeded"
                current.stage = "complete"
                current.execution_token = None
                session.flush()
                return self._status(session, current)
        except ProviderError as exc:
            code, unknown = exc.code, exc.unknown
        except Exception:
            # Controlled boundary: never expose prompts, private fields or upstream details.
            code, unknown = "generation_failed", transmitted
        with self.db.session() as session:
            self._lock(session)
            current = session.get(ReadingRequest, request_id)
            if current is None:
                raise HTTPException(404, "Not found")
            if current.status in ACTIVE and current.execution_token == token:
                current.status = (
                    "cancelled"
                    if code == "request_cancelled"
                    else ("unknown" if unknown else "failed")
                )
                current.failure_code = code
                current.execution_token = None
                current.stage = "complete"
            return self._status(session, current)

    def request_status(self, user_id, request_id):
        with self.db.session() as session:
            row = session.scalar(
                select(ReadingRequest).where(
                    ReadingRequest.id == request_id, ReadingRequest.owner_id == user_id
                )
            )
            if row is None:
                raise HTTPException(404, "Not found")
            return self._status(session, row)

    def cancel(self, user_id, request_id):
        with self.db.session() as session:
            self._lock(session)
            row = session.scalar(
                select(ReadingRequest).where(
                    ReadingRequest.id == request_id, ReadingRequest.owner_id == user_id
                )
            )
            if row is None:
                raise HTTPException(404, "Not found")
            if row.status in ACTIVE:
                row.status = "cancelled"
                row.failure_code = "request_cancelled"
                row.execution_token = None
            return self._status(session, row)

    def set_consent(self, user_id, granted, notice_version):
        with self.db.session() as session:
            self._lock(session)
            user = session.get(User, user_id)
            if user is None or user.deleted_at:
                raise HTTPException(404, "Not found")
            session.execute(
                update(Consent)
                .where(
                    Consent.user_id == user_id,
                    Consent.purpose == "model_processing",
                    Consent.revoked_at.is_(None),
                )
                .values(revoked_at=utcnow())
            )
            if granted:
                session.add(
                    Consent(
                        user_id=user_id, purpose="model_processing", notice_version=notice_version
                    )
                )
            else:
                session.execute(
                    update(ReadingRequest)
                    .where(ReadingRequest.owner_id == user_id, ReadingRequest.status.in_(ACTIVE))
                    .values(
                        status="cancelled", execution_token=None, failure_code="request_cancelled"
                    )
                )
        return {"purpose": "model_processing", "granted": granted}

    def get_reading(self, user_id, reading_id):
        with self.db.session() as session:
            row = session.scalar(
                select(Reading).where(
                    Reading.id == reading_id,
                    Reading.owner_id == user_id,
                    Reading.deleted_at.is_(None),
                )
            )
            if row is None:
                raise HTTPException(404, "Not found")
            chart = session.get(Chart, row.chart_id)
            self._owned_chart(session, user_id, chart.profile_revision_id, row.chart_id)
            manifest = row.evidence_manifest
            result = {
                "id": row.id,
                "request_id": row.request_id,
                "chart_id": row.chart_id,
                "answer": row.answer,
                "evidence_manifest": manifest,
                "versions": row.versions,
            }
        # Current rights and original hashes are authoritative on every serving path.
        for item in manifest.get("passages", []):
            p = self.corpus.source(item["id"], generation_id=item["generation_id"])
            if p is None or p.text_hash != item["text_hash"]:
                raise HTTPException(410, "Source evidence is no longer available")
        return result

    def list_readings(self, user_id):
        with self.db.session() as session:
            rows = session.scalars(
                select(Reading)
                .where(Reading.owner_id == user_id, Reading.deleted_at.is_(None))
                .order_by(Reading.created_at.desc())
                .limit(100)
            ).all()
            return [
                {
                    "id": row.id,
                    "request_id": row.request_id,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]

    def delete(self, user_id, reading_id):
        with self.db.session() as session:
            self._lock(session)
            row = session.scalar(
                select(Reading).where(Reading.id == reading_id, Reading.owner_id == user_id)
            )
            if row is None:
                raise HTTPException(404, "Not found")
            row.deleted_at = utcnow()
            row.answer = {}
            row.evidence_manifest = {}
