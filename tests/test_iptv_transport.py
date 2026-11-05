"""Direct TS trust boundaries and resource ownership; no network or FFmpeg."""
import io
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from services.backend import iptv_catalog as catalog
from services.backend import iptv_transport as mod
from services.backend.iptv_stream import IPTVStream, IPTVStreamError

URL = 'https://stream.example/live'
TS = (b'\x47\x00\x10\x10' + bytes(184)) * 4


@pytest.mark.parametrize('raw', [TS, TS[:564]])
def test_clear_aligned_transport_is_detected(raw):
    assert mod.is_transport(raw)


@pytest.mark.parametrize('raw', [b'<html>' * 100, TS[:563], b'x' + TS,
    TS[:188] + b'X' + TS[189:], b'\x47\x80' + TS[2:],
    TS[:3] + b'\xd0' + TS[4:], TS[:3] + b'\x00' + TS[4:]])
def test_html_misaligned_corrupt_and_scrambled_transport_is_rejected(raw):
    assert not mod.is_transport(raw)


class Response:
    def __init__(self, content=TS, status=200, headers=()):
        self.content, self.status, self.headers = content, status, headers
        self.read_sizes = []

    def getheaders(self):
        return self.headers

    def read1(self, amount):
        self.read_sizes.append(amount)
        block, self.content = self.content[:amount], self.content[amount:]
        return block


def network(monkeypatch, responses, addresses=None):
    connections, resolutions, pinned = [], [], []
    def resolve(host, port, **kwargs):
        resolutions.append(host)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '',
                 ((addresses or {}).get(host, '1.1.1.1'), port))]
    class Connection:
        def __init__(self, host, port, timeout):
            self.host, self.port, self.timeout = host, port, timeout
            self.sock, self.closed = None, False
            self.response = responses[len(connections)]
            connections.append(self)
        def request(self, *args, **kwargs):
            self._create_connection((self.host, self.port), self.timeout)
        def getresponse(self):
            return self.response
        def close(self):
            self.closed = True
    monkeypatch.setattr(socket, 'getaddrinfo', resolve)
    monkeypatch.setattr(socket, 'create_connection', lambda address, *args: pinned.append(address))
    monkeypatch.setattr(catalog, 'HTTPSConnection', Connection)
    return connections, resolutions, pinned


def test_redirect_revalidates_dns_and_hands_off_only_final_pinned_connection(monkeypatch):
    responses = [Response(status=302, headers=[('Location', 'https://cdn.example/live')]), Response()]
    connections, resolutions, pinned = network(monkeypatch, responses)
    handoff = []
    owner = object()
    def factory(*args):
        handoff.append(args)
        return owner
    assert catalog.fetch_public_resource(URL, transport_factory=factory) is owner
    assert resolutions == ['stream.example', 'cdn.example']
    assert pinned == [('1.1.1.1', 443), ('1.1.1.1', 443)]
    assert connections[0].closed and not connections[1].closed
    assert handoff[0][:4] == (responses[1], connections[1], TS, 'https://cdn.example/live')


def test_redirect_to_private_dns_is_blocked_before_connection_or_factory(monkeypatch):
    connections, _, _ = network(monkeypatch,
        [Response(status=302, headers=[('Location', 'https://private.example/live')])],
        {'private.example': '192.168.100.127'})
    with pytest.raises(catalog.IPTVError, match='source_unavailable'):
        catalog.fetch_public_resource(URL, transport_factory=lambda *args: pytest.fail('private handoff'))
    assert len(connections) == 1 and connections[0].closed


def test_failed_factory_does_not_leak_pinned_connection(monkeypatch):
    connections, _, _ = network(monkeypatch, [Response()])
    def fail(*args):
        raise mod.TransportError('recording_ffmpeg_unavailable')
    with pytest.raises(mod.TransportError):
        catalog.fetch_public_resource(URL, transport_factory=fail)
    assert connections[0].closed


@pytest.mark.parametrize('length', [None, '999999', 'invalid'])
def test_non_transport_body_keeps_byte_limit_even_with_transport_factory(monkeypatch, length):
    response = Response(b'<html>' * 300, headers=[] if length is None else [('Content-Length', length)])
    connections, _, _ = network(monkeypatch, [response])
    with pytest.raises(catalog.IPTVError, match='source_too_large'):
        catalog.fetch_public_resource(URL, max_bytes=600,
            transport_factory=lambda *args: pytest.fail('HTML handed to FFmpeg'))
    assert connections[0].closed
    assert sum(response.read_sizes) <= 601


def test_ordinary_hls_stays_a_bounded_tuple_not_a_transport(monkeypatch):
    raw = b'#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\na.ts\n'
    connections, _, _ = network(monkeypatch, [Response(raw)])
    result = catalog.fetch_public_resource(URL, transport_factory=lambda *args: pytest.fail('HLS handed off'))
    assert result[0] == raw and connections[0].closed


@pytest.fixture
def remux(monkeypatch, tmp_path):
    instances = []
    children = []
    class Input(io.BytesIO):
        pass
    class Child:
        def __init__(self, command, **kwargs):
            self.command, self.options = command, kwargs
            self.stdin, self.exit, self.killed = Input(), threading.Event(), False
            children.append(self)
        def poll(self):
            return 0 if self.exit.is_set() else None
        def terminate(self):
            self.exit.set()
        def kill(self):
            self.killed = True
            self.exit.set()
        def wait(self, timeout):
            if not self.exit.wait(timeout):
                raise subprocess.TimeoutExpired('ffmpeg', timeout)
            return 0
    monkeypatch.setattr(mod, '_CAPACITY', threading.BoundedSemaphore(3))
    monkeypatch.setattr(mod.shutil, 'which', lambda _: 'fake-ffmpeg')
    monkeypatch.setattr(mod.shutil, 'disk_usage', lambda _: SimpleNamespace(free=2**40))
    monkeypatch.setattr(mod.tempfile, 'tempdir', str(tmp_path))
    monkeypatch.setattr(mod.subprocess, 'Popen', Child)
    def create(**kwargs):
        stopped = threading.Event()
        connection = SimpleNamespace(closed=False)
        def close():
            connection.closed = True
            stopped.set()
        connection.close = close
        sock = SimpleNamespace(shutdown=lambda _: stopped.set(), close=lambda: stopped.set())
        response = SimpleNamespace(read1=lambda _: (stopped.wait(2), b'')[1], close=lambda: stopped.set())
        transport = mod.DirectTransport(response, connection, TS, URL, sock, **kwargs)
        instances.append(transport)
        return transport
    yield create, children
    for transport in instances:
        transport.close()
        assert transport._done.wait(3), 'normalizer watchdog failed to reap resources'
        assert not transport.directory.exists()


def test_ffmpeg_only_receives_pinned_bytes_over_stdin_and_remuxes_without_encoding(remux):
    create, children = remux
    transport = create()
    command = children[0].command
    assert command[command.index('-i') + 1] == 'pipe:0'
    assert command[command.index('-protocol_whitelist') + 1] == 'pipe'
    assert command[command.index('-format_whitelist') + 1] == 'mpegts'
    assert command[command.index('-c') + 1] == 'copy'
    assert not any('://' in item for item in command)
    assert children[0].options['stdin'] == subprocess.PIPE
    assert children[0].options.get('shell', False) is False
    transport.close()
    assert transport._done.wait(3)
    assert transport.connection.closed and not transport.directory.exists()


@pytest.mark.parametrize('name', ['../secret', 'segment1.ts', 'segment000000000.ts.tmp', '/index.m3u8', 'other.m3u8'])
def test_private_output_reader_rejects_non_generated_paths(remux, name):
    transport = remux[0]()
    with pytest.raises(mod.TransportError, match='resource_expired'):
        transport.read(name)


def test_output_reader_bounds_manifest_and_segment_sizes(remux, monkeypatch):
    transport = remux[0]()
    (transport.directory / 'index.m3u8').write_bytes(b'x' * (64 * 1024 + 1))
    with pytest.raises(mod.TransportError, match='resource_too_large'):
        transport.read('index.m3u8')
    monkeypatch.setattr(mod, 'MAX_FILE', 8)
    (transport.directory / 'segment000000001.ts').write_bytes(b'x' * 9)
    with pytest.raises(mod.TransportError, match='resource_too_large'):
        transport.read('segment000000001.ts')


@pytest.mark.parametrize('kind', ['file', 'directory', 'count', 'disk', 'idle', 'absolute'])
def test_watchdog_enforces_resource_and_lifetime_limits_then_cleans(remux, monkeypatch, kind):
    transport = remux[0]()
    if kind == 'file':
        monkeypatch.setattr(mod, 'MAX_FILE', 8)
        (transport.directory / 'segment000000001.ts').write_bytes(bytes(9))
    elif kind == 'directory':
        monkeypatch.setattr(mod, 'MAX_DIRECTORY', 8)
        for i in range(2):
            (transport.directory / f'segment{i:09d}.ts').write_bytes(bytes(5))
    elif kind == 'count':
        for i in range(25):
            (transport.directory / f'segment{i:09d}.ts').touch()
    elif kind == 'disk':
        monkeypatch.setattr(mod.shutil, 'disk_usage', lambda _: SimpleNamespace(free=0))
    elif kind == 'idle':
        transport._touched -= transport.idle_timeout + 1
    else:
        transport._started -= 86401
    assert transport._done.wait(3)
    expected = ('iptv_session_expired' if kind in {'idle', 'absolute'} else
                'recording_disk_full' if kind == 'disk' else 'iptv_resource_too_large')
    assert transport.error == expected
    assert transport.connection.closed and not transport.directory.exists()


def test_initial_manifest_timeout_reaps_normalizer(remux):
    transport = remux[0]()
    with pytest.raises(mod.TransportError):
        transport.manifest(timeout=0)
    assert transport._done.wait(3), 'readiness timeout must stop the failed normalizer'


def test_capacity_is_bounded_and_close_returns_slot(remux):
    transports = [remux[0]() for _ in range(3)]
    with pytest.raises(mod.TransportError, match='stream_busy'):
        remux[0]()
    transports[0].close()
    assert transports[0]._done.wait(3)
    replacement = remux[0]()
    assert replacement.process.poll() is None


@pytest.mark.parametrize('failure,code', [('ffmpeg', 'recording_ffmpeg_unavailable'),
    ('disk', 'recording_disk_full'), ('launch', None)])
def test_failed_start_does_not_consume_capacity_or_leave_private_directory(remux, monkeypatch, tmp_path, failure, code):
    with monkeypatch.context() as patch:
        if failure == 'ffmpeg':
            patch.setattr(mod.shutil, 'which', lambda _: None)
        elif failure == 'disk':
            patch.setattr(mod.shutil, 'disk_usage', lambda _: SimpleNamespace(free=0))
        else:
            def launch(*args, **kwargs):
                raise OSError('cannot launch')
            patch.setattr(mod.subprocess, 'Popen', launch)
        with pytest.raises(mod.TransportError if code else OSError, match=code):
            remux[0]()
    assert not list(tmp_path.glob('pysh-ts-*'))
    transports = [remux[0]() for _ in range(3)]
    assert all(item.process.poll() is None for item in transports)


def test_local_manifest_and_segments_are_served_only_through_current_opaque_routes(monkeypatch):
    class Owner:
        def __init__(self, *args, **kwargs):
            self.closed = False
        def close(self):
            self.closed = True
        def manifest(self):
            return b'#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\nsegment000000001.ts\n'
        def read(self, name):
            assert name == 'segment000000001.ts'
            return TS
    monkeypatch.setattr(mod, 'DirectTransport', Owner)
    monkeypatch.setattr(catalog, 'fetch_public_resource',
        lambda url, **kwargs: kwargs['transport_factory'](None, None, TS, url))
    proxy = IPTVStream()
    start = proxy.start('one', URL)
    manifest = proxy.fetch(*start['stream_url'].rsplit('/', 2)[-2:])
    path = next(line for line in manifest.data.decode().splitlines() if not line.startswith('#'))
    assert path.startswith('/api/iptv/stream/' + start['session_id'] + '/')
    assert b'segment000000001.ts' not in manifest.data and b'https://' not in manifest.data
    assert proxy.fetch(*path.rsplit('/', 2)[-2:]).data == TS
    owner = proxy._transport
    proxy.close_current()
    assert owner.closed
    with pytest.raises(IPTVStreamError, match='session_expired'):
        proxy.fetch(*path.rsplit('/', 2)[-2:])


def test_channel_change_while_normalizer_waits_cannot_deliver_stale_manifest(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    owners = []
    class Owner:
        def __init__(self, *args, **kwargs):
            self.closed = False
            owners.append(self)
        def close(self):
            self.closed = True
        def manifest(self):
            entered.set()
            assert release.wait(3)
            return b'#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\nsegment000000001.ts\n'
    monkeypatch.setattr(mod, 'DirectTransport', Owner)
    monkeypatch.setattr(catalog, 'fetch_public_resource',
        lambda url, **kwargs: kwargs['transport_factory'](None, None, TS, url))
    proxy = IPTVStream()
    old = proxy.start('old', URL)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(proxy.fetch, *old['stream_url'].rsplit('/', 2)[-2:])
        assert entered.wait(3)
        proxy.start('new', URL)
        release.set()
        with pytest.raises(IPTVStreamError, match='session_expired'):
            future.result(timeout=3)
    assert owners[0].closed and proxy.active()


def test_concurrent_initial_fetches_share_one_child_and_close_redundant_connection(monkeypatch):
    made = []
    class Owner:
        def __init__(self, *args, **kwargs):
            made.append(self)
            self.closed = False
        def close(self):
            self.closed = True
    monkeypatch.setattr(mod, 'DirectTransport', Owner)
    proxy = IPTVStream()
    old = proxy.start('old', URL)
    connections = [SimpleNamespace(close=lambda: None) for _ in range(2)]
    closed, responses_closed, sockets_closed = [], [], []
    responses = [SimpleNamespace(close=lambda i=i: responses_closed.append(i)) for i in range(2)]
    sockets = [SimpleNamespace(close=lambda i=i: sockets_closed.append(i)) for i in range(2)]
    for i, conn in enumerate(connections):
        conn.close = lambda i=i: closed.append(i)
    def make(i):
        return proxy._make_transport(old['session_id'], responses[i], connections[i], TS, URL, sockets[i])
    with ThreadPoolExecutor(max_workers=2) as pool:
        owners = list(pool.map(make, range(2)))
    assert owners[0] is owners[1] and len(made) == 1 and len(closed) == 1
    assert responses_closed == closed == sockets_closed
    new = proxy.start('new', URL)
    assert made[0].closed
    assert not proxy.close(old['session_id'])
    with pytest.raises(IPTVStreamError, match='session_expired'):
        make(0)
    assert proxy.active() and new['session_id'] != old['session_id']
