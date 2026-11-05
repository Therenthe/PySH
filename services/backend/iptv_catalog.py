"""Bounded M3U/XMLTV catalogue. Synchronous methods run in the API's worker pool.

Only playlist metadata is imported: VLC/Kodi options, DRM directives and arbitrary
headers are never executed. Network fetches pin verified public DNS on every hop.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
from html import unescape
from html.parser import HTMLParser
from http.client import HTTPConnection, HTTPSConnection, HTTPException
import io
import ipaddress
import json
from pathlib import Path
import re
import socket
import threading
import time
import unicodedata
from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from .content import _write_json_atomic

DEFAULT_PLAYLISTS = (
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_romania.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
    'https://iptv-org.github.io/iptv/countries/ro.m3u',
    'https://iptv-org.github.io/iptv/index.m3u',
)
DEFAULT_XMLTV = ('https://www.open-epg.com/files/romania1.xml.gz',)
OFFICIAL_PROTV = 'https://www.protv.ro/program'
OFFICIAL_ANTENA = 'https://a1.ro/program-tv/'
FAVORITE_NAMES = (
    'PRO TV HD (1080p)', 'Antena 1 (Romania)', 'Bellator MMA',
    'ESPN 2 (United States) HD (720p)', 'ESPN (United States) HD (720p)',
    'NBA TV (720p)', 'NBC Sports NOW (1080p)', 'PokerGo',
)
MAX_DOWNLOAD = 24 * 1024 * 1024
MAX_XML = 64 * 1024 * 1024
MAX_CHANNELS = 20000
MAX_PROGRAMMES = 60000
MAX_SOURCE_URLS = 8
CACHE_BYTES = 48 * 1024 * 1024
UTC = timezone.utc


class IPTVError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def public_url(url):
    """Validate syntax without doing thousands of DNS lookups during import."""
    if not isinstance(url, str) or not 1 <= len(url) <= 4096 or any(ord(c) < 33 or ord(c) == 127 for c in url):
        raise IPTVError('iptv_invalid_url')
    try:
        parsed = urlsplit(url)
        if (parsed.scheme not in {'http', 'https'} or not parsed.hostname
                or parsed.username is not None or parsed.password is not None or parsed.fragment
                or '\\' in url or parsed.port is not None and not 1 <= parsed.port <= 65535):
            raise ValueError()
        parsed.hostname.encode('idna')
        # Reject literal local addresses immediately; DNS names are checked at use.
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            address = None
        if address is not None and (not address.is_global or address.is_multicast):
            raise ValueError()
        if parsed.hostname.casefold() in {'localhost', 'localhost.localdomain'} or parsed.hostname.casefold().endswith(('.localhost', '.local', '.internal')):
            raise ValueError()
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or '/', parsed.query, ''))
    except (ValueError, UnicodeError) as error:
        raise IPTVError('iptv_invalid_url') from error


def _addresses(url):
    parsed = urlsplit(public_url(url))
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    try:
        addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global
                                or ipaddress.ip_address(item[4][0]).is_multicast for item in addresses):
            raise ValueError()
    except (OSError, ValueError) as error:
        raise IPTVError('iptv_source_unavailable') from error
    return parsed, port, addresses[0][4][0]


def verify_public_url(url):
    _addresses(url)
    return public_url(url)


def fetch_public_resource(url, max_bytes=MAX_DOWNLOAD, timeout=15, headers=None, transport_factory=None):
    """Return bytes, final URL, MIME type and lower-case response headers.

    The original hostname remains the TLS SNI/certificate identity while the
    socket connects to the already verified address. Proxies are not inherited.
    """
    deadline = time.monotonic() + timeout
    url = public_url(url)
    safe_headers = {'User-Agent': 'PiSmartHub/1.0', 'Accept': '*/*', 'Accept-Encoding': 'identity'}
    if headers:
        for key, value in headers.items():
            if key.casefold() not in {'range', 'if-range'} or not isinstance(value, str) or len(value) > 256 or any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise IPTVError('iptv_invalid_request')
            safe_headers[key] = value
    try:
        for hop in range(5):
            parsed, port, address = _addresses(url)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise IPTVError('iptv_source_timeout')
            connection = (HTTPSConnection if parsed.scheme == 'https' else HTTPConnection)(
                parsed.hostname, port, timeout=min(8, remaining))
            connection._create_connection = lambda target, timeout, source_address=None: socket.create_connection((address, port), timeout, source_address)
            handed_off = False
            try:
                path = (parsed.path or '/') + ('?' + parsed.query if parsed.query else '')
                connection.request('GET', path, headers=safe_headers)
                source_socket = getattr(connection, 'sock', None)
                response = connection.getresponse()
                result_headers = {key.lower(): value for key, value in response.getheaders()}
                if response.status in {301, 302, 303, 307, 308}:
                    target = public_url(urljoin(url, result_headers.get('location', '')))
                    if hop == 4 or not result_headers.get('location') or parsed.scheme == 'https' and urlsplit(target).scheme != 'https':
                        raise IPTVError('iptv_invalid_redirect')
                    url = target
                    continue
                if response.status not in {200, 206}:
                    raise IPTVError('iptv_source_unavailable')
                length = result_headers.get('content-length')
                if length and (not length.isdecimal() or int(length) > max_bytes and transport_factory is None):
                    raise IPTVError('iptv_source_too_large')
                raw = bytearray()
                while len(raw) <= max_bytes:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise IPTVError('iptv_source_timeout')
                    if connection.sock:
                        connection.sock.settimeout(min(8, remaining))
                    block = response.read1(min(64 * 1024, max_bytes + 1 - len(raw)))
                    if not block:
                        break
                    raw.extend(block)
                    if transport_factory is not None and len(raw) >= 564:
                        from .iptv_transport import is_transport
                        if is_transport(raw):
                            transport = transport_factory(response, connection, bytes(raw), url, source_socket)
                            handed_off = True
                            return transport
                        transport_factory = None
                        if length and (not length.isdecimal() or int(length) > max_bytes):
                            raise IPTVError('iptv_source_too_large')
                if len(raw) > max_bytes:
                    raise IPTVError('iptv_source_too_large')
                if length and int(length) > max_bytes:
                    raise IPTVError('iptv_source_too_large')
                return bytes(raw), url, result_headers.get('content-type', '').split(';')[0].lower(), result_headers
            finally:
                if not handed_off:connection.close()
    except IPTVError:
        raise
    except (OSError, ValueError, HTTPException) as error:
        raise IPTVError('iptv_source_unavailable') from error
    raise IPTVError('iptv_invalid_redirect')


def fetch_public(url, max_bytes=MAX_DOWNLOAD, timeout=15):
    return fetch_public_resource(url, max_bytes, timeout)[0]


def _key(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', str(value))
                            if not unicodedata.combining(c)).casefold().split())


def _text(value, limit=4000):
    return ' '.join(re.sub(r'<[^>]*>', ' ', unescape(str(value or ''))).split())[:limit]


def _name_key(value):
    value = _key(value)
    value = re.sub(r'@[^\s]+$', '', value)
    value = re.sub(r'\.(?:ro|us|uk|de|fr|it|es|nl|pe)$', '', value)
    value = re.sub(r'\([^)]*\)', '', value)
    value = re.sub(r'\b(?:fhd|uhd|hd|sd|4k|\d{3,4}p)\b', '', value)
    return re.sub(r'[^a-z0-9]', '', value)


def _id_key(value):
    return re.sub(r'[^a-z0-9]', '', _key(value).split('@', 1)[0])


def parse_m3u(raw, source):
    if not isinstance(raw, bytes) or len(raw) > MAX_DOWNLOAD:
        raise IPTVError('iptv_invalid_playlist')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeError as error:
        raise IPTVError('iptv_invalid_playlist') from error
    lines = text.splitlines()
    if not lines or lines[0].strip().upper().split(' ', 1)[0] != '#EXTM3U':
        raise IPTVError('iptv_invalid_playlist')
    channels, pending = [], None
    for line in lines[1:]:
        line = line.strip()
        if len(line) > 16384:
            pending = None
            continue
        if line.upper().startswith('#EXTINF:'):
            attrs = {k.casefold(): v for k, _, v in re.findall(r'([\w-]+)\s*=\s*(["\'])(.*?)\2', line)}
            # A comma inside a quoted attribute must not split the display name.
            separator, quoted = -1, None
            for index, char in enumerate(line):
                if char in {'"', "'"}:
                    quoted = None if quoted == char else char if quoted is None else quoted
                elif char == ',' and quoted is None:
                    separator = index
                    break
            name = _text(line[separator + 1:] if separator >= 0 else attrs.get('tvg-name'), 240)
            pending = {'name': name, 'tvg_id': _text(attrs.get('tvg-id'), 200),
                       'tvg_name': _text(attrs.get('tvg-name'), 240), 'logo': '',
                       'group': _text(attrs.get('group-title'), 120), 'source': source, 'sources': [source]}
            try:
                pending['logo'] = public_url(attrs.get('tvg-logo', ''))
            except IPTVError:
                pass
        elif line and not line.startswith('#'):
            if pending and pending['name']:
                try:
                    url = public_url(urljoin(source, line))
                    channels.append({**pending, 'url': url, 'id': 'tv_' + hashlib.sha256(url.encode()).hexdigest()[:24]})
                except IPTVError:
                    pass
            pending = None
            if len(channels) >= MAX_CHANNELS:
                break
    if not channels:
        raise IPTVError('iptv_empty_playlist')
    return channels


def xmltv_time(value):
    match = re.fullmatch(r'(\d{14})(?:\s+([+-])(\d{2})(\d{2}))?', str(value or '').strip())
    if not match:
        raise ValueError('invalid_xmltv_time')
    hours, minutes = int(match[3] or 0), int(match[4] or 0)
    if hours > 23 or minutes > 59:
        raise ValueError('invalid_xmltv_timezone')
    offset = timedelta(hours=hours, minutes=minutes) * (-1 if match[2] == '-' else 1)
    return datetime.strptime(match[1], '%Y%m%d%H%M%S').replace(tzinfo=timezone(offset)).astimezone(UTC)


def _programme(channel, start, end, title, description, source):
    title = _text(title, 240)
    if not channel or not title or not start < end or end - start > timedelta(hours=24):
        return None
    return {'id': 'pg_' + hashlib.sha256(f'{channel}|{start.isoformat()}|{title}'.encode()).hexdigest()[:24],
            'channel': channel, 'title': title, 'description': _text(description),
            'start': start.isoformat(), 'end': end.isoformat(), 'source': source}


def parse_xmltv(raw, source, now=None):
    if not isinstance(raw, bytes) or len(raw) > MAX_DOWNLOAD:
        raise IPTVError('iptv_invalid_xmltv')
    if raw.startswith(b'\x1f\x8b'):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as compressed:
                raw = compressed.read(MAX_XML + 1)
        except (OSError, EOFError) as error:
            raise IPTVError('iptv_invalid_xmltv') from error
    if len(raw) > MAX_XML or b'\0' in raw or re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b', raw, re.I):
        raise IPTVError('iptv_invalid_xmltv')
    now = (now or datetime.now(UTC)).astimezone(UTC)
    minimum, maximum = now - timedelta(hours=24), now + timedelta(days=14)
    channels, programmes, count, depth = {}, [], 0, 0
    try:
        context = ET.iterparse(io.BytesIO(raw), events=('start', 'end'))
        root = None
        for event, element in context:
            if event == 'start':
                depth += 1
                if root is None:
                    root = element
                    if element.tag != 'tv':
                        raise ValueError()
                if depth > 12:
                    raise ValueError()
                continue
            depth -= 1
            if element.tag == 'channel' and depth == 1:
                identifier = _text(element.get('id'), 200)
                if identifier:
                    if len(channels) >= MAX_CHANNELS:
                        raise ValueError()
                    channels[identifier] = [_text(n.text, 240) for n in element.findall('display-name')[:8]]
                element.clear()
                root.clear()
            elif element.tag == 'programme' and depth == 1:
                count += 1
                if count > MAX_PROGRAMMES:
                    raise ValueError()
                try:
                    start, end = xmltv_time(element.get('start')), xmltv_time(element.get('stop'))
                    if end >= minimum and start <= maximum:
                        item = _programme(_text(element.get('channel'), 200), start, end,
                                          element.findtext('title'), element.findtext('desc'), source)
                        if item:
                            programmes.append(item)
                except (ValueError, OverflowError):
                    pass
                element.clear()
                root.clear()
        if root is None or not channels:
            raise ValueError()
    except (ET.ParseError, ValueError) as error:
        raise IPTVError('iptv_invalid_xmltv') from error
    return channels, programmes


def parse_protv(raw, now=None):
    """Read the official schedule's JSON value, never execute its JavaScript."""
    text = raw.decode('utf-8-sig')
    match = re.search(r'\bvar\s+PageData\s*=\s*', text)
    if not match:
        raise IPTVError('iptv_official_unavailable')
    try:
        page, _ = json.JSONDecoder().raw_decode(text[match.end():])
        programmes = []
        for day in page.get('program', [])[:20]:
            for channel in day.get('channels', [])[:16]:
                if channel.get('id') != 1:
                    continue
                for segment in channel.get('segments', [])[:8]:
                    for entry in segment.get('items', [])[:100]:
                        start = datetime.fromisoformat(entry['start_at'])
                        end = datetime.fromisoformat(entry['end_at'])
                        if start.tzinfo is None or end.tzinfo is None:
                            continue
                        item = _programme('PRO TV.ro', start.astimezone(UTC), end.astimezone(UTC),
                                          entry.get('title'), entry.get('description') or entry.get('short_description'), OFFICIAL_PROTV)
                        if item:
                            programmes.append(item)
        if not programmes:
            raise ValueError()
        return {'PRO TV.ro': ['PRO TV']}, programmes
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise IPTVError('iptv_official_unavailable') from error


class _AntenaSchedule(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.days = [], []
        self.day, self.row, self.heading = None, None, ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get('class', '').split())
        self.stack.append((tag, classes))
        if 'sch__day' in classes:
            self.day = {'heading': '', 'rows': []}
            self.days.append(self.day)
        elif 'sch__item' in classes and self.day is not None:
            self.row = {'time': '', 'title': '', 'description': ''}
            self.day['rows'].append(self.row)

    def handle_endtag(self, tag):
        # HTML void elements have no end tag.
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                removed = self.stack[index:]
                self.stack = self.stack[:index]
                if any('sch__item' in c for _, c in removed):
                    self.row = None
                if any('sch__day' in c for _, c in removed):
                    self.day = None
                break

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_data(self, data):
        if self.day is None or not data.strip():
            return
        if any(tag == 'h2' for tag, _ in self.stack):
            self.day['heading'] += data
        if self.row is None or any('sch__vezi' in c for _, c in self.stack):
            return
        if any('sch__title' in c for _, c in self.stack):
            self.row['title'] += data
        elif any(tag == 'p' for tag, _ in self.stack):
            self.row['description'] += data
        elif re.fullmatch(r'\d{2}:\d{2}', data.strip()):
            self.row['time'] = data.strip()


def parse_antena(raw, now=None):
    now = (now or datetime.now(UTC)).astimezone(ZoneInfo('Europe/Bucharest'))
    parser = _AntenaSchedule()
    parser.feed(raw.decode('utf-8-sig'))
    months = ['ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie', 'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie']
    weekdays = ['luni', 'marti', 'miercuri', 'joi', 'vineri', 'sambata', 'duminica']
    entries = []
    for day in parser.days[:10]:
        match = re.search(r'\b(' + '|'.join(weekdays) + r'),?\s+(\d{1,2})\s+(' + '|'.join(months) + r')\b', _key(day['heading']))
        if not match:
            continue
        date = None
        for year in (now.year - 1, now.year, now.year + 1):
            try:
                candidate = datetime(year, months.index(match[3]) + 1, int(match[2]), tzinfo=now.tzinfo)
                if -2 <= (candidate.date() - now.date()).days <= 8 and weekdays[candidate.weekday()] == match[1]:
                    date = candidate
                    break
            except ValueError:
                pass
        if date is None:
            continue
        previous, rollover = -1, 0
        for row in day['rows'][:100]:
            if not re.fullmatch(r'\d{2}:\d{2}', row['time']):
                continue
            hour, minute = map(int, row['time'].split(':'))
            if hour > 23 or minute > 59:
                continue
            minutes = hour * 60 + minute
            if minutes < previous:
                rollover += 1
            if rollover > 1:
                continue
            previous = minutes
            start = (date + timedelta(days=rollover)).replace(hour=hour, minute=minute).astimezone(UTC)
            entries.append((start, row['title'], row['description']))
    entries = sorted(set(entries))
    programmes = []
    for entry, following in zip(entries, entries[1:]):
        if following[0] - entry[0] <= timedelta(hours=12):
            item = _programme('Antena 1.ro', entry[0], following[0], entry[1], entry[2], OFFICIAL_ANTENA)
            if item:
                programmes.append(item)
    if not programmes:
        raise IPTVError('iptv_official_unavailable')
    return {'Antena 1.ro': ['Antena 1 (Romania)']}, programmes


def _read_cache(path, limit):
    try:
        if path.stat().st_size > limit:
            return {}
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _cached_channel(value):
    if not isinstance(value, dict) or not {'id', 'name', 'url', 'tvg_id', 'logo', 'group'} <= value.keys():
        return False
    if any(not isinstance(value.get(key), str) or len(value[key]) > 4096 for key in ('id', 'name', 'url', 'tvg_id', 'logo', 'group')):
        return False
    try:
        public_url(value['url'])
        return bool(re.fullmatch(r'tv_[a-f0-9]{24}', value['id']))
    except IPTVError:
        return False


def _cached_programme(value):
    keys = {'id', 'channel', 'start', 'end', 'title', 'description', 'source'}
    if not isinstance(value, dict) or not keys <= value.keys() or any(not isinstance(value[key], str) for key in keys):
        return False
    try:
        start, end = datetime.fromisoformat(value['start']), datetime.fromisoformat(value['end'])
        return (start.tzinfo is not None and end.tzinfo is not None and start < end
                and end - start <= timedelta(days=1) and len(value['description']) <= 4000)
    except (ValueError, TypeError):
        return False


class IPTVLibrary:
    def __init__(self, data_dir, *, fetch=None):
        self.directory = Path(data_dir) / 'iptv'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.fetch = fetch or fetch_public
        self._lock, self._refresh_lock = threading.RLock(), threading.Lock()
        self._generation = 0
        config = _read_cache(self.directory / 'config.json', 256 * 1024)
        self.sources = {'playlists': list(DEFAULT_PLAYLISTS), 'xmltv': list(DEFAULT_XMLTV)}
        for kind in self.sources:
            try:
                self.sources[kind] = self._source_urls(config.get(kind, self.sources[kind]))
            except IPTVError:
                pass
        favorites = config.get('favorites', {})
        self.favorite_overrides = {key: value for key, value in (favorites.items() if isinstance(favorites, dict) else ())
                                   if isinstance(key, str) and re.fullmatch(r'tv_[a-f0-9]{24}', key) and type(value) is bool}
        cached = _read_cache(self.directory / 'cache.json', CACHE_BYTES)
        self.channels = cached.get('channels', []) if isinstance(cached.get('channels'), list) else []
        self.channels = [c for c in self.channels[:MAX_CHANNELS] if _cached_channel(c)]
        epg_channels = cached.get('epg_channels', {}) if isinstance(cached.get('epg_channels'), dict) else {}
        self.epg_channels = {key: value for key, value in list(epg_channels.items())[:MAX_CHANNELS]
                             if isinstance(key, str) and isinstance(value, list) and all(isinstance(a, str) for a in value)}
        self.programmes = cached.get('programmes', []) if isinstance(cached.get('programmes'), list) else []
        self.programmes = [p for p in self.programmes[:MAX_PROGRAMMES] if _cached_programme(p)]
        source_status = cached.get('source_status', {}) if isinstance(cached.get('source_status'), dict) else {}
        self.source_status = {key: value for key, value in source_status.items()
                              if isinstance(key, str) and isinstance(value, dict)
                              and value.get('status') in {'ok', 'stale', 'error'}}
        self.updated_at = self._cached_time(cached.get('updated_at'))
        self.guide_updated_at = self._cached_time(cached.get('guide_updated_at'))

    @staticmethod
    def _cached_time(value):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed.astimezone(UTC).isoformat() if parsed.tzinfo is not None else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _source_urls(urls):
        if not isinstance(urls, (list, tuple)) or not 1 <= len(urls) <= MAX_SOURCE_URLS:
            raise IPTVError('iptv_invalid_sources')
        return list(dict.fromkeys(public_url(url) for url in urls))

    def _save_config(self):
        _write_json_atomic(self.directory / 'config.json', {**self.sources, 'favorites': self.favorite_overrides})

    def _save_cache(self):
        value = {key: getattr(self, key) for key in ('channels', 'epg_channels', 'programmes', 'source_status', 'updated_at', 'guide_updated_at')}
        if len(json.dumps(value, ensure_ascii=False).encode('utf-8')) > CACHE_BYTES:
            raise IPTVError('iptv_cache_too_large')
        try:
            _write_json_atomic(self.directory / 'cache.json', value)
        except OSError as error:
            raise IPTVError('iptv_storage_unavailable') from error

    def set_sources(self, kind, urls):
        if kind not in {'playlists', 'xmltv'}:
            raise IPTVError('iptv_invalid_sources')
        urls = self._source_urls(urls)
        with self._lock:
            previous = self.sources[kind]
            self.sources[kind] = urls
            try:
                self._save_config()
            except OSError as error:
                self.sources[kind] = previous
                raise IPTVError('iptv_storage_unavailable') from error
            self._generation += 1
            return self.catalogue()

    def set_favorite(self, channel_id, favorite):
        if type(favorite) is not bool:
            raise IPTVError('iptv_invalid_favorite')
        with self._lock:
            self._find(channel_id)
            previous = self.favorite_overrides.copy()
            self.favorite_overrides[channel_id] = favorite
            try:
                self._save_config()
            except OSError as error:
                self.favorite_overrides = previous
                raise IPTVError('iptv_storage_unavailable') from error
            return self.catalogue()

    def _find(self, channel_id):
        channel = next((c for c in self.channels if c['id'] == channel_id), None)
        if channel is None:
            raise IPTVError('iptv_channel_missing')
        return channel

    def resolve(self, channel_id):
        with self._lock:
            channel = copy.deepcopy(self._find(channel_id))
        channel['url'] = verify_public_url(channel['url'])
        return channel

    def _favorite_requests(self):
        by_name = {}
        for channel in self.channels:
            by_name.setdefault(_key(channel['name']), channel)
        result = []
        for name in FAVORITE_NAMES:
            # An exact requested variant wins; other quality/country variants are
            # not silently substituted for a missing requested channel.
            selected = by_name.get(_key(name))
            result.append({'name': name, 'channel_id': selected['id'] if selected else None,
                           'status': 'listed' if selected else 'not_in_playlists'})
        return result

    def catalogue(self):
        with self._lock:
            requests = self._favorite_requests()
            seeded = {r['channel_id'] for r in requests if r['channel_id']}
            channels = [{**c, 'favorite': self.favorite_overrides.get(c['id'], c['id'] in seeded)} for c in self.channels]
            return copy.deepcopy({'channels': channels, 'sources': self.sources, 'source_status': self.source_status,
                                  'favorite_requests': requests, 'updated_at': self.updated_at,
                                  'guide_updated_at': self.guide_updated_at})

    def refresh_playlists(self):
        if not self._refresh_lock.acquire(blocking=False):
            raise IPTVError('iptv_refresh_busy')
        try:
            with self._lock:
                sources, generation = self.sources['playlists'][:], self._generation
                old_channels = copy.deepcopy(self.channels)
            channels, status = {}, {}
            for source in sources:
                try:
                    items = parse_m3u(self.fetch(source), source)
                    status[source] = {'status': 'ok', 'count': len(items), 'updated_at': datetime.now(UTC).isoformat()}
                except Exception as error:
                    items = [c for c in old_channels if source in c.get('sources', [c.get('source')])]
                    status[source] = {'status': 'stale' if items else 'error', 'error': error.code if isinstance(error, IPTVError) else 'iptv_source_unavailable'}
                for item in items:
                    if item['id'] in channels:
                        channels[item['id']]['sources'] = list(dict.fromkeys([*channels[item['id']].get('sources', []), source]))
                    elif len(channels) < MAX_CHANNELS:
                        channels[item['id']] = {**item, 'sources': [source]}
            with self._lock:
                if generation != self._generation:
                    raise IPTVError('iptv_sources_changed')
                self.channels = list(channels.values())
                self.source_status.update(status)
                if any(value['status'] == 'ok' for value in status.values()):
                    self.updated_at = datetime.now(UTC).isoformat()
                self._save_cache()
                return self.catalogue()
        finally:
            self._refresh_lock.release()

    def refresh_guide(self):
        if not self._refresh_lock.acquire(blocking=False):
            raise IPTVError('iptv_refresh_busy')
        try:
            with self._lock:
                sources, generation = self.sources['xmltv'][:], self._generation
                old_channels, old_programmes = copy.deepcopy(self.epg_channels), copy.deepcopy(self.programmes)
            channels, programmes, status = {}, [], {}
            now = datetime.now(UTC)
            for source in [*sources, OFFICIAL_PROTV, OFFICIAL_ANTENA]:
                try:
                    raw = self.fetch(source)
                    parser = parse_protv if source == OFFICIAL_PROTV else parse_antena if source == OFFICIAL_ANTENA else parse_xmltv
                    channel_items, items = parser(raw, now=now) if parser != parse_xmltv else parser(raw, source, now=now)
                    channels.update(channel_items)
                    programmes.extend(items)
                    status[source] = {'status': 'ok', 'count': len(items), 'updated_at': now.isoformat()}
                except Exception as error:
                    retained = [p for p in old_programmes if p.get('source') == source]
                    programmes.extend(retained)
                    for identifier in {p['channel'] for p in retained}:
                        channels[identifier] = old_channels.get(identifier, [identifier])
                    status[source] = {'status': 'stale' if retained else 'error', 'error': error.code if isinstance(error, IPTVError) else 'iptv_source_unavailable'}
            programmes = [p for p in programmes if now - timedelta(days=1) <= datetime.fromisoformat(p['end'])
                          and datetime.fromisoformat(p['start']) <= now + timedelta(days=14)]
            if len(programmes) > MAX_PROGRAMMES:
                raise IPTVError('iptv_source_too_large')
            with self._lock:
                if generation != self._generation:
                    raise IPTVError('iptv_sources_changed')
                self.epg_channels, self.programmes = channels, programmes
                self.source_status.update(status)
                if any(value['status'] == 'ok' for value in status.values()):
                    self.guide_updated_at = now.isoformat()
                self._save_cache()
                return {'updated_at': self.guide_updated_at, 'source_status': copy.deepcopy(status), 'programmes': len(programmes)}
        finally:
            self._refresh_lock.release()

    def guide(self, channel_id, now=None):
        now = now or datetime.now(UTC)
        if now.tzinfo is None:
            raise IPTVError('iptv_invalid_time')
        now = now.astimezone(UTC)
        with self._lock:
            channel = self._find(channel_id)
            exact = [identifier for identifier in self.epg_channels if _id_key(identifier) == _id_key(channel['tvg_id']) and channel['tvg_id']]
            matched_by = 'identifier' if len(exact) == 1 else None
            matches = exact if len(exact) == 1 else []
            if not matches:
                # Preserve the country identity when supplied; Antena1.pe must
                # never inherit Romania's Antena1 guide merely by display name.
                country = re.search(r'\.([a-z]{2})(?:@|$)', _key(channel['tvg_id']))
                names = {_name_key(channel['name']), _name_key(channel.get('tvg_name', ''))} - {''}
                matches = [identifier for identifier, aliases in self.epg_channels.items()
                           if (not country or re.search(r'\.' + country[1] + r'(?:@|$)', _key(identifier)))
                           and names & {_name_key(identifier), *(_name_key(a) for a in aliases)}]
                if len(matches) == 1:
                    matched_by = 'name'
                else:
                    matches = []
            entries = [p for p in self.programmes if p['channel'] in matches
                       and datetime.fromisoformat(p['end']) > now - timedelta(hours=6)]
            # Prefer each official programme over overlapping XMLTV entries; do
            # not create two simultaneous shows with conflicting titles/times.
            official = [p for p in entries if p['source'] in {OFFICIAL_PROTV, OFFICIAL_ANTENA}]
            entries = [p for p in entries if p in official or not any(
                datetime.fromisoformat(o['start']) < datetime.fromisoformat(p['end']) and
                datetime.fromisoformat(p['start']) < datetime.fromisoformat(o['end']) for o in official)]
            entries = sorted({(p['start'], p['end'], p['title']): p for p in entries}.values(), key=lambda p: p['start'])[:1000]
            current = next((p for p in entries if datetime.fromisoformat(p['start']) <= now < datetime.fromisoformat(p['end'])), None)
            upcoming = [p for p in entries if datetime.fromisoformat(p['start']) > now]
            updated = datetime.fromisoformat(self.guide_updated_at) if self.guide_updated_at else None
            errors = [value.get('error') for source, value in self.source_status.items()
                      if source in {*self.sources['xmltv'], OFFICIAL_PROTV, OFFICIAL_ANTENA} and value.get('error')]
            stale = (updated is None or now - updated > timedelta(hours=12)
                     or not entries or any(self.source_status.get(p['source'], {}).get('status') != 'ok' for p in entries))
            return copy.deepcopy({'channel_id': channel_id, 'matched_by': matched_by, 'programmes': entries,
                                  'current': current, 'upcoming': upcoming, 'updated_at': self.guide_updated_at,
                                  'stale': stale, 'errors': errors})
