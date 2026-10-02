import asyncio
import json

import pytest

from services.backend.content import Content, ContentError


def run(coro):
    return asyncio.run(coro)


def test_weather_normalizes_provider_shape_and_persists_cache(tmp_path, monkeypatch):
    content = Content(tmp_path)
    calls = []

    def response(url, params=None, *, headers=None):
        calls.append((url, params))
        return {
            "current": {
                "time": "2026-09-29T12:00", "temperature_2m": 21.5,
                "apparent_temperature": 20.0, "weather_code": 2, "is_day": 1,
                "precipitation": 0.0, "wind_speed_10m": 8.2,
            },
            "daily": {
                "time": ["2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02", "2026-10-03"],
                "weather_code": [2, 3, 2, 1, 0], "temperature_2m_min": [12, 13, 11, 10, 9],
                "temperature_2m_max": [22, 23, 21, 20, 19], "precipitation_sum": [0, 1.4, 0, 0, 0.2],
            },
        }

    monkeypatch.setattr(content, "_get_json", response)
    location = {"name": "Bucharest", "latitude": 44.4, "longitude": 26.1, "timezone": "Europe/Bucharest"}
    result = run(content.weather(location))
    assert result["current"]["feels_like_c"] == 20.0
    assert result["daily"][1]["precipitation_mm"] == 1.4
    assert len(result["daily"]) == 5
    assert result["stale"] is False
    assert "Open-Meteo" in result["attribution"]
    assert calls and "api.open-meteo.com" in calls[0][0]
    assert (tmp_path / "weather-cache.json").exists()


def test_weather_uses_saved_forecast_when_upstream_fails(tmp_path, monkeypatch):
    content = Content(tmp_path)
    location = {"name": "Bucharest", "latitude": 44.4, "longitude": 26.1}
    cache_file = tmp_path / "weather-cache.json"
    value = {
        "location": location,
        "current": {"temperature_c": 18, "feels_like_c": 18, "weather_code": 1},
        "daily": [{"date": "2026-09-29", "min_c": 10, "max_c": 20}],
        "updated_at": "2026-09-29T10:00:00Z",
        "attribution": Content.WEATHER_ATTRIBUTION,
    }
    cache_file.write_text(json.dumps({"44.4000,26.1000": {"cached_epoch": 1, "value": value}}), encoding="utf-8")
    monkeypatch.setattr(content, "_get_json", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")))
    result = run(content.weather(location))
    assert result["stale"] is True
    assert result["error"] == "weather_unavailable"
    assert result["current"]["temperature_c"] == 18


def test_radio_search_returns_cached_catalog_offline(tmp_path, monkeypatch):
    content = Content(tmp_path)
    monkeypatch.setattr(content, "_radio_request", lambda params: [{
        "stationuuid": "one", "name": "Example FM", "url": "https://radio.example/stream",
        "url_resolved": "https://radio.example/live", "country": "Romania", "language": "romanian",
    }])
    first = run(content.radio_search("Example", "Romania", "romanian"))
    assert first["stale"] is False
    assert first["stations"][0]["url"] == "https://radio.example/live"
    monkeypatch.setattr(content, "_radio_request", lambda params: (_ for _ in ()).throw(OSError("offline")))
    second = run(content.radio_search("Example", "Romania", "romanian"))
    assert second["stale"] is True
    assert second["stations"][0]["stationuuid"] == "one"
    assert second["stations"][0]["uuid"] == "one"


def test_radio_browser_mirror_discovery_uses_dns_reverse_names_and_randomizes(tmp_path, monkeypatch):
    content = Content(tmp_path)
    def bounded(function, *args, deadline):
        if function.__name__ == "getaddrinfo":
            return [(2, 1, 6, "", ("192.0.2.1", 443)), (2, 1, 6, "", ("192.0.2.2", 443))]
        return ("nl1.api.radio-browser.info", [], ["192.0.2.1"])
    monkeypatch.setattr(content, "_bounded_dns_call", bounded)
    monkeypatch.setattr("services.backend.content.random.shuffle", lambda values: values.reverse())
    assert content._discover_radio_servers() == ("nl1.api.radio-browser.info",)
    # DNS discovery is cached rather than repeated for every search.
    monkeypatch.setattr(content, "_bounded_dns_call", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected DNS")))
    assert content._discover_radio_servers() == ("nl1.api.radio-browser.info",)


def test_radio_browser_fails_over_to_discovered_mirror(tmp_path, monkeypatch):
    content = Content(tmp_path)
    monkeypatch.setattr(content, "_discover_radio_servers", lambda: ("first.api.radio-browser.info", "second.api.radio-browser.info"))
    calls = []
    def request(url, params=None, *, headers=None):
        calls.append((url, headers))
        if "first.api" in url:
            raise OSError("offline mirror")
        return []
    monkeypatch.setattr(content, "_get_json", request)
    assert content._radio_request({"limit": 1}) == []
    assert len(calls) == 2
    assert calls[1][1]["User-Agent"] == "PiSmartHub/1.0"


def test_media_listing_filters_extensions_and_rejects_path_escape(tmp_path, monkeypatch):
    music = tmp_path / "Music"
    music.mkdir()
    (music / "song.flac").write_bytes(b"audio")
    (music / "movie.mp4").write_bytes(b"video")
    (music / "notes.txt").write_text("not media", encoding="utf-8")
    album = music / "Album"
    album.mkdir()
    outside = tmp_path / "private.mp3"
    outside.write_bytes(b"private")
    content = Content(tmp_path / "data")
    monkeypatch.setattr(content, "_media_roots", lambda: [music.resolve()])

    listing = run(content.media_list())
    assert {item["name"] for item in listing["items"]} == {"Album", "movie.mp4", "song.flac"}
    assert content.resolve_media(music / "song.flac") == (music / "song.flac").resolve()
    assert run(content.media_list(str(album)))["parent"] == str(music.resolve())
    with pytest.raises(ContentError) as denied:
        content.resolve_media(outside)
    assert denied.value.code == "media_path_not_allowed"


def test_media_roots_exclude_missing_and_non_directories(tmp_path, monkeypatch):
    content = Content(tmp_path)
    root = tmp_path / "Music"
    root.mkdir()
    monkeypatch.setattr("services.backend.content.Path.home", lambda: tmp_path)
    monkeypatch.setattr(content, "_mounted_media_roots", list)
    assert content._media_roots() == [root.resolve()]


def test_invalid_weather_location_is_rejected(tmp_path):
    with pytest.raises(ContentError) as error:
        run(Content(tmp_path).weather({"latitude": 120, "longitude": 0}))
    assert error.value.code == "invalid_location"
