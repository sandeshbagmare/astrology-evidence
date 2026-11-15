# Content rights and license audit

Prepared 2026-11-15. This is a due-diligence plan, not legal advice or a finding that any edition is reusable. No book was downloaded, purchased, OCRed, indexed, or published for this project.

## Decision boundary

The corpus must be licensed at the edition and action level. An ancient author or public URL does not establish that a modern translation, annotation, scan, OCR output, database, or page image is free to reuse. Copyright Office Circular 14 describes translations and other adaptations as derivative works; the translator or adapter may have rights in that contribution while the underlying work may have a different status. The project therefore records underlying work, edition, translation, commentary, scan and software separately. Public-domain status is jurisdiction-specific and must be checked for the launch country, source country, and provider-processing location. A purchase gives possession of a copy; it does not automatically grant reproduction, indexing, model transmission, public display, or commercial-service rights.

The permission matrix is deliberately granular:

| Action | Required evidence | Default until approved |
|---|---|---|
| Preserve private scan/page images | Lawful acquisition plus storage permission | Quarantine |
| OCR and corrected text | Permission covering reproduction/derivatives, or documented exception | Quarantine |
| Normalize/transliterate/translate | Rights to create derivative text; identify contributor | Block |
| Embed and index | License must permit this processing and retention | Block |
| Send selected excerpts to an external model | Explicit provider/subprocessor and transmission permission; inspect provider retention | Block |
| Display excerpt in authenticated UI | Quotation/display limit, attribution, page/verse locator | Block |
| Display full page or scan | Explicit image/page permission | Block |
| Export report or saved citation | License must permit user redistribution and set aggregate limits | Block |
| Commercial service | Commercial grant and territory/duration stated | Block |

A rights profile is attached to every passage and answer manifest. It contains maximum excerpt length, attribution text, image-preview permission, territory, expiry/review date, provider-processing permission, and withdrawal contact. Limits apply across the complete answer and report, not independently per retrieved chunk. The project does not use a universal “25-word rule”; fair use and quotation limits depend on facts and contracts.

## Edition ledger and acquisition gate

Each `edition_id` links to a `work_id` and records exact title/subtitle, author or traditional attribution confidence, editor, translator, commentator, publisher/imprint, printing and year, ISBN/catalog IDs, language/scripts, page count, source URL/vendor, acquisition date, checksums, jurisdiction, provider location, rights evidence, allowed actions, attribution, expiry/renewal terms, reviewer, approval date, and unresolved conflicts. Each passage adds page index and printed page, chapter/verse locator, bounding box, source layer, OCR confidence, reviewer corrections, text hash, parent/child links, rule IDs, and rights profile.

The first pilot remains three to five editions, selected for question coverage rather than prestige. All current candidates are `uncleared`, including editions of ancient works and publisher catalogue records. Before acceptance, the curator obtains title and copyright pages, confirms translator and printing, requests written permission where needed, stores the signed license or terms snapshot, and logs the exact permitted actions. A prepared publisher-contact template may ask for OCR, searchable indexing, embeddings, excerpt display, provider transmission, commercial use, attribution, territory, term, revocation, and derivative-text rights. It has not been sent. Do not buy or download a book solely to test whether its terms are permissive.

Maintain separate layers for original verse, licensed translation, named commentary, and modern synthesis. A translation is not evidence that the underlying Sanskrit says the same thing; commentary and modern synthesis must never be presented as unattributed original authority. Mixed compilations require passage-level authorship and license records. Rights approval does not establish textual authenticity or predictive validity; editorial review is a separate gate.

## Software, model, and transitive licenses

The dependency bill of materials is separate from book rights. OCRmyPDF's inspected repository license is MPL-2.0; Tesseract and its inspected `tessdata_best` repository state Apache-2.0. These notices do not settle every renderer, image library, font, trained-data, or platform dependency. Ghostscript is distributed by Artifex under licensing choices that may require AGPL compliance or a commercial arrangement; inspect the exact version and transitive package path before shipping. OCR worker images must preserve notices and a machine-readable SBOM with version, source URL, checksum, license expression, and distribution obligations.

Swiss Ephemeris has a dual route in its official license material: AGPL, with obligations including licensing the whole combined software project under AGPL or a compatible license, or a Swiss Ephemeris Professional License obtained from Astrodienst by contract. Calling it through a service does not by itself resolve whether the application's distribution, linking, or hosted use falls within those obligations. Choose a licensing path with counsel before public deployment; this audit is not a conclusion that the whole application is AGPL or exempt.

The inspected `intfloat/multilingual-e5-small` model card declares MIT. Preserve the exact model revision and card/license text; verify tokenizer files, weights, training-data terms, and any wrapper package separately. Model license permission does not grant rights to the books used as embedding input. Embeddings and OCR derivatives remain subject to source-license restrictions where they reproduce or enable access to protected expression; do not assume vectors are automatically uncopyrightable or safe to publish.

Creative Commons licenses are standardized permissions, not a blanket “open” label. CC BY permits adaptation and commercial use with attribution; CC BY-SA adds a same-or-compatible-license condition for adaptations. CC BY-NC limits use to noncommercial purposes, and CC BY-NC-SA combines that limit with ShareAlike. Check the exact deed and legal code, attribution requirements, notices, modification marking, database rights, and excluded third-party material. A CC license may not answer AI or provider-processing questions; record an explicit interpretation or obtain permission. Never apply a license to a work where the uploader lacked authority.

## Withdrawal, expiry, and propagation

Withdrawal is a serving decision first. On notice, expiry, failed renewal, or rights-generation mismatch, mark the edition blocked, remove it from retrieval filters, invalidate excerpt caches, and prevent new provider transmission immediately. Then identify answers, exports, logs, jobs, object versions, PostgreSQL rows, Qdrant vectors, OCR derivatives, normalized text, embeddings, and saved citations that contain disallowed material. Purge or redact according to the license and retention schedule, retaining only a restricted audit record of the action. Rebuild or retire affected corpus generations; never reactivate a partial or expired generation.

Propagate rights generation and source hashes into every answer and export. Cached answers must be rechecked before display. Existing user downloads cannot be recalled; mark the affected citation and provide a replacement or withdrawal notice. Renewal dates, auto-renewal authority, termination notice periods, and post-termination deletion duties belong in the ledger. Test restore procedures: backup replay must preserve withdrawal tombstones and deny serving while vectors or provider copies remain unresolved. A provider cannot be assumed to delete a transmitted excerpt unless its contract and operational evidence support that claim.

## Release gates and open legal work

Before real-user mode, a qualified reviewer should confirm launch-jurisdiction public-domain findings, translation and commentary ownership, commercial terms, provider transmission and retention clauses, AGPL/professional Swiss Ephemeris choice, Ghostscript and transitive dependency obligations, and the meaning of any CC license for the intended use. Record counsel, scope, date, and license versions; review is not a one-time universal approval.

The release is blocked when an edition lacks action-specific rights evidence, when a source's provider-processing permission is unclear, when OCR or model dependencies lack an SBOM, when a withdrawal cannot be propagated through caches and backups, or when attribution cannot be generated reliably. This matrix supports due diligence; it is not a legal opinion and does not replace advice for the selected jurisdictions, contracts, or commercial launch.

## Inspected primary sources

- U.S. Copyright Office, *Circular 14: Copyright in Derivative Works*, https://copyright.gov/circs/circ14.pdf (accessed 2026-11-15).
- Creative Commons license overview and legal codes, https://creativecommons.org/cc-licenses/ and https://creativecommons.org/licenses/by-sa/4.0/legalcode.en (accessed 2026-11-15).
- Astrodienst Swiss Ephemeris licensing information and repository license, https://www.astro.com/swisseph/swephinfo_e.htm and https://raw.githubusercontent.com/aloistr/swisseph/master/LICENSE (accessed 2026-11-15).
- `intfloat/multilingual-e5-small` model card, https://huggingface.co/intfloat/multilingual-e5-small (MIT declaration; accessed 2026-11-15).
- OCRmyPDF license, https://raw.githubusercontent.com/ocrmypdf/OCRmyPDF/main/LICENSE; Tesseract license, https://raw.githubusercontent.com/tesseract-ocr/tesseract/main/LICENSE; Ghostscript licensing, https://ghostscript.com/licensing/ (accessed 2026-11-15).

These sources were inspected for license text or official statements. They do not establish permission for any astrology edition, provider contract, or complete dependency graph.
