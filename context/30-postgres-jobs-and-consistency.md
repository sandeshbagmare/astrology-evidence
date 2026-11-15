# PostgreSQL jobs and consistency

Prepared 2026-11-15. Proposed design extending documents 03, 08, 10, 12, 15 and 43; no schema, migration or application tests have run. PostgreSQL remains authoritative; Qdrant is rebuildable. Redis is deferred until measured contention or scheduling needs justify it. Defaults require implementation tests and measurements.

## Transaction and ownership boundaries

Use short Read Committed transactions with explicit row locks, uniqueness constraints and conditional state transitions. PostgreSQL Read Committed uses statement snapshots; a sequence of ordinary reads is not an atomic quota or ownership decision. Serializable can protect complex invariants, but requires whole-transaction retries; never put an external provider call inside a transaction that might be retried. [P3]

Request admission atomically authorizes the active account and immutable profile revision, establishes owner-plus-idempotency-key uniqueness, compares a canonical request hash, and reserves quota. Hash versioned normalized question, revision, settings and requested options; retain the hash algorithm/canonicalization version. Same owner/key/hash returns the existing request, including failed/unknown; a changed hash returns 409. The key cannot authorize another owner's resource. One Reading per request prevents duplicate publication, without exactly-once external execution.

Do network work after committing admission. A short completion transaction rechecks active ownership, cancellation, deadline, request execution token and current source rights before publishing. A disconnected browser polls the persisted request. Proposed states are admitted, generating, succeeded, failed, unknown and cancelled. A crash or ambiguous transmission after sending marks unknown after the deadline; no automatic resend. Deliberate retry uses a new key, a new reservation and an explicit warning about possible duplicate processing. Persisting send intent before transmission can conservatively classify an unsent request as unknown; this is preferable to silently duplicating a potentially billable call.

## Leased queue

Workers claim eligible queued rows in a short transaction using row locking with SKIP LOCKED, ordered by priority, run_after and ID, then commit a lease before processing. PostgreSQL explicitly describes SKIP LOCKED as useful for queues but unsuitable for a consistent general-purpose view; table-level locks can still block it. Monitor oldest eligible job age because ordering does not guarantee fairness. [P1]

Store lease_owner, monotonically increasing lease_generation, lease_expires_at, last_heartbeat_at, attempt_count, payload version and cancellation state. Heartbeat, checkpoint and completion updates must match the current owner/generation and an unexpired lease, using database time. An expired worker cannot renew or finalize; a reclaimed job receives a new generation. External writes use deterministic operation IDs and immutable destinations because database fencing alone cannot stop an old network request.

Proposed starting values: claim one job; lease 120 seconds; heartbeat every 30 seconds; reclaim scans every 30 seconds; poll with jitter between one and five seconds. Benchmark these before adoption, chunk operations to bounded durations, and distinguish job heartbeats from executor-health thresholds still gated in document 43. Pause side effects when renewal fails. Priority favors privacy deletion, then exports, then ingestion, with an aging rule to prevent starvation. No transaction spans OCR, embeddings, object upload or Qdrant calls.

Retry only idempotent storage/index operations with classified transient failures: three total attempts, delays starting at 5 then 20 seconds with jitter, capped at 60 seconds. Exhaustion enters dead-letter review; invalid rights, malformed payloads and schema mismatches fail immediately. Manual requeue creates an audited execution record and does not bypass current rights. Provider calls retain zero automatic retries. A process-local timer or sleeping web host is not an executor guarantee: real-user collection requires independently demonstrated privacy-job execution while web and ingestion workstation are stopped.

Transaction-level advisory locks may serialize a short reconciliation or publication decision when no suitable row exists. Prefer a dedicated publication row otherwise. Session advisory locks survive rollback and persist until released or session termination, making them unsuitable for ordinary pooled request paths. Advisory locks only work when every writer cooperates; they cannot replace constraints or durable leases. [P2]

## Schema and index responsibilities

Proposed migration responsibilities:

| Record | Database responsibility and proposed index |
|---|---|
| Owned profile/revision/chart | Composite owner/resource references prevent cross-owner joins; owner plus creation/ID supports listing and purge |
| ReadingRequest / Reading | Unique owner/key, non-null request hash; unique reading request reference; deadline index for unfinished requests |
| Job | Nonnegative bounded attempts and valid lease-field combinations; unique non-null scope/kind/operation key; partial ready index on priority/run_after/ID; separate leased-expiry index |
| QuotaReservation / QuotaBucket | Unique request reservation and bucket scope/period; nonnegative reserved/consumed values; state and deadline indexes for reconciliation |
| OutboxOperation | Unique destination/action/resource/version; pending/run_after index; immutable payload reference and expected content hash |
| CorpusGeneration / membership | Unique generation/passage membership and expected manifest hash; indexed publication status; one authoritative active-generation pointer |
| DeletionTombstone | Unique opaque subject/resource and deletion generation; indexed incomplete targets and timestamp; no birth details or question text |

Use foreign keys, non-null fields and uniqueness for relationships. PostgreSQL CHECK constraints cannot safely enforce cross-row conditions; a check on the current time also cannot continuously enforce expiration. Foreign keys do not automatically create indexes on referencing columns, so explicitly review deletion and join paths. Scope keys must not rely on nullable uniqueness behavior for administrator jobs. [P4]

Retain passage attribution fields from document 12 and Unicode-codepoint quote offsets from document 26; deleting or replacing a passage must not silently relocate a quote. Exclude source content from jobs/logs. Measure queue bloat, vacuum, latency and index growth.

## Shared quota reservations

In the admission transaction, lock existing global and user quota bucket rows in a consistent order, create missing UTC-day buckets safely, then reserve one question and conservative provider allowance. Enforce global concurrency five, user concurrency one and ten questions per UTC day across all web processes. Reserve both possible generation calls within the 150-second answer deadline; repair consumes the same reservation. Monetary allowance requires verified pricing.

Count admitted questions against the daily allowance; do not charge a duplicate idempotency replay again. Release unused provider allowance only on proven pre-send failure or reconciled usage. Missing usage and uncertain calls retain conservative consumption. Concurrency slots can be released after the request's fenced terminal transition/deadline, but external processing might continue: the cap limits application-managed operations, not provably all provider-side computation. A late response cannot publish after ownership or execution state changes. Reconciliation must atomically settle each reservation once, never decrement counters twice or allow expired leases to publish.

## Two-system publication and withdrawal

A PostgreSQL transaction stores canonical passages, a staging generation manifest and outbox operations together. An executor writes immutable generation-specific vector IDs, records acknowledgments, and verifies expected IDs, hashes, dimensions and count. Counts alone cannot establish completeness. Reconciliation compares pending operations with observed destination state after crashes and repeats safe writes. No cross-system transaction is assumed.

After complete verification, lock the publication pointer, recheck rights and review state, and activate the generation in PostgreSQL. Query a concrete generation/collection from that pointer; do not require a separately switched Qdrant alias to be atomic with PostgreSQL. Capture generation once per retrieval and persist it in the evidence manifest. Retain previous generations while authorized in-flight requests reference them; recheck live rights regardless of that pinned generation.

Withdrawal first commits authoritative denial plus purge outbox entries. Every excerpt, cached reading, export and final answer checks current rights; purge later removes vectors, objects and prohibited stored spans. Late indexing cannot reactivate a withdrawn generation. Reconciliation schedules another deletion if a stale write reappears. Database unavailability fails closed for protected serving. Already transmitted material cannot be recalled; the immediate-denial boundary is successful withdrawal commit and subsequent authorization checks, including a fresh check before returning buffered content.

## Tenant isolation and async connections

Use server-derived owner identity and endpoint authorization plus RLS on private tables. PostgreSQL defaults to denial when RLS is enabled without an applicable policy, but table owners normally bypass it, and superusers/BYPASSRLS roles always bypass it. Use a separate migration owner, restricted runtime role and explicit worker permissions; review FORCE ROW LEVEL SECURITY where appropriate. Review both row visibility and write checks, permissive-policy OR composition, and constraint-error information leaks. Policies consulting mutable authorization tables need special race analysis. [P5]

Set identity transaction-locally before private statements; missing identity denies access. SET LOCAL ends at commit or rollback, unlike session settings that can leak across reused connections. Never accept an identity-setting value directly from a request parameter. Pool reuse tests must include cancellation and failed transactions; every subsequent transaction reinstalls identity. Worker scope is explicit and cannot inherit the last browser user. [P6]

SQLAlchemy AsyncSession is mutable transaction state and requires a separate session per concurrent task. Use bounded session contexts, explicit loading, rollback on failure and close on cancellation; do not share a request session with heartbeat tasks. Release connections during external work. Pool sizing remains a measured deployment decision with headroom for privacy jobs and migrations. [P7]

## Recovery and operations

Run migrations through one controlled deployment job: expand compatible structures, backfill in bounded resumable batches, validate, deploy readers/writers, then remove obsolete structures after rollback compatibility expires. Set bounded lock waits and rehearse on representative data. Keep serving only schema-compatible releases.

Daily encrypted backups, a maximum 30-day retention, monthly restore drills and proposed RPO 24 hours/RTO four hours follow document 10. PostgreSQL distinguishes dumps, filesystem backups and continuous archiving; select a host-supported method and prove restore rather than assuming snapshots include external objects or encryption keys. [P8] Keep deletion/withdrawal tombstones in a separately recoverable protected journal newer than the restored backup. Before serving, replay them, revoke sessions, reconcile uncertain requests and outbox entries, and rebuild/verify indexes. Retain minimal tombstones until every applicable backup expires, with journal retention separately reviewed.

Account deletion immediately denies access and cancels publication; purge target is 24 hours, logs 14 days. Rotate encryption keys by recording key version, encrypting new writes with the new key and rewrapping existing data resumably. Keep required old keys until authorized backup recovery no longer needs them; test revoked-secret replacement. Rotation is not evidence of deletion. Restore and key-loss drills must cover unreadable ciphertext and deleted-account resurrection.

## Failure-injection acceptance targets

None of these tests has been executed.

| Injection | Required observation |
|---|---|
| Two workers claim one job | One current lease; no duplicate canonical result |
| Pause worker beyond lease, then resume | Old heartbeat/completion rejected |
| Crash after external index write | Replay converges on same IDs/hashes |
| Crash after admission commit | Durable request/reservation recovered; no silent provider replay |
| Drop response after provider accepts | Unknown state; conservative usage retained |
| Concurrent identical idempotency submissions | One request/reservation; same result reference |
| Reuse key with changed question | 409; original immutable |
| Race quota requests across processes | No committed bucket exceeds configured admission limit |
| Lose usage or duplicate settlement | Conservative allowance; no double release |
| Kill indexing midway | Staging generation never serves |
| Crash around publication commit | Either previous or complete new generation serves |
| Withdraw rights during generation | Completion cannot expose withdrawn excerpts |
| Late vector write after purge | Denied reads persist; reconciliation deletes residue |
| Delete account during export | Export inaccessible; completion cannot resurrect data |
| Reuse pooled connection for another user | No prior identity or private ORM state survives |
| Run with missing identity or worker role | Default denial or narrowly authorized worker operation |
| Inject deadlock/serialization failure | Bounded transaction retry; no repeated external call |
| Restore backup predating deletion | Journal replay precedes traffic; records remain unavailable |
| Stop web and workstation | Independent executor satisfies privacy target or real-user mode stays disabled |

## Primary sources inspected

Accessed 2026-11-15. PostgreSQL pages resolved to version 18; SQLAlchemy reference is explicitly the 2.0 documentation, not a claim about the latest release. Pin the actual deployment versions and repeat compatibility checks.

- P1: PostgreSQL SELECT, locking clause — `https://www.postgresql.org/docs/current/sql-select.html`
- P2: PostgreSQL explicit locking, row/deadlock/advisory sections — `https://www.postgresql.org/docs/current/explicit-locking.html`
- P3: PostgreSQL transaction isolation — `https://www.postgresql.org/docs/current/transaction-iso.html`
- P4: PostgreSQL constraints — `https://www.postgresql.org/docs/current/ddl-constraints.html`
- P5: PostgreSQL row security policies — `https://www.postgresql.org/docs/current/ddl-rowsecurity.html`
- P6: PostgreSQL SET — `https://www.postgresql.org/docs/current/sql-set.html`
- P7: SQLAlchemy asynchronous I/O, concurrent sessions and implicit I/O — `https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html`
- P8: PostgreSQL backup and restore — `https://www.postgresql.org/docs/current/backup.html`

