# CI, testing and release strategy

Prepared 2026-11-15. Proposed implementation policy only: no workflows, application tests, benchmarks, dependency installs or provider calls were executed. This extends [standards](14-code-standards-and-testing.md), [implementation](15-implementation-plan.md), [calculation references](22-calculation-algorithms-and-reference-tests.md), [evaluation](27-evaluation-and-benchmark-design.md), [threat model](28-security-threat-model.md) and [provider contract](32-responses-provider-compatibility.md). Acceptance targets below are not results.

## Pipeline boundaries

Use three independently visible workflows: unprivileged pull-request verification, trusted release-candidate verification, and manually approved external-service evaluation. A passing PR means the change meets its engineering checks; it does not confer source rights, certify provider privacy, or establish predictive validity.

| Trigger / job | Environment and meaningful checks | Required result |
|---|---|---|
| Every PR: static and unit | Locked development environment; Ruff formatting/lint, mypy, offline pytest; boundary arithmetic, uncertainty, rights, citations, redaction and ownership policy | No errors; application line coverage ≥85%; critical branches exercised |
| Every PR: provider contract | Local synthetic Responses server; no external credential or outbound provider traffic | Exact `/v1/responses`, bounded calls/deadlines, refusal/malformed output and uncertain-send behavior |
| Every PR: integration | Disposable Linux PostgreSQL and Qdrant with pinned image digests, synthetic editions and two fake owners | Constraints, real filters, transactions, leases, rights revocation and publication recovery pass |
| Every PR: browser | Server-rendered application against disposable services; local fake OIDC issuer, synthetic users | Callback validation, consent, unknown-time flow, citations, HTMX authorization, keyboard basics, export/delete |
| Calculation/native change and release | Windows and production Linux architecture; selected Python/native builds; approved reference fixtures | Coordinate residuals, flags, boundary handling and concurrent settings isolation pass |
| Dependency/workflow change and scheduled audit | Dependency diff, advisory scan, license inventory, action-pin review | No unreviewed actionable vulnerability or unacceptable license change |
| Protected release candidate | Exact built artifact, migrations, recovery drills, affected quality evaluation | Signed review record and complete release manifest |
| Manual provider/benchmark | Approved revision, protected environment, explicit budget and authorized corpus | Capability report or independently reviewed benchmark; never an ordinary PR prerequisite |

Security and correctness checks must not disappear through path filtering. An aggregator verifies every required job ran successfully; skipped, cancelled or missing jobs cannot masquerade as success. Cancel superseded PR runs, but serialize deployment and migration jobs and do not cancel a migration mid-operation. Give services explicit health checks and timeouts; do not replace readiness with fixed sleeps. Proposed command groups follow document 14, with integration/browser markers selected explicitly.

## Reproducible dependencies and native builds

Commit `pyproject.toml`, `uv.lock` and the supported Python declaration together. Pin the CI uv tool and Python patch/build, and review lock changes as dependency changes. uv distinguishes `--locked`, which checks whether resolution must change, from `--frozen`, which consumes the lock without freshness checking; use `uv lock --check` before the existing `uv sync --frozen` policy, or a tested equivalent `uv sync --locked`. Run subsequent tools without silently re-resolving dependencies. The universal lock covers platform markers, not a guarantee that every native dependency builds or behaves identically everywhere. [S1, S2]

Support Python 3.12 initially; add versions only after compatibility evidence. Run Linux full integration and Windows installation/calculation tests, using the actual production architecture for release. Capture wheel hashes, native Swiss library/build flags, compiler/runtime where applicable, ephemeris checksums and tzdata version. Test installed production artifacts, not only editable source trees. An explicitly unsupported platform should fail clearly rather than obtain an unrecorded replacement wheel.

Swiss settings require a process-wide transaction lock or isolated processes as specified in document 22. Alternate configurations concurrently and compare each response with its own sequential baseline; test initialization, settings changes and cleanup together. Windows and Linux tests are essential because build-dependent thread-local behavior can differ. Deterministic fake engine tests verify orchestration, but cannot replace native concurrency evidence.

## Fixtures, independence and failures

Keep fixtures small, explicit and owned by the test that changes their state. pytest documents teardown through yield fixtures and recommends separating state-changing actions so cleanup remains dependable. Use function-scoped owners/records, unique run namespaces and bounded cleanup; session-scoped services are acceptable only with per-test isolation. Failed fixture setup must not leave a database, collection or process available to another test. [S3]

Chart goldens require source identity, acquisition date, license/redistribution scope, input/time convention, coordinate frame, flags, expected values, tolerance rationale and independent reviewer. A regenerated snapshot from the same implementation is not an accuracy oracle. Wrapper-to-native Swiss parity catches adapter errors; independently configured JPL references address physical-body coordinates; nodes, houses and traditional labels need separately reviewed references. Retain the ≤1 arcsecond target only for matched supported longitude cases and use circular distance. Exact sign/uncertainty outcomes cannot be averaged away. Never automatically accept regenerated expected values after an engine upgrade.

Synthetic fixtures should intentionally include cross-owner IDs, withdrawn editions, malicious passages, forged citations, Unicode quotation boundaries, DST folds/gaps, unknown-time intervals, changed payload/idempotency keys, crashed workers and late provider completions. Negative controls must demonstrate that tests detect swapped longitude signs, altered citation spans and omitted rights filters. Integration tests use real PostgreSQL constraints and real Qdrant filtering; an in-memory substitute cannot prove these behaviors.

Browser tests use local signed OIDC tokens and keys to exercise nonce, issuer, audience, expiry, replay and callback handling. A test-only authenticated-user shortcut may support isolated UI tests, but does not count as authentication coverage; production startup rejects test-auth configuration. No production account, real birth record or copied credential belongs in fixtures. External network access is denied during test execution except explicitly permitted local services; dependency installation is a separate preparation stage.

## Workflow security and evidence hygiene

Default the workflow token to read-only repository contents and grant additional permissions only to the job needing them. Pin third-party actions to reviewed full commit SHAs and container images to digests, with human-readable version annotations and reviewed update PRs. GitHub documents full-SHA pinning and least-privilege permissions as hardening controls. Treat all PR code, branch names and downloaded artifacts as untrusted. [S4]

Use `pull_request` for fork testing, no repository/provider/deployment secrets, and ephemeral hosted runners. Do not execute PR code through privileged `pull_request_target` or a privileged follow-up workflow consuming executable PR artifacts. Trusted publication rebuilds the approved commit in its own environment. Do not share writable caches across untrusted PRs and credential-bearing release jobs; cache dependencies by lock digest, platform and interpreter, never sessions or private corpus contents.

Dependency review assesses introduced versions and licenses where the repository's feature entitlement permits it. Add a pinned advisory scanner against the exact resolved production and development dependencies; scheduled audits catch new advisories without a code change. `pip-audit` finds known Python vulnerability advisories and supports CycloneDX output; it is not a proof of malware absence or a complete native/container audit. Produce a CycloneDX SBOM from the locked environment/export, supplement it with OS/native components, and inspect license changes separately. Do not auto-fix dependencies during release verification. [S5, S6]

Set explicit artifact retention: proposed 14 days for ordinary redacted test reports, 7 days for failure screenshots/traces, and 90 days for restricted release evidence, subject to repository limits and privacy policy. GitHub supports per-artifact retention configuration. Longer-lived approved manifests belong in the controlled release archive with its documented retention. Upload only allowlisted reports, never entire workspaces, databases, environment dumps, PDFs or browser profiles. Private licensed benchmark material remains in restricted storage; public reports contain hashes, aggregate results and permitted excerpts only. Scrub cookies, authorization headers, URLs containing identifiers and source text before upload. [S7]

## Release gates and recovery

The ≥85% line threshold is a regression guardrail, not a substitute for semantic checks. Require explicit branch evidence for authorization, ambiguous time, rights withdrawal, citation failure and uncertain provider sends. No unauthorized disclosure, fabricated quote/ID, silent ephemeris fallback or unbounded generation is acceptable. Test flakiness has an owner and deadline; retries preserve the original failure and cannot conceal a critical defect.

Apply document 27's frozen evaluation protocol when corpus, retrieval, prompts, model or evidence behavior changes. A custodian runs sealed items after configuration freeze; two independent reviewers adjudicate support and applicability. Recall@10 ≥0.90, claim support ≥0.95, all 14 held-out abstention cases passing, and perfect exercised citation resolution/quote fidelity remain sample gates with denominators and intervals. Ordinary PRs run synthetic regressions; manual live-provider runs use protected secrets, minimized synthetic inputs, an approved spending cap and no uncertain automatic resend. Provider terms and corpus licenses remain independent launch blockers.

Use expand/contract migrations: deploy additive schema first, prove previous and candidate application compatibility, complete resumable backfills, then remove obsolete schema in a later reviewed release. Test fresh installation and upgrade from the previous release with realistic synthetic volume. Destructive rollback requires an assessed restore/forward-fix plan; a successful downgrade command alone proves little. Prove backup restore, deletion-tombstone replay and rights denial before restored traffic resumes.

Crash-inject corpus publication before indexing, between staged index completion and authoritative activation, and after activation before cleanup. Readers must see a complete approved generation or safe unavailability. Rollback may reactivate only a compatible, still-authorized generation; it must never resurrect withdrawn sources or deleted owners. Rehearse duplicate migration execution, worker lease expiry and publication fencing.

The immutable release evidence manifest records commit/artifact/image digests; Python/uv/lock/native/data revisions; migrations and compatibility window; approved corpus generation and edition-rights versions; tokenizer/embedding/index configuration; prompt/schema/rule versions; requested/reported provider model and capabilities; fixture/benchmark hashes and licenses; commands, timestamps, exit codes, residuals, coverage and review outcomes; SBOM/advisory status; known limitations and rollback owner. Missing evidence blocks the affected release claim. No checklist is marked PASS until its actual artifact exists.

## Primary sources and access record

Accessed 2026-11-15 by direct HTTPS with HTTP 200 and relevant text inspected. Web-tool searches returned no usable content. pytest's rendered page returned HTTP 429; its official repository documentation supplied the fixture evidence. Mutable documentation and upstream branches require version pinning during implementation.

- S1: https://docs.astral.sh/uv/concepts/projects/sync/ — locked/frozen semantics and CycloneDX export.
- S2: https://docs.astral.sh/uv/concepts/projects/layout/ — universal lockfile and project metadata.
- S3: https://raw.githubusercontent.com/pytest-dev/pytest/main/doc/en/how-to/fixtures.rst — fixture scope, teardown and safe fixture structure.
- S4: https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions — token permissions, action pinning and untrusted workflow inputs.
- S5: https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review — dependency/security/license review.
- S6: https://raw.githubusercontent.com/pypa/pip-audit/main/README.md — advisory auditing and CycloneDX formats.
- S7: https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts — artifact upload and retention controls.
