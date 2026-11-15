"""Account/profile denial, durable purge and owner-authorized portable exports."""

import hashlib
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select, update

from astrology_evidence.db import Database
from astrology_evidence.jobs import JobService, LeaseLost, database_now
from astrology_evidence.models import (
    AuditEvent,
    Chart,
    Consent,
    DeletionTombstone,
    Export,
    Feedback,
    Job,
    Profile,
    ProfileRevision,
    Reading,
    ReadingRequest,
    Session,
    User,
    new_id,
)


class ResourceUnavailable(LookupError):
    pass


def subject_hash(subject_id: str) -> str:
    return hashlib.sha256(subject_id.encode()).hexdigest()


def fields(row, *names):
    result = {}
    for name in names:
        value = getattr(row, name)
        result[name] = value.isoformat() if hasattr(value, "isoformat") else value
    return result


class PrivacyService:
    def __init__(self, db: Database):
        self.db = db
        self.jobs = JobService(db)

    @staticmethod
    def active_user(session, user_id: str):
        user = session.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None or user.deleted_at is not None:
            raise ResourceUnavailable("resource unavailable")
        return user

    @staticmethod
    def tombstone(session, scope: str, object_id: str):
        digest = subject_hash(object_id)
        tombstone = session.scalar(
            select(DeletionTombstone).where(
                DeletionTombstone.scope == scope, DeletionTombstone.subject_hash == digest
            )
        )
        if tombstone is None:
            tombstone = DeletionTombstone(scope=scope, subject_hash=digest)
            session.add(tombstone)
            session.flush()
        tombstone.completed_at = None
        return tombstone

    def request_account_deletion(self, user_id: str) -> Job:
        with self.db.session() as session:
            user = session.scalar(select(User).where(User.id == user_id).with_for_update())
            if user is None:
                raise ResourceUnavailable("resource unavailable")
            now = database_now(session)
            user.deleted_at = user.deleted_at or now
            session.execute(
                update(Session).where(Session.user_id == user_id).values(revoked_at=now)
            )
            session.execute(
                update(Profile).where(Profile.owner_id == user_id).values(deleted_at=now)
            )
            session.execute(
                update(Reading).where(Reading.owner_id == user_id).values(deleted_at=now)
            )
            session.execute(
                update(ReadingRequest)
                .where(
                    ReadingRequest.owner_id == user_id,
                    ReadingRequest.status.in_(["admitted", "generating"]),
                )
                .values(status="cancelled", execution_token=None)
            )
            session.execute(
                update(Job)
                .where(
                    Job.owner_id == user_id,
                    Job.kind != "account_purge",
                )
                .values(status="cancelled", cancellation_state="cancelled", payload={})
            )
            session.execute(delete(Export).where(Export.owner_id == user_id))
            tombstone = self.tombstone(session, "account", user_id)
            key = f"account_purge:{user_id}"
            job = session.scalar(select(Job).where(Job.idempotency_key == key))
            if job is None:
                job = Job(
                    kind="account_purge",
                    owner_id=user_id,
                    idempotency_key=key,
                    payload={"tombstone_id": tombstone.id},
                    run_after=now,
                )
                session.add(job)
                session.flush()
            return job

    def request_profile_deletion(self, user_id: str, profile_id: str) -> Job:
        with self.db.session() as session:
            self.active_user(session, user_id)
            profile = session.scalar(
                select(Profile)
                .where(Profile.id == profile_id, Profile.owner_id == user_id)
                .with_for_update()
            )
            if profile is None:
                raise ResourceUnavailable("resource unavailable")
            now = database_now(session)
            profile.deleted_at = profile.deleted_at or now
            revisions = select(ProfileRevision.id).where(ProfileRevision.profile_id == profile_id)
            session.execute(
                update(ReadingRequest)
                .where(
                    ReadingRequest.profile_revision_id.in_(revisions),
                    ReadingRequest.status.in_(["admitted", "generating"]),
                )
                .values(status="cancelled", execution_token=None)
            )
            requests = select(ReadingRequest.id).where(
                ReadingRequest.profile_revision_id.in_(revisions)
            )
            session.execute(
                update(Reading).where(Reading.request_id.in_(requests)).values(deleted_at=now)
            )
            # Previously downloaded exports cannot be recalled; all hosted copies are invalidated.
            session.execute(delete(Export).where(Export.owner_id == user_id))
            session.execute(
                update(Job)
                .where(Job.owner_id == user_id, Job.kind == "export")
                .values(status="cancelled", cancellation_state="cancelled", payload={})
            )
            tombstone = self.tombstone(session, "profile", profile_id)
            key = f"profile_purge:{profile_id}"
            job = session.scalar(select(Job).where(Job.idempotency_key == key))
            if job is None:
                job = Job(
                    kind="profile_purge",
                    owner_id=user_id,
                    idempotency_key=key,
                    payload={"profile_id": profile_id, "tombstone_id": tombstone.id},
                    run_after=now,
                )
                session.add(job)
                session.flush()
            return job

    def request_export(self, user_id: str) -> Export:
        with self.db.session() as session:
            self.active_user(session, user_id)
            now = database_now(session)
            export_id = new_id()
            job = Job(
                kind="export",
                owner_id=user_id,
                payload={"export_id": export_id},
                idempotency_key=f"export:{export_id}",
                run_after=now,
            )
            session.add(job)
            session.flush()
            export = Export(
                id=export_id, owner_id=user_id, job_id=job.id, expires_at=now + timedelta(hours=24)
            )
            session.add(export)
            session.flush()
            return export

    def process_job(self, lease: Job) -> None:
        with self.db.session() as session:
            # All publication and denial operations serialize on the same account row.
            user = session.scalar(select(User).where(User.id == lease.owner_id).with_for_update())
            job = session.scalar(
                select(Job).where(self.jobs.fence(lease, database_now(session))).with_for_update()
            )
            if job is None:
                raise LeaseLost("job lease is no longer current")
            if job.payload_version != 1:
                raise ValueError("unsupported job payload version")
            if job.kind == "export":
                if user is None or user.deleted_at:
                    raise ResourceUnavailable("resource unavailable")
                export = session.get(Export, job.payload.get("export_id"))
                if (
                    export is None
                    or export.owner_id != user.id
                    or export.expires_at <= database_now(session)
                ):
                    raise ResourceUnavailable("resource unavailable")
                export.payload = self.build_export(session, user)
                export.status = "ready"
            elif job.kind in {"account_purge", "profile_purge"}:
                tombstone = session.get(DeletionTombstone, job.payload.get("tombstone_id"))
                if tombstone is None:
                    raise ValueError("missing deletion tombstone")
                if job.kind == "account_purge":
                    if user is not None and not user.deleted_at:
                        raise ValueError("account deletion was not requested")
                    if user is not None:
                        self.purge_account(session, user.id, job.id)
                    job.owner_id = None
                else:
                    profile_id = job.payload.get("profile_id")
                    profile = session.get(Profile, profile_id)
                    if profile is not None:
                        if profile.owner_id != job.owner_id or not profile.deleted_at:
                            raise ValueError("profile deletion was not requested")
                        session.execute(delete(Profile).where(Profile.id == profile_id))
                tombstone.completed_at = database_now(session)
                job.payload = {}
            else:
                raise ValueError("unsupported job kind")
            session.flush()
            self.jobs.complete_in_session(session, lease)

    @staticmethod
    def purge_account(session, user_id: str, current_job_id: str):
        # Null the retained receipt's FK before deleting the account and all private children.
        session.execute(update(Job).where(Job.id == current_job_id).values(owner_id=None))
        session.execute(delete(Job).where(Job.owner_id == user_id))
        session.execute(delete(AuditEvent).where(AuditEvent.actor_id == user_id))
        session.execute(delete(User).where(User.id == user_id))

    @staticmethod
    def build_export(session, user: User) -> dict:
        owner_id = user.id
        profiles = []
        for profile in session.scalars(
            select(Profile).where(Profile.owner_id == owner_id, Profile.deleted_at.is_(None))
        ):
            item = fields(profile, "id", "alias", "version", "created_at")
            item["revisions"] = [
                fields(r, "id", "revision", "birth_input", "created_at")
                for r in session.scalars(
                    select(ProfileRevision).where(ProfileRevision.profile_id == profile.id)
                )
            ]
            profiles.append(item)
        revisions = [r["id"] for p in profiles for r in p["revisions"]]
        return {
            "format_version": 1,
            "account": fields(user, "id", "email", "display_name", "created_at"),
            "consents": [
                fields(c, "purpose", "notice_version", "granted_at", "revoked_at")
                for c in session.scalars(select(Consent).where(Consent.user_id == owner_id))
            ],
            "sessions": [
                fields(s, "created_at", "expires_at", "revoked_at")
                for s in session.scalars(select(Session).where(Session.user_id == owner_id))
            ],
            "profiles": profiles,
            "charts": [
                fields(
                    c,
                    "id",
                    "profile_revision_id",
                    "settings",
                    "manifest",
                    "facts",
                    "unavailable_facts",
                    "created_at",
                )
                for c in session.scalars(
                    select(Chart).where(
                        Chart.owner_id == owner_id, Chart.profile_revision_id.in_(revisions)
                    )
                )
            ],
            "requests": [
                fields(r, "id", "profile_revision_id", "question", "status", "created_at")
                for r in session.scalars(
                    select(ReadingRequest).where(
                        ReadingRequest.owner_id == owner_id,
                        ReadingRequest.profile_revision_id.in_(revisions),
                    )
                )
            ],
            "readings": [
                PrivacyService.export_reading(r)
                for r in session.scalars(
                    select(Reading).where(
                        Reading.owner_id == owner_id, Reading.deleted_at.is_(None)
                    )
                )
            ],
            "feedback": [
                fields(f, "reading_id", "category", "comment", "created_at")
                for f in session.scalars(select(Feedback).where(Feedback.owner_id == owner_id))
            ],
            "source_notice": "Source excerpts and raw model payloads are excluded from exports.",
        }

    @staticmethod
    def export_reading(reading: Reading) -> dict:
        result = fields(reading, "id", "request_id", "chart_id", "versions", "created_at")
        result["answer_omitted_reason"] = "citation export rights could not be verified"
        return result

    @staticmethod
    def safe_answer(answer: dict) -> dict:
        allowed = {
            "status",
            "concise_summary",
            "computed_facts",
            "traditional_claims",
            "interpretation",
            "disagreements",
            "limitations",
            "suggested_questions",
        }
        forbidden = {
            "quote",
            "exact_text",
            "excerpt",
            "exact_span",
            "text_span",
            "raw_response",
            "prompt",
            "provider_response",
            "evidence_manifest",
            "citations",
        }

        def clean(value):
            if isinstance(value, dict):
                return {k: clean(v) for k, v in value.items() if k not in forbidden}
            if isinstance(value, list):
                return [clean(v) for v in value]
            return value

        return {key: clean(value) for key, value in answer.items() if key in allowed}

    def download_export(self, user_id: str, export_id: str) -> dict:
        with self.db.session() as session:
            self.active_user(session, user_id)
            export = session.scalar(
                select(Export).where(
                    Export.id == export_id,
                    Export.owner_id == user_id,
                    Export.status == "ready",
                    Export.expires_at > database_now(session),
                )
            )
            if export is None or export.payload is None:
                raise ResourceUnavailable("resource unavailable")
            return export.payload

    def get_job(self, user_id: str, job_id: str) -> dict:
        with self.db.session() as session:
            self.active_user(session, user_id)
            job = session.scalar(select(Job).where(Job.id == job_id, Job.owner_id == user_id))
            if job is None:
                raise ResourceUnavailable("resource unavailable")
            return fields(job, "id", "kind", "status", "attempt_count", "error_code")

    def purge_expired_exports(self) -> int:
        with self.db.session() as session:
            return session.execute(
                delete(Export).where(Export.expires_at <= database_now(session))
            ).rowcount

    def replay_tombstones(self, journal: list[dict]) -> None:
        """Replay a separately recovered journal before allowing restored traffic."""
        with self.db.session() as session:
            session.execute(update(Session).values(revoked_at=database_now(session)))
            users = [(u.id, subject_hash(u.id)) for u in session.scalars(select(User))]
            profiles = [
                (p.id, p.owner_id, subject_hash(p.id)) for p in session.scalars(select(Profile))
            ]
        for entry in journal:
            if entry["scope"] == "account":
                for user_id, digest in users:
                    if digest == entry["subject_hash"]:
                        self.request_account_deletion(user_id)
            elif entry["scope"] == "profile":
                for profile_id, user_id, digest in profiles:
                    if digest == entry["subject_hash"]:
                        try:
                            self.request_profile_deletion(user_id, profile_id)
                        except ResourceUnavailable:
                            # An account purge already covers this profile.
                            pass
            else:
                raise ValueError("unsupported tombstone scope")
        self.purge_expired_exports()


router = APIRouter()


def service(request: Request) -> PrivacyService:
    return PrivacyService(request.app.state.db)


def respond(action):
    try:
        return action()
    except ResourceUnavailable as exc:
        raise HTTPException(404, "Resource unavailable") from exc


@router.delete("/api/me", status_code=202)
def delete_account(request: Request):
    from astrology_evidence.identity import require_csrf

    user = require_csrf(request)
    job = respond(lambda: service(request).request_account_deletion(user.user_id))
    return {"job_id": job.id, "status": "pending"}


@router.delete("/api/profiles/{profile_id}", status_code=202)
def delete_profile(request: Request, profile_id: str):
    from astrology_evidence.identity import require_csrf

    user = require_csrf(request)
    job = respond(lambda: service(request).request_profile_deletion(user.user_id, profile_id))
    return {"job_id": job.id, "status": "pending"}


@router.post("/api/me/export", status_code=202)
def export_account(request: Request):
    from astrology_evidence.identity import require_csrf

    user = require_csrf(request)
    export = respond(lambda: service(request).request_export(user.user_id))
    return {"job_id": export.job_id, "export_id": export.id, "status": export.status}


@router.get("/api/jobs/{job_id}")
def job_status(request: Request, job_id: str):
    from astrology_evidence.identity import require_user

    user = require_user(request)
    return respond(lambda: service(request).get_job(user.user_id, job_id))


@router.get("/api/exports/{export_id}")
def download_export(request: Request, export_id: str):
    from astrology_evidence.identity import require_user

    user = require_user(request)
    payload = respond(lambda: service(request).download_export(user.user_id, export_id))
    return JSONResponse(
        payload,
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": "attachment; filename=export.json",
        },
    )
