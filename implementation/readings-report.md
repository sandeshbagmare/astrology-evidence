# Reading implementation verification — 2026-11-15

Implemented `ReadingService(db, retriever, provider, settings)` with owned chart selection, 2,000-character questions, durable request idempotency and safe polling. `create(user_id, profile_revision_id, question, idempotency_key, chart_id=None)` returns `{id, request_id, status, reading_id, failure_code}`. No replay resumes provider work. An admission SQL row serializes request counts (global 5, per-user active 1, daily 10); a current execution token, deadline and transaction fence publication. Expired active requests become failed/unknown, never automatically resent.

The real LangGraph executes retrieve → abstain or generate → validate, with at most one validation repair (two provider calls), recursion limit 8, 150-second request deadline and each provider timeout bounded by the lesser of 120 seconds and remaining time. Empty evidence and disabled AI do not call the provider. Model consent, current ownership/deletion, source hashes, published generation and current rights are checked before transmission and publication. Cancellation/consent revocation prevent late publication. Provider ambiguity becomes unknown without an automatic retry. Tracing is disabled around graph invocation.

The answer gate is deliberately extractive: exact source excerpts, exact canonical Unicode code-point spans and grapheme boundaries, original source hashes/locators, and server-computed chart facts. Generated uncited narrative, invented fact references, arbitrary conclusions, free-form summaries and self-certified reviewed applicability are rejected. Source excerpt claims are marked not_established; summaries and limitations use bounded reviewed server text. A data-only equality predicate evaluator returns true/false/unknown and rejects arbitrary expression fields. The production reviewed-rule registry is empty because no expert-reviewed traditional rule data was supplied. This is not semantic-entailment verification or an astrology prediction validation claim.

Routes provide create/list/read/delete, request status/cancel, explicit model-processing consent, and minimal feedback. All private resources derive ownership from the session, all mutations require CSRF, provider/owner/tool overrides are rejected. Saved reading delivery rechecks current source rights and suppresses the entire narrative with HTTP 410 on withdrawal. Deletion clears answer/evidence content. Existing privacy exports omit answer text and source excerpts conservatively.

## Recorded checks

- `./scripts/dev.ps1 -m pytest tests/test_validation.py -q`: initial missing-module failures; successive failures for Hangul grapheme splitting and missing reviewed-rule evaluator were corrected.
- `./scripts/dev.ps1 -m pytest tests/test_readings.py -q`: initial missing service and route failures; new 2,001-character test failed before limiting both service and route to 2,000.
- Final `./scripts/dev.ps1 -m pytest tests/test_readings.py tests/test_validation.py tests/test_provider.py -q`: **97 passed**, exit 0. Includes 55 reading/validation tests and 42 existing provider tests; offline fakes with real LangGraph and real SQLAlchemy schema.
- Final Ruff check on all seven owned implementation/test files: **passed**, exit 0.
- Final mypy on five owned source modules: **passed**, exit 0.
- Ruff formatter run on the seven owned files. Third-party LangSmith asyncio and Authlib deprecation warnings remain.

## Limits

No live provider call, PostgreSQL concurrency deployment test, real expert-reviewed traditional rule registry, semantic relevance evaluation, or 150-item evaluation benchmark was performed. Retrieval/transport cannot be forcibly interrupted while a synchronous dependency is running, but all transmission timeouts and publication deadline fences are enforced; no over-deadline answer is saved. Database-based admission is implemented for SQLite and PostgreSQL, tested here on SQLite. Publication and consent mutations share the admission lock; corpus rights mutations use their existing independent service, with authoritative checks immediately before saving and on every read. No claim of public-production readiness.
