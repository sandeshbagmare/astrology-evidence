# Code standards, testing and release evidence

This document governs future implementation. No package environment or tests have been run for an application in this planning task.

## Project layout

```text
AGENTS.md
context/                       # This specification and progress
pyproject.toml                 # Python >=3.12 baseline; verify supported range
uv.lock                        # Reproducible dependency lock
src/astrology_evidence/
  main.py                      # FastAPI composition, middleware, route registration
  config.py                    # Typed environment settings; secrets redacted
  db.py                        # Connections, transactions, request sessions
  identity/                    # Google OIDC, sessions, authorization
  profiles/                    # Birth input and revision services
  calculations/                # Timezone normalization and ephemeris adapter
  corpus/                      # Rights, editions, passage extraction/review
  retrieval/                   # Embeddings, hybrid search, context assembly
  answers/                     # Workflow, provider, validation, saved readings
  jobs/                        # Durable leases and ingestion/export/deletion jobs
  web/                         # Page routes, templates, static assets
  observability.py             # Redacted structured events and metrics
migrations/                    # Reviewed Alembic migrations
worker/                        # Entrypoint using the same application services
tests/                         # Unit, integration, browser and evaluation fixtures
```

Do not create all directories until their task needs them. Prefer feature-focused modules with explicit contracts to generic base classes, service locators or deep repository abstractions.

## Python rules

Use typed Pydantic models at external boundaries and clear typed internal contracts. Centralize configuration with pydantic-settings, fail startup on missing required settings, and keep secrets out of repr/logging. Use SQLAlchemy/Alembic with explicit transactions and parameterized queries. Use UTC-aware datetimes for instants and distinct local-time types for birth input.

Async handlers do not make CPU-heavy work nonblocking. Offload CPU-bound ephemeris/embedding tasks via bounded execution; test thread safety of the selected wrapper before sharing mutable engine state. In particular, serialize configuration-sensitive Swiss Ephemeris calls or use isolated worker processes if global engine settings make concurrent requests unsafe. Never allow concurrent charts to contaminate ayanamsha/flags.

Use lifespan-managed HTTP/database clients with explicit timeouts. Avoid network calls at module import. Avoid broad `except Exception` except at a controlled request/job boundary where the failure is sanitized, recorded and converted into a stable error. Retry only classified transient idempotent operations, with deadlines and capped attempts. No silent exception swallowing, fake default charts or catch-all fabricated answers.

Formatting: Ruff format and lint, 100-character target line length, explicit exports only when needed. Type-check application code with mypy; strict checking for calculations, identity and ownership logic, gradually extend to adapters with third-party typing limits documented. Comments explain domain or security constraints, not obvious syntax. Exact dependency rules live in the lockfile, not copied across documents.

## UI and security standards

Jinja escaping is always on; never mark model or source text as safe HTML. Markdown output, if offered later, must use a reviewed sanitizer and conservative allowlist. CSP, secure cookies, CSRF and ownership enforcement apply to HTMX fragments as well as full pages. Compile and self-host production assets; avoid runtime stylesheet/CDN dependencies. Forms have labels, keyboard focus and textual validation. SVG chart data has an accessible table.

Never test against production accounts or use the disclosed key in fixtures. Offline fakes are the default for provider tests; a real provider smoke test is explicitly opt-in and uses an environment secret. Redaction tests include Authorization headers, session cookies, raw birth input and provider error bodies. Keep private birth data and source text out of analytics.

## Test layers

| Layer | Required evidence |
|---|---|
| Unit | Time normalization, circular angle math, rule prerequisites, chunk boundaries, citation matching, rights and schema validation |
| Integration | PostgreSQL migrations/constraints, session lifecycle, owner checks, Qdrant filters/fusion, idempotent jobs and corpus publication |
| Provider contract | Actual outbound path is /v1/responses; no /chat/completions; supported request fields and output extraction; timeout/malformed response behavior |
| Calculation reference | Independent reference charts with matched flags, uncertainty intervals, DST fold/gap, lunar-node settings and no silent ephemeris fallback |
| Browser | Google callback simulated locally; profile flow, keyboard navigation, citations, error/abstention, consent decline, export/delete |
| RAG evaluation | Fixed 150-item corpus split, retrieval relevance, source applicability, contradictions, abstention, multilingual limits |
| Security | Cross-user IDs, prompt injection, stored XSS, CSRF, OAuth replay, malicious PDFs, SSRF, unauthorized excerpts, export links and cache leakage |
| Operations | Clean install, restart recovery, backup/restore, source withdrawal, account deletion, host memory/cold-start budget |

Tests should prove behavior and failure handling, not copy implementation details. Test every consequential condition; avoid elaborate tests for static cosmetic text. Use small rights-cleared or synthetic fixtures with explicit expected outputs. At least two expert reviewers adjudicate ambiguous traditional interpretations; record disagreements.

## Numeric and evaluation conventions

For equivalent independently configured reference ephemerides, initial longitude tolerance is <=1 arcsecond, using circular distance. A fixture is valid only when time basis, zodiac and flags match. Houses and boundary-sensitive derived facts require dedicated expected outcomes; do not hide a sign mismatch inside an average error. Floating-point output comparisons never use arbitrary display rounding as validation.

The central release thresholds are in [product scope](01-product-and-scope.md) and [retrieval](07-ingestion-and-retrieval.md). Overall test coverage target is >=85% of application lines with explicit branch tests for auth, ownership, time ambiguity and citation validation; coverage is a guardrail, not evidence of semantic correctness. A small held-out set establishes only bounded measured performance.

## Future verification commands

After the project is implemented and dependencies locked: `uv sync --frozen`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `uv run pytest`, followed by targeted integration/browser/evaluation commands configured by the relevant task. Run clean migrations and rollback/recovery tests against a disposable database. Scan staged changes for secrets and inspect dependency/license reports. Record actual command, date, exit code and summary in progress; never write PASS from a proposed checklist.

## Review and change control

Every change states user-visible behavior, changed contracts, test evidence and limitations. Changes to embeddings, corpus, ephemeris, rule interpretation, provider or prompts need a new version and appropriate regression evaluation. Do not retroactively alter a saved reading without an explicit revision or rights/deletion action. Document schema compatibility and migration recovery before release.


## Expanded test inventories

Read the specialist inventories before writing tests: [calculation fixtures](22-calculation-algorithms-and-reference-tests.md), [time/place](23-time-place-and-uncertainty.md), [OCR](25-ocr-and-multilingual-quality.md), [claim evidence](26-evidence-validation-and-contradictions.md), [evaluation design](27-evaluation-and-benchmark-design.md), and [security threats](28-security-threat-model.md). These define concrete adverse inputs and independent validation needs; none is evidence that the future application has passed.

## Expanded delivery and accessibility checks

[36 Accessibility validation](36-accessibility-and-responsive-validation.md) specifies keyboard/screen-reader and responsive cases; [37 CI and release](37-ci-testing-and-release-strategy.md) separates untrusted PR checks from secret-bearing manual integration, expert evaluation and release evidence. Use these task-specific inventories when implementing Tasks 8–9. A successful dependency install or coverage percentage is not enough for a release.
