# Configuration inventory and environment boundaries

Prepared 2026-11-15. These are proposed application-owned setting names and defaults, not a generated environment file or vendor SDK parameter guarantee. Values must be validated through typed settings at startup. No credentials belong in this document.

## Configuration precedence

Use explicit deployment environment values over a developer-only untracked environment file, over safe documented defaults. Never fall back from production to an embedded demo credential or insecure development cookie. Secrets are required for the capabilities that need them. If external AI is intentionally disabled, the UI may expose chart/library features and must say generation is unavailable; do not fail unrelated local computation merely because an optional gateway is absent.

Record a redacted settings manifest with version hashes and non-secret capability flags. Changes to chart conventions or embedding identity create new artifact/index versions, not a transparent runtime toggle that invalidates old readings.

## Service and identity settings

| Proposed name | Initial value/policy | Validation and consequence |
|---|---|---|
| APP_ENV | development, staging or production | Explicit enum; production enables strict security requirements |
| APP_PUBLIC_ORIGIN | Exact HTTPS origin in deployed environments | No user-controlled host/redirect construction |
| DATABASE_URL | Secret injected PostgreSQL connection | Require TLS policy appropriate to host; redact credentials |
| GOOGLE_CLIENT_ID | Deployment-specific OAuth client | Must match validated token audience |
| GOOGLE_CLIENT_SECRET | Secret injection | Never exposed to template/browser |
| GOOGLE_REDIRECT_URI | Origin plus /auth/google/callback | Exact registered URI, separate environments |
| SESSION_IDLE_SECONDS | 86400 | 24-hour idle expiry |
| SESSION_ABSOLUTE_SECONDS | 604800 | Seven-day maximum, never extended by activity |
| OAUTH_TRANSACTION_SECONDS | 600 | Single-use state/nonce/PKCE expiration |
| CSRF_ENABLED | true | Cannot disable for deployed browser writes |
| COOKIE_SECURE | true outside local development | Fail production startup when false |
| DATA_ENCRYPTION_KEY_REF | Secret-manager/key reference | Required if application-level encryption selected; key version stored with ciphertext |
| PROFILE_STORAGE_ENABLED | Only after privacy job executor gate | Disable new real-user collection when obligations cannot be met |

Deployment must also define trusted proxy headers/hosts deliberately; blindly accepting forwarded headers changes origin and secure-cookie decisions. OAuth state belongs to a browser-bound expiring transaction, not a reusable query string token.

## Generation and provider settings

| Proposed name | Initial value/policy | Validation and consequence |
|---|---|---|
| AI_ENABLED | Explicit capability flag | Requires processing disclosure and operational approval for real users |
| OPENAI_API_KEY | Runtime secret only | The key disclosed in chat is never copied to the project |
| AI_BASE_URL | https://freegg.app/v1 | Administrator allowlist, exact single /v1 prefix |
| AI_MODEL | gpt-6.1-sol | Provider alias; record requested/reported identifiers |
| AI_USE_RESPONSES_API | true | Contract test must show /v1/responses |
| AI_TIMEOUT_SECONDS | 120 maximum | Reduce to remaining total request deadline |
| AI_MAX_RETRIES | 0 | Avoid hidden duplicate provider requests |
| ANSWER_DEADLINE_SECONDS | 150 | Includes the entire bounded answer operation; repair cannot reset |
| ANSWER_MAX_GENERATIONS | 2 | Initial generation plus at most one repair |
| ANSWER_INPUT_CONTEXT_TOKENS | 6000 | Proposed retrieved-context budget, count headers and qualifiers |
| ANSWER_OUTPUT_TOKENS | 1800 | Enable only after provider parameter compatibility verified |
| QUESTION_MAX_CHARACTERS | 2000 | Validate server-side and reflect in UI |
| PROVIDER_STORE | false if supported | Acceptance does not prove retention behavior; review provider policy |
| LITELLM_ENABLED | false | Native Responses wire test required before enabling |
| ALLOW_PROVIDER_FALLBACK | false | No silent third-party data transfer |

A missing usage field must not turn budget enforcement off. The later budget design should reserve a conservative maximum request allowance before sending, then reconcile available usage. No monetary rate or provider quota is assumed until verified.

## Retrieval and corpus settings

| Proposed name | Initial value/policy | Validation and consequence |
|---|---|---|
| QDRANT_URL | Backend-only service address | Not exposed as a browser endpoint |
| QDRANT_API_KEY | Deployment secret where required | Scope service access and redact logs |
| CORPUS_ACTIVE_GENERATION | Published immutable generation ID | Must match PostgreSQL publication state and index manifest |
| EMBEDDING_MODEL | intfloat/multilingual-e5-small | Candidate; release requires corpus-specific evaluation |
| EMBEDDING_REVISION | Exact reviewed revision | Mandatory before indexing production corpus |
| EMBEDDING_DIMENSIONS | 384 | Collection schema must match; reject mixed revisions |
| EMBEDDING_NORMALIZE | true | Cosine configuration pinned with model |
| EMBEDDING_QUERY_PREFIX | query: followed by a space | Must match verified model contract |
| EMBEDDING_PASSAGE_PREFIX | passage: followed by a space | Included in token budget |
| CHUNK_TARGET_MIN_TOKENS | 180 | Semantic boundaries take precedence within hard cap |
| CHUNK_TARGET_MAX_TOKENS | 300 | Target, not license to sever a needed exception |
| CHUNK_HARD_TOTAL_TOKENS | 448 | Embedding tokenizer, including metadata and prefix |
| DENSE_CANDIDATE_COUNT | 30 | Filters before retrieval |
| SPARSE_CANDIDATE_COUNT | 30 | Same authoritative filter predicates |
| EVIDENCE_MAX_PASSAGES | 8 | Selection before bounded parent/exception expansion |
| SPARSE_SCHEMA_VERSION | Chosen by compatibility experiment | No guessed BM25/native API default |
| RRF_CONFIG_VERSION | Chosen by development evaluation | Pin fusion constant/rank conventions explicitly |
| PRIVATE_UPLOADS_ENABLED | false | Requires new ownership/security review before enabling |
| RAW_SCAN_PUBLIC_ACCESS | false | Excerpt/page permissions are edition-specific |

Do not embed secrets or personal history in public payload metadata. A collection alias is a serving mechanism, not the rights authority. Final excerpt reads always recheck database rights and publication state.

## Calculations, geography and UI

Default chart convention is Vedic/Jyotish, sidereal Lahiri, whole-sign, mean nodes, geocentric placements. Store engine flags and data checksums per result. Setting names are represented in ChartSettings rather than global hidden environment values; a process adapter must apply them safely for each request.

Pin the actual timezone data source, not just the package dependency: operating system data can otherwise override a Python package. Record selected source/revision. Place lookup defaults to manual coordinates/timezone or a reviewed local catalogue. Optional external geocoder requires provider-policy approval, a configured identifying User-Agent, attribution, caching, aggregate rate limit and no birth-date/question transmission.

UI configuration lives in versioned application-owned tokens documented in [UI flows](09-ui-and-user-flows.md) and [interaction specification](21-ui-interaction-specification.md): colors, typography, spacing, focus styles, breakpoints, chart labels and evidence-class copy. Users can choose display preferences; they cannot disable safety labels or source validation. Theme changes must preserve contrast and evidence labels in print/export as well as the live page.

## Quotas, deletion and observability

| Proposed name | Initial value/policy | Validation and consequence |
|---|---|---|
| ANSWER_GLOBAL_CONCURRENCY | 5 demo maximum | Shared lease/reservation, not per-process counter |
| ANSWER_USER_CONCURRENCY | 1 | Release stale reservations safely |
| ANSWER_DAILY_LIMIT_PER_USER | 10 | Define UTC quota day and shared atomic counter |
| OPERATIONAL_LOG_RETENTION_DAYS | 14 | Logs exclude private content and secrets |
| ACCOUNT_PURGE_TARGET_HOURS | 24 | Real-user mode requires reliable executor |
| BACKUP_MAX_RETENTION_DAYS | 30 | Delete/restore policy includes tombstone replay |
| JOB_MAX_TRANSIENT_ATTEMPTS | 3 | Only retryable idempotent storage/index jobs |
| WORKER_HEARTBEAT_THRESHOLD | Measured and set before deployment | Missing worker disables new collection and alerts operator |
| RAW_CONTENT_TRACE_ENABLED | false | Explicit temporary diagnostic approval and expiry required |
| QUOTA_WARNING_LEVELS | 70% and 90% | No synthetic keepalive or unlimited retry on exhaustion |

Some values remain intentionally gated by measurements: database pool size, worker heartbeat threshold, encoder process/thread count, chart-engine isolation strategy and hosted memory tier. Assign them in deployment evidence before launch; do not substitute arbitrary defaults just to populate a table.

## Configuration validation cases

Require tests for production insecure cookie rejection; invalid origin/redirect; missing secret without secret echo; wrong embedding dimension/revision; rights-inactive generation; unavailable privacy executor; excessive provider timeout; remaining-budget exhaustion; duplicate quota reservation; and a model response with missing usage. A settings change that influences chart facts, retrieval or interpretation must appear in the relevant immutable manifest.

## Additional configuration policies

Use 24-hour expiry for generated export links/artifacts, purge failed-request private payloads within 24 hours, and keep private-answer response caching disabled initially. User-owned saved readings are explicit durable records, not a cross-user cache. These refinements come from the privacy dossier and must be tested across jobs and backups.

## Emergency serving controls

Add an application-wide `EDITION_SERVING_ENABLED` emergency switch defaulting to true only for approved published corpus service. Per-edition denial is represented by authoritative rights/publication state, not a separate environment variable for every title. Disabling this switch stops evidence serving and generation from those sources, while preserving account deletion and non-source administrative recovery. Audit capability changes without logging private content. See the incident runbooks for ownership and recovery tests.
