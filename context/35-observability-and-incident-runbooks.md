# Observability and incident runbooks

**Status:** proposed operating design, researched 2026-11-15. This document defines instrumentation and response procedures; no telemetry pipeline or alert has been deployed. Thresholds are launch defaults to validate in local, demonstration, and production load tests.

## Privacy boundary and telemetry contract

Observability must explain whether a request was admitted, where time was spent, and why it failed without becoming a second copy of a user’s chart, question, source text, or answer. Structured logs, traces, and metrics therefore carry opaque `request_id` and `trace_id`, deployment and service identity, route template, operation name, status class, duration, outcome code, retry/attempt number, provider route class, corpus generation, model revision, and redaction decision. They never carry prompt text, birth date/time/place, profile IDs, email, session cookies, access tokens, API keys, raw provider bodies, retrieved excerpts, question text, answer text, source titles, or unrestricted URLs. IDs are short-lived opaque correlation values; a user or profile identifier is not a metric label.

Propagate W3C trace context and `request_id` across internal FastAPI, calculation, retrieval, PostgreSQL, Qdrant, storage and worker boundaries. Instrument the provider client internally without forwarding application trace identifiers to the external supplier unless separately reviewed. A worker span links to the enqueueing trace through a durable correlation field, while logs include the current trace/span IDs. Do not trust a client-supplied request ID: accept only a validated format or replace it, and record whether replacement occurred. Return the opaque request ID to the browser for support. Provider request IDs may be stored in a restricted operational record, but never in public errors.

Use OpenTelemetry semantic conventions for HTTP spans and duration metrics. The stable `http.server.request.duration` and `http.client.request.duration` instruments use seconds and low-cardinality route attributes; dynamic path values must remain placeholders. Prometheus naming should use one quantity and base units, with `_seconds`, `_bytes`, and `_total` suffixes. Prometheus specifically warns against labels such as user IDs or email addresses and recommends investigating metrics that exceed roughly 100 series; OpenTelemetry likewise requires `http.route` to be low cardinality. [O1][P1][P2]

Every log event has `timestamp`, `severity`, `event_name`, `service`, `environment`, `version`, `request_id`, `trace_id`, `span_id` where available, and a bounded `reason_code`. Keep error messages from exception text through an allowlisted classifier. Hashes are keyed or truncated only for deduplication and must not be reversible identifiers. Redaction tests seed fake birth data, prompts, source excerpts, tokens, cookies, and provider payloads, then assert these markers are absent from application, reverse-proxy, database, worker, trace-exporter, and crash logs. Raw SDK or HTTP body tracing is disabled; a temporary diagnostic capture requires an explicit, expiring operator change and separate access review.

## Metrics, dimensions, and SLOs

Use bounded dimensions: `environment` (local/demo/staging/prod), `route` (template), `operation` (admit/calculate/retrieve/generate/validate/delete/export), `outcome` (success/abstain/rejected/timeout/error), `provider_route` (direct/gateway/disabled), `error_class`, `job_kind`, and `rights_state`. Avoid chart settings, language, edition, model alias, request ID, profile, account, IP, question topic, or exception message as labels unless reduced to a reviewed finite set. Keep ordinary metric families below ten series per dimension and aggregate high-cardinality analysis in logs or sampled traces.

Core metrics:

- `http.server.request.duration` and its exported histogram count, by route and status class.
- `astrology_answer_duration_seconds` histogram by operation and outcome; total deadline breaches and citation-validation rejections.
- `astrology_provider_requests_total`, `astrology_provider_errors_total`, and `astrology_provider_duration_seconds` by route class and error class; never by model request ID.
- `astrology_retrieval_duration_seconds`, `astrology_retrieval_no_evidence_total`, and `astrology_citation_rejections_total`.
- `astrology_queue_oldest_age_seconds`, `astrology_jobs_in_flight`, `astrology_jobs_failed_total`, and `astrology_worker_heartbeat_age_seconds` by bounded job kind.
- `astrology_memory_working_set_bytes`, `astrology_oom_events_total`, database pool saturation, Qdrant request errors, and `astrology_rights_withdrawal_backlog`.
- `astrology_quota_reserved_ratio` and `astrology_quota_consumed_ratio` by quota scope (`global`, `user_daily`, `provider_budget`), never by user.
- `astrology_deletion_backlog` and oldest deletion age, plus kill-switch state gauges for `AI_ENABLED`, `PROFILE_STORAGE_ENABLED`, and `EDITION_SERVING_ENABLED`.

Local mode is a developer diagnostic: no availability SLO, but answer p95 under 30 seconds with a 150-second hard deadline, no unbounded memory growth, and zero redaction failures. Demonstration mode targets 99% successful health checks during declared hours, answer p95 under 45 seconds, provider error rate under 5%, and deletion backlog age under 1 hour; real-user collection remains disabled if a reliable purge executor is absent. Production targets monthly 99.5% successful non-admin HTTP requests, 99% of accepted answers completing within 150 seconds, retrieval p95 under 2 seconds, citation rejection under 2% of generated attempts, and account purge completion within 24 hours. These are service objectives, not claims of current performance. Burn-rate alerts should page only when an objective is being materially consumed; dashboards show numerator, denominator, and excluded maintenance windows.

Quota and resource alerts fire at 70% (warning) and 90% (critical) of configured daily/provider/storage limits. Alert on queue oldest age above 5 minutes warning and 15 minutes critical for privacy jobs; worker heartbeat older than two lease intervals; memory above 75% warning and 90% critical; OOM immediately; deletion backlog above 10 items or oldest age above 1 hour warning, 24 hours critical; rights-withdrawal backlog older than 5 minutes warning and 30 minutes critical. Tune after baseline measurements and keep alert labels bounded.

## Incident runbooks

**Provider route returns 410 or incompatible responses.** Confirm the route-class error metric and inspect a redacted provider status event. Disable that route with the provider kill switch, preserve already admitted requests as failed or unknown according to transmission state, and do not silently retry through another supplier. Set `AI_ENABLED=false` if no approved route remains; chart and library features continue. Validate the Responses endpoint contract in staging, then restore traffic gradually with a canary and compare latency, schema, and usage fields.

**Leaked secret or credential.** Revoke and rotate the secret immediately, disable the affected integration, and search restricted logs for only metadata fingerprints. Never paste the value into tickets or incident channels. Determine exposure window and recipients, invalidate provider sessions if applicable, and rerun redaction tests before re-enabling. The credential disclosed during planning must be rotated before any deployment.

**Cross-user access suspicion.** Stop affected reads/writes and disable profile collection and answer generation. Revoke sessions, preserve minimal access logs, identify accounts, object classes, and time window, and test ownership checks across API, polling, exports, caches, PostgreSQL, and Qdrant. Notify the privacy owner for jurisdiction-specific assessment. Rebuild or invalidate caches and reopen only after adversarial tests show no cross-owner response.

**Stale or poisoned vector generation.** Pin serving to the last verified PostgreSQL generation, freeze publication, and deny candidates whose rights/revision checks fail. Compare manifest hashes, point IDs, dimensions, and generation pointers; rebuild in an isolated collection and run retrieval, rights, and citation tests before atomic publication. Never repair by trusting vector payload text.

**Rights withdrawal backlog.** Commit authoritative denial first, invalidate excerpt and answer caches, cancel queued exports, then process vector/object deletion jobs. Alert at five and 30 minutes; if deletion workers are down, set `EDITION_SERVING_ENABLED=false` for affected editions and keep the backlog prioritized. Recheck rights immediately before every excerpt response. Already downloaded files cannot be recalled; record that boundary.

**Worker down, memory OOM, or quota exhaustion.** Stop admitting ingestion or profile collection when the worker heartbeat or purge SLO is at risk. For OOM, lower concurrency and batch sizes, capture a heap/resource profile without user content, and restart from a fenced lease. For quota exhaustion, reject new generation with a clear retry-later state; do not run synthetic keepalives or unbounded retries. Restore only after health, backlog age, memory headroom, and idempotency checks pass.

**Rollback and restore.** Freeze writes requiring the affected release, switch to the last compatible application image and corpus generation, and keep the failed generation unreferenced. Restore PostgreSQL and Qdrant into isolation, replay deletion and rights tombstones, verify manifests and ownership, then publish through the normal compare-and-swap protocol. Reconcile unknown provider requests conservatively; never replay automatically. Document RPO/RTO evidence after the drill.

## Kill switches and release checks

`AI_ENABLED` disables external generation while preserving deterministic charts and book lookup. `PROFILE_STORAGE_ENABLED` blocks new birth-profile writes and exports while allowing deletion. `EDITION_SERVING_ENABLED` (globally or by rights generation) denies excerpts and evidence use during withdrawal or corruption. Each switch is audited with actor, reason, expiry, and resulting capability; startup fails closed for unsafe production combinations. Before launch, verify trace/request propagation, redaction across every sink, bounded metric cardinality, alert delivery at 70/90%, synthetic provider 410 handling, cross-user canaries, stale-vector rollback, worker fencing, OOM recovery, and deletion while web and workstation processes are stopped.

Additional operational proposals: retain metadata logs and traces for at most 14 days. Reserve the 150-second deadline as five seconds admission/calculation, five retrieval, a proposed 120-second total provider-time allocation shared across both calls (stricter than the per-call maximum; benchmark before adopting), and 20 validation/persistence/response. Unknown provider outcomes require review and never automatic resend. Provider timing is unmeasured. Monitor unknown outcomes separately. Keep telemetry correlation internal: no user baggage or internal request IDs to the provider without explicit review. A confirmed rights-serving violation or cross-user response pages immediately regardless of volume. The edition serving switch is a proposed addition to document 43; per-edition denial remains authoritative PostgreSQL rights state. Profile storage uses the existing PROFILE_STORAGE_ENABLED setting.

## Primary sources

- [O1: OpenTelemetry HTTP metrics semantic conventions](https://opentelemetry.io/docs/specs/semconv/http/http-metrics/) — stable HTTP duration names, seconds, route and attribute guidance; inspected 2026-11-15.
- [O2: OpenTelemetry naming](https://opentelemetry.io/docs/specs/semconv/general/naming/) — duration naming and client/server metric patterns; inspected 2026-11-15.
- [O3: OpenTelemetry semantic conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/) — common names across traces, metrics and logs; inspected 2026-11-15.
- [P1: Prometheus metric and label naming](https://prometheus.io/docs/practices/naming/) — base units, suffixes, and prohibition on unbounded labels; inspected 2026-11-15.
- [P2: Prometheus instrumentation](https://prometheus.io/docs/practices/instrumentation/) — cardinality guidance and queue latency instrumentation; inspected 2026-11-15.
- [P3: Prometheus Zen](https://prometheus.io/docs/practices/the_zen/) — measure user-visible latency/availability and control label cardinality; inspected 2026-11-15.
- [O4: OpenTelemetry handling sensitive data](https://opentelemetry.io/docs/security/handling-sensitive-data/) — minimize collection and apply collector filtering/redaction; inspected 2026-11-15.
- [S1: Google SRE alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) — multiwindow burn-rate alerting pattern; inspected 2026-11-15.

All thresholds and SLOs above are proposed acceptance targets. They require measured validation in each operating mode and must be updated in [16 progress and open decisions](16-progress-and-open-decisions.md) when evidence changes them.



