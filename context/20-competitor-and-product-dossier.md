# Competitor and product research dossier

Prepared 2026-11-15. This extends [02 Market research](02-market-research.md) and does not replace the approved scope. This dossier records competitor observations, not an evaluation of the later-built Astrology Evidence app. Research used direct HTTP retrieval of official pages and upstream repositories because web-search calls returned no readable payloads. No paid subscriptions, logged-in applications, binaries, or source code executions were tested. “Observed” below means documented in a readable primary source; it does not mean independently verified in operation.

## Research questions and evidence vocabulary

The comparison asks how a reader enters uncertain birth information, understands calculation conventions, examines why a statement was produced, and controls stored personal information. It also asks which existing tools can inform a Python implementation. Popularity, testimonials and broad claims of accuracy do not answer those questions.

Use **O** for an observed statement or feature in the cited source, **U** for unknown in the material inspected, and **L** for limited access to the source. U never means absent. An observable privacy policy is a policy claim, not an audit of encryption, deletion, vendors or employee access. A downloadable desktop tool is not automatically offline in every mode. A source repository permits inspection but does not establish numerical correctness or license compatibility with this application.

The most consequential research question remains open: whether ordinary users find a chart-to-rule-to-edition evidence chain useful enough to prefer it to a familiar reading. This dossier identifies what to test; it does not manufacture an answer from competitor marketing.

## Feature matrix

Abbreviations: uncertainty means explicit unknown/interval birth-time behavior; conventions means visible zodiac/house/ayanamsa controls; citations means a particular generated claim linked to an identifiable edition and passage, not merely a bibliography; data controls means export/deletion behavior.

| Product | Birth-time uncertainty | Calculation conventions | Edition/passage citations | Access and exports | Privacy/data controls | AI/interpretation authorship |
|---|---|---|---|---|---|---|
| Co-Star [C1] | U | U | U | L: static title only | L: privacy route returned app shell | U in retrieved body |
| The Pattern [C2] | U | U | U | O: consumer app and relationship features; export U | O: policy discusses birth/chat data and private profiles; operational deletion U | O: policy describes AI chat processing |
| CHANI [C3] | U | U | U | O: app, chart readings, journal; export U | O: policy describes encrypted journal storage and choices; not audited | O: app page explicitly attributes content to professional astrologers |
| TimePassages [C4] | U | O: house calculations, points, aspects | U | O: mobile, desktop, web and saved charts; export U in pages inspected | O: policy route exists; detailed privacy body not reliably isolated | O: expert interpretations; AI use U |
| AstroSage [C5] | U: time field observed, no interval behavior established | O: ayanamsa, coordinates, zone, DST, chart style | U | O: kundli/cloud/software/AI offerings; export U in sources inspected | O: policy documents emailed account-deletion request | O: AI astrologer offerings and human consultation |
| Astrotalk [C6] | U | U in inspected pages | U | O: chat/call, kundli, calculators; export U | O: policy documents account deletion, collection and recordings | O: human consultation; automation details U |
| Sanctuary [C7] | U | U | U | O: reader marketplace and horoscopes; export U | O: policy describes data shared with advisors | O: reader-led sessions; AI use U |
| Astrodienst [C8] | L | L | L | L: browser challenge | L | L |
| Jagannatha Hora [C9] | U | O: configurable Vedic software; exact controls need runtime review | U | O: Windows downloads, atlas/ephemeris variants; export U | U: no privacy audit; download alone proves little | U: no AI inference from silence |
| PyJHora [C10] | U: README requires a birth-time input | O: ayanamsa, node and calculation options | O: work-level references; per-claim edition citations U | O: Python/PyQt and documented PDF output | U: deployment-specific; web service differs from local library | U: no interpretation-generation audit |
| Kerykeion [C11] | U: explicit input modes documented, interval semantics not established | O: sidereal modes, houses, perspectives, nodes | U: structured provenance is not textual citation | O: Python, JSON/Pydantic, SVG, CLI, hosted API | O: explicit offline calculation mode; hosted data policies U | O: AI context/integration features, not a proof of cited synthesis |
| Astrolog [C12] | U in retrieved repository overview | U in retrieved overview; implementation available for later inspection | U | O: desktop source distribution and chart modules | U: execution/network behavior not audited | U |

The matrix deliberately leaves many cells unknown. A public homepage is not sufficient to conclude that no competitor handles uncertainty, citations or export. Conversely, a competitor's mention of AI, NASA data or sophisticated calculations would not establish that its interpretations are scientifically valid.

## Twelve product dossiers

### 1. Co-Star: consumer-personalization benchmark with access limits

The homepage, FAQ and privacy routes returned HTTP 200 but only a short application title in readable static text [C1]. This establishes an accessible web application shell and a personalized-horoscope positioning, not its current social features, engine, privacy terms or unknown-time behavior. Do not reuse remembered descriptions as verified research. The follow-up should be an interactive, consented walkthrough of account creation, uncertain time input and source inspection. Capture screenshots only with synthetic information and review the actual policy before transmitting personal birth details.

### 2. The Pattern: relationship interpretation and AI disclosure

The about page emphasizes self-understanding, compatibility and significant life periods while saying it does not make predictions or judgments [C2]. Its privacy policy, dated August 11, 2025, describes collected birth/profile information and AI chat data processing. It also explains some effects of making a profile private. This is useful evidence that approachable language, relationship context and explicit AI disclosure can coexist. It does not establish chart reproducibility, text citations or deletion completion. Our hypothesis is that users would benefit from separate controls for visibility to other users and sharing with an AI provider; those permissions are conceptually different.

### 3. CHANI: editorial quality and reflection benchmark

CHANI's app page describes chart readings, transit updates, weekly readings, guided practices and journal prompts; it explicitly says the content is written and recorded by astrologers [C3]. Its policy, effective July 23, 2026, states that journal entries are encrypted and not sold or shared with third parties. That is a specific vendor statement, not independently verified storage behavior. The lesson is that human editorial coherence is a strong comparator. An AI feature should be compared against a well-written, appropriately limited explanation, not against an intentionally weak generic horoscope.

### 4. TimePassages: technical depth without abandoning consumer use

The public site describes birth-chart dashboards, daily transits, chart comparison, saved charts, a glossary and settings for houses, points and aspects [C4]. That supports an interaction pattern where beginners receive readable explanations and experienced readers inspect settings. The retrieved policy route mostly exposed surrounding page/terms content; it is insufficient to summarize all privacy practices. Our proposed product should make calculation settings visible beside the reading and explain changes in plain language. Whether a particular chart disagreement is a bug or a convention difference must be diagnosed from settings, not aesthetics.

### 5. AstroSage: breadth and AI are already established offerings

The homepage visibly exposes kundli entry and advanced longitude, latitude, timezone, DST, ayanamsa and style controls, alongside panchang, matching, dasha, KP, Lal Kitab and AI astrologer offerings [C5]. Its privacy policy describes an account-deletion request by email. This broad catalog makes “AI plus astrology” insufficient as a uniqueness claim. Our narrower response is a coherent Vedic natal workflow whose interpretation evidence can be inspected. We do not infer the model, retrieval stack, quality controls or underlying databases from the product's marketing.

### 6. Astrotalk: service interaction and privacy boundaries

The public product presents chat/call consultations, kundli, calculators and panchang [C6]. Its privacy policy describes personal information collection, account deletion through settings, some recording practices, and limitations involving information users share with astrologers or others. These are relevant to our separation of profile storage, model transmission and sharing. A familiar conversational interface must not imply a human professional has reviewed an AI answer. Compare clarity of follow-up questions and recovery from misunderstanding, without copying urgency, accuracy guarantees or remedy-sales pressure.

### 7. Sanctuary: a practitioner marketplace, not a direct RAG comparator

The official site presents readers and horoscope content. Its combined terms/privacy page describes birth details and other information that may be passed to advisors [C7]. This is evidence for the service model and data boundary, not its technical implementation. A useful benchmark is whether the user understands who produced an interpretation and who can see the question. Our MVP has no marketplace, live reader or anonymous handoff to an advisor. That boundary should be obvious in both the answer and privacy explanation.

### 8. Astrodienst: important technical comparator, pending inspection

Both FAQ URLs attempted returned a JavaScript browser-check page [C8]. No feature cell is promoted to observed based on remembered product capabilities. Later research should inspect available chart settings, unknown-time outputs, export and documentation interactively. Astrodienst's separately accessible Swiss Ephemeris manual is relevant to the calculation architecture, but that manual does not prove the behavior of every hosted report. Keep the library-engine research and consumer-product research separate.

### 9. Jagannatha Hora: traditional-tool comparison instrument

The author's page describes a free Windows Vedic application, configurable behavior and packages with different atlas/ephemeris content [C9]. It is a useful candidate for reference comparisons with matched conventions, but “free” is not permission to redistribute proprietary binaries or reuse source. No installation was run. A fair comparison must record version, input, ayanamsa, node mode and other relevant flags. Differences are investigation targets; agreement with one program is not proof of either doctrinal authority or future-event accuracy.

### 10. PyJHora: inspectable domain implementation with evolving defaults

The README describes Python functionality derived from P.V.R. Narasimha Rao's book and JHora, extensive calculation options, a desktop interface, PDF output and a separate web service [C10]. It also documents changes in default ayanamsa and matching behavior across versions. This is unusually useful evidence for the risk of unpinned defaults. Work-level attribution is not automatically an edition-specific citation for each rule. Audit algorithms, transitive licenses and fixtures before reuse; upstream test-count claims remain claims until tests are actually executed.

### 11. Kerykeion: structured data and rendering separation

The current README separates subject calculation, chart data, rendering, reports and AI context, with explicit offline inputs and structured JSON/Pydantic output [C11]. It documents houses, sidereal settings and configurable points. This supports a design where calculation facts are reusable independently of chart graphics. It does not demonstrate the full Vedic interpretive corpus or uncertainty interval behavior required here. Its current ephemeris backend and license need version-specific review; using an old description of the package would be unsafe architectural research.

### 12. Astrolog: inspectable mature desktop source

The upstream repository identifies Astrolog 8.00 and contains calculation, chart, interpretation, atlas, timezone and ephemeris modules [C12]. Repository structure is evidence that those modules exist, not an audit of their algorithms or network activity. A guessed manual URL failed, so this review does not assert detailed manual behavior. Treat Astrolog as a possible comparison/reference tool and rendering study, not as a ready-made Python service. Inspect its license and the license of bundled astronomical data before any reuse.

## Five journey case studies to test

These are **proposed research walkthroughs**, grounded in the observed capabilities above; they are not reports of completed usability sessions.

1. **Uncertain-time newcomer.** Use a synthetic date/place and an explicit unknown time. Try CHANI, AstroSage and the proposed UI. Record whether unknown time is accepted, whether a default time is disclosed, which placements disappear, and whether the explanation overstates certainty. Hypothesis: an honest limited answer is understandable if the unavailable factors are named. Do not assume competitor behavior in advance [C3, C5].
2. **Experienced reader comparing conventions.** Start from the same synthetic input in TimePassages, PyJHora and the proposed chart. Record displayed house/zodiac/ayanamsa/node settings and the effort to reproduce a placement. Hypothesis: a compact immutable method manifest reduces disagreements caused by hidden settings. Western and Vedic readings are not interchangeable comparison targets [C4, C10].
3. **User asking “why does this apply to me?”** Compare an editorial reading, a marketplace consultation and a citation-first prototype. Ask the user to identify the asserted chart condition, the source rule and the inference. Hypothesis: local evidence cards reduce unsupported authority, but longer answers may reduce comprehension. The current research does not establish whether CHANI or marketplace providers offer such references in every interaction [C3, C6, C7].
4. **Privacy-conscious returning user.** Compare how policy descriptions explain birth data, chat processing and deletion in The Pattern, CHANI and AstroSage. Then test our separate saved-profile and provider-sharing controls. Record comprehension rather than judging a company solely from policy length. Hypothesis: a small before-send disclosure is more effective than a long policy alone [C2, C3, C5].
5. **Developer seeking reproducibility.** Recreate a chart using documented offline inputs in Kerykeion and a matched PyJHora configuration. Record package/data revisions, coordinate source and output differences. Hypothesis: a versioned chart manifest will prevent accidental comparison of incompatible conventions. This requires actual execution later; none occurred here [C10, C11].

## Interview protocol and decision thresholds

Recruit separately: five astrology newcomers, five regular users and three experienced practitioners/domain reviewers. These are proposed research targets, not statistically representative samples. Obtain consent, permit skipping personal questions, and use invented birth profiles. Avoid asking participants to disclose distress, relationship history or identifiable third-party data.

A 40-minute session begins with five minutes about the last astrology interaction they chose and what made it credible. Ask for concrete experiences before presenting our preferred solution. Spend ten minutes on a neutral competitor task, fifteen on a clickable prototype, five on a source-comprehension exercise and five on privacy controls. Counterbalance presentation order. Record product version, tier, date, device and task wording. Do not call scripted prototype states real AI results.

Ask: “Which part can you check?”, “What would change if the birth time is wrong?”, “What does this source prove?”, and “Who will receive your question?” Avoid “Do you like our transparent design?” Record completed tasks, time to find the supporting passage, misidentified evidence classes, perceived certainty and privacy misunderstandings. Separate satisfaction from trust calibration: high trust in an unsupported answer is a failure.

Initial decision rule: at least eight of ten non-expert participants should correctly distinguish calculated placement, source interpretation and model synthesis after normal onboarding; at least eight should locate the supporting excerpt without moderator help. These are prototype iteration triggers, not population estimates. Any participant interpreting a label as a guaranteed future outcome triggers a copy/design review. Practitioner review separately evaluates doctrinal consistency and applicability; it cannot establish scientific predictive validity.

The next research pass should fill unknown matrix cells with direct task evidence and retain an access log. Do not add more competitors merely to increase the count. Prioritize unknown-time handling, exact source navigation, export/deletion and setting reproducibility because those change implementation decisions.

## Primary-source register and access record

All retrieved on 2026-11-15 unless stated otherwise. Links describe the particular evidence used, not blanket endorsement.

- **C1:** [Co-Star home](https://www.costarastrology.com/), [FAQ attempt](https://www.costarastrology.com/faq), [privacy attempt](https://www.costarastrology.com/privacy). HTTP 200 app shell only; detailed claims unverified.
- **C2:** [The Pattern about](https://www.thepattern.com/about-us), [privacy](https://www.thepattern.com/privacy-policy), [support](https://www.thepattern.com/support). Readable; `/faq` and the attempted help-center search API returned 404.
- **C3:** [CHANI app](https://www.chani.com/app), [privacy](https://www.chani.com/privacy-policy). Readable; guessed `/faq` returned 404.
- **C4:** [TimePassages home](https://astrograph.com/), [policy route](https://astrograph.com/company/policies). Product readable; privacy detail extraction limited by surrounding content.
- **C5:** [AstroSage home](https://www.astrosage.com/), [privacy](https://www.astrosage.com/privacy-policy.asp), [support](https://www.astrosage.com/support/). Readable; an initial spelling without the hyphen returned 404 and was corrected from the official homepage link.
- **C6:** [Astrotalk home](https://astrotalk.com/), [privacy](https://astrotalk.com/privacy-policies). Readable; singular `/privacy-policy` produced only an application shell.
- **C7:** [Sanctuary home](https://www.sanctuaryworld.co/), [terms/privacy](https://www.sanctuaryworld.co/privacy-policy). Readable, including advisor data-sharing statements.
- **C8:** [Astrodienst settings FAQ](https://www.astro.com/faq/fq_fh_setup_e.htm), [additional FAQ attempt](https://www.astro.com/faq/fq_fh_astro_e.htm). Browser challenge; no feature verification.
- **C9:** [Jagannatha Hora author/download page](https://www.vedicastrologer.org/jh/). Readable; binary not downloaded or executed.
- **C10:** [PyJHora repository](https://github.com/naturalstupid/PyJHora), [upstream README](https://raw.githubusercontent.com/naturalstupid/PyJHora/main/README.md). Readable; tests not run.
- **C11:** [Kerykeion repository](https://github.com/g-battaglia/kerykeion), [upstream README](https://raw.githubusercontent.com/g-battaglia/kerykeion/master/README.md). Readable; no package installation or hosted API request.
- **C12:** [Astrolog repository](https://github.com/CruiserOne/Astrolog). Readable; attempted `https://www.astrolog.org/astrolog/astrolog.htm` returned 404. No installation or algorithm audit.
