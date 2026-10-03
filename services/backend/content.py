"""Open-Meteo and Radio Browser adapters plus safe local media discovery."""

from __future__ import annotations

import asyncio
import json
import math
import os
import queue
import random
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ContentError(Exception):
    """A stable, user-safe content error."""

    def __init__(self, code: str, message: str = "The requested content is unavailable."):
        super().__init__(message)
        self.code = code


class Content:
    WEATHER_ATTRIBUTION = "Weather data by Open-Meteo, CC BY 4.0"
    RADIO_USER_AGENT = "PiSmartHub/1.0"
    RADIO_SERVERS = ("de1.api.radio-browser.info", "nl1.api.radio-browser.info")
    AUDIO_EXTENSIONS: ClassVar[set[str]] = {".mp3", ".aac", ".m4a", ".flac", ".ogg", ".oga", ".opus", ".wav"}
    VIDEO_EXTENSIONS: ClassVar[set[str]] = {".mp4", ".m4v", ".webm", ".mkv", ".mov"}

    def __init__(self, data_dir: str | Path, *, timeout: float = 8.0):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self._radio_server_index = 0
        self._radio_servers_discovered: tuple[str, ...] = ()
        self._radio_discovered_at = 0.0

    async def geocode(self, query: str) -> list[dict[str, Any]]:
        query = str(query).strip()
        if not query:
            raise ContentError("invalid_query", "Enter a city or postal code.")
        params = {"name": query, "count": 8, "language": "en", "format": "json"}
        try:
            data = await asyncio.to_thread(self._get_json, "https://geocoding-api.open-meteo.com/v1/search", params)
        except Exception as exc:
            raise ContentError("geocoding_unavailable", "Location search is unavailable.") from exc
        return [
            {
                "name": item.get("name", ""),
                "admin1": item.get("admin1", ""),
                "country": item.get("country", ""),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone", "")
            }
            for item in data.get("results", [])
            if isinstance(item, dict) and _number(item.get("latitude")) and _number(item.get("longitude"))
        ]

    async def weather(self, location: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
        try:
            latitude = float(location["latitude"])
            longitude = float(location["longitude"])
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("coordinates out of range")
        except (KeyError, TypeError, ValueError) as exc:
            raise ContentError("invalid_location", "Choose a valid weather location.") from exc
        key = f"{latitude:.4f},{longitude:.4f}"
        cache_path = self.data_dir / "weather-cache.json"
        now = _utc_now()
        try:
            cached = await asyncio.to_thread(_read_json, cache_path, {})
            cached_entry = cached.get(key) if isinstance(cached, dict) else None
            if not force and cached_entry and time.time() - float(cached_entry.get("cached_epoch", 0)) < 900:
                return {**cached_entry["value"], "stale": False, "error": None}
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,relative_humidity_2m,pressure_msl,wind_direction_10m",
                "hourly": "uv_index",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "forecast_days": 5,
                "timezone": "auto",
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm",
            }
            raw = await asyncio.to_thread(self._get_json, "https://api.open-meteo.com/v1/forecast", params)
            value = self._normalize_weather(raw, location, now)
            cached = cached if isinstance(cached, dict) else {}
            cached[key] = {"cached_epoch": time.time(), "value": value}
            await asyncio.to_thread(_write_json_atomic, cache_path, cached)
            return {**value, "stale": False, "error": None}
        except Exception as exc:
            entry = locals().get("cached_entry")
            if entry and isinstance(entry.get("value"), dict):
                return {**entry["value"], "stale": True, "error": "weather_unavailable"}
            if isinstance(exc, ContentError):
                raise
            raise ContentError("weather_unavailable", "Weather is unavailable and no saved forecast exists.") from exc

    @staticmethod
    def _normalize_weather(raw: dict[str, Any], location: dict[str, Any], updated_at: str) -> dict[str, Any]:
        current = raw.get("current") or {}
        daily = raw.get("daily") or {}
        times = daily.get("time", [])
        def day_value(key: str, index: int) -> Any:
            values = daily.get(key, [])
            return values[index] if index < len(values) else None
        days = [
            {
                "date": day,
                "weather_code": day_value("weather_code", i),
                "min_c": day_value("temperature_2m_min", i),
                "max_c": day_value("temperature_2m_max", i),
                "precipitation_mm": day_value("precipitation_sum", i),
            }
            for i, day in enumerate(times[:5])
        ]
        required_current = ("temperature_2m", "apparent_temperature", "weather_code", "precipitation", "wind_speed_10m")
        if not isinstance(current, dict) or any(not _number(current.get(key)) for key in required_current):
            raise ContentError("invalid_weather_response", "Weather service returned incomplete current conditions.")
        if not isinstance(times, list) or len(days) != 5 or any(
            not isinstance(day.get("date"), str)
            or any(not _number(day.get(key)) for key in ("weather_code", "min_c", "max_c", "precipitation_mm"))
            for day in days
        ):
            raise ContentError("invalid_weather_response", "Weather service returned incomplete data.")
        # Optional model variables must not make otherwise usable weather fail.
        # UV is an hourly forecast matched to the provider's current local hour,
        # never a daily maximum, a neighbouring sample, or an inferred night zero.
        uv_index, uv_time = _current_hour_uv(raw.get("hourly"), current.get("time"))
        return {
            "location": {k: location.get(k) for k in ("name", "admin1", "country", "latitude", "longitude", "timezone")},
            "current": {
                "time": current.get("time"),
                "temperature_c": current.get("temperature_2m"),
                "feels_like_c": current.get("apparent_temperature"),
                "weather_code": current.get("weather_code"),
                "is_day": current.get("is_day"),
                "precipitation_mm": current.get("precipitation"),
                "wind_kmh": current.get("wind_speed_10m"),
                "humidity_pct": _optional_measurement(current.get("relative_humidity_2m"), minimum=0, maximum=100),
                "pressure_hpa": _optional_measurement(current.get("pressure_msl"), minimum=0, exclusive_minimum=True),
                "wind_direction_deg": _optional_measurement(current.get("wind_direction_10m"), minimum=0, maximum=360),
                "uv_index": uv_index,
                "uv_index_time": uv_time,
            },
            "daily": days,
            "updated_at": updated_at,
            "stale": False,
            "error": None,
            "attribution": Content.WEATHER_ATTRIBUTION,
        }

    async def radio_search(self, query: str, country: str = "", language: str = "") -> dict[str, Any]:
        query, country, language = query.strip(), country.strip(), language.strip()
        cache_path = self.data_dir / "radio-cache.json"
        cache_key = f"{query.casefold()}|{country.casefold()}|{language.casefold()}"
        cache = await asyncio.to_thread(_read_json, cache_path, {})
        params: dict[str, str | int] = {"limit": 40, "hidebroken": "true", "order": "votes", "reverse": "true"}
        if query:
            params["name"] = query
        if country:
            params["country"] = country
        if language:
            params["language"] = language
        try:
            raw = await asyncio.to_thread(self._radio_request, params)
            stations = [self._station(item) for item in raw if isinstance(item, dict)]
            stations = [item for item in stations if item["url"]]
            if not isinstance(cache, dict):
                cache = {}
            cache[cache_key] = {"cached_epoch": time.time(), "stations": stations}
            await asyncio.to_thread(_write_json_atomic, cache_path, cache)
            return {"stations": stations, "stale": False, "error": None}
        except (ContentError, OSError, ValueError, TypeError):
            entry = cache.get(cache_key) if isinstance(cache, dict) else None
            if entry:
                return {"stations": entry.get("stations", []), "stale": True, "error": "radio_catalog_unavailable"}
            return {"stations": [], "stale": False, "error": "radio_catalog_unavailable"}

    @staticmethod
    def _station(item: dict[str, Any]) -> dict[str, Any]:
        station_uuid = item.get("stationuuid", "")
        return {
            "uuid": station_uuid,
            "stationuuid": station_uuid,
            "name": item.get("name", ""),
            "url": item.get("url_resolved") or item.get("url", ""),
            "url_resolved": item.get("url_resolved") or item.get("url", ""),
            "country": item.get("country", ""),
            "countrycode": item.get("countrycode", ""),
            "language": item.get("language", ""),
            "tags": item.get("tags", ""),
            "favicon": item.get("favicon", ""),
            "homepage": item.get("homepage", ""),
            "bitrate": item.get("bitrate", 0),
            "codec": item.get("codec", ""),
        }

    def _radio_request(self, params: dict[str, Any]) -> Any:
        # Radio Browser recommends DNS resolution of all.api followed by reverse
        # lookup of its addresses. Cache the discovered mirrors and randomize their
        # order, then rotate the first choice after each request.
        errors: list[Exception] = []
        servers = self._discover_radio_servers()
        count = len(servers)
        start = self._radio_server_index % count
        for offset in range(count):
            server = servers[(start + offset) % count]
            url = f"https://{server}/json/stations/search?{urlencode(params)}"
            try:
                response = self._get_json(url, headers={"User-Agent": self.RADIO_USER_AGENT, "Accept": "application/json"})
                self._radio_server_index = (start + offset + 1) % count
                return response
            except (ContentError, OSError, ValueError, TypeError) as exc:
                errors.append(exc)
        raise ContentError("radio_catalog_unavailable", "Radio station search is unavailable.") from errors[-1]

    def _discover_radio_servers(self) -> tuple[str, ...]:
        now = time.monotonic()
        if self._radio_servers_discovered and now - self._radio_discovered_at < 600:
            return self._radio_servers_discovered
        deadline = now + self.timeout
        try:
            addresses = self._bounded_dns_call(socket.getaddrinfo, "all.api.radio-browser.info", 443, 0, socket.SOCK_STREAM, deadline=deadline)
        except (OSError, TimeoutError):
            addresses = []
        hosts: list[str] = []
        seen: set[str] = set()
        ips: list[str] = []
        if isinstance(addresses, list):
            for address in addresses:
                try:
                    ip = address[4][0]
                    if ip not in ips:
                        ips.append(ip)
                except (IndexError, TypeError):
                    continue
        for ip in ips[:8]:
            try:
                reverse = self._bounded_dns_call(socket.gethostbyaddr, ip, deadline=deadline)
            except (OSError, TimeoutError):
                continue
            hostname = reverse[0].rstrip(".").lower() if isinstance(reverse, tuple) and reverse else ""
            if hostname.endswith(".api.radio-browser.info") and hostname not in seen:
                seen.add(hostname)
                hosts.append(hostname)
        if not hosts:
            hosts = list(self.RADIO_SERVERS)
        random.shuffle(hosts)
        self._radio_servers_discovered = tuple(hosts)
        self._radio_discovered_at = time.monotonic()
        self._radio_server_index %= len(hosts)
        return self._radio_servers_discovered

    def _bounded_dns_call(self, function: Any, *args: Any, deadline: float) -> Any:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Radio Browser DNS discovery timed out")
        result: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

        def resolve() -> None:
            try:
                result.put((True, function(*args)))
            except OSError as exc:
                result.put((False, exc))

        threading.Thread(target=resolve, name="radio-browser-dns", daemon=True).start()
        try:
            succeeded, value = result.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError("Radio Browser DNS discovery timed out") from exc
        if not succeeded:
            raise value
        return value

    async def media_list(self, path: str = "") -> dict[str, Any]:
        roots = self._media_roots()
        if path:
            current = self._resolve_approved_path(path)
            if not current.is_dir():
                raise ContentError("not_a_directory", "Choose a media folder.")
        else:
            current = None
        scan_roots = [current] if current else roots
        items: list[dict[str, Any]] = []
        warnings: list[dict[str, str]] = []
        for root in scan_roots:
            try:
                entries = await asyncio.to_thread(lambda p=root: list(p.iterdir()))
            except OSError as exc:
                if current:
                    raise ContentError("media_unavailable", "This media folder cannot be read. Try again.") from exc
                warnings.append({"path": str(root), "error": "media_unavailable"})
                continue
            for entry in entries:
                try:
                    canonical = entry.resolve(strict=True)
                    if not self._within_any(canonical, roots):
                        continue
                    stat = canonical.stat()
                except (OSError, RuntimeError):
                    continue
                is_dir = canonical.is_dir()
                suffix = canonical.suffix.lower()
                kind = "directory" if is_dir else "audio" if suffix in self.AUDIO_EXTENSIONS else "video" if suffix in self.VIDEO_EXTENSIONS else None
                if not is_dir and kind is None:
                    continue
                items.append({"name": entry.name, "path": str(canonical), "kind": kind, "is_dir": is_dir, "size": stat.st_size, "modified": stat.st_mtime})
        items.sort(key=lambda item: (not item["is_dir"], item["name"].casefold()))
        if scan_roots and len(warnings) == len(scan_roots):
            raise ContentError("media_unavailable", "The media folders cannot be read. Try again.")
        parent = None
        if current:
            root = next((candidate for candidate in roots if self._within_any(current, [candidate])), current)
            if current != root:
                parent = str(current.parent)
        return {"path": str(current) if current else "", "parent": parent, "roots": [str(root) for root in roots], "items": items, "partial": bool(warnings), "warnings": warnings}

    def resolve_media(self, path: str | Path) -> Path:
        target = self._resolve_approved_path(path)
        if not target.is_file():
            raise ContentError("media_not_file", "Choose a media file.")
        return target

    def _resolve_approved_path(self, path: str | Path) -> Path:
        try:
            target = Path(path).expanduser().resolve(strict=True)
        except (OSError, RuntimeError, TypeError) as exc:
            raise ContentError("media_not_found", "This media file or folder is unavailable.") from exc
        if not self._within_any(target, self._media_roots()):
            raise ContentError("media_path_not_allowed", "This location is outside approved media folders.")
        return target

    @staticmethod
    def _within_any(target: Path, roots: list[Path]) -> bool:
        for root in roots:
            try:
                target.relative_to(root)
                return True
            except ValueError:
                pass
        return False

    def _media_roots(self) -> list[Path]:
        home = Path.home()
        candidates = [home / "Music", home / "Videos"]
        candidates.extend(self._mounted_media_roots())
        roots: list[Path] = []
        for candidate in candidates:
            try:
                resolved = candidate.resolve(strict=True)
                if resolved.is_dir() and resolved not in roots:
                    roots.append(resolved)
            except (OSError, RuntimeError):
                continue
        return roots

    @staticmethod
    def _mounted_media_roots() -> list[Path]:
        if sys.platform.startswith("linux"):
            mountinfo = Path("/proc/self/mountinfo")
            roots = []
            try:
                for line in mountinfo.read_text(encoding="utf-8").splitlines():
                    fields = line.split()
                    if len(fields) < 6:
                        continue
                    mount = Path(fields[4].replace("\\040", " "))
                    if any(mount != base and base in mount.parents for base in (Path("/media"), Path("/run/media"), Path("/mnt"))):
                        roots.append(mount)
            except OSError:
                pass
            return roots
        if os.name == "nt":
            # Windows mounted removable volumes are exposed by the OS under drive roots.
            # Avoid enumerating system drives here; Linux is the supported target.
            return []
        return []

    def _get_json(self, url: str, params: dict[str, Any] | None = None, *, headers: dict[str, str] | None = None) -> Any:
        if params:
            url += ("&" if "?" in url else "?") + urlencode(params)
        request = Request(url, headers={"User-Agent": "PiSmartHub/1.0", "Accept": "application/json", **(headers or {})})
        with urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data, dict) and data.get("error"):
            raise ContentError("upstream_error", str(data.get("reason", "Upstream service error")))
        return data


def _optional_measurement(value: Any, *, minimum: float, maximum: float | None = None,
                          exclusive_minimum: bool = False) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        if not math.isfinite(value):
            return None
    except OverflowError:
        return None
    if value < minimum or (exclusive_minimum and value == minimum) or (maximum is not None and value > maximum):
        return None
    return value


def _current_hour_uv(hourly: Any, current_time: Any) -> tuple[int | float | None, str | None]:
    from datetime import datetime
    if not isinstance(hourly, dict) or not isinstance(current_time, str) or len(current_time) < 16 or current_time[10] != "T":
        return None, None
    times, values = hourly.get("time"), hourly.get("uv_index")
    if not isinstance(times, list) or not isinstance(values, list) or len(times) != len(values):
        return None, None
    try:
        current = datetime.fromisoformat(current_time)
    except ValueError:
        return None, None
    target = current.replace(minute=0, second=0, microsecond=0)
    matches = []
    for index, stamp in enumerate(times):
        if not isinstance(stamp, str) or len(stamp) < 16 or stamp[10] != "T":
            continue
        try:
            sample = datetime.fromisoformat(stamp)
        except ValueError:
            continue
        if sample.minute == 0 and sample.second == 0 and sample.microsecond == 0 and sample == target:
            matches.append(index)
    # Duplicate local timestamps around clock changes are ambiguous.
    if len(matches) != 1:
        return None, None
    index = matches[0]
    value = _optional_measurement(values[index], minimum=0)
    return (value, times[index]) if value is not None else (None, None)


def _number(value: Any) -> bool:
    try:
        return value is not None and float(value) == float(value)
    except (TypeError, ValueError):
        return False


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
