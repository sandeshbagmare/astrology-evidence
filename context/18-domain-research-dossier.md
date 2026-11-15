# Domain research dossier: what the astrology engine must know

Prepared 2026-11-15. This extends [the domain contract](05-astrology-domain.md). It is a researched design dossier, not an assertion that the texts have been comprehensively read, that chart calculations have been implemented, or that astrology has demonstrated predictive validity. Source inspection notes appear at the end. Traditional definitions below require edition-specific editorial approval before becoming executable rules.

## 1. Research conclusion and product boundary

The difficult part is not producing a fluent horoscope. It is preserving the difference between an astronomical measurement, a choice of astrological convention, a traditional rule, and an interpretation of that rule for a person. The architecture needs four corresponding artifacts: a reproducible chart; a versioned convention profile; an attributed rule/passage record; and a validated answer. A single vector index and a general chat prompt cannot substitute for those artifacts.

The pilot should cover a small, explicit Parashari-oriented D1 natal vocabulary in English, using 3–5 rights-cleared editions. It should answer questions about how a placement is interpreted and why sources differ. Timing, compatibility and additional schools follow only after their independent conventions and test sets exist. This creates a measurable first product rather than an untestable claim to know all astrology.

There are two different confidence questions. “Are these coordinates and classifications reproducible?” can be tested against reference calculations. “Will the interpreted life event happen?” is a separate empirical question that citations and consistency cannot resolve. The UI must never turn computational precision into a probability of a future event. Authentic traditional passages can contain unsupported, frightening, discriminatory or medically unsafe claims; faithful attribution does not require endorsing or operationalizing them.

## 2. Tradition map and consequences for the architecture

| Family | Research scope | Why it needs separate configuration |
|---|---|---|
| Parashari-oriented Jyotish | Grahas, rashi/bhava distinctions, planetary aspects, dignity, yogas, divisional charts and selected dashas | Text editions and later commentators differ. A named rule set identifies its sources and exceptions. |
| Jaimini | Sign-based techniques, chara karakas and selected rashi dashas | The inspected Jaiminisutras catalogue describes a distinct system and layered translation/annotations. Do not relabel Parashari predicates as Jaimini. |
| Krishnamurti Paddhati (KP) | Stellar/sub-lord analysis and cusp-dependent interpretation | Needs separately verified ayanamsha, house/cusp convention and sub-division algorithm. Swiss Ephemeris documents multiple Krishnamurti ayanamshas. |
| Tajika/annual charts | Annual return techniques and their vocabulary | Solar return calculation, locality choice and annual-chart rules differ from D1 natal interpretation. |
| Prashna/horary | Question-time charts and context-specific rules | Requires question instant/place and its own interpretive scope; birth information is not a substitute. |
| Muhurta/electional | Choosing a time under a declared tradition | Requires search constraints and local calendar; favorable classification is not a guarantee of success. |
| Western Hellenistic/traditional | Tropical or explicitly sidereal conventions, houses, aspects, dignities and time-lord systems | Separate collections and rule namespaces prevent accidental reuse of Vedic terminology. |
| Western modern/psychological | Modern author-specific interpretive frameworks | Label the author's framework; psychological language is not a clinical assessment. |
| Historical astronomy/calendrics | Siddhanta and calendrical literature | Historical context; production positions use a tested ephemeris, not unreviewed historical formulas. |

A tradition profile names zodiac, ayanamsha identifier, house model, node model, aspect model, divisional-chart algorithm, dasha convention, calendar/day-boundary convention and rule-set version. The first release exposes the approved profile; it does not present every engine flag as an equally supported option.

## 3. Coordinate and classification hierarchy

Graha is a traditional category, not the modern astronomical category planet. The standard Jyotish vocabulary includes Sun and Moon, five visible planets, and Rahu/Ketu. The nodes describe points associated with the lunar orbit; they are not physical planets. Store this distinction so explanatory copy does not make an astronomical error while using traditional names.

Swiss Ephemeris distinguishes mean and true lunar-node calculations. Choose mean nodes for the proposed pilot, preserve that choice on every chart, and make node-sensitive differences visible in later comparisons. Do not use a true-node position for one predicate and a mean-node position for another under one unlabeled chart.

A normalized longitude is represented on [0,360). A rashi classification partitions that circle; a house classification depends on house scheme and birth geometry. They are not interchangeable. Whole-sign houses start the first house at the beginning of the sign containing the ascendant, as the inspected Swiss manual explains. The ascendant itself remains a specific degree.

Ayanamsha is a selected relation between tropical and sidereal frames. It must not be inferred from the user's nationality. The Swiss manual discusses multiple sidereal systems and Krishnamurti variants, demonstrating why the full identifier and engine version belong in provenance. Two charts differing near a sign boundary may reflect conventions rather than a broken API.

Retrograde status derives from computed longitudinal motion. It is a chart fact; interpretations are source-specific. Conjunction is not one universal boolean: a rule may require same-sign occupancy, degree separation, a named orb, or a textual relationship. Store the predicate actually used; a lexical synonym is not a mathematical definition.

## 4. D1, D9 and other divisional charts

D1 is the natal pilot foundation. D9/Navamsha is a later, separately verified derivation. In commonly used formulations, a sign's 30 degrees is divided into nine portions of 3 degrees 20 minutes, with sign-assignment rules requiring explicit convention selection. This is a candidate specification for editorial and calculation review, not an invented verse citation.

A small longitude difference can cross a subdivision boundary. Divisional ascendants are particularly sensitive to birth time. A beautifully rendered D9 chart from an unknown birth time is misleading. Suppress unsupported derived positions and show which available positions change across the declared uncertainty interval.

Do not implement every varga as multiply-longitude-by-N without checking the selected mapping. Each supported varga needs a named algorithm, source, boundary fixtures and scope statement. Store numerical input, derived interval and resulting classification so reviewers can audit disputed results.

D9 cannot automatically use every D1 passage. A passage must support the requested chart type or be labeled as a later commentator's extension. The applicability filter therefore needs chart type, school and topic.

## 5. Aspects, dignity, strength and yogas

Aspects are a major source of plausible but wrong answers. Parashari graha aspects, Jaimini rashi aspects and Western angular aspects need different predicate identifiers. Degree-based orbs must not be imported into a sign-based rule because vocabulary overlaps. An exception remains linked to its main rule and participates in retrieval.

Dignity includes source-defined classifications such as own sign, exaltation/debilitation and relationship categories. Initially implement a small reviewed lookup table. Friendship can have permanent/temporary/compound treatments; one generic friendly-planet value erases assumptions. Strength calculations such as shadbala introduce multiple components, units and normalization choices and belong in a later audited module.

Represent a yoga as an interpretable predicate graph, not a sentence the model asserts when it sees familiar words. Its record needs required planets/houses/signs; conjunction/aspect definitions; dignity or strength requirements; exceptions/cancellations; source location; traditional result; applicable chart type; and reviewer approval. Distinguish geometric conditions met from complete traditional applicability reviewed.

Illustrative logic example, not a classical quotation: an approved source requires A and B and absence of C. The engine returns A=true, B=true, C=unknown because birth time is uncertain. Return indeterminate, not confirmed. Unknown is not false; this distinction prevents the model from asserting a favorable or alarming conclusion simply because an exception cannot be checked.

Modern compendia may mix original verses and added rules. The inspected Phaldeepika English product description explicitly describes added Bhavartha Ratnakara material. Book-level author metadata is insufficient attribution for every passage. Mark original text, added compilation and commentary separately before a rule enters production.

## 6. Dashas and transit timing

Vimshottari depends on declared lunar/nakshatra conventions and a balance-at-birth calculation. The familiar 120-year scheme is a candidate domain fact to confirm against the selected edition; exact year length and conversion of fractional periods to calendar instants must be recorded. Do not claim agreement with another application until ayanamsha, year-length and rounding conventions match.

The timing module needs deterministic intervals, half-open boundary rules, period hierarchy, and an explanation of which interval contains the query instant. A request exactly at a boundary must give the same result regardless of display timezone. Interpretation then references eligible chart factors and passages; timing arithmetic alone does not establish a real event.

Transit analysis combines a natal artifact and a second dated astronomical artifact. Store observation time in UTC and display timezone separately. Distinguish transit-to-natal relationships from transit-only configurations. If current location matters to the technique, collect it explicitly; otherwise do not request it unnecessarily.

Avoid searching every transit until something sounds relevant. That encourages retrospective selection and can always find a symbolic explanation. Define the allowed transit set, time window and relevance rules before answering. Any future empirical prediction study needs pre-registered outcome definitions and dates; post-hoc anecdotes cannot establish predictive performance.

## 7. Panchanga and local-calendar complexity

Panchanga is a separate calendrical module. Its familiar components are vara, tithi, nakshatra, yoga and karana. Candidate definitions include lunar-solar elongation partitions for tithi, lunar longitude divisions for nakshatra, and a combined-longitude partition for yoga. Confirm exact conventions against an authoritative almanac/reference implementation before release.

Day labels may depend on sunrise and locality rather than midnight. A daily output therefore needs coordinates, timezone, sunrise model, calendar convention and transition times. “Today is tithi X” without location and transition time can be ambiguous even when astronomical calculations are correct.

High-latitude locations and absent sunrise/sunset need explicit behavior. Do not silently borrow a nearby city's sunrise or invent one. The natal pilot does not need panchanga; defer it until a dedicated reference dataset and local-day test suite exist. Include daylight-saving transitions, local midnight, sunrise boundary and a day containing a component transition in that suite.

## 8. Uncertain birth information and rectification

Birth time is user-provided evidence with a quality label: documented, remembered, approximate interval, or unknown. Documented records can still have transcription or timezone errors. Preserve original input and resolution history instead of overwriting them with a cleaned timestamp.

Historical timezone resolution is separate from place lookup. Modern UTC offset is not a historical rule. Repeated local times require explicit selection; nonexistent local times require correction. Uncertain historical records need warnings that survive export. Supported input remains Gregorian 1900 through the present.

Compute a sensitivity envelope across the interval, but do not assume checking endpoints catches every relevant change. The implementation needs boundary-aware search or sampling justified for the reported properties. State which placements are stable, which change and which were withheld. Unknown-time mode can answer textual questions without fabricating a chart.

Rectification is vulnerable to overfitting: enough candidate times and flexible life-event interpretations can produce a convincing retrospective fit. It also invites collection of sensitive medical, relationship and family events. Keep automated rectification outside the pilot. Later research would need consent, predefined scoring, held-out events, uncertainty intervals and baseline comparisons; never label a selected time as established truth.

## 9. What a defensible answer looks like

For a question about work, first name the eligible chart fact and settings. State what an identified edition teaches, give a permitted excerpt and exact locator, explain whether prerequisites hold, and show qualifications or conflicting interpretations. Offer a limited interpretation rather than a guaranteed occupation or event date.

The source panel explains inclusion: chart type, school, matching predicate or topic, and known exceptions. This is an auditable evidence path, not hidden model reasoning. A user can challenge settings or sources and regenerate under a new versioned configuration while preserving the original report.

Unsafe traditional claims need explicit treatment. Do not generate death dates, diagnose disease, prescribe trades or promote fear-based remedies. A scholarly question about a historical passage may receive context and attribution; a personalized harmful directive is withheld. This is an answer-policy distinction, not an alteration of stored source text.

## 10. Unresolved questions and decision implications

1. Which 3–5 editions permit indexing, provider-processing of excerpts and display? Without those rights, the retrieval pilot cannot claim source-backed coverage.
2. Which named domain reviewer approves the initial profile? Without approval, rules remain draft commentary rather than production predicates.
3. Which independent fixtures have compatible terms? Two wrappers around one engine provide integration tests, not strong independent validation.
4. Which uncertainty-interval policy is understandable? It changes UI input, compute cost and eligibility rules.
5. Is bilingual Sanskrit/Hindi explanation a launch requirement? It changes staffing, OCR benchmarks, terminology review and embedding evaluation. English remains the default.
6. Which technique improves the first supported questions? That determines whether D9, timing or additional acquisition is next; popular feature lists alone do not decide priority.

## 11. Inspected sources and limits

- [Swiss Ephemeris manual](https://www.astro.com/ftp/swisseph/doc/swisseph.htm), directly read 2026-11-15: mean/true nodes, whole-sign definition, sidereal systems and Krishnamurti variants. Supports calculation distinctions, not prediction validity.
- [Jaiminisutras publisher record](https://www.motilalbanarsidass.com/products/jaiminisutras-english-translation-with-full-notes-and-original-texts-in-devanagari-and-transliteration), directly read: B. Suryanarain Rao translation, revised/annotated presentation and first two adhyayas discussed. Full edition not read.
- [Phaldeepika English record](https://www.motilalbanarsidass.com/products/phaldeepika-bhavartha-bodhini-english-edition), directly read: Ojha metadata and described added Bhavartha Ratnakara material. Marketing claims of predictive success are not adopted as evidence.
- [Jagannatha Hora official page](https://www.vedicastrologer.org/jh/), HTTP 200 and readable: comparison-software discovery only; no installation or calculation comparison performed.
- [P. V. R. Narasimha Rao book page](https://www.vedicastrologer.org/articles/astro_books.htm), HTTP 200 and readable: author-distributed book/translation links, not permission for commercial embedding or republication.
- [IANA timezone database](https://www.iana.org/time-zones), inspected in summary research: timezone data authority.

No verse-level rule here was verified against a full licensed edition. That editorial work is scheduled before rule implementation. Retrieval evaluation follows the coordinated plan: 150 items split into 20 calibration, 30 development and 100 held-out items, with 86 answerable and 14 unanswerable held-out questions; proposed Recall@10 target is at least 0.90 before selecting up to eight generation passages. These are future acceptance criteria, not achieved results.
