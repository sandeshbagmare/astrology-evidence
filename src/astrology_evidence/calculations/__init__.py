"""Deterministic D1 calculations; no interpretation or stability claims for intervals."""

import hashlib
import json
import math
import struct
import threading
from datetime import UTC, date, datetime, time, timedelta
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_ENGINE_LOCK = threading.RLock()


def _zone_bytes(key: str) -> bytes:
    if not key or any(part in {"", ".", ".."} for part in key.split("/")) or "\\" in key:
        raise ValueError("Invalid IANA timezone")
    try:
        return files("tzdata.zoneinfo").joinpath(*key.split("/")).read_bytes()
    except (FileNotFoundError, IsADirectoryError, ModuleNotFoundError) as exc:
        raise ValueError("Unknown IANA timezone") from exc


def _zone(key: str) -> ZoneInfo:
    # Direct file loading pins this object to the package, independent of OS caches/TZPATH.
    import io

    return ZoneInfo.from_file(io.BytesIO(_zone_bytes(key)), key=key)


class BirthInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    birth_date: date
    local_time: time | None = None
    time_precision: Literal["exact", "approximate", "unknown"]
    earliest_local: datetime | None = None
    latest_local: datetime | None = None
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False, strict=True)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False, strict=True)
    timezone: str
    fold: Literal[0, 1] | None = None
    timezone_history: Literal["confirmed", "uncertain"] = "uncertain"
    calendar: Literal["gregorian"] = "gregorian"

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value: str) -> str:
        _zone(value)
        return value

    @model_validator(mode="after")
    def valid_input(self):
        today = datetime.now(UTC).date()
        if not date(1900, 1, 1) <= self.birth_date <= today:
            raise ValueError("Birth date must be between 1900-01-01 and today UTC")
        if self.local_time is not None:
            if self.local_time.tzinfo or self.local_time.second or self.local_time.microsecond:
                raise ValueError("Birth time must be a naive minute-level local time")
        if self.time_precision == "exact":
            if self.local_time is None or self.earliest_local or self.latest_local:
                raise ValueError("Exact time needs local_time and no interval")
        elif self.time_precision == "unknown":
            if (
                self.local_time is not None
                or self.earliest_local
                or self.latest_local
                or self.fold is not None
            ):
                raise ValueError("Unknown time cannot contain a guessed clock time or fold")
        else:
            start, end = self.earliest_local, self.latest_local
            if self.local_time is not None or start is None or end is None or self.fold is not None:
                raise ValueError("Approximate time requires explicit local datetime endpoints")
            if (
                start.tzinfo
                or end.tzinfo
                or any((start.second, start.microsecond, end.second, end.microsecond))
            ):
                raise ValueError("Interval endpoints must be naive minute-level local datetimes")
            if not start < end or end - start > timedelta(days=2):
                raise ValueError("Interval must be positive and at most two days")
            if start.date() != self.birth_date or end.date() > today:
                raise ValueError("Interval must start on birth_date and end no later than today")
        return self


class ChartSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tradition: Literal["jyotish"] = "jyotish"
    zodiac: Literal["sidereal"] = "sidereal"
    ayanamsha: Literal["lahiri"] = "lahiri"
    house_system: Literal["whole_sign"] = "whole_sign"
    node_mode: Literal["mean"] = "mean"
    engine_mode: Literal["moshier", "swiss"] = "moshier"
    ephemeris_path: str | None = None
    calculation_schema_version: Literal["1"] = "1"


class UTCInterval(BaseModel):
    model_config = ConfigDict(frozen=True)
    start: datetime
    end: datetime


class ResolvedBirthTime(BaseModel):
    model_config = ConfigDict(frozen=True)
    candidates: tuple[datetime, ...] = ()
    intervals: tuple[UTCInterval, ...] = ()


def _candidates(local: datetime, zone: ZoneInfo) -> tuple[datetime, ...]:
    results = set()
    for fold in (0, 1):
        utc = local.replace(tzinfo=zone, fold=fold).astimezone(UTC)
        if utc.astimezone(zone).replace(tzinfo=None) == local:
            results.add(utc)
    return tuple(sorted(results))


def _transitions(data: bytes) -> list[int]:
    """Read explicit TZif transition instants, including historical second offsets."""
    counts = struct.unpack(">6I", data[20:44])
    isgmt, isstd, leap, count, types, chars = counts
    offset = 44
    size = 4
    if data[4:5] in (b"2", b"3", b"4"):
        offset += count * 5 + types * 6 + chars + leap * 8 + isstd + isgmt
        counts = struct.unpack(">6I", data[offset + 20 : offset + 44])
        count = counts[3]
        offset += 44
        size = 8
    return list(
        struct.unpack(f">{count}{'q' if size == 8 else 'i'}", data[offset : offset + count * size])
    )


def _intervals(start: datetime, end: datetime, key: str, zone: ZoneInfo) -> tuple[UTCInterval, ...]:
    # Every possible IANA offset lies inside +/-24 hours; this brackets the civil interval.
    lower = start.replace(tzinfo=UTC) - timedelta(days=1)
    upper = end.replace(tzinfo=UTC) + timedelta(days=1)
    cuts = {lower, upper}
    transitions = _transitions(_zone_bytes(key))
    for stamp in transitions:
        if lower.timestamp() < stamp < upper.timestamp():
            cuts.add(datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=stamp))
    # TZif's recurring POSIX tail is resolved by ZoneInfo. Tail transitions are annual
    # rules, separated by days; hourly bracketing locates them to the exact second.
    tail_start = (
        (datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=transitions[-1]))
        if transitions
        else lower
    )
    cursor = max(lower, tail_start)
    while cursor < upper:
        right = min(cursor + timedelta(hours=1), upper)
        if cursor.astimezone(zone).utcoffset() != right.astimezone(zone).utcoffset():
            lo, hi = cursor, right
            old = lo.astimezone(zone).utcoffset()
            while (hi - lo).total_seconds() > 1:
                mid = lo + timedelta(seconds=int((hi - lo).total_seconds()) // 2)
                if mid.astimezone(zone).utcoffset() == old:
                    lo = mid
                else:
                    hi = mid
            cuts.add(hi)
        cursor = right
    result: list[UTCInterval] = []
    boundaries = sorted(cuts)
    for left, right in zip(boundaries, boundaries[1:], strict=False):
        offset = left.astimezone(zone).utcoffset()
        assert offset is not None
        first = max(left, (start - offset).replace(tzinfo=UTC))
        last = min(right, (end - offset).replace(tzinfo=UTC))
        if first < last:
            if result and result[-1].end == first:
                result[-1] = UTCInterval(start=result[-1].start, end=last)
            else:
                result.append(UTCInterval(start=first, end=last))
    if not result:
        raise ValueError("Birth interval is nonexistent in the selected timezone")
    return tuple(result)


def resolve_birth_time(birth: BirthInput) -> ResolvedBirthTime:
    zone = _zone(birth.timezone)
    if birth.time_precision == "exact":
        assert birth.local_time is not None
        local = datetime.combine(birth.birth_date, birth.local_time)
        candidates = _candidates(local, zone)
        if not candidates:
            raise ValueError("Birth time is nonexistent in the selected timezone")
        if birth.fold is not None:
            if len(candidates) != 2:
                raise ValueError("fold selection is only valid for ambiguous local times")
            selected = local.replace(tzinfo=zone, fold=birth.fold).astimezone(UTC)
            if selected not in candidates:
                raise ValueError("fold selection is invalid for this local time")
            candidates = (selected,)
        return ResolvedBirthTime(candidates=candidates)
    if birth.time_precision == "unknown":
        start = datetime.combine(birth.birth_date, time())
        end = start + timedelta(days=1)
    else:
        assert birth.earliest_local is not None and birth.latest_local is not None
        start, end = birth.earliest_local, birth.latest_local
        if not _candidates(start, zone) or not _candidates(end, zone):
            raise ValueError("Interval endpoint is nonexistent in the selected timezone")
    return ResolvedBirthTime(intervals=_intervals(start, end, birth.timezone, zone))


class ChartFact(BaseModel):
    model_config = ConfigDict(frozen=True)
    fact_id: str
    kind: str
    body: str
    value: float | int | bool
    unit: str
    stability: Literal["stable"] = "stable"
    provenance: Literal["computed"] = "computed"
    epoch: datetime


class ChartSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    settings: ChartSettings
    facts: tuple[ChartFact, ...]
    unavailable_facts: dict[str, str]
    manifest: dict


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def calculate_chart(birth: BirthInput, settings: ChartSettings | None = None) -> ChartSnapshot:
    try:
        import swisseph as swe
    except ImportError as exc:
        raise RuntimeError(
            "Calculation engine unavailable; use the supported Python 3.12 runtime"
        ) from exc
    settings = settings or ChartSettings()
    resolved = resolve_birth_time(birth)
    input_hash = _digest(birth.model_dump(mode="json"))
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    flags |= swe.FLG_MOSEPH if settings.engine_mode == "moshier" else swe.FLG_SWIEPH
    data_hashes = {}
    if settings.engine_mode == "swiss" and settings.ephemeris_path:
        for path in sorted(Path(settings.ephemeris_path).glob("*.se1")):
            data_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "input_hash": input_hash,
        "settings_hash": _digest(settings.model_dump()),
        "tzdata_version": version("tzdata"),
        "timezone_source": "tzdata-package",
        "timezone_sha256": hashlib.sha256(_zone_bytes(birth.timezone)).hexdigest(),
        "resolved_time": resolved.model_dump(mode="json"),
        "engine_version": swe.version,
        "wrapper_distribution": "pysweph",
        "wrapper_version": version("pysweph"),
        "engine_mode": settings.engine_mode,
        "engine_binary_sha256": hashlib.sha256(Path(swe.__file__).read_bytes()).hexdigest(),
        "ephemeris_sha256": data_hashes,
        "requested_flags": flags,
        "actual_flags": {},
        "computed_at": datetime.now(UTC).isoformat(),
        "warnings": ["Moshier analytical ephemeris; independent reference validation pending"]
        if settings.engine_mode == "moshier"
        else [],
        "time_scale_policy": "swe.utc_to_jd Gregorian UTC -> UT1/TT; engine historical policy",
        "delta_t_policy": "Swiss Ephemeris automatic default",
        "coordinate_contract": "geocentric apparent ecliptic of date; Lahiri sidereal; degrees",
        "sector_index_policy": "one-based signs, 27 nakshatras, four padas; half-open sectors",
        "derived_nodes": {"ketu": "rahu mean-node longitude + 180 degrees modulo 360"},
        "interval_end_policy": "half-open civil intervals; exact candidates are discrete",
        "external_reference_validation": "not yet performed",
    }
    manifest["reproducibility_hash"] = _digest(
        {key: value for key, value in manifest.items() if key != "computed_at"}
    )
    unavailable: dict[str, str] = {}
    if len(resolved.candidates) != 1 or birth.timezone_history != "confirmed":
        reason = "Uncertain time: interval stability is not certified"
        if birth.timezone_history != "confirmed":
            reason = "Timezone history is unconfirmed"
        unavailable = dict.fromkeys(
            ("planetary_positions", "signs", "nakshatras", "ascendant", "houses"), reason
        )
        return ChartSnapshot(
            settings=settings, facts=(), unavailable_facts=unavailable, manifest=manifest
        )
    instant = resolved.candidates[0]
    facts: list[ChartFact] = []

    def add(body: str, kind: str, value: float | int | bool, unit: str) -> None:
        facts.append(
            ChartFact(
                fact_id=f"{manifest['reproducibility_hash']}:{body}:{kind}",
                kind=kind,
                body=body,
                value=value,
                unit=unit,
                epoch=instant,
            )
        )

    with _ENGINE_LOCK:
        # Every mutable configuration call and calculation shares this lock.
        swe.set_ephe_path(settings.ephemeris_path or "")
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        swe.set_topo(0, 0, 0)
        swe.set_delta_t_userdef(swe.DELTAT_AUTOMATIC)
        swe.set_tid_acc(swe.TIDAL_AUTOMATIC)
        tt, ut = swe.utc_to_jd(
            instant.year,
            instant.month,
            instant.day,
            instant.hour,
            instant.minute,
            instant.second,
            swe.GREG_CAL,
        )
        manifest["julian_day_tt"] = tt
        manifest["julian_day_ut1"] = ut
        positions = {}
        bodies = {
            "sun": swe.SUN,
            "moon": swe.MOON,
            "mercury": swe.MERCURY,
            "venus": swe.VENUS,
            "mars": swe.MARS,
            "jupiter": swe.JUPITER,
            "saturn": swe.SATURN,
            "rahu": swe.MEAN_NODE,
        }
        for body, body_id in bodies.items():
            values, actual, warning = swe.calc_ut(ut, body_id, flags)
            if warning:
                manifest["warnings"].append(f"{body}: {warning}")
            manifest["actual_flags"][body] = actual
            expected = swe.FLG_MOSEPH if settings.engine_mode == "moshier" else swe.FLG_SWIEPH
            if (actual & (swe.FLG_MOSEPH | swe.FLG_SWIEPH | swe.FLG_JPLEPH)) != expected:
                raise ValueError("Ephemeris fallback detected; requested engine unavailable")
            if not all(math.isfinite(x) for x in values):
                raise ValueError("Ephemeris returned nonfinite output")
            positions[body] = (values[0] % 360, values[3])
        positions["ketu"] = ((positions["rahu"][0] + 180) % 360, positions["rahu"][1])
        ascendant = None
        if abs(birth.latitude) == 90:
            unavailable["ascendant"] = unavailable["houses"] = (
                "Geometry unavailable at geographic poles"
            )
        else:
            try:
                _, points = swe.houses_ex(
                    ut, birth.latitude, birth.longitude, b"W", swe.FLG_SIDEREAL
                )
                if math.isfinite(points[0]):
                    ascendant = points[0] % 360
            except swe.Error:
                pass
            if ascendant is None:
                unavailable["ascendant"] = unavailable["houses"] = "House geometry unavailable"
        if ascendant is not None:
            add("ascendant", "longitude", ascendant, "degrees")
            add("ascendant", "sign", int(ascendant // 30) + 1, "index")
        for body, (longitude, speed) in positions.items():
            add(body, "longitude", longitude, "degrees")
            add(body, "speed", speed, "degrees/day")
            add(body, "retrograde", speed < 0, "boolean")
            add(body, "sign", int(longitude // 30) + 1, "index")
            add(body, "nakshatra", int(longitude / (360 / 27)) + 1, "index")
            add(body, "nakshatra_pada", int(longitude / (360 / 108)) % 4 + 1, "index")
            if ascendant is not None:
                add(body, "house", (int(longitude // 30) - int(ascendant // 30)) % 12 + 1, "index")
    return ChartSnapshot(
        settings=settings, facts=tuple(facts), unavailable_facts=unavailable, manifest=manifest
    )
