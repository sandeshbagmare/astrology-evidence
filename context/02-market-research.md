# Market research and product positioning

Research date: 2026-11-15. Scope: public product pages, publisher documentation, and upstream source repositories; no paid accounts or private implementation access. Web search returned no usable content in this session, so primary URLs were fetched directly with PowerShell Invoke-WebRequest. Ten comparator sources returned substantive readable content; Co-Star returned only its page title and Astrodienst returned a JavaScript browser challenge. These limitations are explicit below. Features are source observations, not independent validation of efficacy. Proposed gaps are research hypotheses, not claims that competitors lack a feature.

## Product comparison

| Product | Publicly documented capability | Architectural evidence and unknowns | Lesson for this product |
|---|---|---|---|
| [Co-Star](https://www.costarastrology.com/) | Retrieved title advertises personalized, real-time horoscopes. Detailed feature content was unavailable in the static response. | Model, corpus, retrieval system, and chart features remain unverified in this review. | Candidate for a later interactive comparison; do not infer its architecture from reputation. |
| [The Pattern](https://www.thepattern.com/about-us) | Self-understanding, relationship compatibility, and significant time periods. Its about page says it does not make predictions or judgments. | Public product description does not establish its computation or retrieval architecture. | Offer understandable themes without forced certainty or technical overload. |
| [CHANI](https://www.chani.com/app) | Birth-chart interpretation, transit updates, reflection prompts, meditation, and weekly readings. Describes content as written and recorded by professional astrologers. | Editorial authorship is disclosed; internal delivery stack is unknown. | Human editorial review is a quality benchmark; AI alone is not differentiation. |
| [TimePassages](https://astrograph.com/) | Interactive chart dashboard, daily horoscope, transits, comparison charts, saved charts, glossary, and calculation settings. | Product exposes configurable chart concepts; internal service/database architecture is unknown. | Visible method settings and a glossary are baseline expectations. |
| [AstroSage](https://www.astrosage.com/) | Kundli, matching, panchang, Vimshottari dasha, KP and Lal Kitab sections, multilingual navigation, and AI astrologer offerings. | Homepage establishes breadth and AI offerings, not model/provider/RAG internals. | An AI astrology chat by itself is already a crowded proposition; specialize in citation integrity and coherent traditions. |
| [Astrotalk](https://astrotalk.com/) | Human chat/call consultation, kundli and matching, calculators, panchang, multilingual navigation. | A consultation marketplace is observable; private ranking, calculation, and model systems are unknown. | Capture the understandable conversational experience without reproducing pressure to buy remedies. |
| [Sanctuary](https://www.sanctuaryworld.co/) | Reader marketplace, astrology/tarot categories, horoscopes, account flows, and per-minute consultations. | Public pages describe product/service workflows; backend and interpretation methodology are unknown. | Users want follow-up and accessible explanations; source inspection must fit the conversation. |
| [Astrodienst](https://www.astro.com/faq/fq_fh_setup_e.htm) | Candidate technical chart comparator; page fetch returned a JavaScript browser challenge, so its feature list was not verified here. | No inference about hosted architecture from the blocked page. | Revisit interactively when benchmarking configuration and chart calculations. |
| [Jagannatha Hora](https://www.vedicastrologer.org/jh/) | Free Windows Vedic astrology software with extensive calculations, configurable behavior, atlas and ephemeris packages. | Author documents package ranges and features; free download is not an open-source redistribution license. | Use as a comparison instrument with matched settings, not an unquestioned oracle or redistributable dependency. |
| [PyJHora](https://github.com/naturalstupid/PyJHora) | Python Vedic calculations inspired by P.V.R. Narasimha Rao's book and JHora, with documented tests and a web service. | Source is inspectable and repository identifies AGPL-3.0. Upstream notes that comparisons depend on ayanamsa and other settings. | Useful domain reference and test comparator; audit specific algorithms, license, dependencies and fixtures before adoption. |
| [Kerykeion](https://github.com/g-battaglia/kerykeion) | Python structured chart data, aspects, birth/synastry/transit/composite SVG charts; documented AI integrations. | Source is inspectable; repository identifies AGPL-3.0 and additional licensing material. Ephemeris implementation must be checked at the selected version. | Reuse may save chart effort, but Western-oriented breadth is not evidence of completeness for Vedic rules. |
| [Astrolog](https://github.com/CruiserOne/Astrolog) | Source-available astrology calculation and visualization software with ephemeris, atlas, chart, and interpretation modules. | C/C++ implementation and license documents are available. This is not a Python web application template. | Inspect calculation behavior and rendering ideas; do not copy source before a license review. |

The table deliberately excludes live prices, ratings, customer counts, and claims such as “most accurate”: they are unnecessary for the architectural decision and do not establish predictive validity. Readable product pages were inspected where available; the two limited-access results above remain unverified beyond their returned content. Applications were not exercised end-to-end. Every link is a primary product or upstream repository source, not an affiliate roundup.

## What is distinctive enough to test

The proposed differentiator is an **audit trail for each interpretation**: a verified chart fact, a source rule with edition and passage, an explanation of applicability, and an explicit statement of uncertainty or disagreement. This is a product hypothesis derived from the public descriptions above; the research does not prove that no existing product offers it.

Evaluate four hypotheses with users before calling the product superior:

1. Users can tell which statements are calculated, which come from a named tradition, and which are AI synthesis.
2. A reader can open a citation and find the exact supporting passage without searching a whole book.
3. Conflicting schools and uncertain birth times are more useful when exposed than when silently resolved.
4. A concise answer with expandable evidence feels more useful than a long generic reading.

A source-grounded explanation demonstrates fidelity to a text. It does not turn a traditional claim into an established fact about a person's future. Book count, vector similarity, positive ratings, and user agreement are not predictive-accuracy metrics.

## Build-versus-reuse decision

Build the provenance contract, chart-to-rule applicability, uncertainty UX, and citation verification because these define the product. Reuse infrastructure for identity, relational storage, vector retrieval, template rendering, and model transport. Evaluate existing astronomy/chart libraries against explicit conventions and a license decision; do not build a numerical ephemeris from scratch.

Three approaches considered:

| Approach | Strength | Weakness | Decision |
|---|---|---|---|
| General LLM astrology chatbot | Quick demonstration | Weak source attribution, fabricated charts, uncertain method consistency | Reject as the product architecture |
| Deterministic charts plus fixed editorial paragraphs | Easy to audit, predictable costs | Limited question coverage and weak cross-source synthesis | Keep as degraded/no-model mode and baseline |
| Deterministic charts plus constrained retrieval and verified synthesis | Addresses the explanation and provenance goal | Requires corpus rights, careful metadata, evaluation and runtime checks | Recommended design |

## Research backlog and validation protocol

- Conduct five novice and five experienced-reader sessions, using identical questions and consented/synthetic birth inputs. No recruitment or outreach has occurred.
- Ask participants to distinguish calculation accuracy, agreement with a tradition, and real-world predictive validity.
- Compare a short fixed-template baseline against the proposed cited answer. Score source discovery, comprehension, completion time and misleading certainty; do not score agreement alone.
- Trial at least one consumer app and one technical chart tool directly before finalizing UX claims. Record date, platform, product version, account tier and settings. Current research is public-document research only.
- Compare chart engines only after matching zodiac, ayanamsa, node mode, houses, time zone and ephemeris settings. A disagreement is a debugging input, not evidence of one system's superior astrology.
- Revisit public features before launch. Do not market “first”, “only”, “best”, “scientifically proven”, or “more accurate than astrologers” without evidence supporting the exact statement.

## Implications for the first release

A coherent Vedic-first scope with excellent evidence navigation is preferable to superficial support for every school. Keep public demonstrations, a transparent library, Google sign-in, one birth profile, chart methods, question/answer history, and expandable source cards. Defer social matching, payments, practitioner marketplace, push predictions and automated remedy sales. The architecture should permit later additions without making them prerequisites for learning whether source transparency matters.
