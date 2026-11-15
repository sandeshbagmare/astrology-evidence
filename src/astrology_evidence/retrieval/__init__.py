"""Local dense/sparse retrieval; database rights remain authoritative."""

import math
import re
import unicodedata
from collections import Counter
from hashlib import blake2b

from qdrant_client import QdrantClient, models
from sqlalchemy import select

from astrology_evidence.corpus import CorpusService, EvidencePassage, embedding_text, permitted
from astrology_evidence.db import Database
from astrology_evidence.models import ActiveCorpus, CorpusGeneration, Edition, Passage, RightsRecord


def sparse_vector(text: str) -> models.SparseVector:
    """Versioned Unicode TF hashing baseline, not BM25 or a semantic embedding."""
    terms = re.findall(r"[^\W_]+", unicodedata.normalize("NFC", text).casefold())
    counts: Counter[int] = Counter()
    for term in terms:
        counts[int.from_bytes(blake2b(term.encode("utf-8"), digest_size=4).digest(), "big")] += 1
    indices = sorted(counts)
    return models.SparseVector(indices=indices, values=[float(counts[i]) for i in indices])


class E5Encoder:
    """Lazy CPU model loading; no download or model substitution at module import."""

    def __init__(self, revision: str, local_files_only: bool = True):
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("a pinned 40-character E5 model revision is required")
        self.revision = f"intfloat/multilingual-e5-small@{revision}"
        self.model_revision = revision
        self.local_files_only = local_files_only
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                "intfloat/multilingual-e5-small",
                revision=self.model_revision,
                device="cpu",
                local_files_only=self.local_files_only,
            )
        return self._model

    def count_tokens(self, text: str) -> int:
        return len(self.model.tokenizer.encode(text, add_special_tokens=True, truncation=False))

    def encode(self, text: str) -> list[float]:
        if not text.startswith(("query: ", "passage: ")):
            raise ValueError("E5 requires an explicit query or passage prefix")
        if self.count_tokens(text) > 448:
            raise ValueError("embedding input exceeds the 448-token cap")
        return self.model.encode(text, normalize_embeddings=True).tolist()


class QdrantIndex:
    def __init__(self, client: QdrantClient):
        self.client = client

    def build(self, collection: str, passages: list, encoder) -> None:
        self.client.create_collection(
            collection_name=collection,
            vectors_config={
                "dense": models.VectorParams(size=384, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={"lexical": models.SparseVectorParams()},
        )
        batch = []
        for passage, edition in passages:
            text = embedding_text(edition.title, passage.exact_text)
            if encoder.count_tokens(text) > 448:
                raise ValueError(
                    "passage exceeds embedding token cap; reimport with model tokenizer"
                )
            dense = encoder.encode(text)
            if len(dense) != 384 or not all(math.isfinite(value) for value in dense):
                raise ValueError("encoder must produce finite 384-dimensional vectors")
            if not any(dense):
                raise ValueError("encoder produced a zero vector")
            batch.append(
                models.PointStruct(
                    id=passage.id,
                    vector={"dense": dense, "lexical": sparse_vector(passage.exact_text)},
                    payload={
                        "edition_id": edition.id,
                        "tradition": edition.tradition,
                        "language": edition.language,
                        "text_hash": passage.text_hash,
                    },
                )
            )
            if len(batch) == 128:
                self.client.upsert(collection, points=batch, wait=True)
                batch = []
        if batch:
            self.client.upsert(collection, points=batch, wait=True)

    def verify(self, collection: str, expected: dict[str, str]) -> None:
        found = {}
        offset = None
        while True:
            records, offset = self.client.scroll(
                collection,
                limit=128,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            for record in records:
                dense = record.vector.get("dense", [])
                if len(dense) != 384 or not all(math.isfinite(value) for value in dense):
                    raise ValueError("index dimension verification failed")
                found[str(record.id)] = record.payload.get("text_hash")
            if offset is None:
                break
        if found != expected:
            raise ValueError("index ID/hash verification failed")

    def search(
        self, collection: str, question: str, encoder, eligible_ids: list[str], tradition: str
    ) -> list[str]:
        if not eligible_ids:
            return []
        shared_filter = models.Filter(
            must=[
                models.HasIdCondition(has_id=eligible_ids),
                models.FieldCondition(key="tradition", match=models.MatchValue(value=tradition)),
            ]
        )
        dense = encoder.encode(f"query: {question}")
        branches = [
            self.client.query_points(
                collection,
                query=dense,
                using="dense",
                query_filter=shared_filter,
                limit=30,
                with_payload=False,
            ).points
        ]
        sparse = sparse_vector(question)
        if sparse.indices:
            branches.append(
                self.client.query_points(
                    collection,
                    query=sparse,
                    using="lexical",
                    query_filter=shared_filter,
                    limit=30,
                    with_payload=False,
                ).points
            )
        scores: Counter[str] = Counter()
        for branch in branches:
            for rank, point in enumerate(branch, start=1):
                scores[str(point.id)] += 1 / (60 + rank)
        return sorted(scores, key=lambda identifier: (-scores[identifier], identifier))


class RetrievalService:
    def __init__(self, db: Database, index: QdrantIndex, encoder):
        if encoder is None:
            raise ValueError("a configured embedding encoder is required")
        self.db = db
        self.index = index
        self.encoder = encoder
        self.corpus = CorpusService(db)

    def search(
        self,
        question: str,
        tradition: str = "jyotish",
        limit: int = 8,
        action: str = "model_transmit",
    ) -> list[EvidencePassage]:
        if not question.strip() or len(question) > 4000 or not 1 <= limit <= 8:
            raise ValueError("question or result limit is invalid")
        if action not in {"display", "model_transmit"}:
            raise ValueError("invalid retrieval action")
        with self.db.session() as session:
            active = session.get(ActiveCorpus, 1)
            if active is None:
                return []
            generation = session.get(CorpusGeneration, active.generation_id)
            if generation.status != "published":
                return []
            if generation.manifest["encoder_revision"] != self.encoder.revision:
                raise ValueError("query encoder differs from published generation")
            rows = session.execute(
                select(Passage, Edition, RightsRecord)
                .join(Edition, Passage.edition_id == Edition.id)
                .join(RightsRecord, Edition.rights_id == RightsRecord.id)
                .where(Edition.tradition == tradition)
            ).all()
            indexed = set(generation.manifest["indexed_ids"])
            eligible = [
                p.id
                for p, e, r in rows
                if p.id in indexed
                and p.review_state == "approved"
                and all(permitted(e, r, permission) for permission in {"index", "display", action})
            ]
            collection, generation_id = generation.physical_collection_name, generation.id
        ranked = self.index.search(collection, question, self.encoder, eligible, tradition)
        result: list[EvidencePassage] = []
        seen = set()
        used_tokens = 0
        used_chars: Counter[str] = Counter()
        for passage_id in ranked:
            passage = self.corpus.source(passage_id, action=action, generation_id=generation_id)
            if passage is None:
                continue
            # Whole parent is the evidence unit: children cannot silently omit exceptions.
            if passage.parent_id:
                parent = self.corpus.source(
                    passage.parent_id, action=action, generation_id=generation_id
                )
                if parent is None or parent.edition_id != passage.edition_id:
                    continue
                passage = parent
            if passage.id in seen:
                continue
            # Recheck every permission after index access; an in-flight withdrawal fails closed.
            with self.db.session() as session:
                edition = session.get(Edition, passage.edition_id)
                rights = session.get(RightsRecord, edition.rights_id)
                if not all(
                    permitted(edition, rights, permission)
                    for permission in {"index", "display", action}
                ):
                    continue
            cost = self.encoder.count_tokens(embedding_text(passage.title, passage.text))
            if used_tokens + cost > 6000:
                continue
            if used_chars[passage.edition_id] + len(passage.text) > passage.max_chars:
                continue
            used_chars[passage.edition_id] += len(passage.text)
            used_tokens += cost
            seen.add(passage.id)
            result.append(passage)
            if len(result) == limit:
                break
        return result
