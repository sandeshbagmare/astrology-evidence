"""Idempotent rights-withdrawal outbox reconciliation."""

from qdrant_client import models
from sqlalchemy import select, update

from astrology_evidence.db import Database
from astrology_evidence.models import CorpusGeneration, Edition, OutboxOperation, Passage, Reading


def references(value, identifiers: set[str]) -> bool:
    if isinstance(value, str):
        return value in identifiers
    if isinstance(value, dict):
        return any(references(child, identifiers) for child in value.values())
    if isinstance(value, list):
        return any(references(child, identifiers) for child in value)
    return False


def process_withdrawal(db: Database, client) -> bool:
    """Redact local copies first, acknowledge only after every vector deletion succeeds.

    Multiple workers may replay the same deletion; deterministic point IDs make that safe.
    A failed reconciliation remains pending and is retried on the next worker poll.
    """
    with db.session() as session:
        operation = session.scalar(
            select(OutboxOperation)
            .where(
                OutboxOperation.kind == "purge_edition",
                OutboxOperation.status == "pending",
            )
            .order_by(OutboxOperation.created_at, OutboxOperation.id)
            .limit(1)
        )
        if operation is None:
            return False
        edition = session.get(Edition, operation.payload.get("edition_id"))
        if edition is None or edition.withdrawn_at is None:
            return False
        operation_id, edition_id = operation.id, edition.id
        passages = list(session.scalars(select(Passage).where(Passage.edition_id == edition_id)))
        passage_ids = [passage.id for passage in passages]
        identifiers = set(passage_ids) | {edition_id}
        for passage in passages:
            passage.exact_text = ""
            passage.normalized_text = ""
            passage.review_state = "withdrawn"
        for reading in session.scalars(select(Reading)):
            if references(reading.evidence_manifest, identifiers) or references(
                reading.answer, identifiers
            ):
                reading.answer = {
                    "status": "insufficient_evidence",
                    "limitations": ["Source rights were withdrawn."],
                }
                reading.evidence_manifest = {"withdrawn_edition_ids": [edition_id]}
        collections = list(session.scalars(select(CorpusGeneration.physical_collection_name)))
    if collections and client is None:
        return False
    try:
        for collection in collections:
            if not client.collection_exists(collection):
                continue
            if passage_ids:
                client.delete(
                    collection_name=collection,
                    points_selector=models.PointIdsList(
                        points=[str(point_id) for point_id in passage_ids]
                    ),
                    wait=True,
                )
            # Also remove any delayed/obsolete point with the edition payload.
            client.delete(
                collection_name=collection,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="edition_id", match=models.MatchValue(value=edition_id)
                            )
                        ]
                    )
                ),
                wait=True,
            )
    except Exception:
        # No upstream body enters logs. Rights denial already applies; preserve retry obligation.
        return False
    with db.session() as session:
        edition = session.get(Edition, edition_id)
        if edition is None or edition.withdrawn_at is None:
            return False
        session.execute(
            update(OutboxOperation)
            .where(
                OutboxOperation.id == operation_id,
                OutboxOperation.status == "pending",
            )
            .values(status="succeeded")
        )
    return True
