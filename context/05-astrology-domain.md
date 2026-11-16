# Astrology domain and calculation contract

Status: domain design drafted 2026-11-15 and partially implemented. The app computes versioned chart facts, but this document's domain recommendations are not all implemented and independent ephemeris/domain validation remains open. Astrology's predictive validity is not established by calculation tests.

## What the product can establish

The application can reproduce astronomical positions under a declared model, explain an interpretation from a particular astrological tradition, and show its textual basis. These are different achievements. A citation demonstrates what a source teaches; it does not establish that the source predicts an individual's future accurately. Astrology is not an established scientific method for predicting individual outcomes. More books and more consistent calculations do not change that distinction.

Use three explicit evidence classes: `computed` (positions and derived chart properties), `traditional` (interpretive claims attributed to an edition), and `unsupported` (insufficient matching evidence; do not present as a supported answer). Treat ordinary user context as `user_reported`. Do not display a numerical probability of a life event derived from retrieval similarity or model confidence.

## Initial scope and defaults

These are engineering proposals, not preferences confirmed by the user: Jyotish/Vedic natal analysis first; English explanations; original-script excerpts when licensed. Start with D1 chart and a narrow set of reviewed interpretive rules. Lahiri sidereal zodiac, whole-sign houses, geocentric positions, and mean lunar nodes are initial conventions. They must appear in the chart settings and exported report. Do not silently mix tropical/Western, Jaimini, KP, Parashari, or modern psychological rules.

D9, Vimshottari timing, transits, compatibility, electional astrology, and horary are later modules with their own settings and test fixtures. Do not promise all schools in the first release. The Ramayana is culturally important literature, but is not a substitute for a technical natal astrology rule corpus; include it only in a separately labeled cultural collection with appropriate rights.

## Information needed from the user

| Input | Requirement and behavior |
|---|---|
| Birth date | Required for natal calculations; ISO date internally; explicit Gregorian calendar in initial supported range 1900-01-01 to current date |
| Birth time | Exact local time or explicit unknown/approximate; never fill missing time silently |
| Time precision | User-selected exact-to-minute, approximate with interval, or unknown; do not equate remembered time with certified accuracy |
| Birthplace | Search and confirm city plus map coordinates; permit manual latitude/longitude; retain place source and resolution |
| Birth timezone | IANA identifier and resolved historical offset; user confirms ambiguity; do not derive timezone from longitude alone |
| DST ambiguity | Ask which occurrence for repeated local time; reject nonexistent local time until corrected |
| Question | Explicit topic and time horizon; needed for focused retrieval, not to alter chart facts |
| Display name/language | Optional; name is not an astronomical input |
| Current location/time | Only if the selected transit/local-time module requires it; explain why |
| Gender, caste, religion | Not required for positions; do not collect by default or reproduce discriminatory prescriptions |

Unknown birth time permits only claims whose input requirements are met. Hide ascendant, houses, divisional-chart claims and exact timing. Calculate a sensitivity envelope across the possible interval; Moon sign/nakshatra may also change. Show a range or withhold the claim. No unreviewed automatic birth-time rectification.

## Deterministic calculation boundary

Use Swiss Ephemeris through a maintained Python binding after verifying binding maintenance and distribution compatibility. The underlying engine's AGPL/professional dual licensing is a release gate, including public network service, not merely a packaging concern. Select compliant open-source distribution or obtain a professional license before public activation; record the decision in the architecture decision log. Licensing review is separate from correctness review.

A chart artifact records: original local timestamp; timezone identifier and tzdata version; UTC instant; latitude/longitude; calendar; engine and wrapper versions; ephemeris file hashes; calculation flags; ayanamsha; house system; node convention; delta-T handling; normalized longitudes; speed/retrograde flags; ascendant/house output when eligible; and a canonical configuration hash. Store the engine's actual flags and warnings. A fallback to a different ephemeris is visible and must not be silently accepted.

Only deterministic domain functions compute positions, nakshatra, house occupancy, aspects and applicable rule predicates. LLMs explain supplied facts. They cannot invent a birth time, change chart settings, calculate an unsupported placement, or infer a planet position from prose. Precise astronomical positions do not imply precise predictions.

Rules require `rule_id`, tradition, edition locator, input dependencies, predicate specification, exceptions, supported chart types, reviewer identity and version. Where a source does not support a machine-checkable predicate, mark the item as commentary rather than executable rule. An apparent textual contradiction is retained as alternative interpretation, with school and assumptions shown.

## Reproducibility and testing

Prepare fixtures across hemispheres, historical DST changes, UTC date rollover, longitude wrap, sunrise-adjacent cases, retrograde stations, and nakshatra boundaries. Add an explicit no-time fixture and a birth interval crossing an ascendant boundary. Compare against independent published reference outputs under identical settings, recording settings before diagnosing discrepancies. Use an initial position agreement target of 1 arcsecond only where equivalent ephemerides and flags justify it; house/time sensitivity has separate tolerances. Do not count comparing the wrapper with itself as independent validation.

Vimshottari, when added, must name the adopted year length and balance-at-birth convention. Transit interpretations must record the observation instant, timezone used for display, and interaction rules with the natal chart. Full settings plus software/data versions permit reproducible computed results; LLM prose is not promised to be bit-for-bit deterministic.

## Source and research status

- [Swiss Ephemeris official manual](https://www.astro.com/ftp/swisseph/doc/swisseph.htm): fetched successfully by direct HTTP on 2026-11-15; supports configuration detail and confirms AGPL/professional licensing choice before distribution or public service activation.
- [IANA Time Zone Database](https://www.iana.org/time-zones): fetched successfully on 2026-11-15; authoritative timezone data home. Historical birth records may still be uncertain; data provenance is required.
- [Carlson, 1985, A double-blind test of astrology](https://www.nature.com/articles/318419a0): bibliographic research target. Direct HTTP returned a small page without readable article content; the article was not inspected in this task. Do not claim this task evaluated the paper or the whole scientific literature.

Web search tooling returned empty result payloads during this task; successful direct HTTP inspection is distinguished from unverified source candidates. Domain reviewer signoff and independent chart fixtures remain open work.

## Birthplace resolution boundary

Add a `profiles/places.py` service. `search_places(query)` returns candidate labels, coordinates and provider IDs; `suggest_timezone(latitude, longitude, birth_date)` returns a proposed IANA zone plus dataset/version and uncertainty; `confirm_place(candidate, user_zone_choice)` yields the confirmed location used by `BirthInput`. These are design signatures, not implemented code.

Default MVP fallback is manual coordinates and explicit timezone selection, optionally a reviewed local place list. Nominatim is an optional operator-enabled geocoder only after deliberate policy review and acceptance: server-proxied, explicit-submit search with a global maximum of one upstream request per second, identifying User-Agent, result caching, attribution and manual-coordinate fallback. No keystroke autocomplete on the public endpoint. Recheck policy and provider suitability before launch; use a funded commercial/self-hosted service if traffic or requirements exceed the public service policy. Never send birth date, user name or full question to the geocoder.

Proposed timezone suggestion uses a pinned offline timezonefinder dataset, subject to measured memory footprint and its separate data-license requirements. Present-day polygon lookup is a suggestion; it does not prove historical jurisdiction boundaries. Resolve historical offsets with versioned IANA data and require correction/reviewer support where ambiguous. Manual confirmed timezone entry must remain available when lookup is unavailable or historically uncertain. Do not compute timezone from longitude alone.

Tests: duplicate city names, city near a timezone border, remote/ocean coordinates, geocoder timeout, rate-limit cache behavior, historical timezone change, user correction, no birth identifiers in outbound requests, and manual fallback. Source/date: Nominatim official usage policy https://operations.osmfoundation.org/policies/nominatim/ and timezonefinder upstream README https://github.com/jannikmi/timezonefinder — relevant policy/API/license content fetched directly with HTTP 200 on 2026-11-15. Exact package APIs must be checked against pinned versions.

## Calculation-depth findings incorporated

The [calculation dossier](22-calculation-algorithms-and-reference-tests.md) refines implementation requirements: preserve UTC/UT/TT conversion policy, especially historical dates; compare actual returned ephemeris flags with requested flags; test build-specific mutable engine state; and never certify interval stability from endpoints alone. Independent astronomical fixtures must reconcile coordinate frame, time scale and apparent/geometric corrections. These are prerequisites of Task 3, not optional numerical polish.
