# Corpus and retrieval implementation report

Implemented 2026-11-15 in `src/astrology_evidence/corpus` and `retrieval`.

## Public Python contracts

- `CorpusService(db, tokenizer=None, max_tokens=448)`; optional tokenizer is a callable returning the token count. Supply `E5Encoder.count_tokens` for production ingestion. The fallback counts UTF-8 bytes conservatively and is not presented as an embedding tokenizer.
- `import_edition(payload: dict | EditionImport) -> str`: requires explicit approved rights evidence, named reviewer, jurisdictions, unexpired permission to store, excerpt limit and attribution. Every passage requires author, attribution evidence, text layer, review and edition locator. Source text stays exact; search normalization stays separate. Long parents are split into exact character spans, with linked parent qualifications preserved.
- `publish(index, encoder) -> str`: builds a new physical Qdrant collection, checks every ID/hash and dense dimension, then updates the database generation pointer. A failed build or observed mid-build rights/text change leaves the earlier generation active. All indexed snapshots are named independently; no collection alias is involved.
- `withdraw(edition_id) -> None`: database denial and a deduplicated purge outbox record in one transaction. Physical purge requires the application's outbox worker; retained stale vectors cannot be read through retrieval.
- `source(passage_id, action='display', generation_id=None) -> EvidencePassage | None`: reads exact database text only after rights, published-generation membership, hash and quotation-length checks.
- `QdrantIndex(QdrantClient(...))`: actual named dense and sparse vectors, cosine dense matching, Unicode NFC/casefold term-frequency hashing for sparse matching, explicit RRF k=60, 30 candidates per branch, identical eligible-ID/tradition filters on both branches. Sparse baseline is explicitly not BM25. Index payloads contain no excerpts.
- `E5Encoder(revision=<40-character commit SHA>, local_files_only=True)`: lazy optional SentenceTransformer multilingual-e5-small CPU encoder; E5 prefixes and 448 model-token cap; never substitutes a synthetic encoder.
- `RetrievalService(db, index, encoder).search(question, tradition='jyotish', limit=8, action='model_transmit')`: requires a configured encoder and matching generation revision. Use action='display' for source-search UI. Permissions are checked before both branches and after retrieval. Child hits expand to complete same-edition parents; insufficient parent rights/budget suppress the evidence unit. Bundle cap is 6,000 embedding-token counts and aggregate per-edition excerpt characters. The answer assembler must also impose its generation tokenizer's budget.

`EvidencePassage` fields: `id`, `edition_id`, `text`, `title`, `locators`, `text_hash`, `attributed_author`, `layer_type`, `parent_id`, `permission` (permissions mapping), `attribution`, `max_chars`, `generation_id`.

HTTP routes and production configuration are owned by the coordinating integration workstream; these service methods are not themselves HTTP authorization boundaries. Admin authentication and CSRF must guard import/publication/withdrawal routes.

## Verification

Python 3.14, installed qdrant-client 1.20.0, actual Qdrant in-memory local mode, SQLite, explicitly synthetic deterministic 384-dimensional test encoder. `PYTHONPATH=.runtime314;src`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

- `python -m pytest tests/test_corpus.py tests/test_retrieval.py -q`: **25 passed**.
- `python -m ruff check src/astrology_evidence/corpus src/astrology_evidence/retrieval tests/test_corpus.py tests/test_retrieval.py`: **passed**.
- Full test suite attempted during concurrent implementation: collection blocked by `tests/test_privacy.py` importing its then-unimplemented PrivacyService. Coordinator performs the final combined-suite run.

Coverage includes exact Unicode and printed/PDF locator preservation, independent actions, missing rights evidence, expiry, chunk span reconstruction, idempotent withdrawal, actual dense+sparse querying, tradition filters, permission revocation with stale vectors, text tampering, wrong dimensions, failed generation publication, parent exceptions, disabled encoder, Unicode sparse normalization, rights changed during publication, and aggregate excerpt limits.

## Explicit limits

No real books acquired; only `examples/synthetic-corpus.json`. No OCR/extraction worker is claimed. JSON import expects human-reviewed text and provenance. No E5 weights downloaded or semantic quality benchmark run. No ranking/recall/latency/free-tier claim follows from these integration tests. Sparse hashing can collide and lacks reviewed transliteration aliases; multilingual recall remains unvalidated. Parent evidence returns the authoritative parent ID rather than claiming a standalone child supports the complete rule.

The current eligibility scan is deliberately a small-curated-corpus implementation; large corpora need bounded database selection and measured Qdrant filter scaling. Failed staging collections and withdrawn-vector cleanup require the outbox/maintenance worker. Application-level withdrawal takes effect immediately even while cleanup is pending. Generation snapshots are immutable by service convention; a database administrator can still change records, and source hash checks deny altered text.
