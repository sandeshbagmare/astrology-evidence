# Jobs and privacy implementation report

Implemented durable privacy jobs and account data lifecycle in `astrology_evidence.jobs` and `astrology_evidence.privacy`.

- Job queue supports idempotent enqueue, PostgreSQL `SKIP LOCKED` claims with SQLite conditional fallback, lease generations, stale lease reclaim, fenced heartbeat/completion, bounded transient retries and dead-letter state.
- Account deletion revokes sessions and denies access synchronously, marks profile and reading state deleted, writes opaque tombstones, then purges private rows asynchronously while retaining shared corpus rows.
- Profile deletion marks the profile inaccessible immediately and purges revisions and dependent private records through a durable job.
- Exports are owner-scoped, expire after 24 hours, are invalidated on deletion, use no-store downloads, and exclude credentials, raw provider payloads and source excerpts.
- Worker entry point: `python -m astrology_evidence.jobs.worker --once`.

Validation: `python -m pytest tests/test_jobs.py tests/test_privacy.py` ? 16 passed; `ruff check ...` clean; `mypy src/astrology_evidence/jobs src/astrology_evidence/privacy --follow-imports=silent` clean.

Operational executor uptime, backup journal replay in deployment, and current rights/provider retention checks remain deployment gates.
