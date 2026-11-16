# Evidence validation and contradictions

Status: researched proposal, 2026-11-15. No validator, corpus, benchmark or application code was executed. This dossier extends [retrieval](07-ingestion-and-retrieval.md), [contracts](12-data-and-api-contracts.md), [AI rules](13-ai-context-and-rules.md) and [domain research](18-domain-research-dossier.md); proposed additions require contract reconciliation before implementation.

## Research implications

ALCE separates fluency, correctness and citation quality; its published abstract reports substantial incomplete citation support even in its strongest evaluated systems [S1]. The original evaluation implementation checks sentence support using combined cited passages, then investigates unnecessary citations [S2]. This supports separate coverage and citation-usefulness measurements. It does not establish that an astrology interpretation is true, or that sentence-level scoring catches every unsupported clause.

Adversarial NLI demonstrates that people can find weaknesses in natural-language inference models [S3]. Here, an entailment model can prioritize review and detect obvious mismatches; it cannot certify Sanskrit translation, conditional rule applicability or predictive validity. Domain transfer is an untested hypothesis. Human-reviewed labels remain the release authority, including explicit disagreement rather than automatic majority truth.

LangChain distinguishes provider-native structured output from tool-based strategies and documents schema errors and retry handling [S4]. A valid object guarantees neither correct references nor supported content. The custom Responses-compatible endpoint needs its own capability test; provider branding and automatic strategy selection are insufficient. Keep the fixed workflow, no runtime browsing, and maximum two generation calls already specified in architecture.

## Claim-level evidence ledger

Split compound statements into independently checkable claims before publication. “This placement indicates aptitude and guarantees promotion” contains two claims with different support requirements. Store the following proposed ledger beside the existing claim contract; this is an inspectable rationale, never hidden model reasoning.

| Link | Required audit content |
|---|---|
| Claim | Stable claim ID, exact text, type: computed fact, attributed teaching or interpretation; output location |
| Fact | Authorized snapshot and fact IDs, settings hash, value, interval stability; unavailable facts explicitly named |
| Rule conditions | Reviewed rule/version, chart type and school, each predicate and true/false/unknown result, calculation provenance |
| Edition passage | Edition/revision and passage IDs, passage hash, original/translation/commentary layer, author/translator attribution, source coordinates |
| Exceptions | Linked exceptions and parent context, individual truth states, completeness status and any unresolved qualifier |
| Interpretation | Modest conclusion, inference label, missing premises, conflicts and final disposition |

Maintain a distinction between “the source teaches X” and “X applies here.” A textual explanation may be supported while personalized application remains indeterminate. For an approved rule requiring A and B and absence of C, A=true, B=true, C=unknown cannot establish applicability. A missing registry entry is not evidence that no exception exists. An LLM-discovered rule stays unreviewed and cannot receive machine-checked status.

Prevent citation laundering across this chain: a modern summary quoting an older work supports attribution to the summary unless the older edition itself was verified. A translation supports the translator's rendering; a commentary does not automatically become the original author's words. Several reprints of one interpretation are not independent agreement. Do not convert retrieval rank, NLI output, OCR confidence or number of citations into a probability of future events. Show categorical support status and concrete limitations.

## Exact quotations and Unicode

Validate against the authoritative immutable passage, not vector payload text or model-supplied bibliography. The server resolves identifiers, ownership, current rights, edition revision, hash and approved display coordinates before constructing a citation card. Model output selects permitted spans; the server supplies title, translator, locator and displayed text.

Define offsets explicitly as zero-based Unicode code-point indices with an exclusive end in the stored original passage. Record each span separately. JavaScript UTF-16 indices and byte offsets must not be silently substituted. Reject out-of-range spans, hash mismatches and boundaries that split displayed grapheme clusters. A discontinuous excerpt carries multiple spans and a visible editorial ellipsis; it is not a fabricated contiguous quotation.

UAX #15 distinguishes canonical from compatibility equivalence [S5]. Preserve original Unicode text. Maintain an NFC search/comparison representation with a reversible coordinate map if needed; always render the original slice. Canonical equivalence may help locate a candidate but does not authorize rewriting a quote. Do not use NFKC, accent removal, whitespace collapse, punctuation replacement or OCR correction as proof of exact fidelity. Check IAST combining marks, Devanagari sequences, zero-width characters and visually similar letters. HTML escaping changes rendering safety, not source identity. Corrected OCR creates a reviewed revision with lineage; it never silently overwrites old evidence.

## Contradictions and source withdrawal

Before classifying disagreement, compare proposition, school, chart type, conventions, timeframe and source layer. “Contradiction” requires incompatible claims under comparable conditions. Keep the taxonomy explicit:

- **School/convention:** valid different assumptions; show separate attributed views and their settings, without synthesis into consensus.
- **Translation:** different renderings of an aligned original; preserve translator identity and request qualified language review.
- **OCR/transcription:** suspected negation, number or name corruption; quarantine affected evidence pending page inspection.
- **Exception/context:** a general rule narrowed by an adjoining passage; retrieve the qualifier and revise applicability.
- **Unresolved textual disagreement:** competing editions or claims with insufficient editorial evidence; retain both and abstain from choosing an authoritative outcome.

A relation record names both passage revisions, classification, relevant condition difference, reviewer and review status. Absence of retrieved disagreement is not proof of consensus. Context-budget truncation that removes a necessary qualification makes the affected claim insufficiently supported.

Rights checks apply during retrieval, immediately before publication, every saved-reading read and export. Withdrawal invalidates server/CDN caches and pending publication; index deletion may follow asynchronously because PostgreSQL remains the serving authority. Previously generated copies and exports still under service control need the same policy. An already downloaded file cannot be recalled: document that limit. Preserve only permitted audit metadata and show an unavailable-source state where allowed. If source access disappears between generation and validation, remove the dependent claim or return partial/insufficient evidence; never substitute another edition under the old citation.

## Schema and unknown assertions

Use strict enums, bounded arrays/text, forbidden unknown object fields and explicit nullable values. Unknown factual assertions differ from unknown schema fields: reject an invented field structurally; classify an unsupported statement semantically and withhold it. A supplied ID outside the authorized evidence bundle fails even if it exists elsewhere in storage.

Validate schema, references, quotes, fact consistency, reviewed predicates, exceptions and policy independently. Do not let a model set its own validation outcome. Free narrative in summaries, limitations and suggested questions can introduce claims, so assemble summaries from accepted claims or subject them to the same coverage check. A fluent uncited sentence outside `traditional_claims` is still an assertion.

One bounded repair may correct recoverable schema/citation errors within the original deadline. Disable library retries that could exceed this cap. Refusal, truncation, malformed output, repeated failure and uncertain provider timeout produce explicit failure/partial states. Never coerce “unknown” into false, repair missing evidence through invention or retry rights denials.

## Invented worked example

Everything here is synthetic: no named classical work, real verse or historical teaching is implied. Fictional fixture passage P says: “If condition A and condition B hold, quality Q is suggested, unless condition C holds.” Fixture edition E and reviewer rule R exist only in a test harness, outside the production corpus.

A mock chart supplies A=true, B=true and C=unknown. The ledger links those mock facts to R, the exact span in P, and exception C. The textual claim “Fixture P associates A and B with Q, subject to C” is supported as a description of the fixture. “You have Q” is withheld because the exception cannot be evaluated. The answer states that applicability is not established. If a second invented fixture says Q is absent under the same conditions, display an unresolved fixture disagreement; do not average the two claims or report fifty-percent confidence.

## Meaningful test matrix

This is the full proposed test matrix, not a claim that every case has been executed. Core quote/hash/span and rights-validation cases have automated coverage; expert applicability judgments and the remaining adversarial cases still require review and evaluation. See [implementation progress](../implementation/PROGRESS.md).

| Case | Required outcome |
|---|---|
| Authentic ID, unrelated passage | Semantic support fails despite citation resolution |
| Supported first clause, unsupported second | Split claims; suppress second clause |
| Invented citation or foreign-owner ID | Reject without leaking existence |
| Correct quotation, wrong edition label | Server metadata prevents misattribution |
| NFC/NFD equivalent spelling | Map candidate to original; render exact original |
| Homoglyph or missing negation | Fidelity fails; no fuzzy acceptance |
| Emoji before quoted span | Code-point/UTF-16 mismatch detected |
| Ellipsis hiding exception | Require exception context; reject misleading claim |
| Unknown cancellation condition | Personalized applicability remains unknown |
| D1 rule applied to D9 | Scope validation rejects application |
| Commentary attributed to original | Attribution review fails |
| Same passage in five reprints | No increase in independent support |
| Conflicting translations | Separate labels; language-review queue |
| OCR loses planet name or numeral | Quarantine affected passage |
| Rights revoked during generation | Publication recheck blocks excerpt and dependent claim |
| Saved reading/export after revocation | Current rights enforced; permitted unavailable state |
| Unknown schema property or truncated JSON | Bounded repair or explicit failure |
| Injection embedded in passage | Treated as source text; no tools/policy override |
| Unsupported assertion in summary | Coverage check removes it |

## Reviewer rubric and gates

Two reviewers independently mark atomic claims: supported, partially supported, unsupported or indeterminate. Score attribution, exact fidelity, condition matching, exception completeness, disagreement disclosure and interpretation restraint separately; record reasons and adjudicate material disputes with a qualified domain/language reviewer. Never collapse these dimensions into a prediction-confidence score.

Report claim-support coverage with numerator/denominator, unnecessary-citation rate, quote fidelity, authorization failures, exception recall and abstention recall. Preserve unanswerable questions in evaluation; exclusion would inflate quality. Follow the existing 20 calibration/30 development/100 held-out split, 86 answerable and 14 unanswerable held-out items, and work/edition separation. Existing proposed gates remain 100% citation resolution/quote fidelity, zero authorization failures, at least 95% supported substantive claims and 95% abstention recall. These targets are not achieved results. Unresolved critical provenance or rights defects block release regardless of averages.

## Primary sources and inspection record

All entries accessed 2026-11-15 through direct HTTP, status 200; web-tool calls returned no readable payload, so direct retrieval supplied verification. No paywalled edition was inspected.

- **S1:** [Gao et al., ALCE, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398/). Original paper's publisher abstract and metadata inspected; full PDF not inspected.
- **S2:** [ALCE original evaluation implementation](https://raw.githubusercontent.com/princeton-nlp/ALCE/main/eval.py). `compute_autoais`, joint support and citation precision/recall logic inspected; mutable main branch, not a pinned executable dependency.
- **S3:** [Nie et al., Adversarial NLI, ACL 2020](https://aclanthology.org/2020.acl-main.441/). Original publisher abstract and metadata inspected; full PDF not inspected.
- **S4:** [LangChain structured output](https://docs.langchain.com/oss/python/langchain/structured-output). Strategy, validation and error-handling sections inspected; endpoint compatibility untested.
- **S5:** [Unicode UAX #15, revision 57](https://www.unicode.org/reports/tr15/tr15-57.html). Versioned normalization reference inspected alongside current landing page; no claim that this is the latest revision. Coordinate and display policies above are project proposals.
