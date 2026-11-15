# Product and scope

## Intent

Build an astrology application where users can inspect why an interpretation was produced: the birth inputs and calculation settings, reproducible chart facts, relevant passages from identifiable editions, and the model's explanation. The problem is unsupported authority and hidden reasoning in ordinary readings; the product should help users evaluate claims rather than encourage blind trust.

**User requirements:** Python as the main stack; LangChain using the supplied Responses-compatible provider; Qdrant vector database; lightweight local embeddings; consideration of LiteLLM; Google account authentication; detailed source-backed answers; book/domain research; architecture and UI context; coding rules; progress tracking; realistic free-hosting options; documentation before any code.

**Proposed defaults:** Vedic/Jyotish first, English UI and explanations, aligned Sanskrit passages where rights permit; Lahiri sidereal zodiac, whole-sign houses, mean lunar nodes; adult private beta; one natal-chart reading workflow and book search before expanding traditions. These are design choices, not user-confirmed religious or doctrinal preferences.

## Main journey

A user signs in with Google, sees the privacy and interpretation notice, enters birth date/place and time precision, confirms the resolved place and time zone, and reviews chart settings. They ask a question. The result separates calculated facts, traditional rules, model interpretation, disagreements, and missing information. Every source card opens a permitted excerpt with author/work/edition/page-or-verse reference. Users can save a reading, compare the impact of a changed setting, export their records, or delete them.

No exact birth time? Offer a limited reading and explicitly identify excluded time-sensitive conclusions. A date/place-based chart must not quietly substitute noon as a known birth time. See domain rules for interval-based calculation.

## MVP

- Google sign-in/out, account deletion, private birth profiles and readings.
- Date, time precision/interval, place confirmation, timezone ambiguity handling, versioned calculation settings.
- Deterministic natal chart facts and a simple accessible chart/table.
- Question answering grounded in a small curated corpus, with source cards and explicit abstention.
- Book/verse lookup independent of personalized predictions.
- Saved reading history with immutable evidence manifests and retrieval/model/calculation versions.
- Admin-only rights-controlled corpus import, review, publication and withdrawal.
- Rate limits, service error states, health checks, backups and evaluation report.

## Later phases

After validated natal-chart grounding: reviewed Vimshottari dasha calculations and transits, supported by their own test fixtures; opt-in multilingual explanations; expert annotation tools; comparisons across declared traditions; audited private library uploads; payments only if requested; user-feedback experiments with consent. Larger corpus scale follows measured retrieval quality, not book-count marketing.

Explicitly defer open-ended autonomous agents, generic web crawling at answer time, automated astrology-based life decisions, marketplace astrologers, gemstones/remedies upsells, public user-profile discovery, and arbitrary PDF uploads in the first release. Ramayana and other narrative/religious texts may later be included in a labeled cultural-reference collection; they do not automatically become technical chart rules.

## What quality means

An answer is good if the user can verify its inputs and citations, see uncertainty, understand conflicting rules, and identify what the system does not know. Citation quality and computation correctness are measurable separately from whether traditional predictions are empirically true. The app must never present deterministic future prediction as a solved property.

## Acceptance targets (not achieved results)

| Area | Initial release gate |
|---|---|
| Ownership | Zero cross-user reads/writes in adversarial integration tests |
| Calculations | All curated independent reference fixtures pass defined tolerances |
| Evidence | 100% displayed citation IDs resolve to authorized edition passages |
| Fabrication | Zero invented quoted text or source IDs in the release suite |
| Support | At least 95% substantive traditional claims judged supported by qualified reviewers on a fixed evaluation set |
| Abstention | At least 95% of deliberately unsupported questions avoid unsupported conclusions |
| Retrieval | Recall@10 >= 0.90 on the supported subset of 100 held-out questions (86 answerable and 14 unanswerable), measured before the top-8 generation selection |
| Accessibility | All core flows keyboard-operable; no critical automated accessibility findings, plus manual review |
| Privacy | Account deletion tests cover database, indexes, jobs, stored answer content, and documented backup expiration |
| Runtime | Free-demo and production latency/memory budgets measured before selecting a host |

Create 150 reviewed questions: 20 calibration, 30 development, and a separately held-out set of 100. Freeze test items before tuning; publish sample size and reviewer disagreement. No numerical success claim is allowed before evaluation.

## Product risk

A large library can contain incompatible schools, edition errors and unsupported claims. Retrieval can find a passage without proving it applies to a chart. Therefore applicability checks, disagreement reporting and source review are essential. No source count, AI model name, or attractive UI establishes predictive reliability.
