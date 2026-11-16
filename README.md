# Astrology Evidence

**Understand the app in five minutes:** [Open the reading guide](https://sandeshbagmare.github.io/astrology-evidence/).

A Python astrology application that separates **chart calculations, source passages, and AI interpretation**. The local baseline works with synthetic data; licensed books and expert-reviewed interpretation rules still need to be supplied before real astrology-quality claims.

> **Current state: working local synthetic-data application; not cleared for real-user production.** It implements accounts, charts, rights-gated source search, constrained readings, privacy jobs, and the server-rendered UI. External source, provider, and deployment gates remain open. Citations do not establish that astrology predicts future events.

## What would the app do?

1. Sign in with Google and enter birth information, including whether the time is uncertain.
2. Compute a chart using a declared, reproducible method.
3. Retrieve relevant passages from a small, rights-cleared library.
4. Explain the interpretation with exact edition/page/verse references, exceptions and disagreements.
5. Show missing evidence rather than inventing a precise prediction.

## What should I read?

| Time available | Read | What you will learn |
|---|---|---|
| 5 minutes | [Pages overview](https://sandeshbagmare.github.io/astrology-evidence/) | What we are building, how it works and current readiness |
| 10 minutes | [Readiness report](REPORT.md) | What is complete, what is unproven and what happens next |
| 10 minutes | [Context-to-code audit](implementation/CONTEXT-CODE-REVIEW.md) | Coverage and remaining gates across all 44 context documents |
| 20 minutes | [GPT-6.1 Sol implementation handoff](implementation/GPT-6.1-SOL-IMPLEMENTATION-ARTICLE.md) | Detailed implementation record, commit list, tests and continuation guide |
| 20 minutes | [Product scope](context/01-product-and-scope.md) and [architecture](context/03-architecture.md) | MVP, boundaries, technology and diagrams |
| Before coding | [Implementation plan](context/15-implementation-plan.md) and [contribution rules](CONTRIBUTING.md) | Small work units, tests, review and release gates |
| A specific question | [Full context index](context/README.md) and [research map](context/42-expanded-research-program.md) | Find the relevant specialist dossier without reading everything |

## Implemented stack

Python / FastAPI · Jinja2 / small fetch enhancement / CSS · PostgreSQL · Qdrant · local multilingual embeddings · Swiss Ephemeris (licensing decision pending) · LangChain / bounded LangGraph workflow · Google OIDC.

The generation adapter has offline Responses wire-contract tests but has not been called against the third-party service. Upstream model identity, data handling and reliability remain unverified. AI and embeddings are disabled by default. Secrets are never part of this repository.

## Is the plan good enough?

**The local engineering prototype works. Production readiness is not established.** Research covers 42 candidate books, 12 product comparisons, seven hosting options and 20 additional specialist assignments. These are research counts, not ingested books or quality benchmarks.

Before real users, acquire and review source editions, validate chart outputs against independent references, review provider data handling, produce expert-labeled quality results, and run production backup and recovery drills. See the [runbook](implementation/RUNBOOK.md) and [implementation ledger](implementation/PROGRESS.md).

## Small commits, continuous testing

One coherent behavior and its tests per commit. Write the meaningful failing test first, implement the smallest complete change, and rerun relevant checks before committing. Agents may review and test independently in parallel; final verification must cover the combined revision. Never describe future acceptance targets as passing tests.

Detailed policy: [small commits and verification](context/44-small-commits-and-continuous-verification.md). Agent instructions: [AGENTS.md](AGENTS.md).

## Check this documentation

Requires Node.js 24 or newer; no package installation:

```text
node --test scripts/check-docs.test.mjs
node scripts/check-docs.mjs
```

GitHub Actions runs these checks on pushes and pull requests. They check local links, credential-shaped text, damaged Unicode and fenced Markdown. They do **not** verify astrology claims, external source rights, provider behavior or application readiness.

The public site is static HTML/CSS in `docs/`, published by GitHub Pages. It explains the working local app and its release gates; Pages does not host the Python application. No real books or credentials are distributed here.

## Implementation update

A functioning local application baseline exists. Start with [the runbook](implementation/RUNBOOK.md) and [actual implementation progress](implementation/PROGRESS.md). Current code supports accounts/profiles, chart calculations, source retrieval, bounded readings and privacy jobs. Production knowledge, provider and operating gates remain unresolved.

Standard development: `uv sync --frozen --python 3.12`, then `uv run uvicorn astrology_evidence.main:create_app --factory`. Python 3.12 is the verified baseline; Python 3.12 or 3.13 is required for the native chart engine. Enable synthetic login only for local development. See the runbook for Docker, worker execution, curator setup and this laptop's approved runtime configuration. Never use real birth data or represent the synthetic corpus as licensed astrological knowledge.
