# Astrology UI research and refresh recommendations

Research date: November 16, 2026. Prepared for the user's request to remove sign-in from the current experience, defer authentication, and improve the astrology interface through comparison with existing sites. This dossier complements [UI design](09-ui-and-user-flows.md), [interaction requirements](21-ui-interaction-specification.md), [accessibility validation](36-accessibility-and-responsive-validation.md), and [the anonymous workspace plan](46-anonymous-workspace-and-ui-plan.md). It does not grant source-content rights or validate astrology's predictive claims.

## Scope and evidence

Eight official public sites were inspected through readable web-tool page content. Public navigation, field labels, headings, explanatory text and product descriptions support the observations below. No account, paid product, private application screen or real person's birth details was used. A readable public page is not proof that a chart calculator, paid feature, privacy claim or mobile flow works as advertised. Visual design recommendations below are our design choices; they are not copied layouts or a claim that every competitor received a rendered-browser or accessibility audit.

Astro-Seek's birth-chart calculator returned HTTP 403 in this tool. CHANI's `/birth-chart-calculator` URL was unavailable; its official homepage was readable. These limits are recorded rather than filled with third-party descriptions. Search results from forums were not used to establish product behavior.

## Public-site comparison

| Site and inspected page | Observed navigation and chart/reading presentation | Useful pattern for this app | Limits and differences |
|---|---|---|---|
| [Astrodienst / Astro.com](https://www.astro.com/horoscope) | Public navigation separates horoscope topics, chart drawings/data, learning articles, and ephemeris/atlas resources. Simple chart drawing and extended chart selection are separate destinations. Author-specific reports and beginner education are identifiable. | Separate a clear first chart action from advanced method details. Keep learning and source research reachable without burying the chart workflow. | The inspected page has many navigation choices. It does not establish that a smaller app needs comparable breadth. No account-based report or chart result was generated. |
| [AstroSage Kundli](https://www.astrosage.com/kundli/) | The public form places date, clock time and birthplace before a settings area containing coordinates, timezone, ayanamsa and chart style. The site groups calculators, reports, learning and Panchang into topic menus. | Group ordinary birth inputs and reveal technical inputs deliberately; give sections clear labels and a primary calculation action. | The public form includes gender and many unrelated services; these are not necessary for this app. Promotional accuracy statements are not independent evidence. No generated result, mobile app or paid report was tested. |
| [CHANI homepage](https://www.chani.com/) | Search, beginner material, current articles, podcasts and annual reference material are presented as separate editorial groups with brief entry points. A beginner route is explicitly offered. | Use a warm editorial hierarchy, short explanatory cards and a beginner path alongside tools. A small glossary can explain chart terms without requiring users to leave their task. | Homepage content and public illustrations were inspected, not the private mobile application. Its birth-chart-calculator path was unavailable. Its content, art and branding are not assets to reproduce. |
| [TimePassages official product page](https://astrograph.com/timepassages/desktop) | The public page distinguishes desktop editions, mobile applications, manuals, examples and feature comparisons. Its product description explains selecting a chart feature to read an interpretation. | Make chart facts and their explanations visibly connected. For this app, an accessible placement table and source-linked explanation can provide the connection without adding unsupported chart calculations. | This is a product/marketing page, not an executed desktop or mobile app. Interactive behavior, accuracy and accessibility claims were not tested. Do not copy its pricing or commercial feature breadth into the roadmap. |
| [Cafe Astrology natal report](https://cafeastrology.com/free-natal-chart-report.html) | The chart form includes an explicit unknown-time choice. The page names its default house system, identifies the interpretation author, explains unavailable factors when time is unknown, and discusses historical timezone and atlas limitations. | Put time certainty, calculation method, author/source identity and missing facts next to the relevant decision or result. Keep a recoverable manual path for location/timezone problems. | This page states that its form needs JavaScript. Its interpretation text is not a licensed corpus for this application. Its house defaults and omitted factors cannot simply be copied into the current Jyotish calculation contract. |
| [Astrotheme birth chart](https://www.astrotheme.com/birth-chart-sign-ascendant.php) | A manual birth form sits alongside explanatory chart content. Unknown time is exposed, and house/method controls are under advanced options. The public description links wheel interaction to interpretation and explains Sun/Moon/Ascendant summaries. | Offer a concise chart summary followed by diagram, placement table, uncertainty and method. Advanced controls belong in a secondary area. | The page promotes account storage but also displays a manual form. No account or generated report was tested. Western chart conventions and broad psychological statements are not evidence for this app's Vedic rules. |
| [Navagraha Kundli tool](https://navagraha.app/tools/kundli/) | Public tool navigation is separated from learning material. The form exposes optional name and unknown time; surrounding sections explain method, privacy, output and how to read results. The page says no account is needed. | Provide a direct chart entry, a brief method summary, a small orientation section and a visible path to learning. Explain storage honestly near input. | Browser-only calculation/privacy and output claims were not independently tested. Its unknown-time noon/Moon-chart fallback and true-node convention differ from this app's uncertainty and mean-node settings; do not transplant them. |
| [Astrolabe free chart](https://alabe.com/freechart/default.asp) | The form groups when, where and personal information. A skip link and a separate troubleshooting section are present. It explains location resolution, time accuracy, printing and house-method differences. | Use meaningful fieldsets, a clear form heading, a single primary button and concise troubleshooting close to the flow. Offer browser printing for private chart records without publishing them. | Its public instruction to use noon for unknown time and its duplicate-place fallback conflict with this app's safeguards. No chart was submitted, and public report text is explicitly protected. A skip link alone does not prove accessibility conformance. |

Additional access record: [Astro-Seek birth calculator](https://horoscopes.astro-seek.com/birth-chart-horoscope-online) returned 403; [CHANI calculator](https://www.chani.com/birth-chart-calculator) was not accessible in the web tool. The comparisons use CHANI's readable official homepage and do not attribute uninspected Astro-Seek behavior.

## Synthesis for the current application

The recurring useful pattern is a direct tool followed by optional depth: enter the minimum birth information, understand the method, inspect a chart, then read explanations or research. The evidence supports this interaction pattern; it does not establish that any competitor is more accurate or that its visual style causes better outcomes.

The current application already has chart/provenance boundaries, uncertain-time handling, source permissions and ordinary forms. Its prior UI placed many fields and results in a plain vertical sequence, and sign-in interrupted the first useful action. The refresh should make the existing capabilities easier to reach and understand. It should not add daily predictions, transits, dashas, compatibility scores or book quotations that the backend cannot substantiate.

## Recommended information architecture

Use six stable destinations with meaningful ordinary URLs and one current-page indicator:

1. **Overview:** a short welcome, next action, saved profile/chart/reading counts and recent work. No sign-in or account-creation call to action.
2. **Birth profiles:** a focused create/edit path with time certainty and the current browser's records. Display names are optional.
3. **Chart explorer:** saved chart snapshots, diagram and equivalent table, a compact method strip, uncertainty state and edit-input action.
4. **Readings:** a new-question action, saved reading list, concise result, calculated facts, permitted sources and limitations. Preserve explicit insufficient-evidence states.
5. **Source library:** search independent of a personal reading, permission-aware passage cards, clear metadata and a stable return path.
6. **Data and settings:** browser-workspace explanation, data export/deletion, model consent, text/display preferences where implemented. Authentication belongs in a future-scope document, not a disabled menu item in the current app.

On desktop, a compact side navigation can keep these subdivisions visible without a large commercial-style mega-menu. On mobile, use a clear wrapping navigation or accessible disclosure that does not hide the current task. Avoid simultaneous desktop/mobile navigation copies in the accessibility tree. Keep curator controls separate and server-authorized; removing sign-in must not make anonymous visitors administrators.

## Recommended visual system

These are implementation choices for the user's calm, sectioned experience, not copied competitor assets:

- Warm ivory page background, white or subtly tinted surfaces, dark ink text, one deep indigo primary accent and restrained sage/gold status accents. Text/status meaning cannot rely on color alone.
- A readable serif heading face using installed fonts and a system body font. Avoid remote font dependence and decorative type for fields or placement values.
- A consistent spacing scale, larger section headings, short lead paragraphs, compact eyebrow labels and a single primary action per section. Secondary/destructive actions should not compete with chart creation.
- A chart illustration can anchor the overview if it is application-owned and clearly decorative or a labeled synthetic example. Do not populate a decorative wheel with fabricated live placements.
- Use plain-language badges such as calculated, uncertain, source excerpt and unavailable. Do not show prediction confidence percentages or similarity scores as truth.
- Cards should group related content, not turn every sentence into a box. Put long method/provenance identifiers in disclosures while keeping the method summary and uncertainty visible.
- Avoid broad banners that repeatedly expose backend setup names. Tell a reader what they can do now and how to recover from an unavailable feature; detailed operator setup belongs in documentation.

## Functional priorities and verification

| Priority | Change grounded in current capabilities | Evidence required before calling it done |
|---|---|---|
| P0 | Open directly into a separate browser workspace without Google/local sign-in. | Fresh browser reaches overview and creates a profile; two browser contexts cannot read each other's private IDs; CSRF and origin rejection still work; new workspace after deletion cannot revive old data. |
| P0 | Make exact, approximate and unknown time a comprehensible form choice. Group date/time, place/timezone and consent/method into labeled sections. | Unknown time has no required hidden clock value; exact gaps/folds have explicit recovery and offset choices; changed inputs invalidate prior fold confirmation; drafts remain after errors with and without JavaScript. |
| P0 | Provide complete overview/profile/chart/readings/library/data navigation. | Every navigation target returns an intentional page or useful empty state; active-page semantics are correct; no visible sign-in/sign-out links or redirect loops in current mode. |
| P0 | Make chart and reading source inspection readable. | Diagram/table carry the same fact information; sources recheck permissions and saved-reading ownership; unsupported and withdrawn evidence stay explicit; provider absence cannot fabricate a reading. |
| P1 | Add actionable empty states and clear task progression. | A fresh workspace can navigate from overview to profile to chart to reading; a missing corpus/search capability offers an honest explanation, not a fake result. |
| P1 | Add a chart print action or a print stylesheet if implemented. | Printed chart includes method, uncertainty and readable fact table without sidebar controls; private birth/question data is not put in a public URL. |
| P1 | Offer display preferences only if wired to real behavior. | Keyboard-operable controls change the expected text/theme presentation, persist appropriately, honor reduced motion and never change calculation conventions. |

Run desktop and 320px browser journeys, keyboard traversal, 200% zoom/reflow, JavaScript-disabled form submission, field validation/error recovery, empty states, destructive-action confirmation, browser isolation and revoked/expired-cookie cases. Check color contrast against the project's accessibility targets and preserve at least the existing 44px control-height goal. Passing these targeted checks is not a screen-reader certification or a completed WCAG audit.

## Boundaries that survive the redesign

Removing account sign-in removes an onboarding step; it does not remove server-derived ownership, consent or data protection. Anonymous browser cookies are a possession boundary, not proof of a person's identity. Explain that clearing cookies or changing browser can lose access, and provide the current export/deletion controls. Do not promise account recovery or cross-device sync until authentication is deliberately reintroduced.

Only deterministic code calculates chart facts. Keep unsupported birth-time facts unavailable, reviewed rule applicability distinct from a retrieved quotation, and scientific-validity limitations visible. Do not advertise the best app, verified predictions, a licensed book library or completed expert evaluation on the basis of this UI research. No competitor content, artwork or source code was copied into the application by this research task.
