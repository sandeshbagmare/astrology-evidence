# Deployment, capacity, and operating cost

Status: proposed plan. Official pages were retrieved directly on 2026-11-15; quotas are a snapshot, not a guarantee. No service account, deployment, domain, payment, or provider call was created.

## Operating modes

| Mode | Components | Use | Constraint |
|---|---|---|---|
| Local | FastAPI UI/API, PostgreSQL, Qdrant, embedding encoder and worker | Build, ingest, evaluate | Computer must run; external LLM has availability/data/cost implications |
| Free demonstration | Render web, Neon PostgreSQL, Qdrant Cloud; local administrator ingestion | Invitation-only small curated corpus | Sleeps, quotas; encoder must pass host memory tests |
| Production | Paid always-on Python app/worker, managed PostgreSQL, Qdrant, durable object storage | Public availability and regular ingestion | Budget based on measured use; no permanent-free promise |

Keep one codebase with environment-specific configuration. Docker packaging is proposed, not created. Use PostgreSQL durable jobs with leases/idempotency; add Redis/Celery only when measured demand warrants. Demo handles bounded answers in its web process; corpus ingestion runs locally. Production adds a worker. A web background task is never treated as durable execution.

## Current free-service facts

| Service | Observed official terms | Consequence |
|---|---|---|
| Render free web | Sleeps after 15 minutes without inbound traffic; 750 instance hours/workspace/month; ephemeral local filesystem [D1] | Cold starts; no durable books/database on app disk; no always-running worker assumption |
| Render free Postgres | 1 GB; expires 30 days after creation [D1] | Excluded from durable demo database choice |
| Neon Free | 100 CU-hours, 1 GB storage, 5 GB network transfer/project/month; compute suspends on usage exhaustion [D2] | Pooled connections, idle cleanup, quota alerts; verify storage-limit behavior at provisioning |
| Qdrant Cloud free | 1 GB RAM, 0.5 vCPU, 4 GB disk, 1 node; suspends after 1 week unused, can be deleted after 4 weeks inactivity [D3] | Keep exports/rebuild instructions; free cluster is not a backup or uptime commitment |
| FreeGG | Availability, rates, data handling, context and quotas unverified | Treat as external dependency; enforce application quotas regardless of the name |

Avoid synthetic keepalives to bypass free-tier intent. Show status/reactivation guidance when the demonstration is unavailable. Verify terms/limits again at provisioning.

## Free-demo feasibility gate

Semantic queries still need a query encoder; precomputed document vectors do not remove it. Default: `intfloat/multilingual-e5-small`, optionally a validated quantized CPU export. Pin model revision, runtime and tokenizer. Model card specifications are 384 dimensions, 512-token input limit and query/passage prefixes [D4].

Gate: boot + encoder initialization + chart + retrieval + concurrent answer stays below 75% of the chosen memory limit, without OOM or blocking the event loop. Measure peak resident memory, warm/cold latency and image size. If a free tier fails, keep the complete demo local or fund a larger app instance. An external embedding endpoint needs its own price/privacy assessment; it is not assumed free. Do not silently remove semantic retrieval to claim deployment.

OCR, PDF parsing, large embedding batches, corpus verification and reindexing run locally in demo mode. Upload only rights-cleared chunks, metadata and vectors. No public book-upload UI. Keep approved artifacts locally with a separate backup; required snippets live persistently with rights controls. Hosted ingestion/full scan viewing requires durable object storage.

## Capacity estimates

One 384-dimensional float32 vector contains 1,536 raw bytes. 100,000 vectors need approximately 154 MB decimal before HNSW, payload, indexes, replication, snapshots and overhead; 1,000,000 need approximately 1.54 GB raw. Actual RAM/disk and ingestion peaks require representative benchmarks.

Measure usable pages, chunks, tokens, OCR quality, vectors, source bytes and ingestion time; book count alone is misleading. Begin with 3–5 rights-cleared editions and a 10,000-chunk benchmark; evaluate 100,000 before acquiring hundreds of books. A thousand-book corpus is an expansion goal, not a free-tier assumption.

## Environments and release

1. Local: synthetic birth records, approved excerpts, deterministic chart fixtures.
2. Staging: separate OAuth client/callback, database and Qdrant collection; test users only.
3. Production: HTTPS, approved privacy notice/provider contract, redacted errors, budgets, backups and operational owner.

Required release checks: pinned image/dependencies; migration rehearsal; chart regressions; retrieval quality; Google login/ownership tests; Responses contract; readiness checks; rollback and restore. Do not start migrations from every web process. Versioned corpus collections and an alias allow independent index rollback.

## Budgets and recovery

Monthly cost = app + worker + PostgreSQL + Qdrant + object storage/egress + LLM + optional geocoding + domain. LLM estimate uses measured questions × input/output tokens × verified rates, plus billable retries/failures. No FreeGG rate is assumed. Enforce request/token budgets in the app and fail closed on exhaustion; supplier billing controls supplement this.

Demo quotas are in [security](08-authentication-and-security.md). Track latency, provider errors, no-evidence results, citation-validator rejection, peak memory, DB connections and corpus growth. Alert at 70% and 90% of known quotas; do not retry endlessly when exhausted.

Production backup target: daily encrypted PostgreSQL backup, versioned corpus manifests and Qdrant snapshots/exports; 7 daily and 4 weekly copies within the deletion retention contract. Test restore monthly. Qdrant can also be rebuilt from canonical chunks and pinned embeddings; measure recovery time. Proposed production RPO 24 hours/RTO 4 hours requires a successful drill and funded infrastructure. Free demo has no availability or recovery guarantee.

## Sources

- [D1: Render free services](https://render.com/docs/free) — HTTP 200, 2026-11-15.
- [D2: Neon pricing](https://neon.com/pricing) — HTTP 200, 2026-11-15. Older material can show different quotas; check current dashboard at provisioning.
- [D3: Qdrant free cluster](https://qdrant.tech/documentation/cloud/create-cluster/) — HTTP 200, 2026-11-15.
- [D4: multilingual-e5-small model card](https://huggingface.co/intfloat/multilingual-e5-small) — HTTP 200, 2026-11-15; serving revision/runtime must be pinned later.


## Free-demo privacy job execution gate

A sleeping free web service and an occasionally running ingestion workstation cannot guarantee a 24-hour deletion deadline. The free-demo label does not waive privacy requirements. Before inviting anyone, choose one of two explicit modes: (a) operator-attended demonstration with synthetic records only, no real-user collection; or (b) real-user beta with a reliably scheduled executor, hosted worker or continuously available operator machine whose uptime and retry/alert behavior have been demonstrated. Mode (b) may require paid compute and therefore is not promised as zero-cost.

Deletion revokes sessions and denies reads synchronously in the web transaction. Durable purge/export jobs still need the executor. If a worker heartbeat exceeds its allowed delay, disable new exports and profile collection, alert the operator, and recover queued deletion jobs before restoring collection. Rights withdrawal denies serving immediately through authoritative database checks even if vector cleanup is delayed. The acceptance test stops the web process and workstation, creates an already-queued privacy job, and proves that the chosen independent executor meets the deadline. If it cannot, do not advertise the real-user free demo.

## Expanded host comparison

[34 Hosting options and budget model](34-hosting-options-and-budget-model.md) compares seven inspected offerings, distinguishes subscription eligibility from free hardware, tests network/dependency fit conceptually and provides explicitly hypothetical cost calculations. The initial free-demo choice is a candidate only. Recheck service prices/quotas and measure memory/connectivity before provisioning. Model-provider spend is unknown rather than assumed zero.

## Operations dossier

[35 Observability and incident runbooks](35-observability-and-incident-runbooks.md) defines privacy-safe metrics, proposed SLOs, bounded alert dimensions, recovery steps and kill switches. Proposed latency/availability objectives require measurements and an operational owner; they are not uptime promises for a sleeping free demo.
