# Persistence foundation report

Implemented synchronous SQLAlchemy persistence for local SQLite and PostgreSQL deployments.

- `create_db(url)` returns an explicit `Database` with engine, session factory, transaction context and local-only `initialize()`.
- UUID string identifiers and timezone-aware UTC timestamp handling.
- Ownership-safe composite foreign keys for profiles, charts, requests, readings and feedback.
- Immutable profile revisions at ORM update boundary; revisions remain removable for privacy deletion.
- Auth/session/OAuth/consent, corpus rights/edition/passage/generation, reading workflow, fenced jobs, exports, feedback, quotas, outbox, tombstones and audit records.
- Request states and corpus states are constrained; owner/idempotency uniqueness is database-enforced.
- Explicit Alembic initial revision, upgrade/downgrade support and PostgreSQL-compatible timezone/composite-FK DDL.

Verification on Python 3.12 with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`:

- `pytest tests/test_database.py`: 5 passed.
- `mypy src/astrology_evidence/db.py src/astrology_evidence/models.py`: passed.
- `ruff check ...`: passed after formatting.
- Migration metadata parity and offline PostgreSQL DDL checks passed.

No live PostgreSQL server was available; deployment migrations must still be exercised against the supported PostgreSQL version.
