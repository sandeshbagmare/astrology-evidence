# Implementation handoff: GPT-6.1 Sol

**Updated:** November 16, 2026  
**Repository:** `sandeshbagmare/astrology-evidence`  
**Integrated branch:** `main`  
**Development branch:** `implementation/mvp`  
**Reviewed application baseline:** `91812d1` (sign-in-free UI and subsequent reviewed security fixes); see the end-to-end report for later demo/publication verification.

This article records the implementation and subsequent reviews completed with GPT-6.1 Sol. It is intended for the owner and a later coding model. The current app is a tested sign-in-free local engineering baseline. Authentication is future scope, and live Google configuration is not required now. It is not fully production-ready: licensed sources, provider review, expert/domain validation, inactive-workspace retention/purge, a real operating host and recovery drills remain gates.

## Executive account

The latest user-directed change removes sign-in and replaces it with isolated anonymous browser workspaces, while preserving ownership/CSRF/privacy boundaries. The calm light UI now has Overview, Birth profiles, Chart explorer, Readings, Source library and Data & settings. The original Google/OIDC implementation described below is retained behind a disabled future mode. Current scope is governed by [the guest/UI plan](../context/46-anonymous-workspace-and-ui-plan.md).

The approved design was translated into a Python application with a FastAPI modular monolith, server-rendered Jinja UI with a small fetch enhancement and application CSS, SQLAlchemy/Alembic persistence, PostgreSQL deployment configuration, Qdrant hybrid retrieval, a Swiss Ephemeris-compatible calculation boundary, Google OIDC integration and a bounded LangGraph workflow using LangChain's Responses API adapter. The original HTMX/Tailwind proposal was superseded by this simpler implemented UI in ADR-02.

The current local demo uses synthetic data, separate anonymous browser workspaces and Moshier engine mode. AI and embeddings default off. The reading workflow returns an honest insufficient-evidence result if there is no published rights-approved corpus or no reviewed material for the question. When generation is configured, the current implementation limits output to whole retrieved passages with exact source references; it does not infer chart applicability from an unreviewed rule.

No credential from chat was copied into the repository. No authenticated model request was made. No real books were acquired, OCRed, indexed or published. These are deliberate evidence boundaries, not omitted test results.

## Work completed

### Sign-in-free refresh and independent validation

The owner asked for competitor research and a stronger UI/functionality pass, then explicitly asked to review the agents' work and test broadly. Eight official public sites were compared in [45 UI research](../context/45-ui-refresh-research.md), with exact URLs and access limits; no paid/private app was represented as inspected and no proprietary artwork/text was copied. The resulting design uses warm light surfaces, teal/ink, a restrained celestial motif built in CSS, readable grouped screens, responsive navigation and actionable empty states. The original Python/Jinja/fetch stack remains; no new frontend framework was installed.

Research commit `65dd33a` changed current scope and context. Guest implementation `f2fe708` creates distinct random workspace owners/sessions automatically, blocks old authentication endpoints, preserves server ownership and CSRF, and keeps old account cookies from being promoted into guest access. Shared database limits admit 60 new workspaces per 60-second window and 100 accepted reading requests per UTC day by default. Restart, deleted readings and cleared cookies do not refund the global reading budget; at most two model attempts per accepted reading still apply. PostgreSQL and SQLite race regressions accompany these controls without a schema migration.

Workbench commit `ca3556f` adds six sections, profile/chart indexes, grouped time/location/consent/method controls, chart/provenance panels, readable source and reading screens, clearer data controls, loading and duplicate-submit protection. A chart's reading link now binds its exact historical revision/snapshot; a profile without a current chart receives a calculation step before question submission. Ordinary forms and explicit DST-offset confirmation still work without JavaScript. Access limits—24 hours idle, seven days maximum, possible cookie loss and no recovery—are disclosed near storage and data controls.

Independent reviewers found and verified corrections beyond the implementers' own tests: operation/error/export pages lacked shared render context; source/reading actions needed exact chart context; informational text contrast needed correction; short-height navigation clipped links; and a no-chart reading action led to an opaque failure. The guest security reviewer reproduced unbounded Session creation during CSRF repair, absolute-expiry extension, and stuck stale cookies after revocation/expiry/deletion. Session repair now updates in place with conditional fencing, keeps the original expiry, caps cookie lifetime at remaining expiry, and treats the session ID portion only as a concurrency hint—full secret-token hash remains required for authorization. All findings were cleared in scoped re-review.

Final local evidence: **342 non-native Python tests passed, 5 service-dependent tests skipped**, **35 native calculation tests passed**, Ruff passed, mypy passed on **31 modules**, **8 Node tests passed**, and **90-file documentation validation passed**. The security reviewer independently passed **15 adversarial tests**, including cross-workspace reads/mutations/exports, swapped CSRF, invalid sessions, secure cookies and all three reproduced recovery defects. Coordinator Edge checks covered **24 screen/width combinations**, guest isolation and chart/readings, JavaScript-disabled DST entry/export/deletion, plus a completed worker export with 200/no-store owner access and 404 from another browser. Keyboard focus reaches lower sidebar links at 720×450. This remains a focused browser test, not a formal accessibility certification.

Publication `d9c1846` passed [Python CI 43817226635](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43817226635) with **382 tests passed, none skipped**, in 23.09s, plus Ruff/mypy, wheel build and packaged-asset checks. This run used real PostgreSQL/Qdrant and exercised the issuance/reading/repair race variants unavailable locally. [Docs/UI JavaScript checks](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43817226568) and [Pages deployment](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43817224650) also passed. The public screenshot and UI-research link load successfully, and the guide fits 1440/768/320px. The local app's home/readiness returned 200 after its final-code restart. These are engineering/build checks; inactive guest retention/purge, licensed sources, independent chart/domain evaluation and production operations remain unverified gates.

The research, implementation and two fresh validation assignments ran in waves, at most three workers plus the coordinator. A temporary service 503 interrupted worker turns; the coordinator inspected partial files, resumed workers and verified the combined result. Git commit counts are reproducible; model-call/token totals were not logged and are not invented. Current release evidence is in [implementation progress](PROGRESS.md). Earlier counts and account-specific descriptions below are historical snapshots.

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
- Added chart facts and an accessible table/house overview. Independent ephemeris parity is not asserted: the current suite runs 35 unit/edge tests, not an independently reviewed chart benchmark. The near-station tolerance is still awaiting a domain decision.

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

There are **18 commits** after the published planning baseline `dc7ae71` through audited application commit `fb8ae33`: 11 in the initial implementation phase and 7 later handoff/audit/fix commits. Ten commit subjects in that range contain `GPT-6.1 Sol`, beginning at the user's attribution instruction. Later documentation/CI publication commits are excluded from this dated count. Reproduce the live count with `git rev-list --count dc7ae71..HEAD`; do not treat this as a model-token or model-call count, which was not recorded.

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
13. `5c6b530` — reconcile handoff and startup instructions.
14. `9771456` — reconcile all context status records and add the context-to-code map.
15. `7c06c69` — bound curator edition JSON bodies before parsing.
16. `e865f3d` — validate meaningful fold choices and close the ordinary-form import bypass.
17. `ddad60c` — implement source search/detail, delete confirmation and complete offset-review UI, including stale-response and no-JavaScript fixes.
18. `fb8ae33` — cap all raw mutation bodies at 1 MiB with 25 MiB curator import/form allowance.

This is a commit count, not a model-token count or generated-lines attribution. Parallel workers owned separate modules and the coordinator integrated/tested the combined tree. The environment allows at most four agents total, so implementation ran in waves rather than 50 simultaneously.

## Verification record

On the Windows host, the final audit code passed **284 non-native Python tests**, with **2 tests skipped** because local Docker/PostgreSQL/Qdrant services were unavailable. The native calculation suite ran separately using the existing approved Python 3.12 interpreter and passed **35 tests**. Ruff passed across `src` and `tests`; mypy passed across **30 source modules**. The Markdown checker passed on **86 files**; its 3 unit tests and 4 UI JavaScript regressions also pass. Separate runtimes are a laptop policy constraint; all calculation tests were still executed.

GitHub Actions passed on `bc3e5a0`, `11610bf` and `5c6b530`. The audit publication commit `cf36edd` then passed [Python run 43793711956](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43793711956): pytest with PostgreSQL 16/Qdrant 1.20, Ruff, mypy, the new distributable-wheel build and packaged-web-asset validation. [Documentation/UI JavaScript checks](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43793711969) and [Pages deployment](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43793711138) also passed. The public guide returned 200 with the audit link and corrected stack. Docker image/Compose execution is a separate unverified gate; a wheel build does not prove a container starts.

Known warnings include Authlib's deprecated legacy JOSE API and a LangSmith asyncio deprecation. They are non-failing warnings, but should be reviewed during dependency upgrades. CI uses no production secrets and no provider call.

## November 16 review and development work

The user reported that the app was inaccessible and asked for a full context/code audit with parallel reviews. Independent specialists checked identity/privacy, calculations/corpus, UI/accessibility, deployment/operations and security/tests. A fresh reviewer inspected the resulting code rather than relying on implementer self-review. The environment permits four active agents including the coordinator, so the work ran in waves of at most three workers. No claim is made that 50 agents ran at once.

The app was confirmed listening on loopback port 18766. One probe used the unsupported `/health` path and returned 404; the actual `/health/live` and `/health/ready` both returned 200, as did `/` and `/login`. The process was restarted with the final code, synthetic local login, disabled AI/embeddings and a narrow native-calculation interpreter configuration. This is a temporary developer process, not a public persistent service. The public Pages guide is a separate static site.

The review found and corrected several gaps:

- **Context drift:** numerous design files still said no app/tests existed or implementation was unauthorized. Updated the status language without marking unexecuted domain/release targets complete. Added [a map of all 44 numbered documents](CONTEXT-CODE-REVIEW.md). Pinned Python 3.12 in setup guidance and recorded the delivered Jinja/fetch/CSS UI in ADR-02.
- **Repeated-time input:** added offset-labelled alternatives using the calculation service's pinned timezone candidates. JavaScript clears a prior choice on changed input; both the JavaScript and ordinary-form paths require an explicit choice. No-JavaScript forms preserve draft values and bind confirmation to the reviewed time fields/session. A delayed old JSON response was reproduced restoring an obsolete fold; a post-parse sequence check now prevents that race. Fresh review cleared both findings.
- **Source usability:** added independent library search using display-authorized retrieval, contextual permitted-source pages, and owner-checked links/back navigation from saved readings. The source service still rechecks current rights, corpus generation and text hashes. Search shows a clear unavailable state while embeddings are disabled.
- **Deletion guard:** deleting a saved reading now requires typing DELETE, with enforcement server-side as well as in the form.
- **Resource bounds:** added declared/streamed raw-body accounting before framework parsing. Mutations default to 1 MiB; curator JSON and ordinary import/form paths allow 25 MiB. Tests cover understated/missing Content-Length, all mutation methods, the exact boundary, UTF-8 chunk replay, and unaffected GET/HEAD behavior. The fresh reviewer found no new high/medium issue in this follow-up.
- **Native semantics:** explicit fold values are rejected when a local time has no repeated occurrence, while both valid repeated-time choices work. An initial suspicion that ordinary unambiguous fold=1 shifted UTC was not reproduced; this is a meaningful-input policy, not a claimed fix for an observed hour shift.

Final local commands were `./scripts/dev.ps1 -m pytest --ignore=tests/test_calculations.py`, the native calculation pytest command under the existing approved Python 3.12 interpreter, `./scripts/dev.ps1 -m ruff check src tests`, `./scripts/dev.ps1 -m mypy src`, `node --test scripts/check-docs.test.mjs tests/ui_app_js.test.mjs`, and `node scripts/check-docs.mjs`. The non-native result was 284 passed/2 skipped in 31.16s; the native result was 35 passed. A real Edge browser completed synthetic profile/DST/chart/abstention/deletion/library flows and a separate JavaScript-disabled repeated-time profile flow at 320px without horizontal overflow or JavaScript page errors. A test locator initially timed out on the profile selector; selecting it by its accessible combobox role resolved that harness issue.

This review did not turn the missing licensed corpus, expert rule registry, independent ephemeris references, expert evaluation set, live provider/Google configuration or production operating evidence into completed work. Those remain concrete gates below. Full display preferences and the broader optional place-search design are also not implemented; the current app uses manual coordinates/timezone entry.

## Release gates that remain open

- Acquire and record action-specific rights for 3–5 real editions before indexing or showing text. The synthetic corpus is not a source of astrology knowledge.
- Have qualified reviewers create the reviewed rule registry and label the 150-item benchmark (20 calibration, 30 development, 100 held out). No measured retrieval/claim-quality result is reported.
- Select and document a Swiss Ephemeris-compatible distribution/license path. The local Moshier setting does not resolve the production licensing choice.
- Authentication is future scope. If account mode is restored, configure Google client credentials/callback URLs and run live OAuth tests before enabling it.
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
- To deploy: use the runbook, configure the domain and secret store, resolve the applicable release gates, test restore and deletion, build the container, and wait for green CI on the exact release commit. Keep authentication disabled for current scope; Google redirects apply only if account mode is restored.

Changes should remain small, tested and committed in phases. Current branch history includes the initial implementation commits; use new commits for later work rather than rewriting published history.

## Recorded end-to-end demos and publication verification

The subsequent GPT-6.1 Sol pass repeated the full local application suite (342 passed, five service-dependent skips), all 35 native calculation tests, Ruff and mypy. An additional focused web/health regression run passed 38 tests after adding the application favicon. Two successful recorded Edge journeys use only invented inputs: desktop with repeated-time offset selection, and mobile with JavaScript disabled and unknown birth time. Both calculate a chart, keep the question bound to that snapshot, show insufficient evidence, complete a private expiring export and explicitly revoke workspace access.

Three downloadable videos, English captions, screenshots and written steps are attached to the public guide. The browser scripts are in `tests/browser/`; the guide verifier checks assets including posters, fragment targets, repository links, five viewport widths, keyboard navigation/disclosure, complete video playback and caption bounds. Independent reviewers found the portrait-player sizing and incomplete media checks, which were corrected before publication. The [end-to-end report](E2E-AND-DEMO-REPORT.md) records final deployment evidence and limits. This work does not turn disabled AI, missing licensed sources or untested production operations into completed release gates. Model call/token totals remain unknown; no count is inferred from the number of agents, tests or commits.

At demo publication `992f094`, the reachable `main` history contains **19 commit subjects tagged `[GPT-6.1 Sol]`**. This is a dated Git attribution count, reproduced by counting matching subjects in `git log 992f094 --format=%s`; it is not a count of model requests or tokens. This demo pass added `e2da911` (application favicon) and `992f094` (recordings, browser checks, public guide and evidence). [Python CI](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43832094881) passed 382 tests with no skips, plus lint/types and build/assets. The final public-browser results and verifier follow-ups are recorded in the end-to-end report.

## Subsequent quality pass: reproduced regressions

The next user-directed test/review pass used three specialist reviewers alongside the coordinator. It reproduced four defects despite the previously green suite: premature concurrency-slot release after cancellation/consent revocation/privacy purge; stale chart-cache reuse after runtime/data updates; boolean/numeric substitutions accepted in computed evidence; and unconfirmed profile deletion cascading to charts/readings. Each received regression coverage and a targeted fix in commits `6f96a3e`, `b63458e` and `a67b180`, carrying the user-requested `[GPT-6.1 Sol]` attribution label. The label records the requested workflow attribution; it is not provider telemetry or proof of the identity behind any routed call.

The integrated local suite passed 368 tests with six external-service skips and 35 native calculation tests. Ruff/mypy passed. Nine Node tests include the new browser-cleanup failure-preservation regression. Independent review checked cache compatibility, strict nested JSON equality and cancellation permit lifetime. No schema migration, model call or real-book ingestion was needed.

The local Edge renderer produced zero animation frames and blocked ordinary click stability checks; two independent sessions reproduced this. The browser harness now preserves the original failure even if cleanup fails, and the application flow is added to Linux CI so future commits exercise real forms, isolated owners, charts, abstention and deletion. CI results and remaining scope are recorded in [implementation progress](PROGRESS.md). Lease expiry is bounded crash recovery, not a guarantee that an uncooperative provider physically stops processing. Model-call/token totals remain unmeasured.

The first Linux browser rollout exposed environment and layout differences that the earlier Windows run did not catch. `fa23014` passed all 409 Python tests but Playwright 1.58.2 could not install on the moving Ubuntu 26.04 runner. `00688aa` pins Ubuntu 24.04; its browser then reported a real new-profile overflow (798px document width at a 768px viewport). The assertion was retained; `1994158` constrains grid tracks and native controls without hiding overflow. A local intrinsic-size stress reproduction shrank the overflowing 888px document back to its 768px viewport. These failed browser runs are not counted as passes; final evidence follows in the progress ledger.

Final quality-pass application revision `1994158` passed [all 409 Python tests and the full Linux Chromium journey](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43888917993), including 24 layouts, zero JavaScript page errors, workspace isolation, profile-deletion confirmation and completed private export. Nine Node checks, documentation and Pages deployment passed. The pass added six implementation/verification commits through this revision: `6f96a3e`, `b63458e`, `a67b180`, `fa23014`, `00688aa` and `1994158`. The follow-up documentation commit records these results; no model-call/token count is inferred. The user-requested commit attribution is preserved.

### No-JavaScript browser verification follow-up

The documentation-only revision `153bd19` repeated all 409 passing Python tests but encountered an intermittent Chromium mouse stability timeout at the first no-JavaScript consent checkbox; cleanup also stalled. This failed browser run is retained as evidence, not replaced by the earlier passing run. Playwright's mouse stability check waits on animation frames, consistent with the separately observed local frame stalls. `3052717` makes the no-JavaScript journey explicitly keyboard-driven: native Space toggles consent (checked afterward) and Enter submits visible, enabled forms. Desktop mouse checks remain. This tests native keyboard use and server outcomes; it does not claim the no-JavaScript mouse stall is resolved. Final keyboard browser CI passed in [43897908870](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43897908870): 409 Python tests with no skips and the complete Chromium journey. It reported `noJsKeyboard: true`, 24 layouts, chart facts, isolation denials, profile/reading/workspace deletion, owner-only export and zero page errors.
