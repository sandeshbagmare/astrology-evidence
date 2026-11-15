# Progress, risks and open decisions

Updated 2026-11-15. Status reflects this documentation task, not a running application.

## Work completed in this task

- [x] Created documentation-only project folder and root AGENTS.md.
- [x] Defined product scope and explicit proposed defaults.
- [x] Researched public competitor/project sources and documented access limitations.
- [x] Compiled a candidate bibliography and edition-specific acquisition/rights process.
- [x] Designed architecture, data/API contracts and calculation boundary.
- [x] Specified retrieval, chunking, local embeddings and evaluation gates.
- [x] Specified Google authentication, UI configuration and privacy flows.
- [x] Compared local, free-demo and production deployment paths.
- [x] Documented supplied provider settings without copying the secret.
- [x] Defined code standards and a sequenced implementation plan.
- [x] Independent initial builder review; issues corrected in core design.
- [x] Twenty additional focused research assignments delivered; final integration audit performed.
- [x] Final documentation link/secret/format verification; results recorded below.

Three specialist research agents worked alongside the coordinator, within the environment's four-active-agent limit. A further independent integration review was performed after the expanded research. No claim of 10–50 concurrent agents is made.

## Implementation status

| Milestone | Status | Completion evidence needed |
|---|---|---|
| Feasibility and project setup | Not started | Locked stack, route contract tests, measured memory and provider smoke test |
| Auth and profiles | Not started | OAuth/session/ownership tests, migration evidence |
| Calculation engine | Not started | Independent reference fixtures and uncertainty tests |
| Rights-cleared pilot corpus | Not acquired | Edition rights, artifact hashes, editorial review |
| Retrieval | Not started | Indexed pilot and held-out evaluation |
| Rule validation | Not started | Reviewed predicates and adversarial citation tests |
| Answer workflow | Not started | Provider contract and grounding/abstention metrics |
| UI and privacy | Not started | Browser/accessibility/export/deletion checks |
| Deployment | Not provisioned | Live host measurements, security and recovery gates |

No dependencies or skills were installed. No application code was written. No API request using the user's key was made. No books were downloaded or indexed. No Git repository or public service was created.

## Decisions proposed for the user to review

| Question | Working default | When it must be settled |
|---|---|---|
| First astrological tradition? | Vedic/Jyotish natal, explicit Lahiri/whole-sign/mean-node settings | Before domain fixtures and corpus selection |
| Initial languages? | English UI/explanations, licensed original-script source display | Before multilingual quality claims |
| Open-source licensing or commercial license? | Unresolved; no public activation before decision | Before distributing/hosting Swiss Ephemeris integration |
| Is a paid reliable service acceptable after a free demo? | Plan both; no paid resources authorized | Before provisioning production |
| Who reviews rules and translations? | At least one qualified domain lead, second reviewer for evaluation ambiguity | Before claiming support/applicability quality |
| What rights can be obtained? | Acquire 3–5 specific pilot editions with ingestion/excerpt permission | Before real corpus publication |
| Is the supplied provider suitable for sensitive processing? | Unverified; minimize transmitted data; local library/chart still usable | Before sending real user data |
| Product branding and intended market? | Provisional Astrology Evidence, adult private beta | Before public brand/terms and launch |

These questions do not block producing this documentation. They are decision gates for the later build or release. Design proposals can be changed in the decision log.

## Risk register

| Risk | Impact | Mitigation / trigger |
|---|---|---|
| Model fabricates applicability or sources | False authority | Structured claims, verified IDs/spans, expert evaluation, abstention |
| Birth time/history is uncertain | Misleading chart precision | Explicit interval handling and withheld facts |
| Sources disagree or OCR changes a negation | Invalid interpretation | Edition/translation separation, exception retrieval, human review |
| Rights unavailable or withdrawn | Corpus cannot legally be served | Rights gate, small pilot, immediate serving denial and purge |
| Ephemeris licensing incompatible with business model | Public launch blocked | Resolve license path before launch; review binding as well as engine |
| FreeGG changes route/model or keeps sensitive data | Downtime/privacy concern | Contract tests, minimized facts, provider review, no fake fallback |
| LiteLLM converts Responses to chat | 410 regression | Native passthrough test before enabling gateway |
| Free hosting cannot load local model | Demo cannot serve queries | Actual memory benchmark; local deployment or paid compute |
| Free storage sleeps/deletes data | Availability/data loss | Source-of-truth backups, rebuildable vector index, paid reliable tier when needed |
| Cross-user cache/index leakage | Privacy breach | Ownership in queries/cache keys and adversarial tests |
| More corpus decreases relevance | Lower support quality | Grow only after measured evaluation, avoid duplicate-source voting |
| Marketing claims deterministic prediction | Misrepresents capabilities | Product copy distinguishes calculation and tradition; no guarantee language |

## Verification log

Documentation verification and independent review results are appended here after execution. Application test counts remain zero until implementation starts; this is an intentional planning-only deliverable.

## Initial independent builder review — 2026-11-15

The reviewer identified four substantive gaps, all corrected in the core design: (1) session-only chart support was promised without a contract, so it is explicitly deferred and saved profiles require consent; (2) free-demo privacy jobs lacked a reliable executor, so a synthetic-only demo is distinguished from a real-user beta requiring a proven scheduler/worker; (3) Recall@10 denominator differed across documents, now defined on 86 supported questions within the 100-item held-out set (later fixed allocation) before top-8 answer selection; (4) birthplace search/timezone suggestion lacked task ownership, now assigned to the places service and Task 3 with manual-fallback tests.

The user then requested substantially deeper research and twenty additional research-agent assignments. See [expanded research program](42-expanded-research-program.md). Final integration review was completed after that work was incorporated; see dossier 41.


## Research 23 delivered

The time/place dossier adds finite candidate preservation for unresolved local-time folds, pinned timezone source requirements, pre-1970 uncertainty, skipped dates and non-hour transitions. Its acceptance cases are inputs to Task 3. Nominatim remains opt-in after policy review; manual coordinates and timezone entry remain available.


## Expanded research completion — 2026-11-15

Twenty additional agents were assigned distinct research topics and ran in waves of up to three researchers plus the coordinator. Dossiers 22–41 are all written. Earlier specialist follow-ups produced the deeper domain, 42-work bibliography, competitor and UI dossiers 18–21. One database researcher disconnected after writing its complete file; the coordinator read and checked the saved artifact. The assignment status table records this accurately.

The final integration review identified and the coordinator resolved: explicit-submit geocoder behavior, canonical request versus answer statuses, timeout versus explicit cancellation, missing cancellation/job/export/profile/chart endpoint contracts, exact 86-answerable/14-unanswerable held-out allocation, source-layer attribution, physical Qdrant collection authority, conditional application-encryption tests, and consistent calculated/traditional/AI-synthesis labels with empirical validity kept separate.

Research is delivered; implementation, rights acquisition, provider validation, measured hosting fit, book ingestion, expert labels and application tests remain unstarted. This is a detailed build specification with launch gates, not a running product or a claim that all research uncertainties are settled.




## Final documentation verification — 2026-11-15

Checked 46 Markdown files: zero broken local Markdown links, zero credential-pattern findings after token-boundary matching, zero Unicode replacement characters, and zero unbalanced fenced blocks. All project files are Markdown; no application files or dependency artifacts were created. A broad preliminary secret regex matched part of the official NIST risk-management URL; inspection confirmed a false positive, and the final scan used token boundaries. The initial and final independent reviews are recorded above and in dossier 41. External source accessibility and research completeness remain governed by each dossier's source register; local link checking is not a claim that every external URL stays available.


## Publishing phase — November 15, 2026

The user subsequently authorized a public repository and static GitHub Pages guide. README, REPORT, contribution rules, policy44, static assets and documentation CI were added. Earlier no-repository/no-deployment statements describe the original research phase. This publication does not implement or deploy the astrology application. Local documentation tests and an independent review pass; production application gates remain pending.

