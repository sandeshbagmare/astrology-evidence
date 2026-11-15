# Data model and API contracts

Contracts below are design specifications, not implemented interfaces. All resource IDs are opaque UUIDs unless an explicit content hash is specified. All recorded instants use UTC with timezone-aware values; original local birth input remains preserved separately.

## Database model

| Entity | Required fields and invariants |
|---|---|
| User | id, Google issuer+subject unique, display name, verified-email snapshot, created_at, deletion_state; email is not identity |
| Session | hashed random token, user_id, created_at, expires_at, last_seen_at, revoked_at; never log raw token |
| Consent | user_id, notice_version, purpose, granted_at, revoked_at; record provider processing opt-in separately |
| BirthProfile | id, owner_id, name/alias, birth_date, local_time nullable, time_precision enum, earliest/latest local time nullable, place label, latitude, longitude, IANA timezone, historical offset resolution status, DST fold nullable, created_at |
| ProfileRevision | id, profile_id, immutable normalized input, created_at; edits create revisions |
| ChartSnapshot | id, owner_id, profile_revision_id, input_hash, settings, manifest, facts, unavailable_facts; unique owner+input+engine settings digest |
| SourceWork | id, canonical title, attributed author, tradition, genre; attribution uncertainty allowed |
| Edition | id, work_id, editor/translator, publisher, publication year nullable, language, artifact checksum, bibliographic completeness, rights_id, review_state |
| RightsRecord | id, evidence reference, permitted uses, jurisdictions, expiry nullable, excerpt policy, reviewer, status; status must allow serving before publication |
| Passage | id, edition_id, chapter/verse range, printed page, scan page index, bounding boxes, exact text, normalized search text, text checksum, parent_id, OCR/review confidence, language, layer_type, attributed_author_or_translator, attribution_evidence, review_state |
| CorpusGeneration | id, physical_collection_name, generation_manifest_hash, index schema, embedding model+revision, sparse config, expected/indexed passage counts, status, published_at |
| InterpretationRule | id, edition-specific passage IDs, tradition, required chart fact types, reviewed condition expression, exceptions, reviewer/version; only reviewed rules can claim machine-checked applicability |
| ReadingRequest | id, owner_id, profile_revision_id, question, idempotency_key, request_hash, status, deadline, failure_code; owner+key unique |
| Reading | id, request_id, chart_snapshot_id, structured answer, evidence manifest, model/prompt/workflow versions, created_at; immutable after publication |
| Citation | id, reading_id, passage_id, original passage hash, exact permitted displayed span, source coordinates, rights state checked on read |
| Job | id, kind, payload reference, owner or administrator scope, status, attempt_count, max_attempts, lease_owner, lease_expires_at, run_after, idempotency_key, error_code |
| Feedback | id, owner_id, reading_id, category, optional comment, created_at; never treat agreement as proof of prediction |
| AuditEvent | actor id or system, action, object id, time, outcome, request id; no raw question, birth data, token or source text |

Foreign keys and check constraints enforce ownership relationships and allowed states; application-level authorization is still required. PostgreSQL row-level security can provide defense in depth, with explicit request-scoped user identity and tested admin/worker exceptions. It does not replace endpoint authorization.

## Birth and chart contracts

**BirthInput:** calendar date, optional local time/interval, precision (`exact`, `approximate`, `unknown`), confirmed geographic coordinates and timezone, calendar convention and explicit ambiguity resolution. MVP accepts Gregorian dates from 1900-01-01 through the current date; earlier dates require a later reviewed calendar/timezone expansion. Unknown historical timezone accuracy blocks exact-time claims. Preserve a finite set of UTC candidates when a repeated local time remains unresolved; an interval envelope is conservative context and does not replace candidate evaluation. Unknown time is represented by the actual local civil-day interval under the pinned timezone data, not a guessed noon or assumed 24-hour duration.

**ChartSettings:** tradition, zodiac, ayanamsha, house_system, node_mode, ephemeris_flags, calculation_schema_version. Default values are Jyotish, sidereal, Lahiri, whole_sign, mean. Do not expose settings that have not been supported by calculation and interpretation tests.

**ChartFact:** immutable fact_id, kind, value, unit, body/point, epoch or interval, provenance and stability. Angular values are degrees in [0,360); comparisons use circular distance. Stable signs for an interval can be reported only after checking relevant boundary crossings. Ascendant/houses are unavailable for unknown time in MVP. Exact timing modules remain disabled until separately tested.

**ChartManifest:** normalized input digest, tzdata revision, resolved UTC interval, engine/package/data versions, data checksums, settings, computation timestamp. Identical manifest inputs should yield identical numeric output within the defined platform tolerance; use an implementation-safe numeric serialization.

## Retrieval contracts

**RetrievalRequest:** question, authorized user context, tradition, language preferences, chart_fact_ids, active corpus generation, maximum candidate/evidence counts. Owner context comes from the authenticated session, never from an untrusted user-supplied owner_id.

**EvidenceBundle:** ordered passages with immutable IDs, edition metadata, permitted exact excerpt, coordinates, language, parent context, retrieval score components, rights/review status, applicable reviewed rule IDs and known disagreements. Scores are internal ranking metadata. The generation prompt does not receive an unexplained prediction-confidence percentage.

Public MVP collection holds only approved shared corpus passages. Later private collections require server-derived owner filters on dense AND sparse candidates and all follow-up lookups, export and caches. No private upload feature until cross-tenant tests exist.

## Answer contract

**ReadingAnswer:** status (`supported`, `partial`, `insufficient_evidence`), concise_summary, computed_facts[], traditional_claims[], interpretation[], disagreements[], limitations[], suggested_questions[], evidence_manifest.

Each traditional claim contains claim_id, text, citation_ids[], chart_fact_ids[], applicability_status (`reviewed_rule`, `model_inference`, `not_established`) and scope/exception note. Model-inferred applicability is shown as interpretation and cannot appear as a validated rule. Inferred connections cannot turn a condition absent from the chart into a fact.

Each citation contains immutable passage ID, edition/work metadata, exact permitted span and original coordinates. Server validation verifies passage access, text matching and known coordinates; an LLM assertion that a citation is valid is insufficient. Semantic support is checked by review/evaluation; string matching alone cannot prove entailment.

When rights are withdrawn, show bibliographic reference and an unavailable-excerpt message where permitted, remove copyrighted excerpt text from served/stored reading copies as required, and keep only allowed audit metadata. Reproducibility is subordinate to deletion and rights obligations.

## HTTP interface (proposed)

| Method/path | Purpose and behavior |
|---|---|
| GET /auth/google/start | Create short-lived state/nonce and PKCE transaction; redirect |
| GET /auth/google/callback | Validate OIDC response; rotate session; safe internal redirect |
| POST /auth/logout | CSRF-protected session revocation |
| GET /api/me | Minimal authenticated identity and preferences |
| POST /api/profiles | Validate and create owned birth profile; 201 |
| GET /api/profiles | Current user's profiles only |
| PATCH /api/profiles/{id} | Create revision; optimistic version precondition; 409 on conflict |
| DELETE /api/profiles/{id} | Mark for deletion, invalidate dependent content, schedule purge; 202 |
| POST /api/charts | Owned profile revision + supported settings; return snapshot or validation problem |
| POST /api/readings | Idempotency-Key header; create request and bounded generation; 201 completed, 202 if client resumes by status |
| GET /api/reading-requests/{id} | Owned status/result reference; no other user's request existence leak |
| GET /api/readings/{id} | Owned immutable answer, rechecked excerpt rights |
| DELETE /api/readings/{id} | Remove owned reading and derived stored content; 204 or 202 if asynchronous |
| GET /api/sources/{id} | Authorized source metadata/excerpt only; pagination and excerpt limits |
| POST /api/search | Shared approved corpus search, rights filters, bounded results |
| POST /api/feedback | Owned reading feedback |
| POST /api/me/export | Create expiring authenticated export job |
| DELETE /api/me | Revoke sessions and schedule complete account purge; 202 |
| POST /api/admin/editions | Admin import record + rights review; no arbitrary URL fetch |
| POST /api/admin/editions/{id}/publish | Reviewed corpus publish job; returns job ID |
| POST /api/admin/editions/{id}/withdraw | Immediately deny serving and schedule index/cache purge |
| GET /health/live | Process liveness; no sensitive dependency data |
| GET /health/ready | Short dependency checks, generic success/failure |

JSON and HTML/HTMX endpoints reuse the same service layer; HTML routes may wrap these operations without duplicating authorization. State-changing browser requests require CSRF protection. A route is not exempt because it is named /api.

## Error and retry semantics

Problem response fields: stable code, safe message, request_id, field_errors when appropriate, retryable flag. Use 401 unauthenticated, 404 missing or unowned resources, 409 conflict, 422 invalid/ambiguous input, 429 quota, 503 dependency unavailable, 504 bounded generation deadline. Do not leak upstream body, prompts or credentials to clients.

The same owner+idempotency key and identical request hash returns the existing request. Reusing the key with different content returns 409. After an ambiguous provider timeout, mark request failed/unknown and require a deliberate new request; do not silently incur duplicate calls. Corpus jobs can retry idempotently with leases and heartbeat; a maximum of three attempts for retryable transient storage/index failures, then dead-letter review. Rights and schema errors do not retry.



## Editorial attribution refinement

Passage-level layer_type distinguishes original verse, translation, named commentary, compiler addition and generated explanation. Each layer has its own attributed author/translator and provenance evidence. A volume can contain multiple works and commentators; edition-level author metadata must not be copied blindly onto every passage. This requirement follows the publisher-record conflicts and mixed-content examples documented in the acquisition playbook.


## Persistence refinements from database and vector research

Add `QuotaBucket` and `QuotaReservation` records for atomic shared limits and conservative provider allowances, `OutboxOperation` for idempotent cross-service writes, and minimal `DeletionTombstone` records in a separately recoverable protected journal. Jobs additionally carry lease_generation, last_heartbeat_at, payload_version and cancellation_state; all completion/heartbeat updates are fenced by current lease generation. See dossier 30 for transaction and index responsibilities.

A retrieval captures PostgreSQL's authoritative generation and physical Qdrant collection name once. An alias is operational convenience, not the authority for cross-store publication. Verify passage IDs/hashes/dimensions as well as counts before publishing. Current rights are checked independently of the pinned generation, including before final output and export.

Privacy refinements: proposed export TTL is 24 hours; failed-request question/provider-content payloads purge within 24 hours; no persistent private-answer response cache. Saved owned readings remain the explicit history. Minimal operational and deletion metadata follows the documented retention purpose; no birth details in tombstones. These are product policies to implement and test, not supplier guarantees.

## Canonical execution, publication and endpoint registry

These integrated definitions supersede informal workflow labels elsewhere. `ReadingRequest.status` is exactly `admitted`, `generating`, `succeeded`, `failed`, `unknown`, or `cancelled`. `ReadingAnswer.status` remains `supported`, `partial`, or `insufficient_evidence` and exists only for a succeeded request. Workflow names such as Calculate, Retrieve and Validate are internal stages, not request states.

| Workflow outcome | Request state | Answer/status behavior |
|---|---|---|
| Valid supported answer | succeeded | supported |
| Valid qualified subset | succeeded | partial |
| Valid explanation of missing evidence | succeeded | insufficient_evidence |
| Clarification needed | failed | Safe code clarification_required; no ReadingAnswer |
| Deterministic error or known pre-send deadline | failed | Safe error/deadline_exceeded; no ReadingAnswer |
| Transport loss/deadline with uncertain provider processing | unknown | No automatic resend and no ReadingAnswer |
| Explicit user cancellation, deletion or consent revocation | cancelled | No late publication; already transmitted data cannot be recalled |

Reading requests start admitted and enter generating before provider work; pre-generation calculation/retrieval stages remain admitted with an internal stage field. Terminal transitions are fenced; no saved answer is published for failed/unknown/cancelled. A valid partial answer takes the succeeded publication path, never a failed-with-partial hybrid.

CorpusGeneration publication states are `draft`, `indexing`, `staged`, `published`, `withdrawn`, `failed`. Draft enters indexing after rights/review admission; staged means expected IDs/hashes/dimensions verified; only staged may atomically become the PostgreSQL active published generation. A published generation can be superseded by changing the active pointer while remaining available to authorized pinned requests; withdrawal immediately denies serving. Failed staging needs a new audited attempt, not an alias switch. Rights are independently live-checked for every serving path.

Provider route is fixed initially: base URL `https://freegg.app/v1`, resolved POST `https://freegg.app/v1/responses`. Reject endpoint-shaped base URLs, duplicate version prefixes, credentials/query strings and non-allowlisted destinations. Future provider configuration is a separate reviewed capability, not arbitrary runtime user input.

Additional endpoints needed by the UI:

| Method/path | Contract |
|---|---|
| GET /api/profiles/{id} | Owned profile and current revision; nondisclosing404 otherwise |
| GET /api/charts/{id} | Owned immutable chart and manifest |
| POST /api/reading-requests/{id}/cancel | CSRF/ownership checked; idempotently fence active work; terminal state unchanged if already completed |
| GET /api/jobs/{id} | Owned job status; admin corpus jobs require curator role |
| GET /api/exports/{id} | Authenticated owner-only short-lived result, current deletion/rights recheck; expired result410 |
| POST /api/places/search | Optional enabled provider; explicit submission, aggregate throttle, no private birth/question payload |

An export job returns an opaque export ID, not a public storage URL. Profile alias is optional trimmed text <=80 characters; equal aliases across users confer no shared authority. Birth dates are bounded through the server's current UTC calendar date, explicitly shown by the UI for validation consistency. All state-changing endpoints require CSRF for session-authenticated browser calls.

Canonical quote spans are zero-based Unicode code-point offsets with exclusive end into the immutable original passage; disjoint spans are individually stored and separated by a visible editorial ellipsis. Reject grapheme-splitting boundaries. Render original text with HTML escaping; normalized search text never replaces the quoted original.
