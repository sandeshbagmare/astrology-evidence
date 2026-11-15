# Readiness report

Updated November 16, 2026. This report describes the implementation and its tested limits.

## Verdict

**A working local application is implemented. It is not cleared for real-user production.** The app provides authentication integration, birth profiles, deterministic charts, a rights-controlled Qdrant corpus, constrained readings, privacy jobs, and a server-rendered UI. External content, provider, accuracy, and deployment gates remain open.

## Implemented

- Python 3.12 application, FastAPI, PostgreSQL migrations, Google OIDC integration and an explicitly enabled local synthetic login.
- Owner-scoped profiles/revisions, timezone fold/gap handling, isolated chart calculation and accessible chart fact views.
- Curated edition import, explicit rights permissions, immutable index generations, Qdrant dense/lexical retrieval, source withdrawal cleanup.
- Bounded LangGraph/Responses workflow, model-processing consent, citation hash/span validation, abstention when evidence is missing.
- Durable jobs for privacy/export, worker lease fencing, deletion tombstones and rights-aware exports.
- Server-rendered browser UI, curator workflow, bounded extraction/OCR adapter and offline retrieval evaluation tool.
- Docker/Compose packaging and CI tests with PostgreSQL 16 and Qdrant 1.20 services.

## Verification

The latest local integrated run passed 250 Python tests with two external-service checks skipped because Docker is unavailable locally. The native chart suite passed 33 tests under Python 3.12. Ruff and mypy pass. GitHub Actions passed on commit `a366b6ee8f1b6ab03f1f62d579c59d5f4f760dfd`, running the Python suite with PostgreSQL and Qdrant, plus Ruff and mypy. Browser testing covered synthetic login, saved birth profile, chart rendering, insufficient-evidence reading and a 320px viewport without horizontal overflow.

The app runs locally at `http://127.0.0.1:18766` in the current development session. Use [the runbook](implementation/RUNBOOK.md) to start it independently. The GitHub Pages site is a reading guide, not the Python backend.

## Release gates

| Area | Current status |
|---|---|
| Source corpus | No real books ingested; edition-specific rights required |
| Domain rules | No expert-reviewed production rules or 150-question labeled evaluation set |
| Chart accuracy | Unit/edge-case tests pass; independent reference parity remains unmeasured |
| Provider | Offline Responses wire tests pass; no real provider request or provider data review |
| Identity | OAuth protocol tests pass; live Google credentials/domain not configured |
| Embeddings | Local adapter implemented; model weights, memory and retrieval quality not benchmarked |
| Security/privacy | Offline adversarial tests pass; live backup/restore and deployment operations not exercised |
| Hosting | Compose provided; Docker image was not built on this machine, and no public Python app host is configured |
| Scientific claims | Astrology's predictive validity is not established by calculations or citation fidelity |

AI and embeddings remain disabled by default. The local demo uses invented inputs. Do not enable real-user operation until the source-rights, licensing, provider, identity, expert-evaluation, hosting and recovery gates are resolved.

## Start here

Read [the Pages guide](https://sandeshbagmare.github.io/astrology-evidence/), then [the runbook](implementation/RUNBOOK.md) and [implementation progress](implementation/PROGRESS.md). The [full context index](context/README.md) holds the detailed design and research.
