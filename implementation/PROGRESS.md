# Implementation ledger

User approved full implementation and testing on 2026-11-15. Work proceeds on implementation/mvp with small reviewed commits. The documentation-only restriction is superseded. No public app deployment or paid infrastructure is implied.

## Decisions

- Ruling: parallel implementers use disjoint directories; coordinator owns integration and Git commits. This follows the user's explicit parallel-work request over the skill's sequential-worker default. Cost if wrong: integration rework; final combined tests are mandatory.
- Ruling: use Python 3.12 via `python -m uv`; uv is installed but absent from PATH. Docker is unavailable, so portable local tests use SQLite and embedded Qdrant, while PostgreSQL service tests are supplied and run separately when a service exists. Never equate SQLite passing with PostgreSQL verification.
- Ruling: local synthetic mode may use explicit Moshier ephemeris mode, never silently labeled Swiss-file calculations. Production requires the reviewed engine/data/license settings and release gates.
- Rights-cleared real books, domain-review benchmark labels, Google credentials, replacement provider secret and provider privacy review are external release inputs. Build all corresponding interfaces and test fixtures without fabricating approvals.

## Phases

1. Foundation/provider/calculation contracts — in progress.
2. Persistence, Google identity, profile ownership — queued.
3. Corpus, retrieval, rules and jobs — queued.
4. Grounded workflow, privacy and application UI — queued.
5. Integration, browser testing, release packaging and independent review — queued.

Each phase records actual test commands/results and commit IDs below. Do not mark launch gates passed from synthetic tests.
