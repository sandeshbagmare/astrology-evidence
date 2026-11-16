# Time, birthplace and uncertainty

Research dossier, 2026-11-15. This extends [domain requirements](05-astrology-domain.md), [contracts](12-data-and-api-contracts.md), and [calculation research](22-calculation-algorithms-and-reference-tests.md). The app implements timezone-aware inputs, unknown-time states and DST gap/fold handling in its calculation service; this dossier's broader place-resolution interfaces and validation matrix are not complete. The supported input range remains Gregorian 1900-01-01 through the current date. Accepting a date does not guarantee its local clock history is known accurately.

## 1. Three uncertainties that must remain separate

Birth-time precision, timezone-history reliability and birthplace precision answer different questions. A user can report an exact minute from a certificate while the applicable historical civil offset remains disputed. A city centroid can support ordinary location entry without identifying the hospital. None of these becomes certain because an ephemeris prints many decimal places.

Proposed resolution record:

| Dimension | Record | User-visible consequence |
|---|---|---|
| Reported clock time | Original local fields, exact/approximate/unknown, source optional | “Reported exact time” is not a verified-accuracy claim |
| Civil-time interpretation | IANA key, data revision, offset candidates, fold choice, history status | Unresolved alternatives prevent a precise chart |
| Geographic resolution | Coordinates, confirmed place, lookup source/version, precision category | City-level or manually entered location stays identifiable |
| Astronomical conversion | UTC-labelled candidate intervals, engine historical-time policy | Refer to the calculation manifest; do not merge civil and astronomical time scales |

Keep uncertainty flags available to retrieval and the answer validator. They cannot exist only as a small warning hidden in the profile editor.

## 2. What IANA can and cannot establish

IANA's theory document explains that timezone partitioning principally distinguishes clocks since 1970. Earlier transitions are retained, but the database is not an exhaustive reconstruction of every historical local clock. It explicitly discusses sparse evidence, unreliable historical sources and differing pre-1970 clocks within regions sharing one zone name. The optional `backzone` material has additional reliability limits. [T1]

Design implication: “1900–present supported” means the application can represent those dates and evaluate their data quality. It must not promise verified offsets for every location throughout that period. A pre-1970 profile needs an explicit historical-resolution status; the interface may require review or display an assumption before using a precise chart. A post-1970 date is not automatically reliable either: place identification and the user's record can still be wrong.

Maintain a small reviewed override registry only where credible local evidence warrants it. An override requires jurisdiction/location scope, effective date interval, offset and clock convention, documentary reference, reviewer and version. Never silently replace an IANA result because an astrology website reports another chart. A manual offset is an explicit assumption or reviewed override, not a replacement timezone identity. MVP can withhold precise output when this evidence is unavailable.

## 3. Reproducible timezone data on Windows and Linux

Python `zoneinfo` searches its configured system paths before falling back to the first-party `tzdata` package. Windows often lacks an IANA database in standard locations. The documentation provides an empty `PYTHONTZPATH` setting to force use of the package instead of system data. It also notes that changing search paths does not clear existing cached zone objects. [T2]

Proposed implementation policy: pin Python and `tzdata`, explicitly select the same data source in development and production, and record the actual data package/release plus zone artifact digest. Verify startup can load a known zone. Do not change timezone paths or clear caches during live requests. A data upgrade creates a new deployment/manifest generation; previous chart records retain their original resolution. Pickling a zone key is not sufficient archival evidence of the rules used.

Do not interpret abbreviations such as IST, CST or BST as unique timezone identifiers. Use canonical/accepted IANA keys internally and clear place-linked labels in the UI. Keep the original user selection and any alias normalization so an upgrade can be audited.

## 4. Gaps, folds and real instants

Python's `fold` distinguishes the earlier and later occurrence of repeated wall-clock times. Constructors do not themselves reject missing local times or all invalid fold combinations. [T3] Therefore simply attaching a zone object is not validation.

Proposed resolver procedure, expressed as a specification rather than application code:

1. Validate Gregorian fields and minute-level MVP precision before conversion. Reject unsupported leap-second input and invalid dates visibly.
2. Build both fold candidates for the selected zone, convert each to UTC and back, and retain only candidates whose returned local fields agree with the original input.
3. Deduplicate candidates by their UTC instant. One surviving instant is ordinary; two are ambiguous; none means a nonexistent local time.
4. For ambiguity, show both offsets and “first occurrence”/“second occurrence.” Do not ask users to understand the programming word `fold` or assume the distinction always means summer versus winter time.
5. Reject gaps until corrected. Never automatically move a birth from 02:30 to 03:30 because the clock skipped the former.

When the user cannot distinguish two valid instants, retain both as alternatives and limit conclusions accordingly. A single earliest-to-latest envelope is conservative but includes instants the record did not permit. Recommend extending `ResolvedBirthInterval` to a finite ordered list of UTC intervals/candidates plus the originating civil-time alternatives. The core contract must explicitly choose this representation before implementation; a fake midpoint is never acceptable.

Elapsed durations must be measured after conversion to UTC. Do not infer the duration of a local day from wall-clock subtraction involving the same timezone object. PEP 495 documents special arithmetic semantics that can otherwise hide a transition. [T3]

## 5. Unknown dates and nonstandard days

An unknown birth time means every valid instant associated with the selected civil date. The day is not universally 24 hours, and local midnight is not universally an ordinary instant. Resolve the set of valid local times over that date, including transitions at midnight and repeated segments; if no valid instant belongs to the date, request correction.

The inspected IANA source contains modern half-hour daylight-saving rules for `Australia/Lord_Howe` and the 2011 date-line change in `Pacific/Apia`. These are useful primary-data test targets: the latter skipped the local date December 30, 2011. [T4] They prevent a design that assumes all changes are one hour or every Gregorian date occurred locally. Fixtures must pin the source revision and independently confirm expected outputs; this research did not execute those conversions.

Do not interpret a remembered “night of the 12th” as a precise date. Ask whether the record refers to before or after midnight. Approximate intervals can cross midnight only when the user explicitly includes the neighboring date. Store interval endpoints as local date-times rather than two unqualified clock times.

## 6. Place search is a privacy and policy boundary

Separate three operations: search a place name, confirm coordinates, then suggest a timezone. The geocoder must receive only the place query and minimal routing information—not birth date, account identity, reading question or chart settings. Do not include user identifiers in upstream cache keys or request headers. Search results should show city, region and country, with manual coordinate/zone entry as a full fallback.

Nominatim's public policy requires an aggregate maximum of one request per second, identifying application headers, attribution and result caching; it forbids client autocomplete and systematic enumeration. Its current LLM section requires a deliberate informed choice by the responsible application developer, and restricts incorporation as a generic service by no-code/low-code/vibe-coding platforms. [T5]

Consequently Nominatim is an optional operator-reviewed adapter, not an automatically enabled default. The policy is at https://operations.osmfoundation.org/policies/nominatim/ and must be reviewed before activation. Use an explicit Search submission, one shared rate limiter across replicas, bounded results, cached repeat queries and a provider-switchable configuration. No bulk town harvesting and no keystroke requests. If product scale needs autocomplete or stronger availability, select a commercial/self-hosted service under its own terms. Offline curated places or manual input keep engineering possible without public geocoding.

Latitude must be finite and within [-90,90]; longitude finite and within [-180,180]. Reject NaN/infinity and ambiguous axis order. Normalize the antimeridian consistently while preserving the entered value. Geographic poles can be valid locations yet unsupported for some chart geometry; that is a calculation limitation, not a reason to silently move the point. A decorative map should not add third-party tracking or become mandatory to use the form.

## 7. A polygon lookup is not historical proof

The inspected timezonefinder README separates library code from a separately versioned `timezonefinder-data` package. It warns that dataset changes can alter results; it also describes ocean zones and overlapping-zone behavior. The code and dataset have different licenses. [T6]

Pin both package and dataset, record the selected point and candidate zones, and use explicit ambiguity handling near borders or overlaps. A returned ocean zone must not make an offshore coordinate look like a confirmed town. Modern boundaries are only a proposal for the historical birthplace: they do not establish which civil authority or clock convention applied in 1920. Couple the suggestion with historical IANA data and a visible review status, not a claim that coordinates determine historic time exactly.

Do not request the current device timezone or GPS location as a substitute for birthplace. If lookup fails, manual confirmed coordinates and an IANA zone remain available. Manual entry is subject to the same time ambiguity and historical-confidence checks.

## 8. Propagating uncertainty into chart facts

Evaluate every permitted candidate interval. For each fact, return `stable`, `varies`, `unresolved`, or `unavailable`, with a reason and supporting manifest. Stable means the calculation method establishes the fact throughout the permitted input set; matching sampled endpoints is insufficient because a crossing and return may occur.

Use the crossing/station strategy in [calculation research](22-calculation-algorithms-and-reference-tests.md). If numerical certification fails, withhold the stable label. Unknown time suppresses ascendant, houses and dependent interpretations in MVP even if some narrower factors remain stable. Geographic and timezone alternatives must be included in sensitivity analysis when relevant; examining time uncertainty alone cannot resolve a disputed longitude or offset.

No rectification from life events is included. Such a feature would require a separate reviewed method and could not turn selected retrospective matches into verified birth-time recovery.

## 9. Acceptance matrix

| Case | Required outcome |
|---|---|
| Two cities share a name | User confirms region/country and coordinates |
| Geocoder returns 429 or times out | Safe error, no unlimited retry; manual fallback works |
| Same city searched by many users | Shared caching/rate limit, no user-data leakage |
| New York repeated local time | Two distinct UTC candidates until selected |
| Spring clock gap | Reject missing time; do not shift silently |
| Lord Howe transition | Handle non-one-hour duration and folds correctly |
| Apia, 2011-12-30 | Reject nonexistent local date under pinned rules |
| Unknown date with midnight transition | Construct actual valid instant set, not assumed midnight+24h |
| Historical location with weak evidence | Show assumption/review gate; no exact-time certainty |
| Approximate interval crosses midnight | Explicit dates and correct UTC candidate intervals |
| Windows and Linux resolve same profile | Identical pinned data source and comparable manifest |
| tzdata or polygon dataset upgraded | New manifest; previous saved interpretation unchanged |
| Near-border/ocean/manual coordinates | Candidate/unsupported status visible and correctable |
| Sign changes and returns in interval | Uncertain outcome; endpoint agreement cannot pass |
| Malformed coordinate or unknown zone | Validation error before ephemeris/provider request |
| Consent to AI declined | Chart/library path remains usable without provider transfer |

## Sources and remaining gates

All six sources below were directly fetched with HTTP 200 and relevant text inspected on 2026-11-15 after web-tool responses were blank. No runtime calculations, geocoding requests, package installs or benchmark measurements were performed.

- **T1:** https://data.iana.org/time-zones/tzdb/theory.html — historical scope and evidence limitations.
- **T2:** https://docs.python.org/3/library/zoneinfo.html — data selection, fold examples, Windows and cache behavior.
- **T3:** https://peps.python.org/pep-0495/ — missing/ambiguous local times and arithmetic semantics.
- **T4:** https://raw.githubusercontent.com/eggert/tz/main/australasia — Lord Howe and Apia transition definitions; mutable source must be pinned for fixtures.
- **T5:** https://operations.osmfoundation.org/policies/nominatim/ — public service restrictions and deliberate developer responsibility.
- **T6:** https://github.com/jannikmi/timezonefinder — upstream README inspected through its raw `master` URL; dataset versioning, overlap/ocean behavior and licenses.

Before implementation: settle the finite-candidate interval representation, pin source datasets, select place-search deployment mode, and assign historical-override review ownership. Before claims of precision: execute the matrix with independent fixtures and record unsupported regional/history cases explicitly.
