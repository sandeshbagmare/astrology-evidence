# Readiness report

Prepared November 15, 2026. This report separates research completion, publication and future implementation.

## Verdict

**The design is ready to guide a controlled prototype. The application is not built and is not production-ready.** The specification connects the major components and includes concrete failure cases. The remaining uncertainty must be resolved through a small implementation, source acquisition, expert review and measured tests.

## What exists today

- A product definition and phased implementation plan, with Python as the main application stack.
- Architecture and workflow diagrams, data/API contracts, UI flows, Google authentication and privacy design.
- A 42-work candidate bibliography and edition-level rights/acquisition workflow; none of these books has been ingested.
- Twelve public product/project comparisons and seven hosting comparisons, with source-access limitations recorded.
- Twenty additional research assignments covering calculations, timezones, retrieval, OCR, security, privacy, databases, provider compatibility, accessibility, operations, rules and validity.
- Independent integration reviews whose documentation findings were reconciled.
- A static reading guide, repository documentation checks and a small-commit/testing policy.

The original planning package comprised 46 Markdown documents. The publishing phase adds this report, contribution guidance, delivery rules, a static site and validation/CI files. File counts are not a quality metric.

## What does not exist yet

No working Google sign-in, birth-profile service, calculation engine integration, vector index, corpus ingestion, AI reading workflow or application deployment. There is no measured retrieval score, independent chart-parity result, accessibility conformance result or real-user security test. The supplied third-party provider has not been called by this project.

Publishing this documentation on GitHub Pages does not deploy the future Python application. Pages serves the overview; the application will require compute, persistent data stores and a reliable privacy-job executor.

## First implementation slice

Build one end-to-end path using synthetic inputs: owned profile contract → deterministic chart fixture → a handful of permitted or synthetic passages → source-grounded answer validation → a readable result. Keep external generation disabled until its contract and data-handling gates pass. Confirm local memory and response-time budgets before selecting a host.

Follow [Task 1 onward](context/15-implementation-plan.md). Each slice carries tests and evidence in its commit. Do not expand to more traditions or a larger corpus before the narrow path passes review.

## Gates before real users

| Gate | Evidence required | Current status |
|---|---|---|
| Rights | Approved edition/action permissions for ingestion, model transmission and excerpts | Not acquired |
| Engine license | Chosen compliant Swiss Ephemeris and dependency-license path | Decision pending |
| Provider | Exact Responses route, capability/error tests, privacy and cost review | User-reported configuration only |
| Chart accuracy | Independent matched references, timezone/interval and concurrency tests | Not run |
| Retrieval | Reviewed dataset; 20 calibration / 30 development / 100 held-out questions | Not created |
| Grounding | Exact citations and expert-reviewed applicability; no unsupported precision | Design only |
| Privacy/security | Ownership, consent, deletion, restore, injection and OAuth tests | Design only |
| Hosting | Measured encoder memory, cold starts, persistent storage and reliable worker | Not measured |
| Accessibility | Keyboard, screen-reader, responsive and error-flow checks for the app | Not run |

The held-out evaluation allocation is 86 answerable and 14 unanswerable questions. Proposed targets are sample gates, not claims of population-wide reliability or predictive validity.

## Choices still needing an owner

Confirm the first tradition and English-first scope; choose an ephemeris licensing route; recruit qualified source/rule reviewers; obtain the first 3–5 editions; assess the provider's data practices; and choose whether to fund reliable compute after a synthetic demo. These choices are tracked in [progress](context/16-progress-and-open-decisions.md).

## How we keep the implementation reviewable

Use small cohesive commits with tests, independent review for high-risk changes, and final integration checks on the combined revision. A test agent must report the exact revision, command and result, and must not claim success from another agent's summary. Failures are fixed before the next dependent slice. Full policy: [continuous verification](context/44-small-commits-and-continuous-verification.md).

Documentation CI validates this repository's links, formatting hazards and credential-shaped text. Its passing status is deliberately separate from future application readiness. Current publication evidence is recorded in the repository commits, Actions runs and Pages deployment.

## Suggested reading path

Read [the overview](https://sandeshbagmare.github.io/astrology-evidence/), then [product scope](context/01-product-and-scope.md), [architecture](context/03-architecture.md), and [the implementation plan](context/15-implementation-plan.md). Use [the context index](context/README.md) as a reference library, not a requirement to read every dossier before starting.
