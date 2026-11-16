# Implementation handoff: GPT-6.1 Sol

**Updated:** November 16, 2026  
**Repository:** `sandeshbagmare/astrology-evidence`  
**Integrated branch:** `main`  
**Development branch:** `implementation/mvp`  
**Current integrated commit:** `11610bf15f83868e6243f83abe944a4f003fe0b0`

This article records the implementation phase completed with GPT-6.1 Sol. It is intended for the owner and for a later coding model that may continue the work. The app is a tested local engineering baseline. It is not represented as fully production-ready: the source corpus, provider review, live identity configuration, expert evaluation, real operating host and recovery drills are still external gates.

## Executive account

The approved design was translated into a Python application with a FastAPI modular monolith, server-rendered Jinja/HTMX UI, SQLAlchemy/Alembic persistence, PostgreSQL deployment configuration, Qdrant hybrid retrieval, a Swiss Ephemeris-compatible calculation boundary, Google OIDC integration and a bounded LangGraph workflow using LangChain's Responses API adapter.

The local demo uses synthetic data, explicit local login and Moshier engine mode. AI and embeddings default off. The reading workflow returns an honest insufficient-evidence result if there is no published rights-approved corpus or no reviewed material for the question. When generation is configured, the current implementation limits output to whole retrieved passages with exact source references; it does not infer chart applicability from an unreviewed rule.

No credential from chat was copied into the repository. No authenticated model request was made. No real books were acquired, OCRed, indexed or published. These are deliberate evidence boundaries, not omitted test results.

## Work completed

### Runtime and persistence

- Added a Python 3.12 baseline, uv lockfile, typed settings, safe local defaults and explicit production configuration gates.
- Added FastAPI startup/composition, health/readiness routes, response security headers and migrations.
- Added SQLAlchemy records for users, browser sessions, OAuth transactions, birth profiles/revisions, immutable charts, rights-cleared works/editions/passages, corpus generations, readings/requests, quotas, jobs, exports, tombstones, audit and publication/outbox operations.
- Added transaction ownership constraints, idempotency keys, leased job generations and migration-versus-metadata parity tests.
- Added Dockerfile and Compose services for PostgreSQL, Qdrant, migrations, web and privacy worker. Docker was unavailable on this Windows host, so image build/start was not claimed as locally verified.

### Login and profiles

- Implemented server-side Google OIDC authorization flow with one-use state, nonce, PKCE transaction state, issuer/subject identity, opaque hashed sessions, CSRF and origin checks.
- Implemented an opt-in local synthetic account for development only. Production configuration rejects this path.
- Implemented owner-scoped profile create/list/read/update, append-only revisions, explicit storage consent, chart snapshots and cross-user non-disclosing 404 behavior.
- The browser can enter a birth date, local time certainty, coordinates and named timezone manually. It does not send background geolocation or use an unreviewed public geocoder.

### Chart calculations

- Implemented exact, approximate and unknown time handling, timezone gaps/folds and conservative unavailable facts.
- Implemented settings/version manifests for Jyotish, sidereal Lahiri, whole-sign houses, mean node and explicit Moshier/Swiss engine selection.
- Isolated native engine work in a subprocess option with a narrow JSON protocol, timeout, explicit interpreter path and environment allowlist. This was needed because Windows Application Control blocked some uv-created/native runtime files.
- Added chart facts and an accessible table/house overview. Independent ephemeris parity is not asserted: this phase ran 33 unit/edge tests, not an independently reviewed chart benchmark.

### Corpus and retrieval

- Added edition import contracts with separate, explicit storage/index/model-transmission/display permissions and reviewer/rights metadata.
- Added passage attribution layers, page and verse locators, source hashes, excerpt caps, corpus generations and a publication state.
- Added Qdrant dense and lexical vectors, exact metadata filters, local CPU E5 adapter with pinned revision requirement, parent-context retrieval and authoritative database rights rechecks.
- Added source withdrawal denial plus an outbox worker that redacts stored passage text/readings and deletes points from recorded Qdrant generations; failures retain the purge obligation for retry.
- Added synthetic fixtures, bounded text/PDF extraction and an evaluation CLI for recorded ranked results. A Tesseract adapter is bounded, but an OS-level isolated OCR/PDF worker and real book sample were not tested or deployed.

### Grounded reading and privacy

- Added a bounded LangGraph workflow and LangChain/OpenAI-compatible Responses adapter pinned to tested dependencies.
- Added offline wire tests for the exact Responses path, no hidden retries, response/refusal/timeout handling, privacy options and credential redaction. There was no call to FreeGG or any other live provider.
- Added database-serialized admission quotas, idempotency, a 150-second request deadline, at most two model attempts, cancellation and execution-token fencing, explicit model consent and current-rights checks before publication and every saved reading read.
- The validator verifies source IDs, hashes, exact code-point spans, grapheme boundaries and chart fact IDs. Until human-reviewed excerpt rules exist, it only permits full evidence passages with applicability marked not established. This deliberately sacrifices answer breadth to prevent a quote from dropping a negation or exception.
- Added privacy jobs, account/profile deletion denial and purge, tombstones for restore, expiring exports that omit source excerpts, and rights withdrawal recovery.

### Browser application

- Added accessible server-rendered pages for landing, local/Google login, dashboard, birth profile create/edit, chart, new/list/detail reading, library, settings and curator screens.
- Added ordinary form submission adapters as well as fetch enhancement; writes retain origin/CSRF validation. Synchronous work is sent through Starlette's thread pool rather than blocking the event loop.
- Added no-store, request IDs, basic security headers and a restrictive static-content policy. Jinja autoescaping is retained; browser-rendered source text is not inserted as unsafe HTML.
- Exercised synthetic login, profile save, chart generation and an insufficient-evidence reading in a local browser. The exercised flow had no horizontal overflow at 320px. A full NVDA/VoiceOver and formal WCAG audit remains outstanding.

## Commits and GPT-6.1 Sol attribution

There are **11 implementation-phase commits** between the published planning baseline `dc7ae71` and integrated app/documentation commit `bc3e5a0`, followed by this handoff-article commit `11610bf`. Four commits since the attribution instruction include `[GPT-6.1 Sol]` in their commit messages: `f85820b`, `a366b6e`, `bc3e5a0`, and `11610bf`.

The implementation commits were:

1. `73bb275` — typed app foundation, config, migrations and transactional persistence.
2. `59803a9` — bounded Responses provider and offline wire tests.
3. `9996653` — versioned chart calculations and birth-time uncertainty.
4. `80b054c` — initial identity, profile, corpus, retrieval and job components.
5. `eae7479` — reading fences, strict evidence validation and source withdrawal cleanup.
6. `f7fde22` — server-rendered app routes and local UI.
7. `dc14a98` — bounded extraction and reproducible evaluation tools.
8. `b191526` — CI, Docker/Compose and real PostgreSQL/Qdrant integration tests.
9. `f85820b` — final integration/readiness rules with GPT-6.1 Sol attribution.
10. `a366b6e` — record passing integrated CI with GPT-6.1 Sol attribution.
11. `bc3e5a0` — update README, readiness report and GitHub Pages site for the implemented app.
12. `11610bf` — write this detailed GPT-6.1 Sol implementation handoff and link it from the guide.

This is a commit count, not a model-token count or generated-lines attribution. Parallel workers owned separate modules and the coordinator integrated/tested the combined tree. The environment allows at most four agents total, so implementation ran in waves rather than 50 simultaneously.

## Verification record

On the Windows host, the final local application suite passed **250 tests**, with **2 tests skipped** because local Docker/PostgreSQL/Qdrant services were unavailable. The native calculation suite ran separately using the available Python 3.12 runtime and passed **33 tests**. Ruff passed across `src` and `tests`; mypy passed across **30 source modules**; the Markdown checker passed on **83 files**. Its 3 checker unit tests also pass.

GitHub Actions passed on `bc3e5a0` and on the final article commit `11610bf`; both ran pytest with PostgreSQL 16 and Qdrant 1.20, Ruff and mypy. GitHub Pages returned HTTP 200 after deployment and the published page described the local application and links to this article.

Known warnings include Authlib's deprecated legacy JOSE API and a LangSmith asyncio deprecation. They are non-failing warnings, but should be reviewed during dependency upgrades. CI uses no production secrets and no provider call.

## Release gates that remain open

- Acquire and record action-specific rights for 3–5 real editions before indexing or showing text. The synthetic corpus is not a source of astrology knowledge.
- Have qualified reviewers create the reviewed rule registry and label the 150-item benchmark (20 calibration, 30 development, 100 held out). No measured retrieval/claim-quality result is reported.
- Select and document a Swiss Ephemeris-compatible distribution/license path. The local Moshier setting does not resolve the production licensing choice.
- Configure Google client credentials and callback URLs on the actual domain, then run live OAuth tests.
- Review the external provider's model identity, terms, processing/retention, quotas and pricing. Supply a replacement secret through runtime secret management. Enable AI only after this review and pass the live synthetic smoke test.
- Install/cache the exact E5 revision, benchmark Sanskrit/transliteration retrieval and host memory, then run the held-out corpus benchmark.
- Configure and test backups, restore, deletion replay, Qdrant rebuild, worker availability, alerting and the real-user privacy executor.
- Build and run the Docker image/Compose stack on an approved Docker host. This Windows laptop had no Docker installation.
- Perform keyboard, screen-reader, browser matrix and security review before real-user beta.

The app rejects production settings unless key configuration, secure cookies, HTTPS, the privacy executor and engine-license gate are declared. Those flags cannot manufacture legal approval or proof of operations; an operator must supply evidence before enabling the deployment.

## Safe continuation points for a future model

The latest integrated application is on `main`; feature work can branch from there. Before changing the product, read `AGENTS.md`, this article, `implementation/RUNBOOK.md`, `implementation/PROGRESS.md` and the relevant specialist documents in `context/`.

- To add reviewed astrology rules: first acquire licensed editions, update attribution/provenance at passage level, add human-approved predicates with three-valued applicability and exceptions, then add frozen tests. Never convert generated commentary into an approved rule.
- To broaden answers: establish excerpt segmentation rules that preserve each passage's qualifiers, expand validator tests, then re-run source-support and abstention evaluation. Do not simply allow arbitrary model paraphrases.
- To enable real AI: configure only a replacement secret at runtime, review provider terms, run the existing fake-server tests and approved synthetic live smoke, document result, then obtain explicit consent in product before sending user content.
- To enable embeddings: pin model weights/revision locally, benchmark against the held-out Sanskrit/English set, test cold-load RAM and latency, and create a new Qdrant generation. Keep AI generation consent separate from vector embedding permission.
- To add a new tradition or birth-timing module: create separate versioned chart/rule settings and reference fixtures. Do not silently mix Western, Jaimini, KP, dashas or transit rules into existing Jyotish outputs.
- To deploy: use the runbook, configure the domain/Google redirect and secret store, resolve every tabled release gate, test restore and deletion, build the container, and wait for green CI on the exact release commit.

Changes should remain small, tested and committed in phases. Current branch history includes the initial implementation commits; use new commits for later work rather than rewriting published history.
