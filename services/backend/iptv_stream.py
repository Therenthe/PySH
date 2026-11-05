"""Bounded, same-origin HLS resources; upstream URLs never become browser URLs.

Each instance owns one viewer. The recorder uses a separate instance per job,
so changing a watched channel cannot replace a recording's resources.
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
import re
import secrets
import threading
import time
from urllib.parse import urljoin, urlsplit

from anyio import CancelScope


MANIFEST_LIMIT = 2 * 1024 * 1024
RESOURCE_LIMIT = 32 * 1024 * 1024
RESOURCE_COUNT = 2048
_SID = re.compile(r'^[A-Za-z0-9_-]{32}$')
_RID = re.compile(r'^[A-Za-z0-9_-]{24}$')
_URI = re.compile(r'(?P<prefix>(?:^|,)\s*URI\s*=\s*)"(?P<url>[^"\r\n]*)"', re.I)
_ANY_URI = re.compile(r'(?:^|,)\s*URI\s*=', re.I)
_METHOD = re.compile(r'(?:^|,)\s*METHOD\s*=\s*([^,]+)', re.I)
_KEYFORMAT = re.compile(r'(?:^|,)\s*KEYFORMAT\s*=\s*"?([^",]+)', re.I)
_RANGE = re.compile(r'^bytes=(\d*)-(\d*)$')
_CONTENT_RANGE = re.compile(r'^bytes (\d{1,20})-(\d{1,20})/(\d{1,20})$')


class IPTVStreamError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ProxyResource:
    data: bytes
    status_code: int = 200
    media_type: str = 'application/octet-stream'
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class _Resource:
    url: str
    kind: str


class IPTVStream:
    def __init__(self, *, fetcher=None, path_prefix='/api/iptv/stream', clock=time.monotonic,
                 idle_timeout=7200, max_resources=RESOURCE_COUNT):
        if not re.fullmatch(r'/[A-Za-z0-9_/-]+', path_prefix) or '..' in path_prefix:
            raise ValueError('invalid_proxy_prefix')
        if not 16 <= max_resources <= RESOURCE_COUNT or not 30 <= idle_timeout <= 7200:
            raise ValueError('invalid_proxy_limits')
        self._fetcher = fetcher
        self._prefix = path_prefix.rstrip('/')
        self._clock = clock
        self._idle_timeout = idle_timeout
        self._max_resources = max_resources
        self._lock = threading.RLock()
        self._resources: OrderedDict[str, _Resource] = OrderedDict()
        self._urls: dict[tuple[str, str], str] = {}
        self._sid: str | None = None
        self._root: str | None = None
        self._channel_id: str | None = None
        self._touched = 0.0
        self._async_slots = asyncio.Semaphore(4)
        self._async_waiters = 0
        self._fetch_slots = threading.BoundedSemaphore(4)
        self._transport = None

    def start(self, channel_id: str, url: str) -> dict:
        from .iptv_catalog import public_url
        if not isinstance(channel_id, str) or not 1 <= len(channel_id) <= 256:
            raise IPTVStreamError('iptv_invalid_channel')
        try:
            url = public_url(url)
        except Exception as exc:
            raise IPTVStreamError('iptv_unsafe_url') from exc
        with self._lock:
            if self._transport is not None:
                self._transport.close()
                self._transport = None
            self._sid = secrets.token_urlsafe(24)
            self._channel_id = channel_id
            self._resources.clear()
            self._urls.clear()
            self._root = None
            self._touched = self._clock()
            resource_id = self._register(url, 'manifest')
            self._root = resource_id
            return {'session_id': self._sid, 'channel_id': channel_id,
                    'stream_url': self._path(self._sid, resource_id)}

    def close(self, session_id: str) -> bool:
        with self._lock:
            if not isinstance(session_id, str) or self._sid != session_id:
                return False
            if self._transport is not None:
                self._transport.close()
                self._transport = None
            self._sid = None
            self._channel_id = None
            self._root = None
            self._resources.clear()
            self._urls.clear()
            return True

    def active(self) -> bool:
        """Decoder ownership only; never expose the upstream URL in state."""
        with self._lock:
            if self._sid is None:
                return False
            if self._clock() - self._touched > self._idle_timeout:
                self.close(self._sid)
                return False
            return True

    def touch(self, session_id: str) -> None:
        """A visible paused player renews its exact owner without fetching media."""
        with self._lock:
            self._owner(session_id)
            self._touched = self._clock()
            if self._transport is not None:self._transport.touch()

    def close_current(self) -> None:
        with self._lock:
            if self._sid is not None:
                self.close(self._sid)

    def _owner(self, session_id: str):
        if (not isinstance(session_id, str) or not _SID.fullmatch(session_id)
                or session_id != self._sid or self._clock() - self._touched > self._idle_timeout):
            raise IPTVStreamError('iptv_session_expired')

    def _path(self, session_id, resource_id):
        return f'{self._prefix}/{session_id}/{resource_id}'

    def _register(self, url: str, kind: str) -> str:
        from .iptv_catalog import public_url
        try:
            # Every actual fetch additionally resolves and pins public DNS.
            if kind == 'transport':
                from .iptv_transport import SEGMENT
                if not SEGMENT.fullmatch(url):raise ValueError('invalid_local_segment')
            else:url = public_url(url)
        except Exception as exc:
            raise IPTVStreamError('iptv_unsafe_url') from exc
        if len(url) > 8192 or any(c in url for c in '{}'):
            raise IPTVStreamError('iptv_unsupported_manifest')
        key = (url, kind)
        if key in self._urls:
            rid = self._urls[key]
            self._resources.move_to_end(rid)
            return rid
        while len(self._resources) >= self._max_resources:
            # Keep the reloadable root and prefer evicting old live segments.
            old_id = next((rid for rid, item in self._resources.items()
                           if rid != self._root and item.kind != 'manifest'),
                          next(rid for rid in self._resources if rid != self._root))
            old = self._resources.pop(old_id)
            self._urls.pop((old.url, old.kind), None)
        rid = secrets.token_urlsafe(18)
        self._resources[rid] = _Resource(url, kind)
        self._urls[key] = rid
        return rid

    def _transport_manifest(self, session_id, transport):
        raw = transport.manifest()
        result = []
        with self._lock:
            self._owner(session_id)
            if self._transport is not transport:raise IPTVStreamError('iptv_session_expired')
            for line in raw.decode('utf8').splitlines():
                if line and not line.startswith('#'):
                    line = self._path(session_id, self._register(line, 'transport'))
                result.append(line)
        return ProxyResource(('\n'.join(result)+'\n').encode(), media_type='application/vnd.apple.mpegurl', headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

    def _make_transport(self, session_id, *args):
        from .iptv_transport import DirectTransport
        with self._lock:
            self._owner(session_id)
            if self._transport is not None:
                # A racing first manifest fetch must close its redundant socket.
                try:args[0].close()
                finally:
                    try:args[1].close()
                    finally:
                        if len(args)>4 and args[4] is not None:args[4].close()
                return self._transport
            self._transport = DirectTransport(*args, idle_timeout=self._idle_timeout)
            return self._transport

    def _rewrite(self, session_id: str, data: bytes, base_url: str) -> bytes:
        if len(data) > MANIFEST_LIMIT:
            raise IPTVStreamError('iptv_manifest_too_large')
        try:
            text = data.decode('utf-8-sig')
        except UnicodeError as exc:
            raise IPTVStreamError('iptv_invalid_manifest') from exc
        lines = text.splitlines()
        if not lines or lines[0].strip() != '#EXTM3U' or '\x00' in text or len(lines) > 50000:
            raise IPTVStreamError('iptv_invalid_manifest')
        if not any(line.startswith(('#EXT-X-STREAM-INF:', '#EXT-X-TARGETDURATION:', '#EXT-X-MEDIA:')) for line in lines):
            raise IPTVStreamError('iptv_unsupported_stream')
        next_manifest = False
        result = []
        with self._lock:
            self._owner(session_id)
            for raw in lines:
                line = raw.strip()
                if not line:
                    result.append('')
                    continue
                if not line.startswith('#'):
                    kind = 'manifest' if next_manifest else 'binary'
                    rid = self._register(urljoin(base_url, line), kind)
                    result.append(self._path(session_id, rid))
                    next_manifest = False
                    continue
                tag, separator, attributes = line.partition(':')
                if tag in {'#EXT-X-DEFINE', '#EXT-X-CONTENT-STEERING'}:
                    raise IPTVStreamError('iptv_unsupported_manifest')
                if tag in {'#EXT-X-KEY', '#EXT-X-SESSION-KEY'}:
                    method = _METHOD.search(attributes)
                    key_format = _KEYFORMAT.search(attributes)
                    if (not method or method.group(1) not in {'NONE', 'AES-128'}
                            or key_format and key_format.group(1) != 'identity'):
                        raise IPTVStreamError('iptv_drm_unsupported')
                if separator and _ANY_URI.search(attributes):
                    if len(_ANY_URI.findall(attributes)) != len(_URI.findall(attributes)):
                        raise IPTVStreamError('iptv_invalid_manifest')
                    if tag not in {'#EXT-X-MEDIA', '#EXT-X-I-FRAME-STREAM-INF', '#EXT-X-RENDITION-REPORT',
                                   '#EXT-X-KEY', '#EXT-X-SESSION-KEY', '#EXT-X-MAP', '#EXT-X-PART',
                                   '#EXT-X-PRELOAD-HINT'}:
                        raise IPTVStreamError('iptv_unsupported_manifest')
                    kind = ('key' if tag in {'#EXT-X-KEY', '#EXT-X-SESSION-KEY'} else
                            'manifest' if tag in {'#EXT-X-MEDIA', '#EXT-X-I-FRAME-STREAM-INF', '#EXT-X-RENDITION-REPORT'}
                            else 'binary')
                    def replace(match):
                        rid = self._register(urljoin(base_url, match.group('url')), kind)
                        return match.group('prefix') + '"' + self._path(session_id, rid) + '"'
                    line = tag + ':' + _URI.sub(replace, attributes)
                result.append(line)
                if tag == '#EXT-X-STREAM-INF':
                    next_manifest = True
            if next_manifest:
                raise IPTVStreamError('iptv_invalid_manifest')
        rewritten = ('\n'.join(result) + '\n').encode('utf-8')
        if len(rewritten) > MANIFEST_LIMIT:
            raise IPTVStreamError('iptv_manifest_too_large')
        return rewritten

    def fetch(self, session_id: str, resource_id: str, range_header: str | None = None) -> ProxyResource:
        if not self._fetch_slots.acquire(timeout=15):
            raise IPTVStreamError('iptv_stream_busy')
        try:
            return self._fetch(session_id, resource_id, range_header)
        finally:
            self._fetch_slots.release()

    def _fetch(self, session_id: str, resource_id: str, range_header: str | None = None) -> ProxyResource:
        with self._lock:
            self._owner(session_id)
            if not isinstance(resource_id, str) or not _RID.fullmatch(resource_id) or resource_id not in self._resources:
                raise IPTVStreamError('iptv_resource_expired')
            self._touched = self._clock()
            resource = self._resources[resource_id]
            root_url = self._resources[self._root].url
            self._resources.move_to_end(resource_id)
        if range_header is not None and (not isinstance(range_header, str) or len(range_header) > 80):
            raise IPTVStreamError('iptv_invalid_range')
        if range_header is not None and (not _RANGE.fullmatch(range_header) or not any(_RANGE.fullmatch(range_header).groups())):
            raise IPTVStreamError('iptv_invalid_range')
        limit = MANIFEST_LIMIT if resource.kind == 'manifest' else 16 if resource.kind == 'key' else RESOURCE_LIMIT
        request_options = {'max_bytes': limit, 'timeout': 15}
        if range_header is not None and resource.kind != 'manifest':
            request_options['headers'] = {'Range': range_header}
        try:
            with self._lock:
                transport = self._transport
            if transport is not None and resource_id == self._root:
                return self._transport_manifest(session_id, transport)
            if resource.kind == 'transport':
                if transport is None:raise IPTVStreamError('iptv_session_expired')
                fetched = (transport.read(resource.url), root_url, 'video/mp2t', {})
            elif self._fetcher is None:
                from .iptv_catalog import fetch_public_resource
                if resource_id == self._root:
                    request_options['transport_factory'] = lambda *args:self._make_transport(session_id,*args)
                fetched = fetch_public_resource(resource.url, **request_options)
            else:
                fetched = self._fetcher(resource.url, **request_options)
            from .iptv_transport import DirectTransport
            if isinstance(fetched, DirectTransport):return self._transport_manifest(session_id,fetched)
            data, final_url, mime, upstream_headers = fetched
            if not isinstance(data, bytes) or len(data) > limit:
                raise IPTVStreamError('iptv_resource_too_large')
            from .iptv_catalog import public_url
            final_url = public_url(final_url)
        except IPTVStreamError:
            raise
        except Exception as exc:
            code = getattr(exc, 'code', '')
            if code in {'iptv_session_expired','iptv_stream_busy','iptv_resource_too_large','recording_disk_full','recording_ffmpeg_unavailable','iptv_unsupported_stream'}:
                raise IPTVStreamError(code) from exc
            raise IPTVStreamError('iptv_unsafe_url' if code in {'unsafe_url', 'iptv_unsafe_url'} else 'iptv_stream_unavailable') from exc
        with self._lock:
            self._owner(session_id)
            self._touched = self._clock()
        headers = {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}
        upstream_range = upstream_headers.get('content-range') if isinstance(upstream_headers, dict) else None
        if upstream_range:
            parsed_range = _CONTENT_RANGE.fullmatch(upstream_range)
            if not parsed_range:
                raise IPTVStreamError('iptv_invalid_range')
            first, last, total = map(int, parsed_range.groups())
            if first > last or last >= total or last - first + 1 != len(data):
                raise IPTVStreamError('iptv_invalid_range')
            if range_header is None or resource.kind == 'manifest':
                if first != 0 or last != total - 1:
                    raise IPTVStreamError('iptv_invalid_range')
            else:
                left, right = _RANGE.fullmatch(range_header).groups()
                expected_first = int(left) if left else max(0, total - int(right))
                expected_last = min(int(right), total - 1) if left and right else total - 1
                if (first, last) != (expected_first, expected_last):
                    raise IPTVStreamError('iptv_invalid_range')
        if resource.kind == 'manifest' or resource.kind != 'key' and data.lstrip(b'\xef\xbb\xbf \r\n').startswith(b'#EXTM3U'):
            return ProxyResource(self._rewrite(session_id, data, final_url), media_type='application/vnd.apple.mpegurl', headers=headers)
        if resource.kind == 'key' and len(data) != 16:
            raise IPTVStreamError('iptv_invalid_key')
        if not data or str(mime).split(';', 1)[0].strip().lower() in {'text/html', 'application/json', 'application/xhtml+xml'}:
            raise IPTVStreamError('iptv_stream_unavailable')
        if data.lstrip()[:32].lower().startswith((b'<!doctype', b'<html', b'<?xml', b'<mpd', b'{"')):
            raise IPTVStreamError('iptv_stream_unavailable')
        headers['Accept-Ranges'] = 'bytes'
        if range_header is None:
            return ProxyResource(data, media_type='application/octet-stream', headers=headers)
        if upstream_range:
            headers['Content-Range'] = upstream_range
            return ProxyResource(data, 206, headers=headers)
        match = _RANGE.fullmatch(range_header)
        if not match or not any(match.groups()):
            raise IPTVStreamError('iptv_invalid_range')
        left, right = match.groups()
        size = len(data)
        if left:
            start = int(left)
            end = min(int(right), size - 1) if right else size - 1
        else:
            count = int(right)
            if count <= 0:
                return ProxyResource(b'', 416, headers={**headers, 'Content-Range': f'bytes */{size}'})
            start, end = max(0, size - count), size - 1
        if start >= size or end < start:
            return ProxyResource(b'', 416, headers={**headers, 'Content-Range': f'bytes */{size}'})
        headers['Content-Range'] = f'bytes {start}-{end}/{size}'
        return ProxyResource(data[start:end + 1], 206, headers=headers)

    async def afetch(self, session_id: str, resource_id: str, range_header: str | None = None) -> ProxyResource:
        # A cancelled ASGI request must keep its worker slot until the bounded
        # network fetch finishes, rather than opening unbounded detached workers.
        if self._async_waiters >= 16:
            raise IPTVStreamError('iptv_stream_busy')
        self._async_waiters += 1
        try:
            async with self._async_slots:
                task = asyncio.create_task(asyncio.to_thread(self.fetch, session_id, resource_id, range_header))
                try:
                    return await asyncio.shield(task)
                except asyncio.CancelledError:
                    with CancelScope(shield=True):
                        while not task.done():
                            try:
                                await asyncio.shield(task)
                            except asyncio.CancelledError:
                                continue
                            except Exception:
                                break
                        if task.done() and not task.cancelled():
                            task.exception()
                    raise
        finally:
            self._async_waiters -= 1
