from datetime import timedelta

import pytest
from sqlalchemy import select

from astrology_evidence.db import create_db
from astrology_evidence.jobs import JobService, LeaseLost
from astrology_evidence.models import Job, utcnow


@pytest.fixture
def service():
    db = create_db("sqlite://")
    db.initialize()
    yield JobService(db)
    db.engine.dispose()


def test_idempotent_enqueue(service):
    first = service.enqueue("export", {}, "same")
    assert service.enqueue("export", {}, "same").id == first.id
    with pytest.raises(ValueError):
        service.enqueue("export", {"changed": True}, "same")


def test_only_one_lease(service):
    service.enqueue("export", {}, "one")
    assert service.claim("worker-a") is not None
    assert service.claim("worker-b") is None


def test_expired_reclaim_fences_old_worker(service):
    job = service.enqueue("export", {}, "one")
    first = service.claim("worker-a")
    with service.db.session() as session:
        session.get(Job, job.id).lease_expires_at = utcnow() - timedelta(seconds=1)
    second = service.claim("worker-b")
    assert second.lease_generation == first.lease_generation + 1
    with pytest.raises(LeaseLost):
        service.heartbeat(first)
    with pytest.raises(LeaseLost):
        service.complete(first)
    service.complete(second)


def test_expired_worker_cannot_complete_without_reclaim(service):
    service.enqueue("export", {}, "one")
    lease = service.claim("worker")
    with service.db.session() as session:
        session.get(Job, lease.id).lease_expires_at = utcnow() - timedelta(seconds=1)
    with pytest.raises(LeaseLost):
        service.complete(lease)


def test_retry_three_attempts_then_dead_letter(service):
    service.enqueue("export", {}, "one")
    for attempt in range(3):
        lease = service.claim("worker")
        service.fail(lease, "storage_unavailable", transient=True)
        with service.db.session() as session:
            row = session.get(Job, lease.id)
            assert row.attempt_count == attempt + 1
            if attempt < 2:
                assert row.status == "pending" and row.run_after > utcnow()
                row.run_after = utcnow() - timedelta(seconds=1)
            else:
                assert row.status == "dead_letter"
    assert service.claim("worker") is None


def test_heartbeat_and_nonretryable_failure(service):
    service.enqueue("export", {}, "one")
    lease = service.claim("worker")
    service.heartbeat(lease)
    service.fail(lease, "invalid_payload")
    with service.db.session() as session:
        assert session.scalar(select(Job)).status == "failed"


def test_provider_jobs_are_not_claimed(service):
    with pytest.raises(ValueError):
        service.enqueue("provider_call", {}, "unsafe")


def test_two_workers_race_one_durable_job(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    db = create_db("sqlite:///" + str(tmp_path / "jobs.db").replace("\\", "/"))
    db.initialize()
    service = JobService(db)
    service.enqueue("export", {}, "race")
    with ThreadPoolExecutor(max_workers=2) as pool:
        leases = list(pool.map(service.claim, ["a", "b"]))
    assert sum(lease is not None for lease in leases) == 1
    db.engine.dispose()
