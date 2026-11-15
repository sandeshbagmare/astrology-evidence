"""Durable, fenced jobs. Provider calls are deliberately outside this queue."""

from datetime import UTC, timedelta

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.exc import IntegrityError

from astrology_evidence.db import Database
from astrology_evidence.models import Job

JOB_KINDS = {"account_purge", "profile_purge", "export"}


class LeaseLost(RuntimeError):
    pass


def database_now(session):
    clock = (
        func.clock_timestamp()
        if session.bind.dialect.name == "postgresql"
        else func.current_timestamp()
    )
    value = session.scalar(select(clock))
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class JobService:
    def __init__(self, db: Database):
        self.db = db

    def enqueue(
        self, kind: str, payload: dict, idempotency_key: str, owner_id: str | None = None
    ) -> Job:
        if kind not in JOB_KINDS:
            raise ValueError("unsupported job kind")
        try:
            with self.db.session() as session:
                existing = session.scalar(select(Job).where(Job.idempotency_key == idempotency_key))
                if existing is None:
                    job = Job(
                        kind=kind,
                        payload=payload,
                        idempotency_key=idempotency_key,
                        owner_id=owner_id,
                        run_after=database_now(session),
                    )
                    session.add(job)
                    session.flush()
                    return job
        except IntegrityError:
            with self.db.session() as session:
                existing = session.scalar(select(Job).where(Job.idempotency_key == idempotency_key))
                if existing is None:
                    raise
        if (existing.kind, existing.payload, existing.owner_id) != (kind, payload, owner_id):
            raise ValueError("idempotency key conflict")
        return existing

    def claim(self, worker_id: str, lease_seconds: int = 120) -> Job | None:
        if not worker_id or lease_seconds <= 0:
            raise ValueError("worker and positive lease required")
        with self.db.session() as session:
            now = database_now(session)
            session.execute(
                update(Job)
                .where(
                    Job.kind.in_(JOB_KINDS),
                    Job.status == "running",
                    Job.lease_expires_at <= now,
                    Job.attempt_count >= Job.max_attempts,
                )
                .values(status="dead_letter", error_code="lease_exhausted")
            )
            eligible = and_(
                Job.kind.in_(JOB_KINDS),
                Job.cancellation_state == "active",
                Job.attempt_count < Job.max_attempts,
                Job.run_after <= now,
                or_(
                    Job.status == "pending",
                    and_(Job.status == "running", Job.lease_expires_at <= now),
                ),
            )
            candidate = session.scalar(
                select(Job.id)
                .where(eligible)
                .order_by(
                    case((Job.kind.in_(["account_purge", "profile_purge"]), 0), else_=1),
                    Job.run_after,
                    Job.id,
                )
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if candidate is None:
                return None
            # Recheck eligibility in the write: SQLite ignores SELECT FOR UPDATE.
            claimed = session.execute(
                update(Job)
                .where(Job.id == candidate, eligible)
                .values(
                    status="running",
                    lease_owner=worker_id,
                    lease_generation=Job.lease_generation + 1,
                    attempt_count=Job.attempt_count + 1,
                    last_heartbeat_at=now,
                    lease_expires_at=now + timedelta(seconds=lease_seconds),
                )
                .returning(Job)
            ).scalar_one_or_none()
            return claimed

    @staticmethod
    def fence(lease: Job, now):
        return and_(
            Job.id == lease.id,
            Job.status == "running",
            Job.cancellation_state == "active",
            Job.lease_owner == lease.lease_owner,
            Job.lease_generation == lease.lease_generation,
            Job.lease_expires_at > now,
        )

    def heartbeat(self, lease: Job, lease_seconds: int = 120) -> None:
        if lease_seconds <= 0:
            raise ValueError("positive lease required")
        with self.db.session() as session:
            now = database_now(session)
            result = session.execute(
                update(Job)
                .where(self.fence(lease, now))
                .values(
                    last_heartbeat_at=now, lease_expires_at=now + timedelta(seconds=lease_seconds)
                )
            )
            if result.rowcount != 1:  # type: ignore[attr-defined]
                raise LeaseLost("job lease is no longer current")

    def complete(self, lease: Job) -> None:
        with self.db.session() as session:
            self.complete_in_session(session, lease)

    def complete_in_session(self, session, lease: Job) -> None:
        result = session.execute(
            update(Job)
            .where(self.fence(lease, database_now(session)))
            .values(status="succeeded", lease_expires_at=None, lease_owner=None, error_code=None)
        )
        if result.rowcount != 1:  # type: ignore[attr-defined]
            raise LeaseLost("job lease is no longer current")

    def fail(self, lease: Job, error_code: str, transient: bool = False) -> None:
        if error_code not in {"storage_unavailable", "invalid_payload", "unsupported_job"}:
            error_code = "job_failed"
        with self.db.session() as session:
            now = database_now(session)
            retry = transient and lease.attempt_count < min(lease.max_attempts, 3)
            result = session.execute(
                update(Job)
                .where(self.fence(lease, now))
                .values(
                    status="pending" if retry else ("dead_letter" if transient else "failed"),
                    run_after=now + timedelta(seconds=min(60, 5 * 4 ** (lease.attempt_count - 1))),
                    lease_owner=None,
                    lease_expires_at=None,
                    error_code=error_code,
                )
            )
            if result.rowcount != 1:  # type: ignore[attr-defined]
                raise LeaseLost("job lease is no longer current")
