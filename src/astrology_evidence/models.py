"""Transactional records. Public identifiers are opaque UUID strings."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class UTCDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("timestamps must be timezone aware")
            return value.astimezone(UTC)
        return None

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=UTC) if value is not None and value.tzinfo is None else value


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class User(Record, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("issuer", "subject"),)
    issuer: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    display_name: Mapped[str | None] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Session(Record, Base):
    __tablename__ = "sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class OAuthTransaction(Record, Base):
    __tablename__ = "oauth_transactions"
    state_hash: Mapped[str] = mapped_column(String(64), unique=True)
    browser_hash: Mapped[str] = mapped_column(String(64))
    nonce: Mapped[str] = mapped_column(String(255))
    code_verifier: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Consent(Record, Base):
    __tablename__ = "consents"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(80))
    notice_version: Mapped[str] = mapped_column(String(80))
    granted_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Profile(Record, Base):
    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("id", "owner_id"), CheckConstraint("version >= 1"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(80), default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ProfileRevision(Record, Base):
    __tablename__ = "profile_revisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], ondelete="CASCADE"
        ),
        UniqueConstraint("profile_id", "revision"),
        UniqueConstraint("id", "owner_id"),
        CheckConstraint("revision >= 1"),
    )
    profile_id: Mapped[str] = mapped_column(String(36), index=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    birth_input: Mapped[dict] = mapped_column(JSON)


class Chart(Record, Base):
    __tablename__ = "charts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["profile_revision_id", "owner_id"],
            ["profile_revisions.id", "profile_revisions.owner_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("owner_id", "profile_revision_id", "input_hash", "settings_hash"),
        UniqueConstraint("id", "owner_id"),
    )
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    profile_revision_id: Mapped[str] = mapped_column(String(36))
    input_hash: Mapped[str] = mapped_column(String(64))
    settings_hash: Mapped[str] = mapped_column(String(64))
    settings: Mapped[dict] = mapped_column(JSON)
    manifest: Mapped[dict] = mapped_column(JSON)
    facts: Mapped[list] = mapped_column(JSON, default=list)
    unavailable_facts: Mapped[list] = mapped_column(JSON, default=list)


class RightsRecord(Record, Base):
    __tablename__ = "rights_records"
    evidence_reference: Mapped[str] = mapped_column(Text)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    jurisdictions: Mapped[list] = mapped_column(JSON, default=list)
    excerpt_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewer: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    withdrawn_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Edition(Record, Base):
    __tablename__ = "editions"
    rights_id: Mapped[str] = mapped_column(ForeignKey("rights_records.id"))
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(500))
    tradition: Mapped[str] = mapped_column(String(80), default="jyotish")
    language: Mapped[str] = mapped_column(String(30), default="en")
    bibliographic_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    artifact_checksum: Mapped[str | None] = mapped_column(String(64))
    review_state: Mapped[str] = mapped_column(String(30), default="pending")
    withdrawn_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Passage(Record, Base):
    __tablename__ = "passages"
    edition_id: Mapped[str] = mapped_column(ForeignKey("editions.id"), index=True)
    exact_text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64))
    normalized_text: Mapped[str] = mapped_column(Text, default="")
    locators: Mapped[dict] = mapped_column(JSON)
    layer_type: Mapped[str] = mapped_column(String(80))
    attributed_author: Mapped[str | None] = mapped_column(String(500))
    attribution_evidence: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(30), default="en")
    review_state: Mapped[str] = mapped_column(String(30), default="pending")
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("passages.id"))


class CorpusGeneration(Record, Base):
    __tablename__ = "corpus_generations"
    __table_args__ = (
        CheckConstraint("status IN ('draft','indexing','staged','published','withdrawn','failed')"),
    )
    physical_collection_name: Mapped[str] = mapped_column(String(255), unique=True)
    manifest_hash: Mapped[str] = mapped_column(String(64))
    manifest: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    expected_count: Mapped[int] = mapped_column(Integer, default=0)
    indexed_count: Mapped[int] = mapped_column(Integer, default=0)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ActiveCorpus(Base):
    __tablename__ = "active_corpus"
    __table_args__ = (CheckConstraint("id = 1"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    generation_id: Mapped[str] = mapped_column(ForeignKey("corpus_generations.id"))


class ReadingRequest(Record, Base):
    __tablename__ = "reading_requests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["profile_revision_id", "owner_id"],
            ["profile_revisions.id", "profile_revisions.owner_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("owner_id", "idempotency_key"),
        UniqueConstraint("id", "owner_id"),
        CheckConstraint(
            "status IN ('admitted','generating','succeeded','failed','unknown','cancelled')"
        ),
    )
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    profile_revision_id: Mapped[str] = mapped_column(String(36))
    question: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    request_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="admitted")
    execution_token: Mapped[str | None] = mapped_column(String(64))
    stage: Mapped[str | None] = mapped_column(String(80))
    deadline: Mapped[datetime] = mapped_column(UTCDateTime())
    failure_code: Mapped[str | None] = mapped_column(String(80))


class Reading(Record, Base):
    __tablename__ = "readings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["request_id", "owner_id"],
            ["reading_requests.id", "reading_requests.owner_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["chart_id", "owner_id"], ["charts.id", "charts.owner_id"], ondelete="CASCADE"
        ),
        UniqueConstraint("id", "owner_id"),
    )
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    request_id: Mapped[str] = mapped_column(String(36), unique=True)
    chart_id: Mapped[str] = mapped_column(String(36))
    answer: Mapped[dict] = mapped_column(JSON)
    evidence_manifest: Mapped[dict] = mapped_column(JSON, default=dict)
    versions: Mapped[dict] = mapped_column(JSON, default=dict)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Job(Record, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("attempt_count >= 0 AND max_attempts > 0 AND lease_generation >= 0"),
    )
    kind: Mapped[str] = mapped_column(String(80), index=True)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    payload_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    lease_owner: Mapped[str | None] = mapped_column(String(255))
    lease_generation: Mapped[int] = mapped_column(Integer, default=0)
    lease_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    run_after: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True)
    error_code: Mapped[str | None] = mapped_column(String(80))
    cancellation_state: Mapped[str] = mapped_column(String(30), default="active")


class Export(Record, Base):
    __tablename__ = "exports"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    payload: Mapped[dict | None] = mapped_column(JSON)


class Feedback(Record, Base):
    __tablename__ = "feedback"
    __table_args__ = (
        ForeignKeyConstraint(
            ["reading_id", "owner_id"], ["readings.id", "readings.owner_id"], ondelete="CASCADE"
        ),
    )
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    reading_id: Mapped[str] = mapped_column(String(36))
    category: Mapped[str] = mapped_column(String(80))
    comment: Mapped[str | None] = mapped_column(Text)


class QuotaBucket(Base):
    __tablename__ = "quota_buckets"
    __table_args__ = (CheckConstraint("used >= 0 AND capacity >= 0"),)
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    used: Mapped[int] = mapped_column(Integer, default=0)
    capacity: Mapped[int] = mapped_column(Integer)
    resets_at: Mapped[datetime] = mapped_column(UTCDateTime())


class QuotaReservation(Record, Base):
    __tablename__ = "quota_reservations"
    bucket_id: Mapped[str] = mapped_column(ForeignKey("quota_buckets.id", ondelete="CASCADE"))
    request_id: Mapped[str] = mapped_column(
        ForeignKey("reading_requests.id", ondelete="CASCADE"), unique=True
    )
    amount: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="reserved")


class OutboxOperation(Record, Base):
    __tablename__ = "outbox_operations"
    kind: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="pending")


class DeletionTombstone(Record, Base):
    __tablename__ = "deletion_tombstones"
    subject_hash: Mapped[str] = mapped_column(String(64), index=True)
    scope: Mapped[str] = mapped_column(String(80))
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class AuditEvent(Record, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(80))
    object_id: Mapped[str | None] = mapped_column(String(36))
    outcome: Mapped[str] = mapped_column(String(80))
    request_id: Mapped[str | None] = mapped_column(String(36))


# Revisions are append-only through ORM writes; deletion remains available for privacy purge.


@event.listens_for(ProfileRevision, "before_update")
def prevent_revision_update(_mapper, _connection, _target):
    raise ValueError("profile revisions are immutable; create a new revision")
