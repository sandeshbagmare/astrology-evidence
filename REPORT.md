# Readiness report

Updated November 16, 2026. This report describes the implementation and its tested limits.

## Verdict

**A local application is implemented. It is not cleared for real-user production.** The latest user-directed refresh removes sign-in and uses separate anonymous browser workspaces, with a calmer six-section UI. Birth profiles, deterministic charts, rights-controlled Qdrant sources, bounded readings and privacy jobs remain. Authentication is future scope; external content, provider, accuracy and operating gates remain open. Refresh verification is recorded in implementation progress when complete.

## Implemented

- Python 3.12 application, FastAPI/PostgreSQL migrations, automatic isolated browser workspaces, retained optional future OIDC code.
- Owner-scoped profiles/revisions, timezone fold/gap handling, isolated chart calculation and accessible chart fact views.
- Curated edition import, explicit rights permissions, immutable index generations, Qdrant dense/lexical retrieval, source withdrawal cleanup.
- Bounded LangGraph/Responses workflow, model-processing consent, citation hash/span validation, abstention when evidence is missing.
- Durable jobs for privacy/export, worker lease fencing, deletion tombstones and rights-aware exports.
- Server-rendered browser UI, curator workflow, bounded extraction/OCR adapter and offline retrieval evaluation tool.
- Docker/Compose packaging and CI tests with PostgreSQL 16 and Qdrant 1.20 services.

## Verification

The final local audit code through `fb8ae33` passed **284 Python tests**, with **2 external-service skips** because Docker is unavailable locally, and **35 native chart tests** under Python 3.12. Ruff and mypy pass. All 7 Node tests pass, including delayed-response DST regressions. Browser testing covered synthetic login, offset-labelled repeated-time selection with and without JavaScript, profile save, native chart, insufficient-evidence reading, confirmed deletion and library search at 320px without overflow. All workflows passed on `cf36edd`, including [service-backed Python tests and the new wheel/asset build checks](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43793711956), documentation/UI JavaScript checks and Pages deployment.

The app runs locally at `http://127.0.0.1:18766` in the current development session. Use [the runbook](implementation/RUNBOOK.md) to start it independently. The GitHub Pages site is a reading guide, not the Python backend.

## Release gates

| Area | Current status |
|---|---|
| Source corpus | No real books ingested; edition-specific rights required |
| Domain rules | No expert-reviewed production rules or 150-question labeled evaluation set |
| Chart accuracy | Unit/edge-case tests pass; independent reference parity remains unmeasured |
| Provider | Offline Responses wire tests pass; no real provider request or provider data review |
| Browser access | Sign-in removed; per-browser session/CSRF isolation under refresh verification. Authentication/cross-device recovery are future scope |
| Embeddings | Local adapter implemented; model weights, memory and retrieval quality not benchmarked |
| Security/privacy | Offline adversarial tests pass; live backup/restore and deployment operations not exercised |
| Hosting | Compose provided; Docker image was not built on this machine, and no public Python app host is configured |
| Scientific claims | Astrology's predictive validity is not established by calculations or citation fidelity |

AI and embeddings remain disabled by default. The local demo uses invented inputs. Do not enable real-user operation until the source-rights, licensing, provider, identity, expert-evaluation, hosting and recovery gates are resolved.

## Start here

Read [the Pages guide](https://sandeshbagmare.github.io/astrology-evidence/), then [the runbook](implementation/RUNBOOK.md) and [implementation progress](implementation/PROGRESS.md). The [44-document context-to-code review](implementation/CONTEXT-CODE-REVIEW.md) shows implementation coverage and gaps; the [full context index](context/README.md) holds the detailed design and research.
