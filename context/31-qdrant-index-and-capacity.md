# Qdrant index, capacity, and publication

Status: proposed design and primary-document research, 2026-11-15. No cluster was provisioned, no books were ingested, and no performance results exist. This extends contracts 03, 07, 10, 12, 24 and 30; PostgreSQL remains authoritative. Bracketed references identify documentation facts; all operational choices are proposals.

## Concrete collection and sparse spike

Use a physical public collection `corpus_public_g_<generation>_r_<retrieval_revision>` and operational alias `corpus_public_active`. Named dense vector `dense384normalizedCosine` has size 384, float32 values normalized by the encoder, and Cosine distance. Named sparse vector `sparse_bm25_v1` uses dot-product retrieval with Qdrant IDF enabled. This is a chosen compatibility-spike candidate, not a validated production encoder. Specify a pinned BM25 sparse encoder that emits term IDs and document term-frequency/length weights without corpus IDF; reject the candidate if its actual encoder contract cannot establish that separation. Pin vocabulary/hash algorithm, collision handling, tokenization, Unicode normalization, stopwords, document-length normalization and any corpus-average-length parameter. Compare against dense-only and the native text-index BM25 alternative in document 24. Never silently switch sparse implementations.

Sparse vectors support dot product; Qdrant documents an IDF modifier from version 1.10.0 and currently describes shard-scoped statistics with optional narrower scope. These facts do not guarantee an installed release supports every current documentation example. One shard per immutable generation is the initial experiment, so corpus statistics cannot accidentally include old generations. Full-text filtering alone is not ranked BM25. Frozen term mapping must be identical for query and passage encoders. No automatic Sanskrit stemming or transliteration support is assumed. [Q1]

Collection payload: immutable `passage_id`, `edition_id`, `tradition`, `language`, `layer_type`, `generation_id`, `retrieval_revision`, `rights_revision`, `visibility=public`, `publication_state=published`, and `content_hash`. Use keyword indexes for exact filters; rights revision is a keyword revision token, not an ordering assumption. Index `passage_id` for reconciliation; retain content hash as verification metadata unless a demonstrated query needs its index. Do not store authoritative excerpt text or birth data. PostgreSQL supplies exact permitted text after reauthorization. Qdrant recommends payload indexes before ingestion; tenant indexing is a performance mechanism and cannot establish application ownership. [Q1,Q3,Q5]

## Mandatory query predicates and isolation

Compile one server-owned predicate and attach it to every dense/sparse prefetch and final query where supported. It includes exact generation/retrieval revision, public visibility, published state, declared tradition, permitted languages, and currently allowed edition/right-revision pairs. The pairs must be nested alternatives, each containing an AND: `(edition A AND revision 3) OR (edition B AND revision 8)`. Independent edition and revision lists could permit invalid cross-pairs. Missing metadata, empty allowlists, unknown traditions, and stale revisions fail closed. Clients cannot submit arbitrary Qdrant filters. Qdrant supports nested boolean filter conditions and payload indexes for efficient filtering. [Q3]

Initially retrieve 30 candidates per branch and fuse using RRF under document 24. Pin the RRF parameter rather than assuming a documentation example is the default. Qdrant supports prefetch and rank fusion; rank scores are relevance signals, never prediction probabilities. Final PostgreSQL passage fetch rechecks rights, generation and ownership; repeat for parent, exception and translation expansion. If rights change during generation, recheck before sending evidence externally and before serving excerpts. Any denied candidate is dropped, with bounded refill or abstention. A database failure cannot fall back to trusting vector payload. [Q4; proposed safeguards]

No public/private points share this collection. Private uploads remain deferred. If approved later, use a separate private collection, server-derived owner filters on both branches, parent lookups and caches, and a distinct retrieval path. A shared private collection may employ an indexed tenant field; Qdrant discourages creating very many collections solely per tenant because of collection overhead. That efficiency advice does not remove this project's public/private boundary. [Q5]

## Idempotent ingestion and cross-store publication

Use an immutable PostgreSQL manifest containing generation, physical collection, passage identities/hashes, model/sparse/schema revisions and expected point count. A deterministic UUID point ID derives from passage identity and retrieval revision; record the complete source identity to detect collisions. Retries upsert the same immutable content. A corrected passage receives a new identity/revision. PostgreSQL records job lease and batch progress; completion requires confirmed writes and reconciliation of IDs and hashes, not only equal counts.

Build in an unreferenced collection. Create payload indexes first, upload bounded batches, then enable the intended vector index settings and wait for indexing/optimizer completion. For bulk loading, evaluate disabling HNSW construction during loading and rebuilding afterward; pin exact parameter semantics from the installed release rather than conflating point counts, vector kilobytes and optimizer thresholds. Tune batch size and concurrent indexing to measured peak memory. A write acknowledgement alone is not a search-readiness gate. Run missing-ID, revision, dimension, sparse-format, filter and search checks before marking `ready`. [Q1,Q2; proposed process]

Publication needs an application protocol: Qdrant alias actions are atomic within Qdrant; they are not atomic with PostgreSQL. Store desired alias target and manifest in a durable publication intent. Verify readiness, switch alias atomically, inspect the actual target, then commit the PostgreSQL active-generation pointer using compare-and-swap under a publication lock. Every serving request pins the authoritative database generation and queries its recorded physical collection, so an alias/DB mismatch cannot redirect it to incompatible vectors. The alias is an operational convenience and readiness check, not a second authority. Retain the old collection until in-flight requests drain and the rollback retention expires. [Q2]

Crash before alias switch: resume intent. Crash after switch but before DB commit: serving stays on the old physical collection; reconciler either completes the verified intent or restores alias. DB active but alias stale: pin the DB collection and repair alias after readiness verification. Unknown collection, incomplete manifest, or missing points: fail closed, rebuild or explicitly roll back the DB pointer; never activate by count alone. Concurrent publishers must serialize; stale workers cannot commit after losing their lease.

Withdrawal updates database rights first, blocks serving and invalidates excerpt caches, then asynchronously updates/deletes points in active, staged and retained collections. An unchanged old payload might still enter candidate retrieval during propagation; final DB checks prohibit using or exposing it. Refresh the allowlist on each request and bound cache validity with rights revision invalidation. Audit index cleanup separately from immediate access denial.

## Capacity model: estimates are not fit claims

Dense arithmetic is exact for float32 values; every other number below is an explicit hypothetical sizing input, excluding implementation overhead.

| Points | Dense bytes, MB | Payload assumption: 1 KiB/point, MB | Sparse assumption: 80 nonzeros x 8 bytes, MB |
|---:|---:|---:|---:|
| 10,000 | 15.36 | 10.24 | 6.40 |
| 100,000 | 153.60 | 102.40 | 64.00 |
| 600,000 | 921.60 | 614.40 | 384.00 |

Use decimal MB; raw sparse pairs exclude posting-list and dictionary overhead. Do not sum these into predicted RSS. Qdrant's cloud guidance gives a typical HNSW overhead estimate of 20–30%, but actual graph size depends on configuration, segment structure and filter-aware links. Payload indexes, ID tracking, WAL, deletions and optimizer copies add costs. Measure SSD provisioned/used space separately from RSS, page cache and resident mmap pages. On-disk/mmap storage reduces eager residency, not the workload's need for cache or fast random I/O. Two generations, snapshots and rebuild workspace may coexist. Cloud guidance specifically warns that restore/migration needs substantial additional room, including approximately twice source disk for target operations. [Q1,Q7]

Benchmark actual 10k, 100k, and 600k datasets with representative languages, edition cardinality, term distributions and payload lengths. Synthetic records test scale, while rights-cleared representative passages test quality. Record steady and peak RAM, cache, SSD bytes, WAL, ingestion rate, HNSW/optimizer rebuild peaks, snapshot time/size and restore time. Include encoder loading, batch buffers and multiple application processes separately from Qdrant. No "fits 1 GB" conclusion follows from vector arithmetic.

Compare float32 baseline with scalar int8 plus full-precision rescoring; product or binary quantization are later candidates requiring their own compatibility and quality gates. Compression factors describe vector representation, not whole-service memory savings. Record original-vector residency, rescoring I/O and sparse/payload overhead. Any memory win that loses necessary exceptions or multilingual recall fails the document 24 gate. Qdrant documents quantization as a memory/performance tradeoff; select only after measured recall and latency. [Q6]

## Experiments, restore and service tier gates

At each size measure cold/warm p50/p95/p99 retrieval latency, timeouts, throughput, ingestion contention and peak resources at concurrency 1 and a declared beta load. Sweep filter selectivity (100%, 10%, 1%, single edition), HNSW search effort, payload indexing, disk placement and quantization individually. Compare approximate results with exact eligible-vector search where supported, plus editorial Recall@10, exception recall and per-language results. Test adversarial edition/revision cross-pairs, absent fields, stale snapshots, withdrawn editions, mixed traditions and attempted private-owner injection. Acceptance requires zero unauthorized text/IDs exposed, including through expansion, logs and debug responses.

Qdrant Cloud currently documents free resources of 1 GB RAM, 0.5 vCPU, 4 GB disk and one node; upgrades have downtime, resources are not dedicated, snapshots/restores are manual API operations, and inactivity may suspend after a week and delete after four weeks. Its approximate vector-count marketing is not a guarantee for this payload-rich hybrid workload. Production requires a funded availability/replication plan, monitoring, backups and measured recovery targets; verify entitlements and prices at provisioning. [Q7]

Restore a snapshot into an isolated collection, verify compatible version/topology, replay the current PostgreSQL rights/deletion ledger, validate manifest and payload revisions, rebuild indexes if necessary, then publish through the same protocol. A Qdrant snapshot cannot replace PostgreSQL backups or prove current excerpt rights. Test monthly against the proposed recovery targets; rebuilding from canonical passages and pinned embeddings is the alternative when a snapshot is incompatible. Snapshot procedures vary by deployment and must be checked for the selected cloud or self-hosted release. [Q8]

## Primary sources and verification limits

Read on 2026-11-15 using official Qdrant pages. HTTP fetches succeeded; API behavior was not exercised. Version/client pins, sparse analyzer behavior, optimizer parameters, snapshot scope and production resource sizing remain implementation gates.

- Q1 Indexing: `https://qdrant.tech/documentation/concepts/indexing/`
- Q2 Collections and atomic aliases: `https://qdrant.tech/documentation/concepts/collections/`
- Q3 Filtering: `https://qdrant.tech/documentation/concepts/filtering/`
- Q4 Hybrid queries: `https://qdrant.tech/documentation/concepts/hybrid-queries/`
- Q5 Multitenancy: `https://qdrant.tech/documentation/guides/multiple-partitions/`
- Q6 Quantization: `https://qdrant.tech/documentation/guides/quantization/`
- Q7 Cloud resources and limitations: `https://qdrant.tech/documentation/cloud/create-cluster/`
- Q8 Snapshots: `https://qdrant.tech/documentation/snapshots/`

