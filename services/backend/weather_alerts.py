"""Meteoalarm Romania warnings, matched locally; no location leaves the device."""
from __future__ import annotations

import asyncio
import html
import json
import math
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .content import _write_json_atomic

FEED = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-romania"
ATOM = "http://www.w3.org/2005/Atom"
CAP_NAMESPACES = {"urn:oasis:names:tc:emergency:cap:1.1", "urn:oasis:names:tc:emergency:cap:1.2"}
LIMIT = 2_000_000
HAZARDS = {"1": "wind", "2": "snow_ice", "3": "thunderstorm", "4": "fog", "5": "heat",
           "6": "cold", "8": "forest_fire", "9": "avalanche", "10": "rain", "12": "flood", "13": "rain_flood"}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("weather_alert_redirect")


def _key(value):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", str(value))
                            if not unicodedata.combining(c)).casefold().split())


def _text(value, limit=2000):
    return " ".join(re.sub(r"<[^>]*>", " ", html.unescape(str(value or ""))).split())[:limit]


def _date(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


def _xml(raw):
    if not isinstance(raw, bytes) or len(raw) > LIMIT or b"\x00" in raw:
        raise ValueError("invalid_alert_xml")
    text = raw.decode("utf-8-sig")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
        raise ValueError("invalid_alert_xml")
    return ET.fromstring(text)


def _tag(node):
    return node.tag.rsplit("}", 1)[-1]


def _is_cap(node, tag):
    return node.tag in {"{" + ns + "}" + tag for ns in CAP_NAMESPACES}


def _cap_values(node):
    return {_tag(child): _text(child.text, 6000) for child in node
            if child.tag.startswith(tuple("{" + namespace + "}" for namespace in CAP_NAMESPACES))}


def _cap_url(url):
    parts = urlsplit(str(url))
    return (parts.scheme == "https" and parts.netloc == "feeds.meteoalarm.org"
            and not parts.query and not parts.fragment
            and re.fullmatch(r"/api/v1/warnings/feeds-romania/[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", parts.path) is not None)


def _active(values, now):
    sent, expires = _date(values.get("sent")), _date(values.get("expires"))
    start = _date(values.get("onset") or values.get("effective") or values.get("sent"))
    effective = _date(values.get("effective") or values.get("sent"))
    return (values.get("status", "").lower() == "actual" and values.get("scope", "").lower() == "public"
            and values.get("msgType", values.get("message_type", "")).lower() in ("alert", "update")
            and sent is not None and start is not None and expires is not None and effective is not None
            and sent <= now and effective <= now and start <= now < expires and sent < expires
            and values.get("severity", "").lower() in ("minor", "moderate", "severe", "extreme")
            and bool(values.get("identifier")) and bool(values.get("event")))


def _unverified(values, now):
    if values.get("status", "").lower() in ("test", "draft", "exercise", "system") or values.get("msgType", values.get("message_type", "")).lower() in ("cancel", "ack", "error"):
        return False
    if values.get("status", "").lower() != "actual" or values.get("scope", "").lower() != "public":
        return True
    sent, expires = _date(values.get("sent")), _date(values.get("expires"))
    if sent is None or expires is None or sent > now or sent >= expires:
        return True
    if expires <= now:
        return False
    start = _date(values.get("onset") or values.get("effective") or values.get("sent"))
    effective = _date(values.get("effective") or values.get("sent"))
    if start is None or effective is None or start >= expires or effective >= expires:
        return True
    return start <= now and effective <= now and not _active(values, now)


def _superseded(entries, now):
    references = set()
    for entry in entries:
        values = _cap_values(entry)
        kind = values.get("msgType", values.get("message_type", "")).lower()
        sent = _date(values.get("sent"))
        effective = _date(values.get("effective") or values.get("sent"))
        if (values.get("status", "").lower() != "actual" or values.get("scope", "").lower() != "public"
                or kind not in ("cancel", "update") or sent is None or sent > now
                or effective is None or effective > now or not values.get("identifier")):
            continue
        if kind == "update" and _unverified(values, now):
            continue
        for reference in values.get("references", "").split():
            parts = reference.split(",")
            if len(parts) == 3 and parts[0] and parts[1]:
                previous_sent = _date(parts[2])
                if previous_sent is not None and previous_sent <= sent:
                    references.add((parts[0], parts[1], previous_sent))
    superseded = set()
    for entry in entries:
        values = _cap_values(entry)
        identity = (values.get("identifier"), _date(values.get("sent")))
        if any(identifier == identity[0] and sent == identity[1]
               and (not values.get("sender") or values["sender"] == sender)
               for sender, identifier, sent in references):
            superseded.add(identity)
    return superseded


def _bucharest(name):
    return re.fullmatch(r"(?:bucuresti|bucharest|bucarest)(?:\s*[·,\-]?\s*sector(?:ul)?\s*[1-6])?", _key(name)) is not None


def _coordinates(location):
    try:
        lat, lon = location["latitude"], location["longitude"]
        if isinstance(lat, bool) or isinstance(lon, bool):
            return None
        lat, lon = float(lat), float(lon)
        return (lat, lon) if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180 else None
    except (KeyError, TypeError, ValueError):
        return None


def _area_match(area, location, point):
    """None means unverified coverage, never a false 'no warnings'."""
    geometry = [n for n in area if _is_cap(n, "polygon") or _is_cap(n, "circle")]
    if geometry:
        matches = []
        for node in geometry:
            try:
                values = (node.text or "").split()
                if _tag(node) == "polygon":
                    points = [tuple(map(float, pair.split(","))) for pair in values]
                    if len(points) < 4 or points[0] != points[-1]:
                        return None
                    if any(len(p) != 2 or not all(math.isfinite(v) for v in p) or not -90 <= p[0] <= 90 or not -180 <= p[1] <= 180 for p in points):
                        return None
                    x, y = point[1], point[0]
                    inside = False
                    for (y1, x1), (y2, x2) in zip(points, points[1:]):
                        if abs((x-x1)*(y2-y1)-(y-y1)*(x2-x1)) < 1e-9 and min(x1,x2) <= x <= max(x1,x2) and min(y1,y2) <= y <= max(y1,y2):
                            inside = True
                            break
                        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1:
                            inside = not inside
                    matches.append(inside)
                else:
                    if len(values) != 2:
                        return None
                    lat, lon = map(float, values[0].split(","))
                    radius = float(values[1])
                    if not all(math.isfinite(v) for v in (lat,lon,radius)) or not -90 <= lat <= 90 or not -180 <= lon <= 180 or radius < 0:
                        return None
                    a, b = map(math.radians, (lat, point[0]))
                    h = math.sin((b-a)/2)**2 + math.cos(a)*math.cos(b)*math.sin(math.radians(point[1]-lon)/2)**2
                    matches.append(6371 * 2 * math.asin(math.sqrt(min(1,h))) <= radius)
            except (ValueError, TypeError, OverflowError):
                return None
        return any(matches)
    values = _cap_values(area)
    if (_bucharest(location.get("name", "")) and 44.2 <= point[0] <= 44.7 and 25.8 <= point[1] <= 26.4
            and _key(values.get("areaDesc", "")) in {"bucuresti", "bucharest", "bucarest"}):
        return True
    return None


class WeatherAlerts:
    def __init__(self, data_dir: str | Path, *, timeout: float = 8.0):
        self.cache_path = Path(data_dir) / "weather-alerts-cache.json"
        self.timeout = timeout
        self._cache = None
        self._lock = asyncio.Lock()

    def _fetch(self, url):
        if url != FEED and not _cap_url(url):
            raise ValueError("untrusted_weather_alert_source")
        opener = build_opener(_NoRedirect())
        # Meteoalarm rejects explicit XML Accept types with406; validate the XML below.
        with opener.open(Request(url, headers={"User-Agent": "PiSmartHub/1.0", "Accept": "*/*"}), timeout=self.timeout) as response:
            if response.geturl() != url or response.status != 200:
                raise ValueError("weather_alert_response")
            data = response.read(LIMIT + 1)
        _xml(data)
        return data.decode("utf-8-sig")

    @staticmethod
    def _entries(feed):
        if not isinstance(feed, str):
            raise ValueError("invalid_weather_alert_feed")
        root = _xml(feed.encode("utf-8"))
        if root.tag != f"{{{ATOM}}}feed":
            raise ValueError("invalid_weather_alert_feed")
        return root, root.findall(f"{{{ATOM}}}entry")

    async def _refresh(self, now):
        feed = await asyncio.to_thread(self._fetch, FEED)
        root, entries = self._entries(feed)
        if _date(root.findtext(f"{{{ATOM}}}updated")) is None:
            raise ValueError("missing_weather_alert_timestamp")
        urls = []
        superseded = _superseded(entries, now)
        for entry in entries:
            values = _cap_values(entry)
            if (values.get("identifier"), _date(values.get("sent"))) in superseded or not _active(values, now):
                continue
            for link in entry.findall(f"{{{ATOM}}}link"):
                url = link.get("href", "")
                if link.get("type") == "application/cap+xml" and _cap_url(url) and url not in urls:
                    urls.append(url)
        documents = await asyncio.gather(*(asyncio.to_thread(self._fetch, url) for url in urls[:4]), return_exceptions=True)
        value = {"feed": feed, "documents": {url: data for url, data in zip(urls[:4], documents) if isinstance(data, str)}, "fetched_at": now.isoformat()}
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache = value
        try:
            await asyncio.to_thread(_write_json_atomic, self.cache_path, value)
        except OSError:
            pass

    async def snapshot(self, location: dict, *, now: datetime | None = None):
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("UTC-aware time required")
        now = now.astimezone(timezone.utc)
        result = {"state": "unavailable", "updated_at": None, "alerts": [], "coverage": "Romania", "error": "weather_alerts_unavailable"}
        point = _coordinates(location)
        if point is None or (location.get("country") and _key(location["country"]) not in {"romania", "ro", "roumanie"}):
            return result
        async with self._lock:
            failed = False
            if self._cache is None:
                try:
                    if self.cache_path.stat().st_size <= LIMIT * 5 + 100_000:
                        self._cache = json.loads(self.cache_path.read_text("utf-8"))
                except (OSError, ValueError):
                    pass
            cached_at = _date(self._cache.get("fetched_at")) if isinstance(self._cache, dict) else None
            if cached_at is None or not 0 <= (now-cached_at).total_seconds() < 300:
                try:
                    await self._refresh(now)
                except Exception:
                    failed = True
            try:
                root, entries = self._entries(self._cache["feed"])
                updated = _date(root.findtext(f"{{{ATOM}}}updated"))
                if updated is None or updated > now:
                    return result
                result["updated_at"] = updated.isoformat()
                partial = False
                superseded = _superseded(entries, now)
                for entry in entries:
                    values = _cap_values(entry)
                    if (values.get("identifier"), _date(values.get("sent"))) in superseded:
                        continue
                    awareness = re.search(r"(?:^|[,;]\s*)awareness_type\s*=\s*(\d+)\b", values.get("event", ""))
                    hazard = HAZARDS.get(awareness.group(1)) if awareness else None
                    if not _active(values, now):
                        partial = partial or _unverified(values, now)
                        continue
                    areas = [entry]
                    url = next((link.get("href", "") for link in entry.findall(f"{{{ATOM}}}link") if link.get("type") == "application/cap+xml" and _cap_url(link.get("href", ""))), FEED)
                    document = self._cache.get("documents", {}).get(url)
                    if document:
                        if not isinstance(document, str):
                            raise ValueError("invalid_weather_alert_document")
                        cap = _xml(document.encode("utf-8"))
                        if cap.tag not in {"{" + ns + "}alert" for ns in CAP_NAMESPACES}:
                            partial = True
                            continue
                        envelope = _cap_values(cap)
                        infos = [child for child in cap if _is_cap(child, "info")]
                        if not infos:
                            partial = True
                            continue
                        if envelope.get("identifier") != values.get("identifier"):
                            partial = True
                            continue
                        candidates, uncertain = [], False
                        for candidate in infos:
                            full = {**envelope, **_cap_values(candidate)}
                            if not _active(full, now):
                                uncertain = uncertain or _unverified(full, now)
                                continue
                            matches = [_area_match(area, location, point) for area in candidate if _is_cap(area, "area")]
                            if True in matches:
                                candidates.append((candidate, full))
                            else:
                                uncertain = uncertain or not matches or None in matches
                        if not candidates:
                            partial = partial or uncertain
                            continue
                        info, values = next((pair for pair in candidates if pair[1].get("language", "").lower().startswith("ro")), candidates[0])
                        areas = [child for child in info if _is_cap(child, "area")]
                    matched = [_area_match(area, location, point) for area in areas]
                    if True not in matched:
                        partial = partial or not matched or None in matched
                        continue
                    for node in (info if document else entry).iter():
                        if _is_cap(node, "parameter"):
                            pair = _cap_values(node)
                            if pair.get("valueName") == "awareness_type":
                                hazard = HAZARDS.get(pair.get("value", "").split(";",1)[0].strip())
                    event = (entry.findtext(f"{{{ATOM}}}title") or values["event"]) if awareness and not document else values["event"]
                    if re.search(r"\btornad\w*\b", _key(event + " " + values.get("headline", ""))):
                        hazard = "tornado"
                    alert = {"id": values["identifier"], "event": _text(event, 160),
                             "headline": _text(values.get("headline") or event, 240),
                             "description": _text(values.get("description"), 3000), "severity": values["severity"].lower(),
                             "onset": values.get("onset") or values.get("effective") or values["sent"], "expires": values["expires"],
                             "provider": "Meteoalarm / Administrația Națională de Meteorologie", "source": FEED, "url": url}
                    if hazard:
                        alert["hazard"] = hazard
                    if not any(a["id"] == alert["id"] for a in result["alerts"]):
                        result["alerts"].append(alert)
                known_country = _key(location.get("country", "")) in {"romania", "ro", "roumanie"} or _bucharest(location.get("name", ""))
                if not result["alerts"] and not known_country:
                    partial = True
                stale = failed or (now-updated).total_seconds() > 86400
                result["state"] = "stale" if stale else "unavailable" if partial and not result["alerts"] else "available"
                result["error"] = "weather_alerts_unavailable" if stale or partial else None
                if partial:
                    result["partial"] = True
                return result
            except (KeyError, TypeError, ValueError, ET.ParseError):
                return result
