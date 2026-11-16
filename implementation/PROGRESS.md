# Application implementation progress

## Latest: recorded end-to-end verification — November 16, 2026

Recorded desktop and mobile (JavaScript disabled) journeys pass through profiles, chart calculation, chart-bound abstention, source limitations, completed private export and confirmed workspace deletion. The public guide now includes three captioned downloadable demos, screenshots and written steps. Fresh local checks passed 342 application tests with five service-dependent skips, 35 native calculation tests, Ruff and mypy; the favicon follow-up passed 38 web/health tests. Independent reviewers checked the documentation and browser scripts; eight Node tests and 91-file documentation validation passed. See [the end-to-end/demo report](E2E-AND-DEMO-REPORT.md) for exact final publication, playback and CI evidence and remaining gates. Previous results below are historical, not additional unique tests.

## Sign-in-free workbench — November 16, 2026

The user deferred authentication and requested public-site research, UI/function improvements, parallel review and rigorous testing. The current app opens directly into a separate browser workspace. Opaque session ownership, CSRF, consent, exports, deletion and curator authorization remain enforced; no global shared guest account is used. Google/OIDC is retained disabled as future scope. The work is recorded in [45 UI research](../context/45-ui-refresh-research.md) and [46 Guest/UI plan](../context/46-anonymous-workspace-and-ui-plan.md).

- `65dd33a`: research/scope update, eight official-site comparisons and revised authentication requirements.
- `f2fe708`: isolated automatic guest access, disabled auth routes, bounded session recovery and shared issuance/reading quotas.
- `ca3556f`: six-section workbench, responsive styling, grouped forms, profile/chart lists, exact chart-to-reading binding, loading guards, chart prerequisites and zoom-reachable navigation.

Fresh final local verification on that code: **342 Python tests passed, 5 skipped**, **35 native calculation tests passed**, Ruff clean, mypy clean across **31 source modules**, **8 Node tests passed**, and documentation validation passed on **90 files**. Skips are local PostgreSQL/Qdrant delivery and quota/repair concurrency variants; CI supplies those services. No live provider call or credential was used. Existing Authlib/LangSmith deprecation warnings remain non-failing.

Coordinator browser checks exercised eight screens at 1440px, 768px and 320px (**24 layout checks**), plus direct guest entry, DST offset selection, profile save, native chart (65 facts for the synthetic case), snapshot-bound abstention, confirmed reading deletion, a separate browser's 404 ownership denials/403 curator denial, JavaScript-disabled form entry, export queue and workspace deletion. No horizontal page overflow or JavaScript page errors occurred in the exercised flow. A running privacy worker also completed an export: owner download 200/no-store, another browser 404. At 720×450, focusing the final sidebar link scrolls it fully into view. This is focused browser/accessibility evidence, not a full screen-reader/WCAG certification.

Independent research review found missing render context on operation/error/export pages, stale account wording, low-contrast small text and a chart-link mismatch. Independent UI review found short-height navigation clipping and an unusable reading path before chart calculation. Independent security review reproduced session-row growth, renewed absolute expiry and stale historical-cookie recovery. All were fixed and cleared; the security reviewer independently passed **15 adversarial checks**. Implementers and reviewers worked in waves within the four-active-agent limit.

Current defaults bound new workspace issuance to 60 per shared 60-second window and accepted readings to 100 per UTC day in the database. Idempotent replay is free; failure/deletion/restart cannot refund global allowance, and each reading remains capped at two generation attempts. Session repair rotates in place, preserves original expiry and cookie lifetime, and fences concurrent repair. Access ends after 24 hours idle or seven days maximum, possibly sooner if cookies are cleared; this does not erase stored records. Export/deletion and loss-of-access limits are disclosed in the UI. Automated inactive-workspace purge, production ingress/load measurements and recovery proof remain launch work.

Publication `d9c18463cdb6b66eb1d982eee4facdaad974e591` passed [Python CI run 43817226635](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43817226635): **382 passed**, with no skipped tests, in 23.09s. This includes native calculations, real PostgreSQL/Qdrant delivery and PostgreSQL issuance/reading/repair concurrency variants. Ruff, mypy, the distributable wheel and required packaged assets also passed. [Documentation/UI JavaScript run 43817226568](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43817226568) and [Pages deployment 43817224650](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43817224650) passed. The public page returned 200, its preview image loaded, and layouts at 1440/768/320px showed no horizontal overflow. This follow-up only records evidence.

The local app is a developer process at `http://127.0.0.1:18766`; the public Pages guide is separate and now includes an empty-workspace screenshot. Home and readiness were verified 200 after restarting the final code. Historical results below describe earlier revisions and do not supersede this section. Docker image/Compose execution, inactive-workspace purge policy, production capacity/recovery, licensed books and independent expert/domain evaluation remain explicit launch gates; this engineering pass does not establish full production readiness.

Implementation began after explicit user approval on November 15, 2026. The integrated source is on `main`, developed on `implementation/mvp`, with small feature and fix commits and independent agent reviews. The November 16 context review and application fixes are integrated through `fb8ae33`; accompanying CI/documentation publication follows in its own commit.

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

Local integrated Python 3.14 checks on the final audit code: **284 passed, 2 skipped** (`./scripts/dev.ps1 -m pytest --ignore=tests/test_calculations.py`, 31.16s). PostgreSQL/Qdrant delivery tests skip locally because Docker services are unavailable. The native chart suite passed **35 tests** under the existing approved Python 3.12 interpreter. Ruff passes; mypy reports no issues in 30 source files. The documentation checker passes on 86 files, its 3 unit tests pass, and all 4 UI JavaScript regressions pass. The chart and other application suites are separated only for this laptop's supported runtime arrangement, not omitted from verification.

Browser: the restarted final code on `127.0.0.1:18766` completed synthetic login, offset-labelled DST selection, consented profile creation, native chart calculation through an isolated process, an insufficient-evidence reading, confirmed reading deletion and the unconfigured-library-search state. A separate JavaScript-disabled browser context saved an ambiguous-time profile after reviewing both UTC offsets. The exercised 320px flow has no horizontal overflow or JavaScript page errors. This is not full screen-reader/WCAG certification. Port 18766 is a developer process on this workstation, not a permanent public application host.

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
- No live Google account authorization or third-party generation call; supplied chat credential is not reused or saved. A replacement runtime secret and provider review are needed for live AI; Google configuration applies only to future account mode.
- No empirically validated predictive claims. Current AI answers are constrained extracts, not full expert astrological synthesis.
- E5 model weights, actual Sanskrit retrieval quality and host memory/latency still require measured validation.
- No funded production host, backup/restore drill, full accessibility audit or public real-user deployment.
- Docker image/Compose execution cannot run on this laptop; service behavior is exercised by CI, but image execution is a distinct check.

The application is a functioning engineering baseline for local synthetic use, not a claim that the entire production/knowledge acquisition program is complete. External gates are enforced or documented rather than fabricated.

## Context and code review findings — November 16, 2026

Focused independent reviews of identity/privacy, calculations/corpus, deployment, UI, operations and test/security found no confirmed OIDC ownership or source-withdrawal defect. Resolved stale planning-only status text, Python setup/version drift, missing DST-fold UI, source-library search/navigation, reading-delete confirmation and unbounded raw request bodies. Mutation bodies now default to 1 MiB; curator JSON/form imports allow 25 MiB, with declared and streamed sizes enforced before parsing. The calculation review found that retrograde classification has no approved near-station tolerance and chart positions lack independent reference fixtures; these remain domain/accuracy gates, not values to guess in code.

Fresh review caught a delayed-JSON race and incomplete no-JavaScript offset confirmation. Both were reproduced, fixed and cleared in scoped re-review. No-JavaScript offset confirmation is bound to the session and reviewed time fields; altered inputs require a fresh choice. An explicit fold is rejected for a non-repeated time as an input-semantics policy; an earlier suspected normal-time UTC shift was not reproduced and is not claimed as a fixed bug. The final reviewer found no new high/medium issue in the body-limit follow-up. See [the context-to-code map](CONTEXT-CODE-REVIEW.md) for all 44 numbered documents.


## Final review addendum

Independent review reproduced event-loop blocking for ordinary forms; the synchronous dispatcher now runs through Starlette threadpool and has a regression test. Chart caching now includes profile revision; expired request status is terminalized on reads/replay; full passage quoting preserves source qualifications; withdrawal outbox cleanup is executable and tested. The operator command `python -m astrology_evidence.manage` lists opaque user IDs, grants curator role locally and imports bounded edition JSON.

## Handoff article

See [GPT-6.1 Sol implementation handoff](GPT-6.1-SOL-IMPLEMENTATION-ARTICLE.md) for detailed work summary, commit inventory, test evidence, release gates and safe continuation points.

## November 16 context/code audit

The 44-document map separates code, measured evidence, proposed research and external release gates. Status text is reconciled across the context library; ADR-02 now records the actual Jinja/fetch/CSS UI instead of claiming HTMX/Tailwind were installed. The initial native test launcher was blocked by Windows Application Control; the existing approved underlying Python 3.12 binary then ran all 35 native tests without installing software or changing policy. Final local checks are recorded above. Docker image/Compose execution is still unavailable on this laptop.

## Remote audit verification

Audit publication commit `cf36edd838c2cdd84adb9f9c2e086031c02e2e8c` passed [Python CI run 43793711956](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43793711956), including PostgreSQL/Qdrant pytest, Ruff, mypy, **Build distributable wheel** and **Check packaged web assets**. [Documentation run 43793711969](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43793711969) and [Pages deployment 43793711138](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43793711138) also passed. The public guide returned 200 and includes the new context-to-code link and corrected Jinja/fetch/CSS stack. The owner push was accepted before the required documentation check completed; post-push checks are verified here rather than treating that push as an enforced merge gate. This follow-up changes documentation only.

The public guide was exercised in Edge at 1440px and 320px: no horizontal overflow, keyboard focus reaches links, the research disclosure opens, the audit link is available, and no links point to the old implementation branch. This is a focused guide check, not a full accessibility certification.
