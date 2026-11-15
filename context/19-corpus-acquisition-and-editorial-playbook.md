# Corpus acquisition and editorial playbook

Prepared 2026-11-15. Extends [corpus summary](06-corpus-and-sources.md) and [retrieval design](07-ingestion-and-retrieval.md). No books were acquired or ingested. Catalogue records were inspected; complete editions were not read. This distinction prevents a bibliography from becoming a false claim of knowledge already available to the application.

## 1. Research findings that change the design

The first problem is edition identity. A title can exist in multiple translations, revised printings, abridgments and compilations. Publisher search returned unrelated works for several queries: Brihat Parashara Hora Shastra returned Jatakadesamarga Chandrika; Uttara Kalamrita returned Uttara-Ramacharita. A plausible search result is not a verified book match. Acquisition must require author/title/script inspection and a title-page image, not keyword similarity.

The second problem is unreliable catalogue prose. The inspected Jataka Parijata three-volume page lists V. Subramanya Sashtri in its structured metadata and Ranjan Publications in page fields, but its description introduces another translator and ends with conversational assistance wording. Treat this as a metadata conflict, not a reason to choose either attribution automatically. A publisher-hosted page remains evidence of what that page says; it does not replace the physical edition's title/copyright pages.

The third problem is mixed authorship inside a volume. The English Phaldeepika product description states that Bhavartha Ratnakara material was added. Its passages cannot all be attributed to Mantresvara. Similarly, the inspected Jaiminisutras description distinguishes translation, original notes and later annotations. The data model therefore needs authorship at passage/layer level, not only book level.

The fourth problem is language mismatch. The Prasna Marga set inspected here is listed as Sanskrit/Hindi with Shukdev Chaturvedi metadata; it is not the B. V. Raman English translation merely because the title matches. An English-first acquisition request must specify translation and language explicitly.

## 2. Ten-work priority acquisition matrix

All ten remain rights-uncleared. ISBNs below are observed catalogue values, not verified copyright-page identifiers. Do not substitute them for edition inspection. Three to five suitable editions are enough for the first pilot; this ten-work queue is a sequence, not a purchase instruction.

| Order | Candidate and observed record | Why acquire | Missing evidence and editorial action |
|---|---|---|---|
| 1 | Brihat Jataka; B. Suryanarain Rao/B. V. Raman catalogue metadata; English; 639 pages; ISBN variants 9788120813960 and 9788120813953 | Classical natal foundation with commentary lineage | Exact printing/year, title/copyright pages, rights contact, boundaries of translator notes versus source text |
| 2 | Phaldeepika English; Gopesh Kumar and Ashutosh Ojha; 698 pages; ISBN variants 9788120833418 and 9788120833401 | Broad natal vocabulary and interpretations | Identify Mantresvara text, added Bhavartha Ratnakara rules and modern commentary separately |
| 3 | Saravali of Kalyana Verma, two-volume catalogue hit | Classical comparison for rule agreement/disagreement | Exact translator, language, ISBN, printing and permission all missing; request sample before selection |
| 4 | Hora Sara; title attributes Prithuyasas; Ranjan; English/Sanskrit; 333 pages | Independent classical comparison and divisional-chart discussion | Translator and edition year absent from inspected metadata; verify title page and passage numbering |
| 5 | Jataka Parijata, three-volume set; V. Subramanya Sashtri metadata; Ranjan; Sanskrit/English; 1106 pages; catalogue code 8189230642 | Larger reference for exceptions and comparative rules | Resolve conflicting description before ingestion; confirm volume-specific locators |
| 6 | Brihat Parashara Hora Shastra; traditionally attributed to Parashara | Parashari terminology and selected timing foundation | No exact edition verified in this search; commission edition comparison rather than accepting unrelated search hit |
| 7 | How to Judge a Horoscope, two volumes; B. V. Raman; English; 797 pages listed | Modern worked interpretations and house-based pedagogy | Rights for charts/examples, personal-data review, separate modern synthesis from classical quotation |
| 8 | Three Hundred Important Combinations; B. V. Raman; English; 354 pages listed | Candidate yoga catalogue and worked examples | Require permission; examples are not prospective evidence of predictive accuracy |
| 9 | Jaiminisutras; B. Suryanarain Rao; 208 pages; ISBN 9788120813922 | Separate-school research and annotation-layer test | Exact revision/printing and later annotation authorship; not part of initial Parashari rules |
| 10 | Prasna Marga, two-volume inspected set; Shukdev Chaturvedi; Ranjan; Sanskrit/Hindi; 590 pages; code 8188230731 | Later horary collection and regional terminology | English edition must be separately identified if needed; do not relabel this set as Raman translation |

The matrix intentionally leaves missing edition facts blank in meaning rather than inventing specificity. A curator must resolve those fields before the record becomes an accepted edition. Priority can change if rights are unavailable; a readable licensed modern introduction can be more useful than an inaccessible prestigious title.

## 3. Expanded reading map: 42 distinct candidates

This map broadens coverage without promising that every work belongs in the production corpus. Attribution is traditional or bibliographic where stated; disputed/unknown authorship remains explicit. All chosen editions require separate rights review. Entries marked discovery-only have not had a matching exact catalogue record inspected in this task.

| # | Work / attribution | Purpose and inclusion decision |
|---|---|---|
| 1 | Brihat Parashara Hora Shastra; traditionally Parashara | Core candidate; edition/recension comparison required; exact edition discovery-only |
| 2 | Brihat Jataka; Varahamihira | Core natal; matching catalogue inspected |
| 3 | Saravali; Kalyanavarman | Core natal comparison; matching catalogue hit inspected |
| 4 | Phaladeepika; Mantresvara | Core natal; inspected modern compilation requires layer separation |
| 5 | Jataka Parijata; Vaidyanatha Dikshita | Core reference; inspected metadata conflict must be resolved |
| 6 | Hora Sara; Prithuyasas | Classical comparison; matching catalogue inspected |
| 7 | Laghu Parashari; traditional attribution unresolved here | Compact Parashari/dasha study; matching catalogue hit, edition unselected |
| 8 | Madhya Parashari; traditional attribution unresolved here | Later comparison queue; discovery-only |
| 9 | Uttara Kalamrita; traditionally attributed to Kalidasa, identity disputed | Significations/timing comparison; discovery-only; not Uttara-Ramacharita |
| 10 | Bhavartha Ratnakara; Ramanuja attribution to confirm | Source of compiled additions; matching catalogue hit inspected |
| 11 | Chamatkara Chintamani; Bhatta Narayana | Compact interpretive comparison; matching catalogue hit inspected |
| 12 | Jataka Tattva; Mahadeva Pathaka attribution to verify | Extended reference; discovery-only |
| 13 | Jataka Bharana; Dhundiraja attribution to verify | Classical comparison; discovery-only |
| 14 | Sanketa Nidhi; Ramadayalu attribution to verify | Rule comparison and terminology; discovery-only |
| 15 | Jaimini Upadesa Sutras; traditionally Jaimini | Separate school; inspected translated record has annotations |
| 16 | Studies in Jaimini Astrology; B. V. Raman | Modern worked explanations; referenced by inspected Jaiminisutras description |
| 17 | Prasna Marga; original authorship traditionally anonymous | Later horary; inspected Hindi/Sanskrit edition, English edition separate |
| 18 | Prasna Tantra; Nilakantha attribution to verify | Later horary comparison; discovery-only |
| 19 | Daivajna Vallabha; traditionally attributed to Varahamihira | Later horary; attribution and exact edition unverified |
| 20 | Tajika Nilakanthi; Nilakantha | Later annual/horary tradition; discovery-only |
| 21 | Muhurta Chintamani; Ramadaivajna | Later electional module; matching catalogue hit inspected |
| 22 | Brihat Samhita; Varahamihira | Cultural/mundane/astronomical context; matching catalogue and readable translation record inspected |
| 23 | Surya Siddhanta; traditional astronomical text, composite history | History/calendrics; matching catalogue hit, not production ephemeris |
| 24 | Vedanga Jyotisha; traditionally Lagadha | Historical calendrics; discovery-only |
| 25 | Aryabhatiya; Aryabhata | History of mathematical astronomy; matching catalogue hit |
| 26 | Brahmasphutasiddhanta; Brahmagupta | Historical computational context; discovery-only |
| 27 | Siddhanta Shiromani; Bhaskara II | Historical astronomy/math; discovery-only |
| 28 | Panchasiddhantika; Varahamihira | Historical comparison of astronomical systems; discovery-only |
| 29 | How to Judge a Horoscope; B. V. Raman | Licensed modern pedagogy; inspected catalogue |
| 30 | Three Hundred Important Combinations; B. V. Raman | Licensed modern yoga compendium; inspected catalogue |
| 31 | Hindu Predictive Astrology; B. V. Raman | Modern overview; matching catalogue inspected |
| 32 | Notable Horoscopes; B. V. Raman | Historical examples with selection-bias warning; discovery-only |
| 33 | A Manual of Hindu Astrology; B. V. Raman | Introductory comparison; discovery-only |
| 34 | Light on Life; Hart de Fouw and Robert Svoboda | Modern contextual explanation; inspected catalogue |
| 35 | Light on Relationships; Hart de Fouw and Robert Svoboda | Later relationship module; matching catalogue hit |
| 36 | Astrology of the Seers; David Frawley | Modern synthesis; matching catalogue inspected |
| 37 | Vedic Astrology: An Integrated Approach; P. V. R. Narasimha Rao | Author-hosted teaching resource; official book page inspected; reuse rights unconfirmed |
| 38 | Krishnamurti Padhdhati readers; K. S. Krishnamurti | Separate KP acquisition project; volume/edition identity still discovery-only |
| 39 | Tetrabiblos; Claudius Ptolemy | Later Western traditional corpus; chosen translation discovery-only |
| 40 | Anthologies; Vettius Valens | Later Hellenistic corpus; translation rights and edition discovery-only |
| 41 | Christian Astrology; William Lilly | Later Western horary; exact edition discovery-only |
| 42 | Ramayana; traditionally Valmiki | Optional cultural collection only, not technical natal authority; translation rights required |

## 4. Rights and provenance forms

An edition record must contain: `edition_id`; `work_id`; exact title/subtitle; author and attribution confidence; editor; translator; commentator; publisher/imprint; printing/edition; publication year; ISBN/catalog identifiers; language and scripts; page count; source URL or vendor; acquisition date; source checksum; page-image checksum if separate; jurisdiction; provider-processing location; rights evidence; permitted actions; excerpt limits; attribution text; deletion/expiry terms; reviewer; approval date; and unresolved conflicts.

Permitted actions are separate checkboxes: private storage; OCR; normalized-text storage; embedding/indexing; sending selected excerpt to an external model provider; display in authenticated UI; export in a report; internal evaluation; commercial service; and public redistribution. Buying a copy, accessing a free webpage or finding an ancient author does not mark all actions permitted. A source can be indexed under a license that still forbids displaying page images or external processing.

Passage records add: `passage_id`; edition revision; original page label; PDF/image page index; chapter/verse/section locator; line/column or bounding box; original-script text; transliteration; licensed translation; commentary; language; OCR confidence; reviewer corrections; text hash; parent/child links; rule IDs; topic labels; rights profile; and a provenance chain to source file. Every generated excerpt carries source and rights identifiers through answer assembly.

A rights change triggers a collection transition. Mark a source withdrawn, stop retrieval, remove vectors and derived caches, and identify reports containing disallowed excerpts. Do not claim deletion until the retention sweep has evidence from object storage, PostgreSQL, Qdrant and provider logs where applicable.

## 5. Acquisition workflow

**Stage 0: formulate the question set.** Define the first 150 evaluation items and required topics before selecting books. This prevents collecting attractive titles that do not cover the product's actual questions.

**Stage 1: discover editions.** Search publishers, library catalogs and legitimate digital archives. Record the query, URL, timestamp and result. Reject title-only matches. Obtain title page, copyright page, table of contents and sample pages through a legitimate purchase, library access or permission.

**Stage 2: resolve identity.** Match title, author, translator, edition, language, scripts, publisher and year. Compare edition structure and locators. Open a conflict ticket when catalogue fields disagree. A curator may choose an edition; they may not silently repair conflicting metadata.

**Stage 3: obtain rights evidence.** Ask for an explicit license covering the actions required. Store the signed response or license reference in a restricted rights ledger. If the license is ambiguous about model-provider processing, treat it as disallowed until clarified.

**Stage 4: preserve originals.** Compute checksums, retain immutable originals, restrict access and record acquisition. Do not modify the source image to correct OCR; corrections belong in a versioned text layer.

**Stage 5: extract.** Use native text where available. Benchmark OCR on 10 pages per script/layout. Retain OCR output, confidence and coordinates. Multi-column pages, footnotes, tables and Devanagari vowel marks are high-risk.

**Stage 6: align and review.** Align original, IAST and translation by verse/section. A second reviewer checks all executable-rule passages and a random sample of the remainder. Corrections retain before/after text and reason.

**Stage 7: annotate.** Add tradition, chart type, entities, predicates, exceptions, applicability and evidence class. Keep commentary separate from attributed original. Mark modern author synthesis as modern synthesis.

**Stage 8: chunk and index.** Apply the 180–300 token target and 448 total cap from the retrieval design. Store exact child passages and parent sections. Build a staging Qdrant collection with a new embedding revision.

**Stage 9: evaluate and promote.** Run retrieval, citation and rights-filter suites. Promote an alias only when thresholds and reviewer signoff are recorded. A source may be usable for internal research while blocked from production display.

## 6. OCR and script quality controls

Devanagari OCR errors often change meaning through dropped vowel marks, punctuation, conjuncts, danda markers or numerals. The reviewer checks grapheme sequences against the page image, not just an English translation. IAST adds its own risk: macrons, underdots, retroflex letters and anusvara/visarga can be normalized inconsistently. Store the original code points and a deliberately normalized search form separately.

Build a glossary with Devanagari, IAST, common ASCII transliteration, English gloss, domain type and source context. Do not collapse distinct Sanskrit terms because an English gloss looks similar. Search expansion may use the glossary, but the displayed source remains the licensed original/translation.

A passage fails acceptance if it has unresolved OCR uncertainty in a negation, number, planet/rashi name, exception marker or rule predicate. A low-confidence passage may remain in a background discovery index only when the UI labels it unreviewed and prevents it from supporting an executable claim. Translation disagreement is not OCR error; preserve both as attributed alternatives.

## 7. Reviewer workflow and quality gates

Use a two-person review for executable rules and a single trained curator plus sampled second review for contextual passages. Reviewers receive the page image, edition metadata, extraction text, translation/commentary layers and proposed annotations. They answer fixed questions: Is the passage identity correct? Is text complete? Are layers attributed? Is the rule predicate faithful? Are exceptions preserved? Is locator reproducible? Does rights profile allow intended display?

Record reviewer IDs, timestamps, decision, confidence and disagreement. Escalate unresolved disputes to a domain editor. Domain approval does not waive copyright review; rights approval does not establish textual truth.

Release gates are: 100% provenance fields for supporting passages; 100% quote-substring fidelity; no production retrieval from expired/blocked sources; zero silent tradition mixing; no executable rule without reviewer signoff; and measured retrieval targets from the coordinated plan (150 evaluation items, 20 calibration, 30 development, 100 held-out, 86 answerable and 14 unanswerable held-out; Recall@10 target at least 0.90 before top-eight generation). These are acceptance targets pending implementation.

## 8. Editorial rule-authoring template

```text
rule_id:
tradition:
chart_type:
source_passage_ids:
source_layers: [original | translation | commentary | modern_synthesis]
required_facts:
predicate:
exceptions:
unknown_input_behavior:
traditional_result_summary:
modern_safety_notes:
reviewers:
status: draft | reviewed | executable | withdrawn
rights_profile:
version:
```

Executable predicates are authored against deterministic chart facts and tested with positive, negative, boundary and unknown-input fixtures. The prose result is stored as attribution, not as a promise. When multiple editions disagree, create alternative rules with explicit source/tradition tags rather than merging them into a false consensus.

## 9. Source links inspected or used for discovery

- [Motilal Banarsidass catalogue](https://www.motilalbanarsidass.com/) and product records: [Brihat Jataka](https://www.motilalbanarsidass.com/products/varaha-mihiras-brihat-jataka), [Phaladeepika](https://www.motilalbanarsidass.com/products/phaldeepika-bhavartha-bodhini-english-edition), [Jataka Parijata](https://www.motilalbanarsidass.com/products/jataka-parijata-set-of-3-volumes), [Hora Sara](https://www.motilalbanarsidass.com/products/hora-sara-by-prithuyasas-son-of-varahamihira), [Jaiminisutras](https://www.motilalbanarsidass.com/products/jaiminisutras-english-translation-with-full-notes-and-original-texts-in-devanagari-and-transliteration), [Prasna Marga](https://www.motilalbanarsidass.com/products/prasna-marga-the-famous-astrology-book-of-south-india-2-volumes), [Muhurta Chintamani](https://www.motilalbanarsidass.com/products/muhurtachintamani-of-daivagya-ramacharya-srimad-govind-virachit-peeushadhara-hindi-teeka-sahit), [Brihat Samhita](https://www.motilalbanarsidass.com/products/the-brihat-samhita-of-varaha-mihira), [Surya Siddhanta](https://www.motilalbanarsidass.com/products/the-surya-siddhanta).
- [Wisdom Library Brihat Samhita record](https://www.wisdomlib.org/hinduism/book/brihat-samhita): directly readable record identifies an N. Chidambaram Iyer translation and 1884 date; online readability is not permission to ingest or redistribute.
- [Publisher catalogue search](https://www.motilalbanarsidass.com/search?q=astrology&type=product): discovery only; search false matches are documented above.
- [Copyright Office derivative works circular](https://www.copyright.gov/circs/circ14.pdf): legal reference target; not a jurisdiction-specific opinion about any edition.
- [Sanskrit Documents](https://sanskritdocuments.org/): direct access returned HTTP 403 on 2026-11-15, so terms were not inspected and no reuse assumption is made.

## 10. Open acquisition questions

- Which ten records can be licensed for embedding, provider excerpt processing and user display under the launch jurisdictions?
- Does the provider contract permit sending copyrighted retrieved passages, and what retention controls apply?
- Which domain editor will approve Parashari predicates and adjudicate contradictory editions?
- Do users need Devanagari display in the MVP, or is licensed English enough while Sanskrit OCR is benchmarked?
- What is the deletion SLA when a license expires or a source owner requests removal?
- Which editions have stable verse/page locators suitable for user citations?

Until these are answered, corpus growth is research planning and no full text should be downloaded or processed into production.

