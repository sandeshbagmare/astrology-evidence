# Corpus, bibliography and source rights

Status: acquisition plan, 2026-11-15. No book has been downloaded, licensed, OCRed, or ingested. This is a candidate bibliography, not a claim that the application already knows these books.

## Acquisition strategy

Start with 3–5 rights-cleared editions, approximately 300–800 carefully reviewed passages, and a defined group of questions. Expand to 20–30 editions after retrieval and citation evaluation, then scale toward hundreds only when marginal coverage is measurable. Duplicate editions and unreliable OCR can make a larger corpus worse. Count usable passages, question coverage and reviewed rules rather than advertising book totals.

Maintain four separate layers: original verse, translation, named commentary, and modern synthesis. Translation is itself an interpretation. Preserve links between layers and never concatenate them into an unattributed authoritative statement. A work may be ancient while its translation, annotations, scan, or database license remains protected.

## Candidate reading map

The following titles are bibliographic candidates, based on known works. Attribution and edition details must be verified against the title/copyright pages before catalog acceptance. They are not claimed as newly verified search findings. `Uncleared` means no permission decision has been made, including for editions of ancient works.

| Priority | Work / attribution to verify | Use and tradition | Acquisition / rights status |
|---|---|---|---|
| A | Brihat Parashara Hora Shastra; traditionally attributed to Parashara | Parashari natal concepts, yogas and timing; edition differences require tracking | Uncleared; select one named edition first, compare textual variants explicitly |
| A | Brihat Jataka; Varahamihira | Classical natal foundations | Uncleared; historic editions may be candidates after country/edition checks |
| A | Saravali; Kalyanavarman | Classical planetary/sign/house interpretations | Uncleared; modern translation permission required unless demonstrated otherwise |
| A | Phaladeepika; Mantresvara | Natal interpretation and combinations | Uncleared; confirm translator, edition, passage numbering |
| A | Jataka Parijata; Vaidyanatha Dikshita | Comparative natal reference and exceptions | Uncleared; extensive work, ingest narrowly by licensed topics |
| B | Hora Sara; Prithuyasas | Classical natal comparisons | Uncleared; attribution/spelling and edition to verify |
| B | Uttara Kalamrita; traditionally attributed to Kalidasa | House significations and timing traditions | Uncleared; do not assume attribution to the poet is settled |
| B | Jaimini Upadesa Sutras; attributed to Jaimini | Separate Jaimini school collection | Uncleared; translator/commentary essential because terse sutras are ambiguous |
| B | Prasna Marga; traditionally anonymous | Horary; separate later module | Uncleared; modern translated volumes require rights review |
| B | Muhurta Chintamani; Ramadaivajna | Electional astrology; later module | Uncleared; do not apply electional rules to natal questions |
| B | Brihat Samhita; Varahamihira | Mundane/cultural/astronomical material | Uncleared; classify chapter applicability; not all chapters concern natal prediction |
| B | Surya Siddhanta; traditional astronomical treatise | Historical mathematical astronomy | Uncleared edition; historical formulas are not the production ephemeris |
| B | Vedanga Jyotisha; traditionally attributed to Lagadha | History, calendrical foundations | Uncleared edition; cultural/context collection |
| C | Aryabhatiya; Aryabhata | Historical astronomy and computational context | Uncleared translation; contextual rather than natal authority |
| C | Three Hundred Important Combinations; B. V. Raman | Modern interpretation of yogas | Assume protected until permission obtained; purchase alone does not authorize ingestion |
| C | How to Judge a Horoscope, volumes 1–2; B. V. Raman | Modern systematic natal interpretation | Assume protected; negotiate indexing and quotation rights |
| C | Hindu Predictive Astrology; B. V. Raman | Modern overview and teaching | Assume protected; editorial comparison only until licensed |
| C | Light on Life; Hart de Fouw and Robert Svoboda | Modern explanatory Jyotish | Assume protected; permission needed for ingestion/excerpts |
| C | Astrology of the Seers; David Frawley | Modern interpretive synthesis | Assume protected; segregate author interpretation from classical verse |
| C | Tetrabiblos; Claudius Ptolemy | Future Western tradition collection | Uncleared chosen translation; keep tropical/Western rules separate |
| C | Christian Astrology; William Lilly | Future Western horary comparison | Uncleared chosen edition/digital copy; not part of Vedic MVP |
| Cultural | Ramayana; traditionally attributed to Valmiki | Optional cultural literature, not technical chart rule authority | Uncleared translation and edition; separate collection and UI label |

## Discovery sources and verification targets

These URLs identify legitimate discovery starting points, not permission grants. Prefer publisher or library records and inspect the actual edition title/copyright page.

- [Motilal Banarsidass publisher](https://www.motilalbanarsidass.com/): catalogue discovery and licensing contact for relevant published editions; individual title availability remains to verify.
- [Chaukhambha publisher](https://chaukhambabooks.co.in/): Sanskrit editions and publication metadata; catalogue and rights contact to verify.
- [WorldCat](https://search.worldcat.org/): identify edition, translator, publication year and library holdings; catalog metadata is not full-text permission.
- [Internet Archive](https://archive.org/): inspect legitimate scan metadata and rights statements; accessibility or borrowing is not a blanket commercial reuse license.
- [HathiTrust](https://www.hathitrust.org/): edition discovery and rights labels; jurisdiction and access conditions require review.
- [Sanskrit Documents](https://sanskritdocuments.org/): potential original-script discovery. Direct access returned HTTP 403 on 2026-11-15; terms were not inspected. Do not scrape around the restriction or presume reuse rights.
- [Wisdom Library Brihat Samhita](https://www.wisdomlib.org/hinduism/book/brihat-samhita): candidate readable text and edition discovery; access and reuse terms must be checked before ingestion.
- [US Copyright Office, derivative works circular](https://www.copyright.gov/circs/circ14.pdf): legal-reference target for translations and derivative works, not a rights determination for any listed book. Rights decisions need jurisdiction-specific review.

## Rights gate

Each edition receives an internal `edition_id`; underlying `work_id`; author/attribution; editor; translator; publisher; year; ISBN/catalog IDs; source URL; acquisition date; checksum; languages/scripts; tradition; jurisdiction considered; evidence of rights; allowed actions; required attribution; retention/expiry; and approval owner/date.

Allowed actions are independent: store original; OCR; embed/index; transmit excerpts to model provider; display excerpts; show full page; export report excerpts; permit commercial service. Permission for one does not imply all. Until these fields are approved, the edition stays in quarantine and cannot enter production search. Never expose a full scan merely because the app has permission to embed it.

For every displayed excerpt store a rights profile with maximum allowed quotation length, attribution text, and whether an image/page preview is permitted. The response assembler enforces per-source limits across the whole answer, not once per retrieved chunk. A deletion/expiry operation removes original, text, vectors, derived excerpts, caches, and disallowed report copies according to the documented retention policy.

Rights are reviewed for the launch jurisdiction and provider-processing location. This document makes no blanket public-domain finding. Obtain legal review for unclear editions and licenses before a public service uses them.

## Source quality and editorial review

Prefer a complete edition with stable numbering and identifiable translator. Preserve spelling variants and supplied corrections. Record disputed attribution rather than silently resolving it. Reject unsourced social posts as authoritative corpus material; a user may discuss them but the app must not promote them to classical evidence.

Two reviewers should resolve critical OCR discrepancies in planet names, negation, numbers, conjunctions and verse boundaries. Store disagreement and resolution. A source can be authentic yet scientifically unvalidated; provenance quality and predictive validity are separate fields.

## Acquisition deliverables before implementation pilot

- Rights ledger for first 3–5 editions and a reproducible acquisition manifest.
- Ten manually verified pages per edition, plus all pages supporting the first executable rules.
- Versioned glossary linking graha/rashi/bhava/nakshatra terms, English terms, Devanagari and IAST variants.
- Explicit inclusion/exclusion decisions for each question category.
- Expert-reviewed evaluation questions with relevant passage IDs and known contradictory interpretations.

Nothing in this file authorizes downloading protected full texts, bypassing access restrictions, or publishing excerpts without rights review.

## Directly inspected catalogue records (2026-11-15)

The publisher search catalogue returned these matching edition links. Search-result existence verifies discovery only; copyright-page details and permissions remain unchecked.

- [Brihat Jataka](https://www.motilalbanarsidass.com/products/varaha-mihiras-brihat-jataka)
- [Phaladeepika, English edition](https://www.motilalbanarsidass.com/products/phaldeepika-bhavartha-bodhini-english-edition)
- [Jataka Parijata, three-volume set](https://www.motilalbanarsidass.com/products/jataka-parijata-set-of-3-volumes)
- [Prasna Marga, two-volume set](https://www.motilalbanarsidass.com/products/prasna-marga-the-famous-astrology-book-of-south-india-2-volumes)
- [Three Hundred Important Combinations](https://www.motilalbanarsidass.com/products/three-hundred-important-combinations)
- [How to Judge a Horoscope, two-volume set](https://www.motilalbanarsidass.com/products/how-to-judge-a-horoscope-2-volumes-in-set)
- [Hindu Predictive Astrology](https://www.motilalbanarsidass.com/products/hindu-predictive-astrology)

The [Wisdom Library Brihat Samhita record](https://www.wisdomlib.org/hinduism/book/brihat-samhita) was readable by direct HTTP and identifies the N. Chidambaram Iyer translation with an 1884 date. This is useful edition metadata, not an ingestion or redistribution license. Catalogue searches also found Saravali editions; exact selected edition remains open.


## Expanded acquisition research

Read [the editorial playbook](19-corpus-acquisition-and-editorial-playbook.md) for 42 candidate works, a ten-work acquisition matrix, observed edition metadata and source-identity pitfalls. Publisher search matches and descriptions can be wrong or mix commentators; inspect title/copyright pages before assigning edition identity. The initial 22-title table above remains an overview, not the complete research bibliography.
