# Ingestion, chunking and retrieval

Status: proposed engineering specification, 2026-11-15; no corpus or embedding benchmark exists yet. Read [corpus rights](06-corpus-and-sources.md) and [calculation contract](05-astrology-domain.md) first.

## Pipeline and ownership

```mermaid
flowchart LR
 A[Rights-cleared edition] --> B[Immutable original and checksum]
 B --> C[Text extraction or OCR]
 C --> D[Page and verse alignment]
 D --> E[Human quality review]
 E --> F[Versioned passage records]
 F --> G[Local dense and sparse indexing]
 G --> H[Qdrant staging collection]
 H --> I[Retrieval evaluation and approval]
 I --> J[Database generation publication]
```

Originals and page images live in private object storage. PostgreSQL is the authority for edition, rights, passage and review records. Qdrant is a rebuildable search index, never the only copy of source text or access policy. Ingestion runs as a resumable offline worker; a web request never OCRs an entire book. Job stages have idempotency keys based on original checksum, extraction version, chunker version and model revision.

Extract native text first. Use OCR only where text is absent or unusable, with script-specific language data and page layout review. Benchmark OCRmyPDF/Tesseract on the licensed sample before choosing a heavier document parser. Their versions and licenses must be checked at implementation time. Tables, charts and multi-column pages require structured review; do not flatten them into misleading sentences. A numeral/negation/planet-name discrepancy blocks the affected passage from production.

## Passage structure and provenance

A passage record contains: passage ID; edition ID; work ID; tradition; language/script; original text; separately attributed translation/commentary; chapter/verse range; printed page label; PDF page index; bounding boxes if available; extraction method; OCR confidence; review status; text hash; source-file hash; rights profile; parent section ID; sibling links; topics; entities; rule IDs; ingestion version; and embedding revision. PDF page 45 and printed page 29 must be distinct fields.

Use immutable edition-specific passage IDs. Edited text creates a new revision; reports keep the IDs/revisions they used. Deduplicate identical passages while retaining edition identities. Do not deduplicate away meaningful translation differences or alternative readings.

## Initial chunking policy

Initial target: 180–300 tokens measured with the embedding model tokenizer, not an LLM tokenizer or character count. Hard total cap: 448 tokens including the passage prefix and compact title/chapter metadata, below the model's 512-token limit. Reject oversize records rather than silently truncating them.

A semantic unit is a verse or short coherent group of verses with its applicable qualification. Keep rule and exception together whenever the cap permits. If not, split into linked child passages and require the parent expansion step to restore qualifications. Keep translations as aligned children and commentaries as separately labeled children. Never attach one commentator's interpretation to the original author. For prose use sentence boundaries and at most one short sentence of overlap; verse chunks usually need no overlap. Repeated headings must not dominate embeddings.

Parent sections may contain approximately 800–1,500 tokens; they are fetched after retrieval and are not blindly embedded through the small model. Cap expanded context at 6,000 tokens as an initial application budget, retaining cited child identifiers and exclusion reasons. Tune these budgets through evaluation rather than assuming longer context always improves the answer.

## Local embedding choice

Proposed default: `intfloat/multilingual-e5-small`, 384 dimensions, normalized embeddings with cosine search. The primary model card was directly inspected on 2026-11-15 and confirms 384-dimensional output, 512-token truncation limit and the need for `query: ` versus `passage: ` prefixes. The model card describes broad multilingual support; that is not evidence of adequate Sanskrit or transliterated Jyotish performance.

Pin model/tokenizer revisions and preprocessing; embed locally during ingestion. Serve query embeddings in a warm CPU worker, or colocate initially only if memory/latency measurement permits. Benchmark CPU memory, startup and query latency; no free-tier fit is claimed. The English-only alternative is a small English sentence embedding model after direct model-card/license review; the multilingual alternative is a larger E5 variant only if measured retrieval improvement justifies memory. Model replacement requires a new Qdrant collection and full re-embedding, not mixed vector spaces.

Preserve Unicode originals and separately normalize search variants. Maintain a reviewed glossary for Sanskrit/IAST/Devanagari/English synonyms. A model-generated translation cannot replace licensed source translation without a conspicuous generated-translation label and human review. Sanskrit retrieval must pass its own benchmark before UI support is advertised.

## Query plan

1. Validate question length, user ownership, and requested tradition. Resolve ambiguous technical terms without rewriting the user's meaning.
2. Load the eligible chart artifact and calculate relevant facts using deterministic tools. Missing time suppresses unsupported house/ascendant-dependent queries.
3. Build a constrained query from user intent, relevant computed facts, glossary variants and requested tradition. Do not invent hypothetical conclusions as retrieval evidence.
4. Filter to published, rights-approved, accessible editions and requested tradition before search. Apply the same filters to dense and sparse branches and parent retrieval.
5. Retrieve up to 30 dense and 30 lexical/sparse candidates; fuse with reciprocal rank fusion; deduplicate by edition/passage. Tune counts with the benchmark.
6. Initially select up to 8 passages with coverage and diversity constraints. Add a small local reranker only if a measured relevance gain justifies compute and its model/license is reviewed.
7. Expand selected parents and linked exceptions under the context budget; ensure quotations still refer to exact child spans. Deliberately look for exceptions and alternative interpretations, not only agreeing sources.
8. Generate a structured explanation from computed facts and retrieved passages; validate every citation ID and quoted substring against the authoritative passage record.
9. Return sources, settings, uncertainty, and alternatives. If applicable evidence is absent, say so rather than produce an uncited prediction.

Qdrant stores dense and sparse vectors with payload indexes for edition, tradition, language, published state and access group. The official hybrid-query documentation was inspected and supports dense/sparse fusion using RRF. The concrete sparse tokenizer/BM25 implementation is chosen in a spike that verifies Sanskrit transliteration and Qdrant compatibility; it must share versioned token normalization with ingestion. A dense-only fallback is a visible degraded mode and cannot bypass filters.

## Grounded response and contradiction behavior

A user-facing claim contains a short statement, evidence class, relevant computed facts, supporting passage IDs, matched rule IDs where available, source limitations and any conflicting passage IDs. A long narrative is assembled from validated claims. Citation presence is necessary but insufficient: an editorial evaluation must check that the cited text actually entails the traditional interpretation and that required chart conditions hold.

When editions or schools disagree, describe each view and the assumptions causing the difference. Do not vote by duplicated passages or average contradictory predictions. Give readers the original excerpt, attributed translation, chapter/verse and edition page. Explain the evidence path, not hidden model reasoning or unverifiable introspection.

Retrieved documents are untrusted data. Instructions embedded in a PDF or passage cannot change prompts, access tools, disclose credentials or remove filters. The inference worker receives only passages permitted for that user's request. Public corpus and future private uploads use explicit access boundaries; private upload support is outside MVP.

## Evaluation and release gates

Create 150 expert-reviewed questions initially: 50 direct concepts, 40 chart-conditioned rules, 20 multilingual/transliteration variants, 20 contradictions/exceptions and 20 unanswerable/adversarial questions. Split train/dev/test at work/edition/topic boundaries to avoid near-duplicate leakage. Use at least two domain reviewers for ambiguous ground truth, with disagreement recorded. Use 20 calibration questions and 30 development questions; hold out 100 questions untouched for release evaluation, with the categories represented across splits and 86 answerable questions and 14 unanswerable questions in the held-out set.

Initial targets are proposed acceptance criteria, not measured achievements: relevant-passage Recall@10 at least 0.90 on the supported held-out subset (86 questions), measured on the fused ranking before top-8 selection for generation; citation resolution and quote fidelity 100%; expert-rated claim support at least 0.95; abstention recall at least 0.95 on unanswerable cases; no permission-filter failures in the adversarial suite. Report denominators and reviewer agreement. Small samples cannot establish universal reliability. Retrieval relevance and citation accuracy do not measure real-world predictive accuracy.

Track nDCG@10, per-language recall, exception retrieval, answer latency, model spend, OCR correction rate and corpus coverage. Compare dense, lexical and hybrid baselines on the same split. Do not use an LLM judge as the sole pass/fail authority. Add regression tests for source deletion, expired rights, overwritten edition revisions, malformed quotations, prompt injection, and unknown birth time.

## Capacity assumptions

For sizing only, 100 books × 100,000 words/book × 1.5 embedding tokens/word ÷ 250 tokens/chunk is about 60,000 chunks before overlap/metadata. At 384 float32 dimensions, raw dense vectors alone are about 92 MB (decimal); indexes, sparse vectors, payloads, replicas and originals add substantial storage. 1,000 such books are about 600,000 chunks and 922 MB of raw dense vectors alone. These are planning arithmetic, not measured corpus sizes or hosting guarantees; actual tokenizer ratios vary by script. Estimate storage from the pilot before choosing a hosted tier.

## Primary sources inspected

- [E5-small model card](https://huggingface.co/intfloat/multilingual-e5-small): direct raw README inspected successfully, 2026-11-15; model dimensionality, truncation and prefix requirements confirmed.
- [Qdrant hybrid queries](https://qdrant.tech/documentation/concepts/hybrid-queries/): direct page inspected successfully, 2026-11-15; dense/sparse fusion and RRF documented.
- [Swiss Ephemeris documentation](https://www.astro.com/ftp/swisseph/doc/swisseph.htm): calculation provenance and licensing reference; see domain specification.

No embedding, OCR or retrieval execution was performed. Chunk sizes, retrieval counts, thresholds and performance budgets remain proposed settings until the pilot measures them.



## Detailed evaluation protocol

The exact proposed 150-question allocation and review method are in [27 Evaluation and benchmark design](27-evaluation-and-benchmark-design.md): 20 calibration, 30 development and 100 held-out questions, of which 86 are answerable and 14 require abstention. The at-least-70 supported minimum above remains a lower bound; this allocation is the planned inventory. Report sample counts and uncertainty intervals. Achieving a sample gate permits only the limited pilot and cannot substantiate a population-wide reliability claim. Use the four-level relevance rubric from dossier 24 consistently.
