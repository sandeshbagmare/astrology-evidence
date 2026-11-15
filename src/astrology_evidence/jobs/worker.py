"""Independent privacy executor: python -m astrology_evidence.jobs.worker --once."""

import argparse
import logging
import time
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from astrology_evidence.config import Settings
from astrology_evidence.db import Database, create_db
from astrology_evidence.jobs import JobService, LeaseLost
from astrology_evidence.jobs.outbox import process_withdrawal
from astrology_evidence.models import OutboxOperation
from astrology_evidence.privacy import PrivacyService, ResourceUnavailable

log = logging.getLogger(__name__)


def run_once(
    db: Database, worker_id: str, qdrant_client=None, settings: Settings | None = None
) -> bool:
    jobs = JobService(db)
    privacy = PrivacyService(db)
    privacy.purge_expired_exports()
    lease = jobs.claim(worker_id)
    if lease is None:
        with db.session() as session:
            pending = session.scalar(
                select(OutboxOperation.id)
                .where(OutboxOperation.kind == "purge_edition", OutboxOperation.status == "pending")
                .limit(1)
            )
        if pending is None:
            return False
        if qdrant_client is not None or settings is None:
            return process_withdrawal(db, qdrant_client)
        from qdrant_client import QdrantClient

        try:
            client = (
                QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key.get_secret_value()
                    if settings.qdrant_api_key
                    else None,
                )
                if settings.qdrant_url
                else QdrantClient(path=settings.qdrant_path)
            )
        except Exception:
            return process_withdrawal(db, None)
        try:
            return process_withdrawal(db, client)
        finally:
            client.close()
    try:
        privacy.process_job(lease)
    except LeaseLost:
        log.info("job_lease_lost job_id=%s", lease.id)
    except (ValueError, ResourceUnavailable):
        try:
            jobs.fail(lease, "invalid_payload")
        except LeaseLost:
            pass
    except OperationalError:
        try:
            jobs.fail(lease, "storage_unavailable", transient=True)
        except LeaseLost:
            pass
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run durable privacy jobs")
    parser.add_argument("--once", action="store_true", help="Process at most one eligible job")
    args = parser.parse_args()
    settings = Settings()
    db = create_db(settings.database_url)
    worker_id = f"privacy-{uuid4()}"
    try:
        while True:
            worked = run_once(db, worker_id, settings=settings)
            if args.once:
                return
            if not worked:
                time.sleep(2)
    finally:
        db.engine.dispose()


if __name__ == "__main__":
    main()
