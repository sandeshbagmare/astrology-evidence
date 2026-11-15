# Jobs and privacy implementation report

Implemented durable privacy jobs and account data lifecycle in `astrology_evidence.jobs` and `astrology_evidence.privacy`.

- Job queue supports idempotent enqueue, PostgreSQL `SKIP LOCKED` claims with SQLite conditional fallback, lease generations, stale lease reclaim, fenced heartbeat/completion, bounded transient retries and dead-letter state.
- Account deletion revokes sessions and denies access synchronously, marks profile and reading state deleted, writes opaque tombstones, then purges private rows asynchronously while retaining shared corpus rows.
- Profile deletion marks the profile inaccessible immediately and purges revisions and dependent private records through a durable job.
- Exports are owner-scoped, expire after 24 hours, are invalidated on deletion, use no-store downloads, and exclude credentials, raw provider payloads and source excerpts.
- Worker entry point: `python -m astrology_evidence.jobs.worker --once`.

Validation: `python -m pytest tests/test_jobs.py tests/test_privacy.py` ? 16 passed; `ruff check ...` clean; `mypy src/astrology_evidence/jobs src/astrology_evidence/privacy --follow-imports=silent` clean.

Operational executor uptime, backup journal replay in deployment, and current rights/provider retention checks remain deployment gates.

Withdrawal outbox follow-up: the independent worker now consumes pending `purge_edition` operations after privacy jobs. It verifies current withdrawal, clears canonical passage text, replaces saved reading narratives/evidence containing the withdrawn edition or passage IDs with a minimal unavailable notice, deletes deterministic passage IDs and edition-filtered points from every recorded generation collection, and acknowledges only after all index deletions succeed. Replays are idempotent; unavailable index access leaves the operation pending. CLI selects configured remote Qdrant or local path without provider calls. No model changes were required.

Verification: jobs/privacy/outbox suite 21 passed, including real local Qdrant removal, index failure/retry, active-edition denial and saved-reading redaction through the worker. Production Qdrant connectivity, scheduling and operational dead-letter monitoring remain unverified.
