import asyncio
import json
import time

import pytest

from services.backend.content import Content


def payload():
    return {"current": {"time": "2026-10-03T12:45", "temperature_2m": 21,
        "apparent_temperature": 20, "weather_code": 0, "is_day": 1,
        "precipitation": 0, "wind_speed_10m": 8, "relative_humidity_2m": 48,
        "pressure_msl": 1018.3, "wind_direction_10m": 315, "visibility": 8100, "cloud_cover": 23},
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
    assert current["visibility_m"] == 8100
    assert current["cloud_cover_pct"] == 23
    assert current["time"] == "2026-10-03T12:45"
    assert current["uv_index"] == 3.7
    assert current["uv_index_time"] == "2026-10-03T12:00"


@pytest.mark.parametrize("field,target,invalid", [
    ("relative_humidity_2m", "humidity_pct", -1),
    ("relative_humidity_2m", "humidity_pct", 101),
    ("pressure_msl", "pressure_hpa", 0),
    ("pressure_msl", "pressure_hpa", -1),
    ("wind_direction_10m", "wind_direction_deg", -1),
    ("wind_direction_10m", "wind_direction_deg", 361),
    ("visibility", "visibility_m", -1),
    ("cloud_cover", "cloud_cover_pct", -1),
    ("cloud_cover", "cloud_cover_pct", 101),
])
def test_optional_current_metric_bounds(field, target, invalid):
    raw = payload()
    raw["current"][field] = invalid
    assert normalize(raw)[target] is None


@pytest.mark.parametrize("invalid", [None, True, False, "48", {}, [], float("nan"), float("inf"), float("-inf"), 10**400])
def test_optional_metrics_reject_non_numeric_and_non_finite_without_failing_weather(invalid):
    raw = payload()
    for key in ["relative_humidity_2m", "pressure_msl", "wind_direction_10m", "visibility", "cloud_cover"]:
        raw["current"][key] = invalid
    raw["hourly"]["uv_index"][1] = invalid
    current = normalize(raw)
    assert current["temperature_c"] == 21
    assert all(current[key] is None for key in ["humidity_pct", "pressure_hpa", "wind_direction_deg", "visibility_m", "cloud_cover_pct", "uv_index", "uv_index_time"])


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


def test_weather_query_requests_same_time_scene_measurements(tmp_path, monkeypatch):
    content = Content(tmp_path)
    calls = []
    location = {"latitude": 44.4, "longitude": 26.1}
    def response(url, params):
        calls.append(params)
        return payload()
    monkeypatch.setattr(content, "_get_json", response)
    result = asyncio.run(content.weather(location))
    assert result["current"]["uv_index"] == 3.7
    assert {"relative_humidity_2m", "pressure_msl", "wind_direction_10m", "visibility", "cloud_cover"} <= set(calls[0]["current"].split(","))
    assert calls[0]["hourly"] == "uv_index"
    assert result["current"]["visibility_m"] == 8100
    assert result["current"]["cloud_cover_pct"] == 23


@pytest.mark.parametrize("missing", [("visibility_m",), ("cloud_cover_pct",), ("visibility_m", "cloud_cover_pct")])
def test_recent_legacy_weather_cache_is_upgraded_without_losing_other_locations(tmp_path, monkeypatch, missing):
    content = Content(tmp_path)
    location = {"latitude": 44.4, "longitude": 26.1}
    old = {"current": {"temperature_c": 18, "visibility_m": None, "cloud_cover_pct": None},
           "daily": [], "updated_at": "2026-10-03T09:00:00Z"}
    for key in missing:
        old["current"].pop(key)
    cache_file = tmp_path / "weather-cache.json"
    other_location = {"cached_epoch": 1, "value": {"current": {"temperature_c": 11}}}
    cache_file.write_text(json.dumps({"44.4000,26.1000": {"cached_epoch": time.time(), "value": old},
                                    "45.0000,27.0000": other_location}), encoding="utf-8")
    calls = []
    def response(*args):
        calls.append(True)
        return payload()
    monkeypatch.setattr(content, "_get_json", response)
    upgraded = asyncio.run(content.weather(location))
    assert upgraded["stale"] is False
    assert upgraded["current"]["visibility_m"] == 8100
    assert upgraded["current"]["cloud_cover_pct"] == 23
    assert asyncio.run(content.weather(location)) == upgraded
    assert len(calls) == 1
    saved = json.loads(cache_file.read_text(encoding="utf-8"))
    assert saved["45.0000,27.0000"] == other_location
    assert saved["44.4000,26.1000"]["value"]["current"] == upgraded["current"]


@pytest.mark.parametrize("failure", ["offline", "invalid_response"])
def test_legacy_weather_cache_upgrade_failure_retains_stale_data_and_retries(tmp_path, monkeypatch, failure):
    content = Content(tmp_path)
    location = {"latitude": 44.4, "longitude": 26.1}
    old = {"current": {"temperature_c": 18}, "daily": [], "updated_at": "2026-10-03T09:00:00Z"}
    cache_file = tmp_path / "weather-cache.json"
    cache_file.write_text(json.dumps({"44.4000,26.1000": {"cached_epoch": time.time(), "value": old}}), encoding="utf-8")
    saved = cache_file.read_bytes()
    def unavailable(*args):
        if failure == "offline":
            raise OSError("offline")
        return {"current": {}, "daily": {}}
    monkeypatch.setattr(content, "_get_json", unavailable)
    stale = asyncio.run(content.weather(location))
    assert stale == {**old, "stale": True, "error": "weather_unavailable"}
    assert cache_file.read_bytes() == saved
    monkeypatch.setattr(content, "_get_json", lambda *args: payload())
    recovered = asyncio.run(content.weather(location))
    assert recovered["stale"] is False
    assert recovered["current"]["visibility_m"] == 8100


def test_explicit_missing_scene_measurements_remain_cached_without_repeated_requests(tmp_path, monkeypatch):
    content = Content(tmp_path)
    location = {"latitude": 44.4, "longitude": 26.1}
    raw = payload()
    raw["current"].pop("visibility")
    raw["current"]["cloud_cover"] = None
    calls = []
    def response(*args):
        calls.append(True)
        return raw
    monkeypatch.setattr(content, "_get_json", response)
    for _ in range(2):
        result = asyncio.run(content.weather(location))
        assert result["stale"] is False
        assert result["current"]["visibility_m"] is None
        assert result["current"]["cloud_cover_pct"] is None
    assert len(calls) == 1


@pytest.mark.parametrize("visibility,cloud", [(0, 0), (0.5, 100), (8100.25, 23.5)])
def test_current_scene_measurements_preserve_zero_bounds_and_fractional_values(visibility, cloud):
    raw = payload()
    raw["current"].update(visibility=visibility, cloud_cover=cloud)
    current = normalize(raw)
    assert current["visibility_m"] == visibility
    assert current["cloud_cover_pct"] == cloud


def test_missing_current_scene_measurements_never_use_hourly_or_daily_fallbacks():
    raw = payload()
    raw["current"].pop("visibility")
    raw["current"].pop("cloud_cover")
    raw["hourly"].update(visibility=[8000]*3, cloud_cover=[0]*3)
    raw["daily"].update(visibility_mean=[8000]*5, cloud_cover_mean=[0]*5)
    current = normalize(raw)
    assert current["visibility_m"] is None
    assert current["cloud_cover_pct"] is None
    assert current["time"] == raw["current"]["time"]


def test_fresh_provider_response_without_optional_metrics_is_usable():
    raw = payload()
    for key in ["relative_humidity_2m", "pressure_msl", "wind_direction_10m", "visibility", "cloud_cover"]:
        raw["current"].pop(key)
    raw.pop("hourly")
    current = normalize(raw)
    assert current["temperature_c"] == 21
    assert all(current[key] is None for key in ["humidity_pct", "pressure_hpa", "wind_direction_deg", "visibility_m", "cloud_cover_pct", "uv_index", "uv_index_time"])
