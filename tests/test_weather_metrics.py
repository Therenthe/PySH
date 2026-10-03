import asyncio
import json
import time

import pytest

from services.backend.content import Content


def payload():
    return {"current": {"time": "2026-10-03T12:45", "temperature_2m": 21,
        "apparent_temperature": 20, "weather_code": 0, "is_day": 1,
        "precipitation": 0, "wind_speed_10m": 8, "relative_humidity_2m": 48,
        "pressure_msl": 1018.3, "wind_direction_10m": 315},
        "hourly": {"time": ["2026-10-03T11:00", "2026-10-03T12:00", "2026-10-03T13:00"], "uv_index": [2.1, 3.7, 4.8]},
        "daily": {"time": [f"2026-10-0{i}" for i in range(3, 8)], "weather_code": [0]*5,
            "temperature_2m_min": [10]*5, "temperature_2m_max": [22]*5, "precipitation_sum": [0]*5}}


def normalize(raw):
    return Content._normalize_weather(raw, {"name": "București"}, "2026-10-03T10:46:00Z")["current"]


def test_optional_current_metrics_and_uv_use_exact_provider_hour():
    current = normalize(payload())
    assert current["humidity_pct"] == 48
    assert current["pressure_hpa"] == 1018.3
    assert current["wind_direction_deg"] == 315
    assert current["uv_index"] == 3.7
    assert current["uv_index_time"] == "2026-10-03T12:00"


@pytest.mark.parametrize("field,target,invalid", [
    ("relative_humidity_2m", "humidity_pct", -1),
    ("relative_humidity_2m", "humidity_pct", 101),
    ("pressure_msl", "pressure_hpa", 0),
    ("pressure_msl", "pressure_hpa", -1),
    ("wind_direction_10m", "wind_direction_deg", -1),
    ("wind_direction_10m", "wind_direction_deg", 361),
])
def test_optional_current_metric_bounds(field, target, invalid):
    raw = payload()
    raw["current"][field] = invalid
    assert normalize(raw)[target] is None


@pytest.mark.parametrize("invalid", [None, True, False, "48", {}, [], float("nan"), float("inf"), 10**400])
def test_optional_metrics_reject_non_numeric_and_non_finite_without_failing_weather(invalid):
    raw = payload()
    for key in ["relative_humidity_2m", "pressure_msl", "wind_direction_10m"]:
        raw["current"][key] = invalid
    raw["hourly"]["uv_index"][1] = invalid
    current = normalize(raw)
    assert current["temperature_c"] == 21
    assert all(current[key] is None for key in ["humidity_pct", "pressure_hpa", "wind_direction_deg", "uv_index", "uv_index_time"])


@pytest.mark.parametrize("hourly", [None, [], {}, {"time": "2026-10-03T12:00", "uv_index": [1]},
    {"time": ["2026-10-03T11:00", "2026-10-03T13:00"], "uv_index": [9, 9]},
    {"time": ["2026-10-03T12:00"], "uv_index": []},
    {"time": ["2026-10-03T12:00", "2026-10-03T12:00"], "uv_index": [3, 4]},
    {"time": ["2026-10-03T12:00"], "uv_index": [-1]},
    {"time": ["2026-10-03T12:15"], "uv_index": [3]},
    {"time": ["2026-10-04T12:00"], "uv_index": [3]}])
def test_hourly_uv_never_uses_neighbouring_daily_or_ambiguous_samples(hourly):
    raw = payload()
    raw["hourly"] = hourly
    raw["daily"]["uv_index_max"] = [99]*5
    current = normalize(raw)
    assert current["uv_index"] is None
    assert current["uv_index_time"] is None


@pytest.mark.parametrize("stamp", [None, 12, "broken", "2026-10-03", "2026-13-03T12:00"])
def test_uv_missing_current_time_has_no_clock_inference(stamp):
    raw = payload()
    raw["current"]["time"] = stamp
    assert normalize(raw)["uv_index"] is None


def test_zero_uv_is_preserved_only_when_provider_supplies_exact_sample():
    raw = payload()
    raw["current"]["is_day"] = 0
    raw["hourly"]["uv_index"][1] = 0
    assert normalize(raw)["uv_index"] == 0
    raw.pop("hourly")
    assert normalize(raw)["uv_index"] is None


def test_weather_query_requests_documented_fields_and_cached_old_shape_survives(tmp_path, monkeypatch):
    content = Content(tmp_path)
    calls = []
    location = {"latitude": 44.4, "longitude": 26.1}
    def response(url, params):
        calls.append(params)
        return payload()
    monkeypatch.setattr(content, "_get_json", response)
    result = asyncio.run(content.weather(location))
    assert result["current"]["uv_index"] == 3.7
    assert {"relative_humidity_2m", "pressure_msl", "wind_direction_10m"} <= set(calls[0]["current"].split(","))
    assert calls[0]["hourly"] == "uv_index"
    old = {"current": {"temperature_c": 18}, "daily": [], "updated_at": "2026-10-03T09:00:00Z"}
    (tmp_path / "weather-cache.json").write_text(json.dumps({"44.4000,26.1000": {"cached_epoch": time.time(), "value": old}}), encoding="utf-8")
    cached = asyncio.run(content.weather(location))
    assert cached["current"] == old["current"]
    assert len(calls) == 1
    monkeypatch.setattr(content, "_get_json", lambda *args: (_ for _ in ()).throw(OSError("offline")))
    stale = asyncio.run(content.weather(location, force=True))
    assert stale["stale"] is True
    assert stale["current"] == old["current"]


def test_fresh_provider_response_without_optional_metrics_is_usable():
    raw = payload()
    for key in ["relative_humidity_2m", "pressure_msl", "wind_direction_10m"]:
        raw["current"].pop(key)
    raw.pop("hourly")
    current = normalize(raw)
    assert current["temperature_c"] == 21
    assert all(current[key] is None for key in ["humidity_pct", "pressure_hpa", "wind_direction_deg", "uv_index", "uv_index_time"])
