# Astrology Evidence

**Understand the proposal in five minutes:** [Open the reading guide](https://sandeshbagmare.github.io/astrology-evidence/).

A proposed Python astrology application that shows **the chart calculation, the passage from a book, and the AI interpretation separately**. Users should be able to inspect why an interpretation was produced and where its limits are.

> **Current state: research and design, not a working astrology application.** The plan is sufficient to start a controlled prototype. It is not production-ready, and citations do not establish that astrology predicts future events.

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
| 20 minutes | [Product scope](context/01-product-and-scope.md) and [architecture](context/03-architecture.md) | MVP, boundaries, technology and diagrams |
| Before coding | [Implementation plan](context/15-implementation-plan.md) and [contribution rules](CONTRIBUTING.md) | Small work units, tests, review and release gates |
| A specific question | [Full context index](context/README.md) and [research map](context/42-expanded-research-program.md) | Find the relevant specialist dossier without reading everything |

## Proposed technology

Python / FastAPI · Jinja2 / HTMX · PostgreSQL · Qdrant · local multilingual embeddings · Swiss Ephemeris (licensing decision pending) · LangChain / bounded LangGraph workflow · Google OIDC.

The initial generation adapter uses a user-reported third-party Responses endpoint. Compatibility, underlying model identity, data handling and reliability remain unverified. Secrets are never part of this repository. LiteLLM is optional after route compatibility testing.

## Is the plan good enough?

**For a scoped prototype: yes. For real users or production: no.** Research covers 42 candidate books, 12 product comparisons, seven hosting options and 20 additional specialist assignments. These are research counts, not books already ingested, benchmark results or implemented features.

The next stage must prove provider compatibility, chart correctness, source permissions, retrieval quality and deployment fit. Start with synthetic birth records and 3–5 approved editions, not hundreds of unreviewed books. See the [report](REPORT.md) for the release gates.

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

The public site is static HTML/CSS in `docs/`, published by GitHub Pages. The actual application and its Python tests have not been implemented. No books or credentials are distributed here.
