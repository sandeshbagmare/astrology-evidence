# Offline extraction and recorded-result evaluation

Implemented November 15, 2026. These are operator tools, not public upload endpoints. They create extraction drafts and evaluation reports; they do not grant rights, publish sources, call models, or manufacture expert labels.

## Extraction

Run `python -m astrology_evidence.corpus.extract SOURCE --work-root DIRECTORY`. The source must resolve beneath the existing work directory. Supported formats are UTF-8 `.txt` (form feed separates pages), `.json` page records, and native-text `.pdf` with the optional `pypdf` dependency installed. JSON accepts only `pages`, each containing `text`, zero-based `pdf_page_index`, optional `printed_page`, and optional `[left, top, right, bottom]` bounding box. Page indices must be unique nonnegative integers. Printed labels stay separate from PDF indices; text and source hashes retain provenance. Coordinates are preserved when supplied; native PDF extraction does not invent boxes or printed page labels.

Inputs are bounded to 20 MB, 500 pages, 100,000 characters per page and 10 MB total extracted text. UTF-8 decoding is strict. Every nonempty native page remains pending human review. Blank pages are quarantined with `ocr_required`; the PDF adapter never pretends that native extraction performed OCR. Rights and attribution review must precede later import through the existing reviewed-edition importer.

The `ocr_image` Python adapter accepts an operator-selected absolute executable and an image already rendered by the operator. It copies bounded image bytes to a fresh job directory, uses fixed Tesseract English/PSM-3/TSV arguments, `shell=False`, a 1–120 second timeout (30 default), one OpenMP thread, a reduced environment and a 2 MB validated output read. It preserves word boxes and uses the minimum word confidence as a conservative quarantine trigger; below 0.90 requires quality review. Even higher confidence is pending review, never approved. Its source hash identifies the page image, not a PDF it has never seen. The caller supplies the original PDF page index and printed label.

**Security limitation:** these are application bounds, not an OS sandbox. PDF decompression can allocate resources before extracted-text checks. The subprocess can access the host network/filesystem, and timeout/output-read checks do not cap temporary disk growth or peak memory. Run both parsing and OCR in an operator-provisioned isolated job with denied network, read-only source mounts, limited CPU/memory/disk/processes and no credentials. No secured production OCR worker or PDF rasterizer is implemented. TSV words are joined for a review draft; layout, columns, numerals and negations require source-image review. No real books were downloaded or indexed.

## Evaluation

Run `python -m astrology_evidence.retrieval.evaluation examples/evaluation.synthetic.json --allow-small-synthetic` or supply a real recorded-result JSON file without the small-set flag. `--split` selects `calibration`, `development` or `test` (default). The input has `schema_version: 1`, an explicit `synthetic` boolean and an `items` array. Each item contains:

- Unique `id` and `split`.
- `expected_evidence_units`: passage/evidence ID to integer relevance grade 0–3; positive grades are relevant, all-zero/empty maps are unsupported questions.
- `ranked_ids`: ordered unique IDs from retrieval before top-8 generation selection.
- `status`: `ok` or `error`, and `abstained`: boolean.
- `claim_count` and `supported_claim_count`: nonnegative reviewer counts, with support no greater than claims.

The normal validator requires exactly 20 calibration, 30 development and 100 held-out items, including 86 supported and 14 unsupported held-out questions. The explicit small-set flag requires a synthetic label. Question IDs cannot recur across splits. Semantic topic/edition leakage, split freeze, expert qualifications, claim support and reviewer agreement still need independent review; JSON cannot certify them.

The report contains every selected input and its status, counts and macro Recall@10, Hit@10 and graded nDCG@10. Recall is retrieved relevant units divided by all expected positive-grade units for each supported question, then averaged over supported questions. Hit measures whether any relevant unit appeared. nDCG uses `(2^grade - 1) / log2(rank + 1)` with one-based ranks and ideal descending grades. Only the first ten ranks count. Errors receive zero retrieval scores and remain in supported denominators. Claim support reports supported reviewed claims / all recorded claims; an error contributes zero support but retains its recorded claims in the denominator. Errors with no claims cannot enlarge a claim-based denominator, so the separate error count must accompany that rate. Abstention is successful explicit abstentions / all unsupported questions, including failed unsupported inputs in the denominator. Undefined rates are JSON null.

The supplied four-item fixture is synthetic arithmetic verification, not a corpus-quality result: two supported, two unsupported, two errors; Recall@10 0.25, Hit@10 0.5, nDCG@10 0.45865970635647857, claim support 1/2, abstention 1/2. No 150-question expert corpus exists yet. The CLI reads recorded results only and never substitutes model judgments for expert support labels.

## Verification

25 focused tests pass on the available Python 3.14 test runtime, including malicious size/path/page metadata, duplicate rankings/questions, invalid grades/counts, error denominators, exact small metrics, rank-11 exclusion, release split validation, CLI JSON output, adapter timeout and OCR boxes/confidence. Native PDF parsing is currently tested with an adapter double; a real permitted PDF and installed Tesseract integration remain operator checks. Application-wide checks are recorded by the coordinating implementation task.

Full-suite observation on this Python 3.14 runtime: 272 passed, 2 skipped, 9 failed. Eight failures in `test_calculations.py` require unavailable native `swisseph` (`test_fold_keeps_two_candidates_and_explicit_choice`, `test_approximate_cross_midnight_withholds_facts`, `test_chart_invariants_and_manifest`, `test_concurrent_matches_serial`, `test_swiss_without_files_fails`, `test_unconfirmed_history_and_poles_withheld`, `test_settings_and_input_digest_change`, `test_concurrent_missing_swiss_files_cannot_change_moshier`). The concurrent web work also produced `test_fact_table_names_rounding_and_escaping`; the coordinator was notified for combined-revision verification. Focused extraction/evaluation tests, Ruff and mypy passed.
