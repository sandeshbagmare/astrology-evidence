# OCR and multilingual quality

Research date: 2026-11-15. Proposed specification; no books downloaded, OCR executed, or accuracy benchmark measured. Extends [corpus rights](06-corpus-and-sources.md), [ingestion](07-ingestion-and-retrieval.md), and [editorial acquisition](19-corpus-acquisition-and-editorial-playbook.md). Numeric limits below are initial engineering choices requiring a licensed pilot.

## Evidence and tool choice

OCRmyPDF relies on Tesseract language packs and defaults to English unless languages are supplied. Tesseract lists Sanskrit `san`; its command documentation demonstrates `script/Devanagari` for Devanagari and English and notes language ordering matters. These are capabilities, not Sanskrit/IAST accuracy evidence. Compare `san+eng`, `eng+san`, and `script/Devanagari` on identical held-out pages; evaluate IAST regions separately. Never substitute Hindi solely because the script matches. [S1–S3]

Extract native text first, use OCRmyPDF for searchable derivatives where appropriate, and retain Tesseract region output for review coordinates. OCRmyPDF distinguishes skipping text pages, replacing invisible OCR, and force-rasterizing content. Existing text therefore does not prove usable text. The inspected documentation describes newer `--mode` names alongside legacy flags: use the pinned release's interface. Force processing can flatten content and discard structural markup. Preserve the original independently. [S4]

Tesseract documents hOCR bounding boxes and confidence, and TSV page/block/paragraph/line/word fields. Its quality guide recommends adequate resolution and deskewing, while identifying table recognition as problematic without custom layout analysis. A heavier parser is a pilot challenger, not an assumed cure. [S2,S5]

## Proposed pipeline

1. **Admit:** verify edition-specific OCR, storage, indexing, provider-processing and display rights. Hash immutable input and record its acquisition manifest. Hold encrypted or malformed files for operator resolution; never repair the sole original.
2. **Inspect in isolation:** enumerate pages, dimensions, fonts and candidate text. Flag replacement characters, suspicious private-use mappings, duplicated lines, impossible character distributions and visual disagreement. Inspect representative native-text pages manually. Plausible English word counts do not validate Devanagari extraction.
3. **Classify regions:** separate verse, translation, commentary, footnotes, headers, illustrations and tables. Route native/OCR extraction regionally where feasible. Retain conflicting candidates; agreement among engines does not establish correctness.
4. **Recognize:** start at 300 dpi and compare higher resolution on difficult crops. Preserve images before/after rotation, deskew and thresholding. Small marks may be diacritics. Retain language/layout configurations and hashes. [S1–S5]
5. **Reconstruct:** establish columns and reading order before linking verses/translations. Extract table cells with headers and spans; quarantine unresolved tables. Associate footnotes with actual anchors. Never flatten charts into prose or merge adjacent commentators.
6. **Review:** retain raw extraction, normalized text and reviewed transcription separately. Critical corrections require image comparison and second-reviewer resolution. Record old/new text, reviewer, reason, timestamp and coordinates.
7. **Publish:** require rights, attribution, quality and coordinate gates. Skipped/timed-out pages remain incomplete. Publish reviewed passages from partial editions only with complete local context and a coverage manifest. Corrected revisions invalidate affected indexes and cached excerpts.

## Unicode, transliteration and names

Preserve exact Unicode transcription. Use NFC for a separate canonical comparison field: Unicode distinguishes canonical normalization from compatibility folding that can remove distinctions. Never replace archival text with NFKC or strip combining marks globally. Maintain normalized-to-reviewed offset mappings because code-point counts can change. [S6]

Retain IAST diacritics, Devanagari signs, avagraha, danda/double danda and joiners in faithful transcription. Inspect unexpected controls rather than assuming every invisible character is garbage. Test precomposed/decomposed forms such as macron-bearing vowels. OCR repair is distinct from normalization.

ICU describes transliteration as script conversion, not translation, and does not universally guarantee inversion. Generate search aliases with named, versioned transforms and reviewed exceptions. Do not label generic Indic-to-Latin output IAST compliant without mapping tests. ISO 15919, IAST and ALA-LC require distinct scheme labels and verification; no equivalence is certified here. The Library of Congress Sanskrit romanization PDF was reachable but not textually inspected. [S7,S11]

Glossary aliases can link `Śani`, `Shani`, `शनि`, and Saturn without replacing quotation spellings. Preserve ambiguous names and contextual meanings. Critical classes include planets, negation, conjunction/disjunction, conditions/exceptions, houses, signs, degrees, dates and verse locators. Never correct an unexpected planet into a statistically likely one. Sanskrit negation requires language-aware review beyond a standalone-word list.

## Layout and provenance

Every span records original-file and image hashes, zero-based PDF page index, separate printed page label, region ID, reading-order index, attribution, and bounding boxes. Record units, origin, image dimensions, DPI, crop offset, rotation and the transform to the original page. Use multiple boxes/polygons when one rectangle would include another column. Coordinates without image identity and transforms are not reproducible provenance.

ALTO offers a useful exchange model with upper-left coordinates, measurement units and reading-order support; equivalent internal fields suffice. Tesseract TSV coordinates must not be mistaken for PDF points. Test overlays after crop, deskew and rotation. Multipage passages retain each span's page reference. [S2,S8]

Translations/commentaries have separate authorship and alignment links, including one-to-many or uncertain links. Region labels cannot infer authorship. Parallel Sanskrit/English columns differ from two successive commentary columns. Review every layout template and transition.

## Acceptance matrix and audit

These are proposed gates, not results. CER is edit distance over a declared character representation divided by reference length; report code-point and grapheme-aware variants separately. WER requires a declared tokenizer. Aggregate metrics cannot alone detect lost negation, wrong house numbers or swapped attribution.

| Fixture / stratum | Required assertion | Failure handling |
|---|---|---|
| English, Devanagari, IAST, mixed script | Separate CER/WER; proposed page-review trigger CER above 1% | Review/rerun; no average hides a failing script |
| Planets, negations, numerals, conditions | 100% reviewed critical-token agreement on published passages | Block passage/linked rules until dual review |
| Devanagari/Arabic numerals, verse punctuation, Roman preliminaries | Exact locator mapping; retain printed form | Quarantine ambiguous locator |
| Invisible OCR or broken font mapping | Image/text comparison detects seeded corruption | Rerender/review; skipping never implies approval |
| Columns, footnotes, commentary changes | 100% correct attribution/reading order in reviewed release sample | Expand audit of affected layout family |
| Tables and chart labels | Every value preserves row/column or chart-cell context | Exclude unresolved structured content |
| NFC/decomposed diacritics and aliases | Equivalent search; unchanged quotations; resolving offsets | Fail normalization configuration |
| Cropped, rotated, multipage passages | Highlights land on correct image regions | Block publication and preview |
| Timeout, oversized, malformed/encrypted PDF | Bounded termination and explicit incomplete status | Quarantine; process exit alone cannot approve |

For each of the first 3–5 editions, inspect at least ten pages: two randomly drawn from each available English, Devanagari, IAST, mixed-layout and table/footnote stratum. Redistribute absent strata and record their absence. Save sampling seed and inventory. Add all pages supporting executable rules, every layout transition and every flagged page; these do not count as random sampling.

One reviewer transcribes without seeing OCR; a second adjudicates discrepancies and verifies critical spans. Divide pages into development and untouched evaluation sets before configuration selection. Report pages, characters, words and critical tokens by script/layout, exclusions and reviewer disagreement. Ten pages are an acquisition minimum, not edition-wide accuracy proof. A critical error expands inspection to passages sharing its font/layout/configuration; release only corrected, reviewed passages.

## Worker isolation and licensing

Proposed initial limits: 250 MiB input, 1,000 pages, 40 megapixels per render, two concurrent OCR processes, 4 GiB memory, 10 GiB scratch storage, 120 seconds/page and 60 minutes/job. Adjust from licensed pilot measurements. Oversized editions require bounded batches. OCRmyPDF documents timeout and large-image skipping, but these do not isolate hostile parsers. [S4]

Run parsing/OCR in a disposable non-root worker with no network, no application/provider secrets, read-only input, bounded scratch space and process/CPU/memory limits. Cancel the entire process tree; validate output paths, types and page manifests outside the worker. Avoid unauthorized source text in logs. Attachments, links and embedded instructions remain data. Searchable derivatives are not security certifications.

Inspect locked artifact licenses, renderers, image libraries, fonts and traineddata. Inspected OCRmyPDF uses MPL-2.0; Tesseract and tessdata_best show Apache-2.0. This does not settle transitive dependencies, distribution duties or book rights. Preserve notices and require a dependency/license manifest before deployment. [S9,S10]

## Primary sources and access limits

All successful inspections used direct HTTP on 2026-11-15; web search returned no usable results. No benchmarks were reproduced.

- S1: https://ocrmypdf.readthedocs.io/en/latest/languages.html — language packs and multilingual selection.
- S2: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html — language order, script model, hOCR, TSV.
- S3: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html — Sanskrit availability.
- S4: https://ocrmypdf.readthedocs.io/en/latest/advanced.html — OCR modes, structure, time/image limits.
- S5: https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html — image preparation, segmentation, tables.
- S6: https://www.unicode.org/reports/tr15/ — normalization semantics.
- S7: https://unicode-org.github.io/icu/userguide/transforms/general/ — transliteration and inverses.
- S8: https://www.loc.gov/standards/alto/ and https://www.loc.gov/standards/alto/v4/alto-4-4.xsd — layout, reading order, coordinates.
- S9: https://raw.githubusercontent.com/ocrmypdf/OCRmyPDF/main/LICENSE — engine license.
- S10: https://raw.githubusercontent.com/tesseract-ocr/tesseract/main/LICENSE and https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/LICENSE — engine/model license texts.
- S11: https://www.loc.gov/catdir/cpso/romanization/sanskrit.pdf — HTTP 200 only; content uninspected, mapping verification pending.

OCRmyPDF security/cookbook pages returned HTTP 429; attempted repository security-document paths returned 404. Isolation above is proposed engineering policy, not attributed to inaccessible documentation. Pin revisions during implementation; mutable URLs are not dependency locks.
