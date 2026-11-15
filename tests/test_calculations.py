from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, time, timedelta

import pytest
from pydantic import ValidationError

from astrology_evidence.calculations import (
    BirthInput,
    ChartSettings,
    calculate_chart,
    resolve_birth_time,
)


def birth(**overrides):
    fields = dict(
        birth_date=date(2000, 1, 1),
        local_time=time(12),
        time_precision="exact",
        latitude=28.6,
        longitude=77.2,
        timezone="Asia/Kolkata",
        timezone_history="confirmed",
    )
    return BirthInput(**(fields | overrides))


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", float("nan")),
        ("longitude", float("inf")),
        ("latitude", 91),
        ("longitude", -181),
        ("latitude", "12"),
        ("latitude", True),
    ],
)
def test_invalid_coordinates(field, value):
    with pytest.raises(ValidationError):
        birth(**{field: value})


@pytest.mark.parametrize(
    "changes",
    [
        dict(birth_date=date(1899, 1, 1)),
        dict(birth_date=datetime.now(UTC).date() + timedelta(days=1)),
        dict(timezone="../UTC"),
        dict(local_time=None),
        dict(time_precision="unknown"),
        dict(local_time=time(12, 0, 1)),
    ],
)
def test_invalid_inputs(changes):
    with pytest.raises(ValidationError):
        birth(**changes)


def test_exact_utc():
    resolved = resolve_birth_time(birth())
    assert resolved.candidates == (datetime(2000, 1, 1, 6, 30, tzinfo=UTC),)


def test_gap_rejected():
    with pytest.raises(ValueError, match="nonexistent"):
        resolve_birth_time(
            birth(birth_date=date(2024, 3, 10), local_time=time(2, 30), timezone="America/New_York")
        )


def test_fold_keeps_two_candidates_and_explicit_choice():
    fields = dict(birth_date=date(2024, 11, 3), local_time=time(1, 30), timezone="America/New_York")
    result = resolve_birth_time(birth(**fields))
    assert len(result.candidates) == 2
    assert result.candidates[1] - result.candidates[0] == timedelta(hours=1)
    assert resolve_birth_time(birth(**fields, fold=1)).candidates == (result.candidates[1],)
    assert calculate_chart(birth(**fields)).facts == ()


@pytest.mark.parametrize(
    "day,zone,hours",
    [
        (date(2024, 3, 10), "America/New_York", 23),
        (date(2024, 11, 3), "America/New_York", 25),
        (date(2024, 10, 6), "Australia/Lord_Howe", 23.5),
        (date(2018, 11, 4), "America/Sao_Paulo", 23),
    ],
)
def test_unknown_civil_day_duration(day, zone, hours):
    result = resolve_birth_time(
        birth(birth_date=day, timezone=zone, local_time=None, time_precision="unknown")
    )
    assert sum((i.end - i.start).total_seconds() for i in result.intervals) == hours * 3600


def test_skipped_day():
    with pytest.raises(ValueError, match="nonexistent"):
        resolve_birth_time(
            birth(
                birth_date=date(2011, 12, 30),
                timezone="Pacific/Apia",
                local_time=None,
                time_precision="unknown",
            )
        )


def test_approximate_cross_midnight_withholds_facts():
    result = calculate_chart(
        birth(
            local_time=None,
            time_precision="approximate",
            earliest_local=datetime(2000, 1, 1, 23),
            latest_local=datetime(2000, 1, 2, 1),
        )
    )
    assert result.facts == ()
    assert "ascendant" in result.unavailable_facts
    assert result.manifest["resolved_time"]["intervals"]


def test_chart_invariants_and_manifest():
    result = calculate_chart(birth())
    facts = {(f.body, f.kind): f.value for f in result.facts}
    assert all(0 <= v < 360 for (b, k), v in facts.items() if k == "longitude")
    assert (facts["ketu", "longitude"] - facts["rahu", "longitude"]) % 360 == pytest.approx(180)
    assert all(1 <= v <= 12 for (b, k), v in facts.items() if k == "house")
    assert result.manifest["engine_mode"] == "moshier"
    assert result.manifest["actual_flags"]
    assert result.manifest["timezone_source"] == "tzdata-package"
    assert len(result.manifest["timezone_sha256"]) == 64
    assert result.model_dump_json()


def test_concurrent_matches_serial():
    inputs = [birth(longitude=float(x), latitude=float(x) / 2) for x in range(-90, 91, 30)]
    expected = [calculate_chart(x).facts for x in inputs]
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert [x.facts for x in pool.map(calculate_chart, inputs)] == expected


def test_swiss_without_files_fails(tmp_path):
    with pytest.raises(ValueError, match="fallback"):
        calculate_chart(birth(), ChartSettings(engine_mode="swiss", ephemeris_path=str(tmp_path)))


def test_unconfirmed_history_and_poles_withheld():
    assert calculate_chart(birth(timezone_history="uncertain")).facts == ()
    pole = calculate_chart(birth(latitude=90.0))
    assert "ascendant" in pole.unavailable_facts
    assert not any(f.kind == "house" for f in pole.facts)


def test_unsupported_settings():
    with pytest.raises(ValidationError):
        ChartSettings(ayanamsha="raman")


def test_lord_howe_fold_is_half_hour():
    result = resolve_birth_time(
        birth(birth_date=date(2024, 4, 7), local_time=time(1, 45), timezone="Australia/Lord_Howe")
    )
    assert result.candidates[1] - result.candidates[0] == timedelta(minutes=30)


def test_approximate_fold_retains_disjoint_intervals():
    result = resolve_birth_time(
        birth(
            birth_date=date(2024, 11, 3),
            local_time=None,
            time_precision="approximate",
            timezone="America/New_York",
            earliest_local=datetime(2024, 11, 3, 1, 15),
            latest_local=datetime(2024, 11, 3, 1, 45),
        )
    )
    assert len(result.intervals) == 2
    assert all(x.end - x.start == timedelta(minutes=30) for x in result.intervals)
    assert result.intervals[0].end < result.intervals[1].start


def test_timezone_package_overrides_host_paths(monkeypatch):
    import zoneinfo

    monkeypatch.setattr(zoneinfo, "TZPATH", ("/nonexistent",))
    assert resolve_birth_time(birth()).candidates[0].hour == 6


def test_calendar_date_rollover():
    result = resolve_birth_time(birth(local_time=time(0, 15)))
    assert result.candidates == (datetime(1999, 12, 31, 18, 45, tzinfo=UTC),)


def test_approximate_gap_endpoint_rejected():
    with pytest.raises(ValueError, match="nonexistent"):
        resolve_birth_time(
            birth(
                birth_date=date(2024, 3, 10),
                timezone="America/New_York",
                local_time=None,
                time_precision="approximate",
                earliest_local=datetime(2024, 3, 10, 2, 30),
                latest_local=datetime(2024, 3, 10, 3, 30),
            )
        )


def test_settings_and_input_digest_change():
    first = calculate_chart(birth())
    second = calculate_chart(birth(longitude=77.3))
    assert first.manifest["input_hash"] != second.manifest["input_hash"]
    assert first.facts[0].fact_id != second.facts[0].fact_id


def test_concurrent_missing_swiss_files_cannot_change_moshier(tmp_path):
    def invoke(mode):
        settings = ChartSettings(engine_mode=mode, ephemeris_path=str(tmp_path))
        try:
            return calculate_chart(birth(), settings).facts
        except ValueError as exc:
            assert "fallback" in str(exc)
            return None

    expected = invoke("moshier")
    modes = ["moshier", "swiss"] * 8
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(invoke, modes))
    assert results == [expected, None] * 8
