"""HLS proxy boundaries with synthetic bytes; no public streams or device state."""
import asyncio
import re
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
import anyio

from services.backend.iptv_stream import IPTVStream, IPTVStreamError, MANIFEST_LIMIT, RESOURCE_LIMIT


ROOT = 'https://streams.example/channel/master.m3u8'
MASTER = b'#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000\nquality/live.m3u8\n'
LIVE = b'#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nsegment.ts\n'


class Fetch:
    def __init__(self, resources=None):
        self.resources = {ROOT: (MASTER, ROOT, 'application/vnd.apple.mpegurl', {})}
        self.resources.update(resources or {})
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append((url, kwargs))
        value = self.resources[url]
        if isinstance(value, Exception):
            raise value
        return value


def parts(path):
    return path.rsplit('/', 2)[-2:]


def fetch_path(proxy, path, range_header=None):
    return proxy.fetch(*parts(path), range_header)


def uri_lines(raw):
    return [line for line in raw.decode().splitlines() if line and not line.startswith('#')]


def test_master_child_segments_use_final_redirect_base_and_opaque_routes():
    fetcher = Fetch({ROOT: (MASTER, 'https://cdn.example/redirected/master.m3u8', 'text/plain', {}),
                     'https://cdn.example/redirected/quality/live.m3u8': (LIVE, 'https://cdn2.example/live/index.m3u8', 'text/plain', {}),
                     'https://cdn2.example/live/segment.ts': (b'G' * 188, 'https://cdn2.example/live/segment.ts', 'video/mp2t', {})})
    proxy = IPTVStream(fetcher=fetcher)
    start = proxy.start('channel-one', ROOT)
    assert start['channel_id'] == 'channel-one'
    master = fetch_path(proxy, start['stream_url'])
    assert master.media_type == 'application/vnd.apple.mpegurl'
    child = uri_lines(master.data)[0]
    assert child.startswith('/api/iptv/stream/' + start['session_id'] + '/')
    assert b'https://' not in master.data
    live = fetch_path(proxy, child)
    segment = uri_lines(live.data)[0]
    assert fetch_path(proxy, segment).data == b'G' * 188
    assert [item[0] for item in fetcher.calls] == [ROOT, 'https://cdn.example/redirected/quality/live.m3u8', 'https://cdn2.example/live/segment.ts']
    assert fetcher.calls[0][1]['max_bytes'] == MANIFEST_LIMIT
    assert fetcher.calls[-1][1]['max_bytes'] == RESOURCE_LIMIT


def test_key_map_audio_parts_and_renditions_are_rewritten():
    text = b'''#EXTM3U
#EXT-X-TARGETDURATION:6
#EXT-X-KEY:METHOD=AES-128,URI="keys/current",IV=0x00000000000000000000000000000001
#EXT-X-MAP:URI="init.mp4",BYTERANGE="100@0"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="a",URI="audio.m3u8"
#EXT-X-RENDITION-REPORT:URI="other.m3u8",LAST-MSN=7
#EXT-X-PART:DURATION=0.2,URI="part.mp4"
#EXT-X-PRELOAD-HINT:TYPE=PART,URI="next.mp4"
#EXTINF:6,
segment.ts
'''
    fetcher = Fetch({ROOT: (text, ROOT, 'text/plain', {}),
                     'https://streams.example/channel/keys/current': (b'0123456789abcdef', 'https://streams.example/channel/keys/current', 'application/octet-stream', {})})
    proxy = IPTVStream(fetcher=fetcher)
    start = proxy.start('one', ROOT)
    response = fetch_path(proxy, start['stream_url'])
    assert 'URI="keys/current"' not in response.data.decode()
    uris = re.findall(r'URI="([^"]+)"', response.data.decode())
    assert len(uris) == 6
    assert all(uri.startswith('/api/iptv/stream/') for uri in uris)
    assert fetch_path(proxy, uris[0]).data == b'0123456789abcdef'
    assert fetcher.calls[-1][1]['max_bytes'] == 16


@pytest.mark.parametrize('key', [
    '#EXT-X-KEY:METHOD=SAMPLE-AES,URI="key"',
    '#EXT-X-KEY:METHOD=AES-128,KEYFORMAT="com.widevine",URI="key"',
    '#EXT-X-KEY:METHOD=BAD,URI="key"',
    '#EXT-X-KEY:URI="key"',
])
def test_unsupported_drm_is_explicit(key):
    fetcher = Fetch({ROOT: ((f'#EXTM3U\n#EXT-X-TARGETDURATION:6\n{key}\n#EXTINF:6,\nsegment.ts\n').encode(), ROOT, 'text/plain', {})})
    proxy = IPTVStream(fetcher=fetcher)
    start = proxy.start('one', ROOT)
    with pytest.raises(IPTVStreamError, match='iptv_drm_unsupported'):
        fetch_path(proxy, start['stream_url'])


@pytest.mark.parametrize('line,code', [
    ('file:///etc/passwd', 'iptv_unsafe_url'),
    ('data:text/plain,anything', 'iptv_unsafe_url'),
    ('ftp://example.org/video.ts', 'iptv_unsafe_url'),
    ('#EXT-X-KEY:METHOD=AES-128,URI=unquoted.key', 'iptv_invalid_manifest'),
    ('#EXT-X-SESSION-DATA:DATA-ID="x",URI="https://elsewhere.example/data"', 'iptv_unsupported_manifest'),
    ('#EXT-X-CONTENT-STEERING:SERVER-URI="https://elsewhere.example/path"', 'iptv_unsupported_manifest'),
    ('#EXT-X-DEFINE:NAME="host",VALUE="example.org"', 'iptv_unsupported_manifest'),
    ('https://{$host}/video.ts', 'iptv_unsupported_manifest'),
])
def test_unsafe_or_unrewritable_manifest_input_is_rejected(line, code):
    raw = f'#EXTM3U\n#EXT-X-TARGETDURATION:6\n{line}\n'.encode()
    proxy = IPTVStream(fetcher=Fetch({ROOT: (raw, ROOT, 'text/plain', {})}))
    start = proxy.start('one', ROOT)
    with pytest.raises(IPTVStreamError, match=code):
        fetch_path(proxy, start['stream_url'])


@pytest.mark.parametrize('raw', [b'<html>failure</html>', b'#EXTM3U\n#EXTINF:-1,TV\nhttps://example.org/file\n',
                                 b'#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=2\n',
                                 b'#EXTM3U\n#EXT-X-TARGETDURATION:6\n\x00', b'\xff\xff', b'x' * (MANIFEST_LIMIT + 1)],
                         ids=['html', 'iptv-list-not-hls', 'missing-variant', 'nul', 'invalid-utf8', 'oversized'])
def test_invalid_non_hls_and_oversized_manifests_fail(raw):
    proxy = IPTVStream(fetcher=Fetch({ROOT: (raw, ROOT, 'text/plain', {})}))
    start = proxy.start('one', ROOT)
    with pytest.raises(IPTVStreamError):
        fetch_path(proxy, start['stream_url'])


def segment_proxy(data=b'0123456789', mime='video/mp2t'):
    fetcher = Fetch({ROOT: (LIVE, ROOT, 'text/plain', {}),
                     'https://streams.example/channel/segment.ts': (data, 'https://streams.example/channel/segment.ts', mime, {})})
    proxy = IPTVStream(fetcher=fetcher)
    start = proxy.start('one', ROOT)
    path = uri_lines(fetch_path(proxy, start['stream_url']).data)[0]
    return proxy, path, fetcher


@pytest.mark.parametrize('header,expected,status,content_range', [
    (None, b'0123456789', 200, None),
    ('bytes=2-4', b'234', 206, 'bytes 2-4/10'),
    ('bytes=7-', b'789', 206, 'bytes 7-9/10'),
    ('bytes=-3', b'789', 206, 'bytes 7-9/10'),
    ('bytes=0-99', b'0123456789', 206, 'bytes 0-9/10'),
    ('bytes=-99', b'0123456789', 206, 'bytes 0-9/10'),
    ('bytes=30-40', b'', 416, 'bytes */10'),
    ('bytes=7-2', b'', 416, 'bytes */10'),
    ('bytes=-0', b'', 416, 'bytes */10'),
])
def test_single_byte_ranges(header, expected, status, content_range):
    proxy, path, _ = segment_proxy()
    result = fetch_path(proxy, path, header)
    assert result.data == expected
    assert result.status_code == status
    assert result.headers.get('Content-Range') == content_range
    assert result.headers['Cache-Control'] == 'no-store'


def test_large_hls_byte_range_file_downloads_only_the_requested_bounded_range():
    proxy, path, fetcher = segment_proxy()
    start, end, total = RESOURCE_LIMIT + 5, RESOURCE_LIMIT + 14, RESOURCE_LIMIT * 4
    segment = 'https://streams.example/channel/segment.ts'
    fetcher.resources[segment] = (b'0123456789', segment, 'video/mp4', {'content-range': f'bytes {start}-{end}/{total}'})
    response = fetch_path(proxy, path, f'bytes={start}-{end}')
    assert response.data == b'0123456789'
    assert response.status_code == 206
    assert response.headers['Content-Range'] == f'bytes {start}-{end}/{total}'
    assert fetcher.calls[-1][1] == {'max_bytes': RESOURCE_LIMIT, 'timeout': 15,
                                  'headers': {'Range': f'bytes={start}-{end}'}}


@pytest.mark.parametrize('requested,upstream', [
    ('bytes=2-4', 'bytes 1-3/10'),
    ('bytes=2-4', 'bytes 2-9/10'),
    ('bytes=2-4', 'bytes 2-3/10'),
    ('bytes=2-4', 'bytes 2-4/*'),
    ('bytes=2-4', 'bytes 2-4/4'),
    ('bytes=-3', 'bytes 6-8/10'),
    (None, 'bytes 2-4/10'),
])
def test_inconsistent_upstream_ranges_are_not_mislabeled(requested, upstream):
    proxy, path, fetcher = segment_proxy()
    segment = 'https://streams.example/channel/segment.ts'
    fetcher.resources[segment] = (b'234', segment, 'video/mp4', {'content-range': upstream})
    with pytest.raises(IPTVStreamError, match='iptv_invalid_range'):
        fetch_path(proxy, path, requested)


@pytest.mark.parametrize('header', ['bytes=-', 'bytes=0-1,4-5', 'items=1-3', 'bytes=abc', 'x' * 81])
def test_invalid_ranges_do_not_fetch_remote_bytes(header):
    proxy, path, fetcher = segment_proxy()
    before = len(fetcher.calls)
    with pytest.raises(IPTVStreamError, match='iptv_invalid_range'):
        fetch_path(proxy, path, header)
    assert len(fetcher.calls) == before


@pytest.mark.parametrize('data,mime', [(b'<!DOCTYPE html>bad', 'video/mp2t'), (b'<html>bad', 'video/mp2t'),
                                      (b'{"error":true}', 'video/mp2t'), (b'<?xml version="1"?><MPD/>', 'application/octet-stream'),
                                      (b'<MPD/>', 'application/octet-stream'), (b'any bytes', 'text/html'),
                                      (b'', 'video/mp2t'), (b'x' * (RESOURCE_LIMIT + 1), 'video/mp2t')],
                         ids=['doctype', 'html-bytes', 'json', 'xml', 'dash', 'html-mime', 'empty', 'oversized'])
def test_binary_errors_are_not_served_as_playable_media(data, mime):
    proxy, path, _ = segment_proxy(data, mime)
    with pytest.raises(IPTVStreamError):
        fetch_path(proxy, path)


def test_disguised_nested_playlist_is_still_rewritten():
    proxy, path, _ = segment_proxy(LIVE, 'application/octet-stream')
    response = fetch_path(proxy, path)
    assert response.media_type == 'application/vnd.apple.mpegurl'
    assert uri_lines(response.data)[0].startswith('/api/iptv/stream/')


def test_new_owner_invalidates_old_session_but_stale_close_does_not_close_new():
    proxy = IPTVStream(fetcher=Fetch())
    old = proxy.start('old', ROOT)
    new = proxy.start('new', ROOT)
    assert not proxy.close(old['session_id'])
    with pytest.raises(IPTVStreamError, match='iptv_session_expired'):
        fetch_path(proxy, old['stream_url'])
    assert fetch_path(proxy, new['stream_url']).status_code == 200
    assert proxy.close(new['session_id'])
    with pytest.raises(IPTVStreamError, match='iptv_session_expired'):
        fetch_path(proxy, new['stream_url'])


def test_idle_expiry_and_invalid_resource_ids():
    now = [100.0]
    proxy = IPTVStream(fetcher=Fetch(), clock=lambda: now[0], idle_timeout=30)
    start = proxy.start('one', ROOT)
    assert proxy.active()
    with pytest.raises(IPTVStreamError, match='iptv_resource_expired'):
        proxy.fetch(start['session_id'], '../url')
    now[0] = 131
    with pytest.raises(IPTVStreamError, match='iptv_session_expired'):
        fetch_path(proxy, start['stream_url'])
    assert not proxy.active()
    assert not proxy._resources


def test_close_current_releases_only_this_viewer_instance():
    first, second = IPTVStream(fetcher=Fetch()), IPTVStream(fetcher=Fetch())
    first.start('one', ROOT)
    second.start('two', ROOT)
    first.close_current()
    assert not first.active()
    assert second.active()
    first.close_current()


def test_lru_is_bounded_but_live_root_remains_reloadable():
    raw = '#EXTM3U\n#EXT-X-TARGETDURATION:6\n' + ''.join(f'#EXTINF:6,\nsegment-{i}.ts\n' for i in range(100))
    proxy = IPTVStream(fetcher=Fetch({ROOT: (raw.encode(), ROOT, 'text/plain', {})}), max_resources=16)
    start = proxy.start('one', ROOT)
    for _ in range(3):
        assert fetch_path(proxy, start['stream_url']).status_code == 200
        assert len(proxy._resources) == 16
        assert len(proxy._urls) == 16


def test_close_during_fetch_does_not_deliver_stale_bytes():
    entered, release = threading.Event(), threading.Event()
    def blocked(url, **kwargs):
        entered.set()
        assert release.wait(3)
        return MASTER, ROOT, 'text/plain', {}
    proxy = IPTVStream(fetcher=blocked)
    start = proxy.start('one', ROOT)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fetch_path, proxy, start['stream_url'])
        assert entered.wait(3)
        proxy.close(start['session_id'])
        release.set()
        with pytest.raises(IPTVStreamError, match='iptv_session_expired'):
            future.result()


def test_replacing_owner_during_fetch_cannot_deliver_previous_channel():
    entered, release = threading.Event(), threading.Event()
    def blocked(url, **kwargs):
        entered.set()
        assert release.wait(3)
        return MASTER, ROOT, 'text/plain', {}
    proxy = IPTVStream(fetcher=blocked)
    old = proxy.start('old', ROOT)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fetch_path, proxy, old['stream_url'])
        assert entered.wait(3)
        new = proxy.start('new', ROOT)
        release.set()
        with pytest.raises(IPTVStreamError, match='iptv_session_expired'):
            future.result()
    assert not proxy.close(old['session_id'])
    assert fetch_path(proxy, new['stream_url']).status_code == 200


def test_cancelled_async_fetch_drains_worker_and_releases_its_slot():
    async def scenario():
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        def blocked(url, **kwargs):
            entered.set()
            assert release.wait(3)
            finished.set()
            return MASTER, ROOT, 'text/plain', {}
        proxy = IPTVStream(fetcher=blocked)
        start = proxy.start('one', ROOT)
        task = asyncio.create_task(proxy.afetch(*parts(start['stream_url'])))
        assert await asyncio.to_thread(entered.wait, 3)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert proxy._async_waiters == 1
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert finished.is_set()
        assert proxy._async_waiters == 0
        assert proxy._async_slots._value == 4
    asyncio.run(scenario())


def test_async_queue_cap_refuses_without_starting_another_worker():
    async def scenario():
        proxy = IPTVStream(fetcher=Fetch())
        start = proxy.start('one', ROOT)
        proxy._async_waiters = 16
        with pytest.raises(IPTVStreamError, match='iptv_stream_busy'):
            await proxy.afetch(*parts(start['stream_url']))
        assert proxy._async_waiters == 16
    asyncio.run(scenario())


def test_anyio_scope_cancel_keeps_worker_owned_until_it_finishes():
    async def scenario():
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        def blocked(url, **kwargs):
            entered.set()
            assert release.wait(3)
            finished.set()
            return MASTER, ROOT, 'text/plain', {}
        proxy = IPTVStream(fetcher=blocked)
        start = proxy.start('one', ROOT)
        with anyio.CancelScope() as scope:
            async with anyio.create_task_group() as group:
                group.start_soon(proxy.afetch, *parts(start['stream_url']))
                assert await asyncio.to_thread(entered.wait, 3)
                scope.cancel()
                release.set()
        assert finished.is_set()
        assert proxy._async_waiters == 0
        assert proxy._async_slots._value == 4
    anyio.run(scenario, backend='asyncio')


def test_default_fetch_revalidates_network_via_shared_pinned_fetcher(monkeypatch):
    from services.backend import iptv_catalog
    called = []
    def guarded(url, **kwargs):
        called.append(url)
        raise iptv_catalog.IPTVError('iptv_unsafe_url')
    monkeypatch.setattr(iptv_catalog, 'fetch_public_resource', guarded)
    proxy = IPTVStream()
    start = proxy.start('one', ROOT)
    with pytest.raises(IPTVStreamError, match='iptv_unsafe_url'):
        fetch_path(proxy, start['stream_url'])
    assert called == [ROOT]
