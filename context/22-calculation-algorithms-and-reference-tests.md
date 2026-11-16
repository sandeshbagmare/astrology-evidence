# Calculation algorithms and independent reference tests

Research dossier, 2026-11-15. This proposed calculation specification now has a corresponding implementation and 33 native unit/edge tests, but it is not a certified ephemeris or an independent accuracy benchmark. It extends [domain scope](05-astrology-domain.md), [data contracts](12-data-and-api-contracts.md), and implementation Task 3. Defaults remain Gregorian births from 1900 through the present, Vedic sidereal/Lahiri, geocentric positions, whole-sign houses and mean lunar nodes. No numerical chart was generated during the original research task.

## 1. The calculation chain must preserve meaning

The proposed pipeline is: confirmed civil birth input → resolved time interval → explicit astronomical time scales → engine coordinates → chart conventions → derived chart facts → reviewed interpretation prerequisites. Each arrow can fail independently. A correct planet coordinate with an incorrect timezone is still an incorrect birth chart. A correct chart can support a description of traditional interpretation without establishing that interpretation's predictive validity.

Keep these separate in the manifest:

| Layer | Information to preserve | Failure behavior |
|---|---|---|
| Civil record | Original date/time, reported precision, place, calendar | Request correction rather than normalize invalid input silently |
| Time resolution | IANA zone/version, offset, fold choice, UTC interval | Ambiguous or nonexistent local time blocks a precise chart |
| Astronomical time | UT1 and TT Julian days, conversion/version policy | Never pass an unlabelled Julian day between modules |
| Engine | Library/binding/build, ephemeris files, requested and returned flags | Reject missing required files or unapproved fallback |
| Coordinate meaning | Center, frame/equinox, apparent/true, units | Reject incompatible comparison/reference configurations |
| Chart convention | Ayanamsha, house method, node model, boundary policy | Settings change creates a distinct immutable snapshot |
| Derived facts | Sign/house/nakshatra, speed, stable/uncertain state | Withhold facts whose prerequisites are unavailable |

This table is an application design requirement. It is deliberately more explicit than a single `calculate_birth_chart` call.

## 2. UTC, UT1, TT and delta-T

IERS identifies TT as TAI + 32.184 seconds; Earth-orientation products distinguish UT1 from UTC. Delta-T expresses TT minus UT1. Therefore timezone conversion and astronomical time conversion are separate operations. [C1]

Swiss Ephemeris's date implementation produces both TT and UT1 Julian days from its UTC conversion routine. It treats input before 1972 as UT1 and contains leap-second handling and a stale-table fallback condition. This is consequential for the requested 1900–present date range: recording a historical civil time as “UTC” does not prove modern UTC semantics were used by the engine. [C2]

Proposed algorithm:

1. Validate Gregorian date and time precision; keep the user's original representation.
2. Resolve the local date/time through the confirmed IANA zone. Explicitly choose a repeated-time fold; reject a missing local time. Unknown time means the actual local-day interval, which need not contain exactly 24 hours.
3. Convert every interval boundary to a UTC-labelled instant and retain the offset evidence. Do not use today's offset for a historical birth.
4. Use the pinned engine's documented conversion to produce separately typed TT and UT1 Julian days. Record its historical conversion policy and delta-T model/version.
5. Supply the appropriate time scale to each engine operation. Do not add delta-T twice through a mixture of preconversion and an `_ut` convenience function.
6. Preserve uncertainty from the civil record separately from numerical precision. Printing six decimals does not make a recalled birth minute accurate.

MVP UI accepts birth time to the minute. It need not accept a literal leap-second timestamp; reject unsupported seconds clearly instead of coercing them. The time adapter nevertheless needs fixtures covering the engine's leap-second-era behavior because internal reference data may use finer precision. Historical conversion discrepancies require a documented tolerance review, not a hidden “close enough” correction.

## 3. Requested flags are not sufficient evidence

The official programming manual distinguishes TT and UT calculation entry points, provides speed and coordinate flags, and documents automatic ephemeris fallback when files are absent. It also documents house failures that can return a substitute house system. [C3]

Project policy: explicitly request the approved ephemeris mode and record the actual returned flags for each body. A successful function return with a different engine mode is a configuration failure for a reproducible production snapshot. Keep the diagnostic internally, return a safe unavailable state, and repair the installation. Do not accept a Moshier fallback while displaying a Swiss-file manifest.

The default coordinate contract should be written as a complete tuple: geocentric apparent ecliptic longitude of date, degrees, chosen sidereal transformation, requested speed, and a pinned engine/data configuration. Confirm this tuple against the actual wrapper release. No user-facing option should exist solely because the C library exposes a flag.

For comparisons, match center and corrections before examining residuals. NASA/JPL distinguishes astrometric and apparent coordinates; its observer tables incorporate observing geometry and corrections, while available time scales depend on table type. A default Horizons result is not automatically comparable to a default astrology calculation. [C4]

Topocentric planetary positions are outside MVP. If introduced later, altitude and observer coordinates become part of the immutable input and cache key. Keep this distinct from a house method named “topocentric”; similar terminology does not make them the same setting.

## 4. Sidereal transformation and derived boundaries

Swiss Ephemeris documents multiple ayanamsha conventions and more than one sidereal projection approach. Its reference material separately discusses mean and true lunar nodes. [C5] The application should expose only the agreed Lahiri mode initially, preserve its exact engine identifier, and not implement a generic fixed-degree subtraction described merely as “Vedic.”

Proposed derived-fact arithmetic is a project convention requiring domain-review signoff:

- Normalize angular longitudes into the half-open interval [0°, 360°). Treat a full revolution as 0°, not as a thirteenth sign.
- Determine the zero-based sign index by dividing the normalized sidereal longitude into twelve 30° intervals. Use unrounded engine values for classification; round only display text.
- For the standard 27 equal-sector nakshatra model, use sector width 360°/27 and four equal padas per sector. Preserve the adopted label ordering and tradition in a versioned registry; do not silently introduce a 28-sector system.
- For the chosen lunar-node model, derive the opposite node by a half-revolution rotation and explicitly label it as a derived fact. Do not describe nodes as physical planets in the astronomical evidence layer.
- House occupancy in the whole-sign convention is the cyclic sign offset from the ascendant sign, plus one. An unavailable ascendant makes occupancy unavailable, even when the planet's own sign is stable.

Boundary handling must be consistent across engine, API and UI. A planet just below a sign boundary may display a rounded longitude at the next sign; avoid this by displaying adequate precision or an explicit boundary indicator. Never compute sign from formatted degree strings. A “near boundary” annotation is sensitivity information, not a new astrological rule.

## 5. Houses, polar regions and motion

The official house implementation includes a distinct whole-sign branch and explicit behavior around polar geometry. [C6] Our default does not justify assuming every possible latitude/time combination has an unproblematic ascendant. Exact geographic poles and degenerate geometry require validation, an unavailable-fact result, or an explicitly documented supported-domain restriction.

Keep tests for quadrant methods even if their UI is disabled, because an unexpected library fallback must not masquerade as whole-sign output. Do not compare whole-sign first-house boundary with the exact ascendant degree as if equality were required. Nor should a later implementation force the midheaven to equal the tenth whole-sign boundary.

Motion classification is a proposed application contract: use the selected coordinate's returned longitudinal speed, record its units and frame, and derive retrograde/direct from the signed value. If the speed is too close to zero for the agreed classification tolerance, report near-station/uncertain instead of forcing a confident label. The station tolerance must be chosen using reference fixtures and exposed as a versioned calculation setting. Do not substitute a broad astrological “station period” for the engine's numerical sign change.

## 6. Unknown time needs interval reasoning

Evaluating only midnight and the following midnight is insufficient as a general proof that a fact stayed constant. A quantity can cross a boundary and return, and an interval can contain a speed reversal. This is a mathematical limitation, not a library-specific defect.

Proposed conservative procedure:

1. Resolve the full possible birth interval, including timezone transitions.
2. Evaluate positions and relevant motion information over bounded subintervals. Unwrap longitude locally so 359°→0° is continuous motion rather than a 359° jump.
3. Bracket candidate sector crossings and stations; refine crossing times with a bounded root-finding procedure. Record the search resolution and convergence status.
4. If the implementation cannot certify that all relevant crossings were checked, label the fact uncertain. Do not promote “same at sampled endpoints” to “stable throughout.”
5. Return either a stable categorical fact or a finite set/range of possible outcomes, plus the interval used. MVP suppresses ascendant/houses for unknown time even if a narrow numerical experiment appears favorable.

A fixed-time chart and an interval chart are different result contracts. Later dasha, D9 and transit features require their own time-sensitive validation; this dossier does not authorize their inclusion in the natal MVP.

## 7. Concurrency is build-dependent

Upstream `sweph.c` stores engine state using a `TLS` declaration. The corresponding `sweodef.h` enables thread-local storage only under certain compile conditions and defines it empty under others, including the inspected Windows/Apple condition. These source observations do not establish the behavior of an arbitrary packaged Python wheel. [C7, C8]

Design consequence: default to one calculation transaction per isolated process, or a proven process-wide lock covering initialization, every setting mutation, all related calculations and cleanup. A lock around only the final planet call is insufficient if another request can change settings before it. If thread-local builds are used, initialize settings inside the executing thread and verify wrapper behavior; setting a mode in the main thread may not configure a worker thread.

The release test alternates two deliberately different configurations under concurrency and compares each result with its own sequential baseline. Run on the actual Windows development build and production Linux image. Record wheel and native-library build identities, not just the Python package version. No blanket thread-safety claim is made.

## 8. Independent reference strategy

Use three complementary levels:

1. **Internal invariants:** normalization, cyclic sign arithmetic, node opposition, time round trips and consistent manifests. These catch integration errors but cannot establish astronomical accuracy.
2. **Cross-interface parity:** the selected Python wrapper versus the native Swiss command-line/tool output under identical settings. Useful for wrapper mistakes; not independent ephemeris validation.
3. **Independent reference:** matched NASA/JPL output for physical bodies, with a written coordinate/time reconciliation; separately reviewed published or independently implemented references for chart conventions. Horizons does not supply authoritative Jyotish interpretations or validate the chosen nakshatra labels.

JPL warns that displayed precision is not equivalent to physical accuracy and that uncertainty depends on the object/time span. [C4] Accordingly, <=1 arcsecond remains only a proposed acceptance threshold for matched supported reference cases, not a universal guarantee. Preserve actual residuals and the reason each fixture is comparable. Nodes, houses and convention-derived labels need their own reference method.

## 9. Fixture matrix

These are proposed cases and expected invariants, not computed reference results. Acquire exact expected coordinates from approved reference sources during implementation.

| ID | Case | Expected behavior / evidence |
|---|---|---|
| CAL-01 | Ordinary exact-time equatorial birth | Complete manifest; supported longitudes match independently configured reference |
| CAL-02 | Northern versus southern latitude | Correct location propagation; no sign inversion caused by coordinate parsing |
| CAL-03 | East/west longitude input | Explicit sign convention; swapped signs fail an intentional negative control |
| CAL-04 | Local midnight with UTC previous day | Original civil date preserved; UTC rollover correct |
| CAL-05 | Repeated DST local time | Two candidates until fold selected; no silent first-choice resolution |
| CAL-06 | Nonexistent local time | Validation failure with correction guidance |
| CAL-07 | Unknown time on DST transition day | Actual day interval, not a forced 24-hour duration |
| CAL-08 | Pre-1972 date | Historical conversion policy visible; appropriate reference convention |
| CAL-09 | Recent date with stale leap-second data | Detected policy/data problem; no undocumented conversion fallback |
| CAL-10 | Missing ephemeris file | No published chart with falsely claimed engine mode |
| CAL-11 | Alternate ayanamsha negative control | Different snapshot/cache key; request cannot contaminate default chart |
| CAL-12 | Mean versus true node | Distinct setting/result provenance; no accidental reuse |
| CAL-13 | 359.999…° and 0° synthetic arithmetic | Circular distance and sign boundaries behave consistently |
| CAL-14 | Planet near sign/nakshatra/pada boundary | Classify before display rounding; uncertainty propagated |
| CAL-15 | Interval crossing a sector then returning | Crossings detected or fact withheld; endpoint equality insufficient |
| CAL-16 | Retrograde station | Speed units preserved; near-zero classification explicitly reviewed |
| CAL-17 | Whole-sign versus equal-house negative control | Methods cannot be confused by labels or cache reuse |
| CAL-18 | High latitude/quadrant failure | No silent Porphyry substitution represented as requested method |
| CAL-19 | Pole/degenerate geometry | Supported-domain error or unavailable houses; never NaN in a published answer |
| CAL-20 | Concurrent configurations | Every result equals its corresponding sequential baseline within tolerance |
| CAL-21 | Restart with same locked artifacts | Same manifest and outputs within defined tolerance |
| CAL-22 | Changed ephemeris/tzdata revision | New manifest; prior saved result remains reproducible and identifiable |
| CAL-23 | Unknown time | Houses/ascendant suppressed; only certified stable facts reach the model |
| CAL-24 | API receives infinity/NaN/out-of-range coordinates | Rejected before engine execution |

## 10. Phase gates and unresolved work

**Before adapter implementation:** select maintained binding/version, license route, supported native build and ephemeris dataset; establish exact flag tuple and time conversion policy.

**Before a chart beta:** pass boundary/time/ownership tests, verify independent reference compatibility, test concurrency on deployment hardware, and have a domain reviewer approve sign/nakshatra/house conventions. Add fixture metadata to version control only when permitted.

**Before timing modules:** define year lengths, balance conventions, divisional-chart mapping and transit event semantics in separate reviewed specifications. Never infer these settings from a book title alone.

Open questions needing research, not guessed answers: exact binding exposure of warnings/returned flags; available independently licensed chart fixtures; historical birth-place/clock reliability for supported regions; station tolerance; certified interval-crossing strategy; any remaining cross-platform numerical differences. None blocks this design dossier, but each blocks the affected capability's release claim.

## Primary sources inspected

All C1–C8 sources were retrieved directly with HTTP 200 and relevant content inspected on 2026-11-15; the web tool returned empty payloads. Mutable `master` source links describe the inspected upstream state; implementation must pin a commit/release before relying on details.

- **C1** [IERS time argument FAQ](https://www.iers.org/iers/en/service/faqs/time/whatithetimeargumentforusingiersproducts-157) and [time-scale service](https://www.iers.org/iers/en/dataproducts/tools/webservices/webservice-time): time-scale distinctions and IERS products.
- **C2** [Astrodienst swedate.c](https://raw.githubusercontent.com/aloistr/swisseph/master/swedate.c): UTC conversion outputs, historical treatment and leap-second behavior.
- **C3** [Swiss Ephemeris programming manual](https://www.astro.com/swisseph/swephprg.htm): calculation entry points, flags, fallback and house error behavior.
- **C4** [NASA/JPL Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html): coordinate/time semantics and ephemeris limitations. [Official API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html) is an additional verification target for future fixture acquisition; this API page was not inspected in this task.
- **C5** [Swiss Ephemeris reference documentation](https://www.astro.com/swisseph/swisseph.htm): sidereal modes, nodes, centers and house systems.
- **C6** [Astrodienst swehouse.c](https://raw.githubusercontent.com/aloistr/swisseph/master/swehouse.c): implementation-level house branches and polar handling.
- **C7** [Astrodienst sweph.c](https://raw.githubusercontent.com/aloistr/swisseph/master/sweph.c): engine state declaration and returned calculation flags.
- **C8** [Astrodienst sweodef.h](https://raw.githubusercontent.com/aloistr/swisseph/master/sweodef.h): build-conditional TLS definition.

No upstream implementation code has been copied into this application. The calculation engine is implemented, but the formulas and test cases above remain a broader specification, not completed independent reference computations. The current engine also lacks a reviewed near-station tolerance; motion classification must not be treated as domain-validated until that setting and matched reference fixtures are approved.
