# Architecture decisions

Initial entries proposed on 2026-11-15; implemented deviations are recorded below. Change them with evidence and update affected contracts, tests and progress.

| ID | Decision | Reason | Alternative / trigger to reconsider |
|---|---|---|---|
| ADR-01 | Python 3.12 baseline, FastAPI modular monolith | User's Python requirement, typed HTTP boundaries, manageable operations | Move baseline when pinned library compatibility and hosting tests support it |
| ADR-02 | Jinja2 + small fetch enhancement + application CSS (implemented; supersedes HTMX/Tailwind proposal) | Current forms, pages and accessible charts need no extra UI dependency or asset build; ordinary server-rendered forms remain available | Add HTMX or a CSS build only for a demonstrated interaction/maintenance need; React/Next.js only when richer client state warrants another deployment boundary |
| ADR-03 | PostgreSQL for metadata, sessions, jobs; Qdrant for retrieval | Clear transactional authority and user-requested vector DB | pgvector would reduce service count but departs from Qdrant request |
| ADR-04 | LangChain ChatOpenAI with Responses API; direct provider first | User reports chat completions returned 410, Responses worked | Gateway only after exact route tested; no silent chat fallback |
| ADR-05 | Optional LiteLLM, disabled initially | Useful later for policy, accounting and multiple providers, unnecessary initial hop | Enable when native Responses compatibility and data-handling controls pass |
| ADR-06 | Bounded LangGraph workflow | Clear state transitions, limited tool surface, auditability | Ordinary functions sufficient for prototype; no Deep Agents unless a new use case needs open-ended planning |
| ADR-07 | Local multilingual-e5-small candidate | Multilingual retrieval with 384-dimensional vectors | Compare compact English model for English-only corpus and larger multilingual model if held-out quality warrants cost |
| ADR-08 | Hybrid dense + sparse retrieval, verse-aware child/parent chunks | Terms and verse IDs need lexical precision; semantics aid paraphrases | Dense-only baseline retained for ablation, reranking only if quality gains justify latency |
| ADR-09 | Swiss Ephemeris calculation adapter | Reproducible astronomical engine, explicit settings | License decision required; alternative engine only after feature and reference-parity review |
| ADR-10 | Vedic-first Lahiri/whole-sign/mean-node conventions | Coherent initial interpretation framework | Other schools become explicitly separate, versioned profiles |
| ADR-11 | Google OIDC with opaque server-side sessions | User requirement; avoids storing reusable tokens in browser JS | Hosted identity service if operational needs justify extra dependency |
| ADR-12 | Small rights-cleared corpus before mass ingestion | Quality and provenance matter more than quantity | Scale from 3–5 pilot editions to 20–50, then 100+ only after evaluations |
| ADR-13 | Local-first development, constrained free demo, paid reliable service | Free tiers do not imply enough RAM or uptime for all components | A real zero-cash public demo may need reduced scope; document measurements |
| ADR-14 | Human review of traditional rule applicability | Retrieval alone does not prove a rule applies | Structured reviewed rule registry can automate narrow checks, never unlimited LLM rule discovery |
| ADR-15 | Source-grounded explanations, no deterministic future claims | Reproducibility and traditional authority do not establish real-world prediction | Empirical research is a separate consented study with independent methodology |

## Decision dependencies

- Public launch depends on source rights, ephemeris licensing, provider data handling, Google OAuth configuration and measured hosting fit.
- The proposed open-source/AGPL versus commercially licensed deployment choice is unresolved; do not assume either authorization. Swiss Ephemeris primary licensing page was directly inspected on 2026-11-15 and describes AGPL and Professional options: https://www.astro.com/swisseph/swephinfo_e.htm . Review the actual license and wrapper dependencies before distribution or hosted launch.
- Corpus language determines embedding evaluation. A multilingual label alone does not establish Sanskrit retrieval quality.
- Free hosting cannot be chosen solely from advertised CPU credits: measure cold start, model-load peak RAM, steady RAM, query latency and disk behavior.
- User consent cannot replace provider due diligence or corpus rights.

## Dependency selection policy

At implementation start, verify current supported versions from official release metadata; select a mutually compatible set and lock it. Do not pin guessed latest versions in this planning package. Core candidates: fastapi, uvicorn, pydantic-settings, sqlalchemy, alembic, psycopg, authlib, jinja2, httpx, langchain-openai, langgraph, qdrant-client, sentence-transformers, pyswisseph, pytest, ruff and mypy. OCR/parser packages are worker-only and chosen per document type. Production does not install every research tool.
