# Progress, risks and open decisions

Updated 2026-11-16. This file began as a planning-phase record; the current milestone table below and [implementation progress](../implementation/PROGRESS.md) supersede its earlier planning-only status statements.

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
| Feasibility and project setup | Implemented; local checks and CI pass | Provider smoke, measured host capacity, production artifact and recovery evidence |
| Auth and profiles | Implemented; offline OIDC/session/ownership tests pass | Live Google client/callback configuration and real OAuth test |
| Calculation engine | Implemented; 33 native unit/edge tests and CI pass | Independent position references, reviewed near-station tolerance, license decision |
| Rights-cleared pilot corpus | Not acquired | Edition rights, artifact hashes, editorial review |
| Retrieval | Implemented with synthetic fixtures and CI Qdrant tests | Licensed corpus, held-out retrieval evaluation and model/host measurements |
| Rule validation | Conservative evidence validation implemented | Expert-reviewed astrological predicates, disagreement set and applicability labels |
| Answer workflow | Bounded workflow and offline Responses contract tests implemented | Live provider review/smoke and expert grounding/abstention evaluation |
| UI and privacy | Core screens and privacy jobs implemented; synthetic browser flow exercised | Remaining interaction fixes, full keyboard/screen-reader audit and operational deletion proof |
| Deployment | Local app and CI services; documentation site is public | Production app host, image/Compose run, restore drill and live operations |

At the end of the initial planning phase on 2026-11-15, no dependencies or skills had been installed and no application code had been written. No request used the credential supplied in chat; no books have been acquired or indexed. Repository and public-site creation happened in a later phase.

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

The original documentation-only verification is recorded below. Application and CI evidence is now summarized in [implementation progress](../implementation/PROGRESS.md); the measured checks do not cover live-provider behavior, expert astrology quality, or production operations.

## Initial independent builder review — 2026-11-15

The reviewer identified four substantive gaps, all corrected in the core design: (1) session-only chart support was promised without a contract, so it is explicitly deferred and saved profiles require consent; (2) free-demo privacy jobs lacked a reliable executor, so a synthetic-only demo is distinguished from a real-user beta requiring a proven scheduler/worker; (3) Recall@10 denominator differed across documents, now defined on 86 supported questions within the 100-item held-out set (later fixed allocation) before top-8 answer selection; (4) birthplace search/timezone suggestion lacked task ownership, now assigned to the places service and Task 3 with manual-fallback tests.

The user then requested substantially deeper research and twenty additional research-agent assignments. See [expanded research program](42-expanded-research-program.md). Final integration review was completed after that work was incorporated; see dossier 41.


## Research 23 delivered

The time/place dossier adds finite candidate preservation for unresolved local-time folds, pinned timezone source requirements, pre-1970 uncertainty, skipped dates and non-hour transitions. Its acceptance cases are inputs to Task 3. Nominatim remains opt-in after policy review; manual coordinates and timezone entry remain available.


## Expanded research completion — 2026-11-15

Twenty additional agents were assigned distinct research topics and ran in waves of up to three researchers plus the coordinator. Dossiers 22–41 are all written. Earlier specialist follow-ups produced the deeper domain, 42-work bibliography, competitor and UI dossiers 18–21. One database researcher disconnected after writing its complete file; the coordinator read and checked the saved artifact. The assignment status table records this accurately.

The final integration review identified and the coordinator resolved: explicit-submit geocoder behavior, canonical request versus answer statuses, timeout versus explicit cancellation, missing cancellation/job/export/profile/chart endpoint contracts, exact 86-answerable/14-unanswerable held-out allocation, source-layer attribution, physical Qdrant collection authority, conditional application-encryption tests, and consistent calculated/traditional/AI-synthesis labels with empirical validity kept separate.

Research was delivered before implementation authorization. The application is now implemented and locally testable, while rights acquisition, live provider validation, measured hosting fit, book ingestion, expert labels, independent ephemeris validation and production operations remain open. This remains a build specification with release gates, not a claim that all research uncertainties are settled.




## Final documentation verification — 2026-11-15

The planning-phase check covered 46 Markdown files: zero broken local links, credential-pattern findings after token-boundary matching, Unicode replacement characters, or unbalanced fenced blocks. At that time the repository contained no application files or dependency artifacts. A broad preliminary secret regex matched part of the official NIST risk-management URL; inspection confirmed a false positive, and the final scan used token boundaries. External source accessibility and research completeness remain governed by each dossier's source register; local link checking is not a claim that every external URL stays available.


## Publishing phase — November 15, 2026

The user subsequently authorized a public repository and static GitHub Pages guide. README, REPORT, contribution rules, policy44, static assets and documentation CI were added in that publication phase. The Pages site remains a reading guide, separate from the locally running Python application. Earlier no-repository/no-application statements describe only their dated planning snapshot. Current app checks and production gates are recorded in [implementation progress](../implementation/PROGRESS.md).
