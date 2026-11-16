# Application implementation progress

Implementation began after explicit user approval on November 15, 2026. The integrated source is on `main`, developed on `implementation/mvp`, with small feature and fix commits and independent agent reviews. The current local working tree contains an in-progress full-context audit and fixes; update this record with its final commit and exact checks before publishing the audit.

## Implemented

- Typed configuration, runtime capability gates, FastAPI, SQLAlchemy and frozen Alembic migration.
- Google OIDC protocol, browser-bound transactions, opaque sessions, CSRF and explicit synthetic local login.
- Owned birth profiles and revisions; timezone gaps/folds and uncertain-time handling; versioned chart calculations and accessible fact tables/house diagram.
- Rights-controlled curated text import, immutable corpus publication, local E5 adapter and actual Qdrant dense/sparse retrieval.
- Bounded LangGraph reading workflow, explicit provider consent, idempotency, shared quota admission, cancellation/deadline fences and rights-aware history.
- Conservative exact-source answers: no unreviewed traditional rule is treated as validated applicability. Complete evidence units preserve negations/exceptions.
- Durable privacy jobs, account/profile deletion, expiring exports, source-withdrawal outbox and physical vector/text cleanup.
- Server-rendered application pages and working ordinary-form adapters, administrative import/publication, source library and privacy controls.
- Bounded extraction/OCR adapter, evaluation CLI, synthetic fixtures, Docker/Compose package and PostgreSQL/Qdrant CI tests.

## Verification evidence

Local integrated Python 3.14 checks: 250 passed, with two PostgreSQL/Qdrant integration tests skipped because Docker services are unavailable locally. The Python 3.12 native chart suite passed 33 tests. Ruff and mypy pass across the source tree. Documentation validation checks 83 files with no issues. The local browser verified HTTP readiness on port 18766 and completed the synthetic login/profile/chart/reading flow. Port 18766 is a developer process on this workstation, not a permanent public application host.

Browser: local synthetic login, consented profile creation, native chart calculation through an isolated process, and insufficient-evidence reading completed successfully. Mobile320px has no horizontal overflow in the exercised flow. This is not full screen-reader conformance certification.

First Linux CI on b191526 exposed a Windows-only CREATE_NO_WINDOW typing issue; the portable attribute fix is now in place. CI passed on `bc3e5a0d394c0c0337abb2a537ef5a301531f392` (run 43776294459), the GPT-6.1 Sol handoff commit `11610bf15f83868e6243f83abe944a4f003fe0b0` (run 43778862647), and documentation/status commit `5c6b5301c465353bb205ae85c0c27272333b6010`. Each Python CI run used PostgreSQL 16 and Qdrant 1.20 and passed pytest, Ruff and mypy.

## Independent reviews and resolved defects

- Chart cache crossed profile revisions: cache key/constraint now includes revision identity.
- Expired replay remained generating: status reads and replay terminalize expired requests without resending.
- Partial source quotes removed negation: only complete evidence units are accepted until reviewed excerpt boundaries exist.
- Withdrawal outbox had no consumer: worker redacts stored text/readings and deletes vector points, retaining pending state on failure.
- Async ordinary forms blocked the event loop: synchronous service dispatch now runs in a worker thread.
- Nullable database results and malformed Qdrant shapes now fail closed with targeted regression tests.

## Deliberate decisions

Parallel agents owned separate modules; coordinator integrated and committed. Recent commits include GPT-6.1 Sol in their commit trailers. A premature broad staging operation captured an in-progress validator draft in an intermediate commit; subsequent strict validator commit replaces it, and final CI/review applies to the complete branch. Do not deploy intermediate commits.

Windows Application Control blocks the uv-created launcher and selected new native wheels. The policy was not disabled. A runtime installation attempt was rejected by automatic approval review and was not retried. The existing allowed Python3.14 runs app tests with local locked wheels; the allowed existing Python3.12 runs calculations in a process with a minimal environment. Standard Linux/CI uses one Python3.12 environment. Dependencies were pinned to compatible releases; maintained pysweph exposes the swisseph API.

## Unresolved external release gates

- No real editions licensed or ingested, no domain-reviewed production rules, no150-item expert benchmark labels.
- No live Google account authorization or third-party generation call; supplied chat credential is not reused or saved. A replacement runtime secret, configured Google client and provider review are needed.
- No empirically validated predictive claims. Current AI answers are constrained extracts, not full expert astrological synthesis.
- E5 model weights, actual Sanskrit retrieval quality and host memory/latency still require measured validation.
- No funded production host, backup/restore drill, full accessibility audit or public real-user deployment.
- Docker image/Compose execution cannot run on this laptop; service behavior is exercised by CI, but image execution is a distinct check.

The application is a functioning engineering baseline for local synthetic use, not a claim that the entire production/knowledge acquisition program is complete. External gates are enforced or documented rather than fabricated.

## Context and code review findings — November 16, 2026

Focused independent reviews of identity/privacy, calculations/corpus, deployment, UI, operations and test/security found no confirmed OIDC ownership or source-withdrawal defect. Fixes in progress address stale planning-only status text, an unpinned README Python version, user-facing DST-fold selection, source-library search and navigation, reading-delete confirmation, and a bounded curator edition-import request. The calculation review found that retrograde classification has no approved near-station tolerance and that chart positions lack independent reference fixtures; these remain domain/accuracy gates, not values to guess in code. Run a final whole-tree test and doc validation after the review fixes are integrated. The local dev server is available at `http://127.0.0.1:18766` only while its developer process remains running; public Pages is a static reading guide, not a Python application host.


## Final review addendum

Independent review reproduced event-loop blocking for ordinary forms; the synchronous dispatcher now runs through Starlette threadpool and has a regression test. Chart caching now includes profile revision; expired request status is terminalized on reads/replay; full passage quoting preserves source qualifications; withdrawal outbox cleanup is executable and tested. The operator command `python -m astrology_evidence.manage` lists opaque user IDs, grants curator role locally and imports bounded edition JSON.

## Handoff article

See [GPT-6.1 Sol implementation handoff](GPT-6.1-SOL-IMPLEMENTATION-ARTICLE.md) for detailed work summary, commit inventory, test evidence, release gates and safe continuation points.

## November 16 context/code audit

Compared all 44 numbered context documents plus the context index against the implementation and reviewed product/deployment/security/evaluation contracts. Focused independent reviews covered identity/privacy, calculations/corpus, deployment, UI and security. Confirmed the local app responds on `127.0.0.1:18766`; the host process is not a persistent or public deployment. Corrected the README Python pin, curator commands, plan-status warning, provider status and stale agent parallelism note. Reviews identified missing UI flows, a missing import request cap, and an unapproved near-station calculation policy; the first two are being fixed with regression tests. The pre-audit integrated Python run passed 250 tests with two service skips; a prior native calculation run passed 33 tests. A fresh native rerun in this audit was blocked before test startup by Windows Application Control. Focused request-limit tests, Ruff, mypy and documentation checks have passed; record the final integrated results before committing this review.
