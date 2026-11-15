# Evaluation and benchmark design

Status: proposed protocol, 2026-11-15. No questions have been annotated, no benchmark has run, and no result is claimed. This document operationalizes the targets in 01, 07 and 24; numerical examples are illustrations. Evaluation establishes evidence-handling quality, not whether astrology predicts events.

## Research basis and limits

BEIR evaluates heterogeneous retrieval tasks and finds BM25 a robust baseline, with reranking often improving effectiveness at additional computational cost. Its implication here is to compare lexical, dense and hybrid retrieval across explicit question strata; its published results do not select an astrology retriever. [S1]

The original RAGAS paper separates faithfulness, answer relevance and context relevance, using automated proxies without reference answers. Its experiments use GPT-3.5-turbo-16k to evaluate prompts; dependence on that evaluator is a methodological limitation for this project. WikiEval agreement does not validate Sanskrit, edition attribution or conditional astrological reasoning. Therefore use automated scores for development triage, calibrated against experts; never substitute them for release annotations. Freeze evaluator model, prompt and metric implementation, and retain disagreements rather than averaging expert and model scores. This is a project inference from the paper's scope and limitations. [S2]

ALCE separates answer correctness and citation quality, distinguishing whether citations collectively support a statement from whether individual citations contribute support. Its appendix documents a limitation of automatic precision when a citation partially supports a statement. Our protocol consequently uses atomic claims and expert judgments, allowing jointly sufficient evidence. [S3]

## The 150-question inventory

Assign mutually exclusive primary categories and additional tags. Proposed exact allocation:

| Primary category | Calibration | Development | Held out | Total |
|---|---:|---:|---:|---:|
| Direct concepts and source lookup | 7 | 10 | 33 | 50 |
| Chart-conditioned rules | 5 | 8 | 27 | 40 |
| Multilingual/transliteration | 3 | 4 | 13 | 20 |
| Contradictions and exceptions | 3 | 4 | 13 | 20 |
| Unanswerable/adversarial | 2 | 4 | 14 | 20 |
| Total | 20 | 30 | 100 | 150 |

The first 86 held-out questions must be answerable from authorized evidence under their supplied conditions, possibly through an explanation of disagreement. All 14 remaining questions deliberately require abstention from the requested unsupported conclusion; four additionally contain adversarial instructions. If expert review cannot substantiate an item, replace it before freezing. Never relabel answerability after seeing outputs. This 86/14 allocation is the canonical release inventory across the core documents.

Tags cover exact verse lookup, paraphrase, OCR damage, IAST/ASCII/Devanagari variants, commentary versus root text, multiple editions, translation disagreement, missing qualifiers, and contradictory schools. Chart fixtures specify tradition, ayanamsha, house convention and deterministic facts. Include unknown birth time, boundary-sensitive placements, missing location, and rules requiring conditions absent from a fixture. Questions requiring missing chart facts belong in the abstention category; an answerable conceptual question can explain why those facts matter.

Examples are specifications, not invented doctrinal assertions: “What does the licensed edition say, including its exception?” requires the qualifying passage; “Do these two commentaries agree?” requires both sources; “Give my exact marriage date despite unknown birth time” requires refusal of unsupported precision. Cross-language variants share a family ID and never count as independent evidence of broad language coverage.

Split by connected work/topic families before drafting variants: group the same root work, its editions/translations, derivative paraphrases, and narrowly identical rule families. A group belongs to one partition. Ensure sufficient independent groups before committing to the table; an undersized corpus requires more lawful source coverage or a narrower explicitly labeled benchmark, not random chunk splitting. The complete authorized source corpus remains searchable: holding out questions is not withholding their evidence. Prevent tuning access to held-out questions, labels and examples; generic indexing of held-out works remains allowed. Record duplicates, group allocation, corpus hashes and contamination risks from model pretraining. Broad planetary vocabulary inevitably overlaps; disclose that narrow rule/work separation does not establish universal domain generalization.

## Gold evidence and blind review

Two qualified reviewers independently annotate every item and every release output. Match language expertise to the item and disclose school affiliations and conflicts. Calibration uses the 20 visible items to reconcile the rubric; development uses 30 items to select configuration. Seal the 100 test questions and annotations with an evaluation custodian before tuning.

For gold evidence, reviewers search the authorized corpus independently, then assess a pooled candidate set from lexical, dense and hybrid systems without rank or system labels. Store edition-specific passage IDs, relevance grades, alternative equivalent passages, required qualifiers, conflicts, expected answer units and abstention reasons. Deduplicate equivalent windows into evidence units with acceptable passage IDs; a unit may be a supporting rule, exception or competing interpretation. Record incomplete judgments and expand pools before freezing; do not treat every unjudged passage as definitively irrelevant.

For output review, randomize order and mask configuration/provider identity, automated scores and the other reviewer's labels. Show question, deterministic fixture, cited source text and relevant parent context. Reviewers independently segment substantive claims and mark support, applicability, omitted exceptions, attribution and uncertainty. Preserve original labels, agreement percentage and Cohen's kappa for categorical judgments, noting prevalence effects. Discuss disagreements only after independent submission; unresolved cases go to a third domain adjudicator. Keep rationale and version history. Expert inability to establish an answer is a benchmark defect requiring documented replacement before the run, not a convenient post-run exclusion.

## Metrics with fixed denominators

For answerable question q, let Gq be its adjudicated relevant evidence units. Recall@10(q) is units represented among the first ten fused, deduplicated candidates divided by |Gq|. Macro-average over all 86 answerable questions, including retrieval errors as zero. This is measured before reranking/top-eight generation selection; parent expansion cannot retroactively improve it. Report Hit@10 separately: one relevant hit is not full recall. Also report evidence survival into the final eight and completeness after parent expansion.

Use the shared four-level rubric from dossier 24: 0 irrelevant/incompatible, 1 related terminology without usable support, 2 useful partial support or necessary qualification, 3 directly addressing the claim with applicable conditions. Keep exception and alternative-view flags separate. Compute nDCG@10 using gains 2^grade−1 and logarithmic rank discount, normalized by the ideal judged ranking for that question, then macro-average over answerable questions. Equivalent duplicate windows gain credit once. Report Precision@10 as relevant units in ten slots divided by ten, counting missing slots as nonrelevant. These are project metric definitions, informed by heterogeneous retrieval evaluation [S1]; document the evidence-unit mapping so another evaluator can reproduce them.

Claim support is fully supported substantive traditional claims divided by all such generated claims, including uncited claims. Full support requires authorized cited evidence, correct tradition/edition attribution, satisfied chart conditions and preserved material exceptions. Partial, contradictory or unverifiable claims fail. Report pooled claim support and per-answer support; empty answers are N/A for support and fail answer coverage. Coverage is expected answer units correctly delivered divided by all expected units on answerable questions, preventing refusal or verbosity from gaming support.

Citation precision is contributing claim–citation links divided by all displayed claim–citation links. A link contributes when it supports part or all of an atomic claim and the complete cited bundle supports that claim. Separately report citation completeness: fully citation-supported substantive claims divided by all substantive claims. This expert adaptation follows ALCE's distinction rather than claiming identity with its automatic implementation. [S3]

ID resolution is authorized, edition-correct displayed citation occurrences divided by all displayed citation occurrences. Quote fidelity is exact approved-source matches divided by all displayed quotes, under the exact-original Unicode span and explicit multi-span ellipsis policy in dossier 26. Report counts of unique IDs too. No quotes means fidelity N/A, not 100%; a separate fixed quote-rendering fixture suite must exercise quoting.

Abstention recall is correct abstentions divided by the 14 gold-unanswerable questions. Success requires avoiding the unsupported conclusion and explaining the missing evidence/condition; a disclaimer followed by a prediction fails. Abstention precision is correct abstentions divided by all abstentions. Report false abstention rate on the 86 answerable questions and coverage alongside recall. Timeouts and malformed answers are failures, not successful abstentions.

## Uncertainty and experiment budget

Publish every numerator/denominator and 95% interval. Use Wilson intervals for question-level binary rates and exact binomial intervals when counts are small or all successes occur, following NIST's guidance. [S4] Claims within an answer are correlated: estimate claim-support uncertainty by resampling whole question families and recomputing the ratio, not by treating hundreds of claims as independent trials. Use 10,000 paired cluster-bootstrap resamples for macro retrieval metrics and configuration differences; preserve each family's variants, publish seed and method, and disclose the number of independent clusters. Few clusters make intervals unstable; more resamples cannot repair insufficient evidence.

A 95% observed target with 14 abstention cases requires 14/14: 13/14 is only 92.9%. Even 14/14 has an exact two-sided 95% lower bound of approximately 76.8%, calculated as 0.025^(1/14). This meets the sample gate but cannot substantiate 95% population reliability. A future claim that a one-sided exact lower bound exceeds 95% requires at least 59 independent all-success cases; dependent variants do not qualify. These are illustrative binomial calculations, not observations. [S4]

Budget at most six prespecified retrieval configurations on development, two generation finalists, and one frozen release candidate. Run one scored response per held-out question plus two additional runs on a preregistered 20-question stability subset: 140 release generations. Extra runs diagnose instability and never replace first-run failures. Bootstrap reuses observations without model calls. Reserve two independent reviews per response, plus adjudication; if resources cannot cover this, delay evaluation instead of silently using a judge model.

## Release decision and regression

| Check | Proposed decision rule |
|---|---|
| Retrieval | Macro Recall@10 ≥0.90 on all 86 answerable items before top-eight selection |
| Support | Expert claim support ≥0.95; report coverage and false abstention to prevent gaming |
| Abstention | ≥0.95 on 14 unsupported items, therefore all 14 must pass |
| Provenance | 100% ID resolution and quote fidelity across exercised cases; any defect blocks |
| Security | Zero unauthorized retrieval, disclosure or instruction execution in separate adversarial suite |
| Regressions | Any new critical exception, tradition-mixing or unsupported-precision failure blocks; other declines require documented review |
| Uncertainty | Publish intervals; sample gates permit only a limited pilot, not a population reliability claim |

Keep security fixtures separate from quality averages: cross-user ownership, withdrawn rights, stale caches, prompt injection and malicious citation identifiers require deterministic authorization checks and output inspection. The four overlapping benchmark attacks do not replace this suite. Calculation correctness likewise needs separate reference fixtures. Neither calculation accuracy nor source faithfulness measures real-world predictive accuracy; that would require a separate prospective, preregistered outcome study with baselines and independent analysis.

Freeze configuration, corpus, glossary, prompts, provider/model revision and scoring artifacts. On any relevant change, rerun development, provenance/security fixtures and affected strata; compare the candidate against the previous release using paired observations. Inspect uncertainty and individual losses, not only averages. Once held-out failures influence tuning, designate that set a regression suite and commission fresh sealed release items. Archive failed runs and decisions; never repeatedly tune against the same “held-out” score.

## Primary sources checked 2026-11-15

- [S1] Thakur et al., *BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models*, NeurIPS 2021, arXiv:2104.08663v4. Primary abstract inspected; claims above are limited to its benchmark scope and reported comparison.
- [S2] Es et al., *RAGAS: Automated Evaluation of Retrieval Augmented Generation*, EACL 2024, ACL Anthology 2024.eacl-demo.16, DOI 10.18653/v1/2024.eacl-demo.16. Primary ACL record and arXiv:2309.15217v2 HTML inspected, including WikiEval and evaluator setup; domain-transfer limits above are our inference.
- [S3] Gao et al., *Enabling Large Language Models to Generate Text with Citations*, EMNLP 2023, arXiv:2305.14627v2. Primary full text inspected, especially citation quality and appendices E–F.
- [S4] NIST/SEMATECH, *e-Handbook of Statistical Methods*, section 7.2.4.1, “Confidence intervals.” Primary guidance inspected for Wilson, one-sided and exact small-sample binomial intervals.



Primary source URLs: https://arxiv.org/abs/2104.08663 ; https://aclanthology.org/2024.eacl-demo.16/ ; https://arxiv.org/abs/2305.14627 ; https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm . Versioned records identified above should be retained in evaluation manifests.


