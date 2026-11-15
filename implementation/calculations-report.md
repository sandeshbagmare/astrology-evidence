# Calculation implementation report

Implemented 2026-11-15. Module: `src/astrology_evidence/calculations/__init__.py`.

Public API: `BirthInput`, `ChartSettings`, `resolve_birth_time`, `calculate_chart`, `ChartFact`, `ChartSnapshot`, `ResolvedBirthTime`, `UTCInterval`.

BirthInput accepts birth_date, local_time, time_precision (exact/approximate/unknown), earliest_local/latest_local for explicit approximate datetime intervals, finite strict numeric latitude/longitude, IANA timezone, optional fold, timezone_history (confirmed/uncertain), Gregorian calendar. Date range is 1900 through current UTC date. Minute precision only. timezone_history defaults uncertain: callers must explicitly collect confirmation to obtain exact chart facts.

Timezone objects load directly from the pinned tzdata package artifact, independently of OS TZPATH/cache. Resolution preserves discrete ambiguous UTC candidates and disjoint approximate intervals. Unknown time resolves actual civil-day intervals, including midnight transitions, half-hour DST and skipped dates. TZif explicit transitions preserve historical second-level offsets; recurring POSIX-tail transitions use ZoneInfo offset transition bracketing. Approximate endpoints inside a gap are rejected.

Exact charts use geocentric Lahiri sidereal positions, whole-sign houses and mean nodes. Ketu is explicitly derived by opposition. Poles suppress house geometry. Every engine configuration and calculation shares one process lock. Selected distribution is pysweph (coordinator-selected maintained fork); its calc_ut returns values, flags and warnings. Moshier is explicitly labeled; Swiss-file fallback raises an error. Manifest records actual flags, warnings, TT/UT1, package/native versions, actual binary and timezone digests, ephemeris file checksums, settings/input hashes and a reproducibility hash. Fact IDs incorporate that reproducibility hash.

Unresolved folds, unknown/approximate times and unconfirmed history conservatively withhold all precise facts. No endpoint sampling masquerades as interval stability. Interval search/stability certification, independent astronomical reference comparison and domain-review conventions remain release gates. No scientific predictive-validity claim is made.

## Verification

Tests were written before implementation. The first attempted test execution was blocked by the Windows .venv launcher policy, so the initial red state was infrastructure failure, not a verified assertion failure. After coordinator installed the locked runtime packages, the first functional run produced 26 passes and six failures. Failures identified Windows negative timestamp conversion and the fork's three-value calc_ut return; both were corrected and retested.

Final run: **33 passed**, 2.12 seconds. Ruff check: **all checks passed**; Ruff format: both files formatted. Tests cover invalid/nonfinite coordinates and dates, gaps/folds, half-hour folds, 23/25/23.5-hour and midnight-gap civil days, Apia skipped date, disjoint approximate fold intervals, date rollover, unavailable uncertainty/poles, normalized positions and node opposition, manifest digests, and concurrency alternating failing Swiss-file settings with valid Moshier settings.

Windows verification invocation uses the allowed installed Python executable:

```powershell
$env:PYTHONPATH='<repo>/src;<repo>/.runtime312/Lib/site-packages'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
& 'C:/Users/bagma/AppData/Roaming/uv/python/cpython-3.12.16-windows-x86_64-none/python.exe' -m pytest tests/test_calculations.py
```

Plugin autoload is disabled because unrelated LangSmith plugin uuid_utils DLL is blocked by host application-control policy. Native pysweph executes successfully in this runtime. No security policy was changed. No deployment-platform concurrency or independent astronomical parity is claimed. No public deployment or license approval was performed.
