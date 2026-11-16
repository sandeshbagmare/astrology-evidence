# Small commits and continuous verification

Adopted on 2026-11-15 at the user's request and used during the subsequent application implementation. This policy applies to people and coding agents. Implementation and testing are authorized; public real-user launch remains gated by evidence listed in [implementation progress](../implementation/PROGRESS.md).

## One coherent change at a time

A commit should contain one reviewable behavior change and the evidence needed to check it: implementation, relevant tests, and any contract/documentation update that must remain consistent with that behavior. A documentation-only commit can contain one coherent explanation or research correction. Keep formatting sweeps, dependency upgrades and unrelated refactors separate from behavior changes.

There is no universal line-count limit. Split when a reviewer could accept one part and reject another independently. Do not split a working change into commits that intentionally break imports, migrations or required tests. Large generated artifacts can accompany a small meaningful source change, but identify their origin and verify reproducibility.

Suggested messages describe the result: `docs: explain the first reading journey`, `test: cover ambiguous birth-time rejection`, or `fix: reject citations from withdrawn editions`. Do not use messages such as “everything,” “final fixes,” or “production ready” without a specific, supported result.

## The change cycle

1. Read the relevant context and identify the behavior, callers, ownership boundary and failure cases affected.
2. For nontrivial features or bug fixes, write or identify a meaningful test that would expose the missing or incorrect behavior. Confirm the intended failure before implementing a new regression test. Static prose changes need document checks, not artificial unit tests.
3. Implement the smallest complete change. Keep source, tests and contract changes together when their correctness depends on one another.
4. Run the relevant focused tests immediately. If they fail, inspect the failure, fix its cause and rerun. Never replace a failing assertion with a weaker one merely to obtain green output.
5. Run the broader checks warranted by the affected interfaces and risk. Inspect the diff and staged files, including accidental secrets and unrelated edits.
6. Commit only when required checks pass. Record the command, result and scope in the commit/PR evidence or progress record. A command not run is marked “not run,” with a reason; it cannot be counted as passing.
7. Before pushing or merging, verify the actual final tree, not an earlier revision. Re-run affected checks after any post-test edit. A new wording-only edit can need only documentation validation; a changed authorization branch requires its security tests again.

A known failing required check blocks the commit/merge. An unrelated pre-existing failure must be documented and triaged explicitly; do not silently relabel a red build as green. No forced history rewrite, bypassed checks or disabled test is a substitute for a correction.

## Testing while agents work

When parallel agents are authorized, divide work into disjoint owned files or modules and agree on interfaces first. The coordinator records each assignment, dependencies and test responsibility. Agents may prepare test cases, inspect independent fixtures, review source evidence or run checks against a stable snapshot while another agent implements a separate module.

Parallel testing must not race with an agent editing the same code. Identify the tested commit or snapshot; if an uncommitted tree is tested, record its state and ensure relevant files remain unchanged until results are collected. Tests against an earlier snapshot are advisory until the merged final tree passes. Shared test infrastructure, database schemas and contract files have one editing owner at a time.

Each implementer runs focused tests before handing off. A reviewer checks meaningful failure conditions, not only the diff, and reports independently observed results. The coordinator reads findings, resolves conflicts, integrates changes and runs the final applicable checks. A subagent saying “passed” is not sufficient evidence without the command, tested revision/state and result.

Use isolated disposable databases, collections and ports for concurrent integration tests. Never share production accounts, source material without rights, or mutable real-user data between test agents. Mock provider calls by default; live calls are explicit opt-in checks with environment secrets and a bounded budget. Do not multiply model calls simply because several agents are active.

## Current documentation and Pages checks

Run `node scripts/check-docs.mjs` from the repository root before committing documentation or website changes. The script's actual checks define its coverage; inspect its output and do not infer external service availability or application correctness from a local documentation pass.

For website changes, also inspect the relevant desktop and narrow mobile layouts, keyboard navigation, visible focus, disclosure controls and reading links in a browser. Verify GitHub Pages' deployed response and expected content after publishing. A successful push proves source publication; it does not prove that the Pages build finished or the public site works.

Current CI runs application pytest against PostgreSQL 16 and Qdrant 1.20, Ruff and mypy, as well as documentation checks and Pages deployment. It still cannot prove live Google authentication, independent chart accuracy, provider privacy/compatibility, real-corpus retrieval quality, production capacity or deployment recovery. Keep the readiness report explicit about that boundary.

## Application checks and remaining gates

The locked application now runs Ruff, mypy, pytest, PostgreSQL/Qdrant integration tests and focused browser tests. Frozen expert retrieval evaluation, live-provider checks, full accessibility validation, independent chart references and recovery drills remain open gates from [code standards](14-code-standards-and-testing.md), [implementation plan](15-implementation-plan.md), and [CI/release strategy](37-ci-testing-and-release-strategy.md). Do not install every proposed tool merely to make a checklist appear complete.

Authentication, tenant isolation, chart calculations, rights withdrawal, provider charging/replay, migrations and citation validation require an independent review before merge. Check adjacent callers and failure handling. Use independent calculation references and rights-cleared fixtures; tests reproducing the implementation's own formula are not independent validation.

Tests should exercise concrete outcomes: another user's ID is denied; an unknown birth time does not produce houses; a withdrawn edition cannot appear in a saved answer; a lost provider response is not automatically resent. Coverage percentage is a secondary guardrail, never a substitute for these assertions.

## Branch and release discipline

Prefer a short-lived branch and pull request for each coherent change. Configure required CI checks and review protection for the default branch where the repository's account/plan supports it. These are deployment/repository settings, not claims that remote protection has already been configured. For an initial publication, the coordinator may create a small sequence of locally verified commits and push them together.

The final release record names the exact commit, dependency lock, corpus generation, model/provider capability report, calculation data versions, checks run and outstanding limitations. Production readiness additionally requires the [build-readiness gates](41-research-synthesis-and-build-readiness.md): rights, ephemeris licensing, verified provider behavior, expert evidence evaluation, measured hosting capacity, reliable privacy jobs, restore drills and accessibility checks. Passing documentation CI or writing this rule does not satisfy those gates.

If a defect is discovered after publication, reproduce it, add a meaningful regression when appropriate, fix it in a focused commit, rerun affected checks and verify the new deployment. Record the correction without erasing the earlier failed result.
