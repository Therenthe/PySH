"""Private lifecycle units run on Windows; real procfs/HTTP tests require Linux."""
import asyncio
import gc
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
import starlette
import starlette.responses
from starlette.responses import FileResponse


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
def module():
    spec = importlib.util.spec_from_file_location('private_descriptor_response', Path(__file__).resolve().parents[1] / 'services/backend/descriptor_response.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


@pytest.fixture
def portable(module, monkeypatch):
    # Real dup/fstat/close on temporary files; only procfs availability is mocked.
    closed = []
    def close(fd):
        closed.append(fd)
        os.close(fd)
    monkeypatch.setattr(module, 'sys', SimpleNamespace(platform='linux'))
    monkeypatch.setattr(module, 'os', SimpleNamespace(dup=os.dup, fstat=os.fstat, close=close,
        path=SimpleNamespace(isdir=lambda value: value == '/proc/self/fd')))
    return module, closed


@pytest.fixture
def source(tmp_path):
    file = tmp_path / 'fixture.webm'
    file.write_bytes(b'0123456789abcdefghijklmnopqrstuvwxyz')
    fd = os.open(file, os.O_RDONLY | getattr(os, 'O_BINARY', 0))
    try:
        yield file, fd
    finally:
        os.close(fd)


def scope(method='GET', headers=(), extensions=None):
    return {'type':'http', 'method':method, 'path':'/owned-media', 'headers':list(headers),
            'asgi':{'spec_version':'2.4'}, 'extensions':extensions or {}}


async def waiting_receive():
    await asyncio.Event().wait()


async def collect(response, request=None):
    messages = []
    async def send(message):
        messages.append(message)
    await response(request or scope(), waiting_receive, send)
    return messages


def owned_fd(response):
    return int(Path(response.path).name)


def assert_closed(fd):
    with pytest.raises(OSError):
        os.fstat(fd)


def test_exact_library_version():
    assert starlette.__version__ == '1.7.0'


def test_windows_or_missing_procfs_is_an_explicit_unavailable_result(module, monkeypatch):
    monkeypatch.setattr(module, 'sys', SimpleNamespace(platform='win32'))
    with pytest.raises(module.DescriptorResponseUnavailable, match='descriptor_response_unavailable'):
        module.DescriptorFileResponse(123, media_type='video/webm')
    monkeypatch.setattr(module, 'sys', SimpleNamespace(platform='linux'))
    monkeypatch.setattr(module, 'os', SimpleNamespace(path=SimpleNamespace(isdir=lambda _: False)))
    with pytest.raises(module.DescriptorResponseUnavailable):
        module.DescriptorFileResponse(123, media_type='video/webm')


def test_invalid_fd_and_nonregular_fstat_are_rejected_without_leak(portable, source):
    module, closed = portable
    for invalid in [True, -1, '7']:
        with pytest.raises(ValueError):
            module.DescriptorFileResponse(invalid, media_type='video/webm')
    invalid = os.dup(source[1]); os.close(invalid)
    with pytest.raises(OSError):
        module.DescriptorFileResponse(invalid, media_type='video/webm')
    module.os.fstat = lambda _: source[0].parent.stat()
    with pytest.raises(ValueError, match='not_regular'):
        module.DescriptorFileResponse(source[1], media_type='video/webm')
    assert len(closed) == 1
    assert_closed(closed[0])
    os.fstat(source[1])


def test_constructor_failure_closes_owned_dup_but_not_input(portable, source, monkeypatch):
    module, closed = portable
    def fail(*_args, **_kwargs):
        raise RuntimeError('fixture_constructor_failure')
    monkeypatch.setattr(FileResponse, '__init__', fail)
    with pytest.raises(RuntimeError, match='fixture_constructor_failure'):
        module.DescriptorFileResponse(source[1], media_type='video/webm')
    assert len(closed) == 1
    assert_closed(closed[0]); os.fstat(source[1])


def test_unused_response_finalizer_reaps_its_descriptor(portable, source):
    module, closed = portable
    response = module.DescriptorFileResponse(source[1], media_type='video/webm')
    fd = owned_fd(response)
    del response; gc.collect()
    assert closed == [fd]
    assert_closed(fd); os.fstat(source[1])


@pytest.mark.anyio
async def test_delegates_http_and_strips_only_pathsend_without_mutating_scope(portable, source, monkeypatch):
    module, closed = portable
    seen = []
    async def respond(self, request, receive, send):
        seen.append(request)
        os.fstat(owned_fd(self))
        await send({'type':'http.response.start', 'status':200, 'headers':self.raw_headers})
        await send({'type':'http.response.body', 'body':b'fixture', 'more_body':False})
    monkeypatch.setattr(FileResponse, '__call__', respond)
    response = module.DescriptorFileResponse(source[1], media_type='video/webm')
    fd = owned_fd(response)
    request = scope(extensions={'http.response.pathsend':{}, 'other.extension':{'kept':True}})
    assert (await collect(response, request))[-1]['body'] == b'fixture'
    assert seen[0]['extensions'] == {'other.extension':{'kept':True}}
    assert 'http.response.pathsend' in request['extensions']
    assert closed == [fd]; assert_closed(fd); os.fstat(source[1])
    with pytest.raises(RuntimeError, match='already_used'):
        await collect(response)
    assert closed == [fd]


@pytest.mark.anyio
async def test_send_failure_closes_owned_descriptor(portable, source, monkeypatch):
    module, closed = portable
    async def respond(self, request, receive, send):
        await send({'type':'http.response.body','body':b'x'})
    async def broken_send(_message):
        raise OSError('fixture_disconnected_send')
    monkeypatch.setattr(FileResponse, '__call__', respond)
    response = module.DescriptorFileResponse(source[1], media_type='video/webm'); fd = owned_fd(response)
    with pytest.raises(OSError, match='fixture_disconnected_send'):
        await response(scope(), waiting_receive, broken_send)
    assert closed == [fd]; assert_closed(fd)


@pytest.mark.anyio
async def test_http_disconnect_cancels_blocked_response_and_closes_fd(portable, source, monkeypatch):
    module, closed = portable
    started, disconnected = asyncio.Event(), asyncio.Event()
    async def respond(self, request, receive, send):
        await send({'type':'http.response.body','body':b'x'})
    async def receive():
        await disconnected.wait(); return {'type':'http.disconnect'}
    async def send(_message):
        started.set(); await asyncio.Event().wait()
    monkeypatch.setattr(FileResponse, '__call__', respond)
    response = module.DescriptorFileResponse(source[1], media_type='video/webm'); fd = owned_fd(response)
    task = asyncio.create_task(response(scope(), receive, send))
    await started.wait(); disconnected.set(); await asyncio.wait_for(task, 1)
    assert closed == [fd]; assert_closed(fd)


@pytest.mark.anyio
async def test_caller_cancellation_and_concurrent_reuse_do_not_double_close(portable, source, monkeypatch):
    module, closed = portable
    started = asyncio.Event()
    async def respond(self, request, receive, send):
        await send({'type':'http.response.body','body':b'x'})
    async def send(_message):
        started.set(); await asyncio.Event().wait()
    monkeypatch.setattr(FileResponse, '__call__', respond)
    response = module.DescriptorFileResponse(source[1], media_type='video/webm'); fd = owned_fd(response)
    task = asyncio.create_task(response(scope(), waiting_receive, send)); await started.wait()
    with pytest.raises(RuntimeError, match='already_used'):
        await collect(response)
    os.fstat(fd)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert closed == [fd]; assert_closed(fd); os.fstat(source[1])


linux_proc = pytest.mark.skipif(not sys.platform.startswith('linux') or not Path('/proc/self/fd').is_dir(), reason='real Linux procfs integration required')


@linux_proc
@pytest.mark.anyio
@pytest.mark.parametrize('method,headers',[
    ('GET',[]),('HEAD',[]),('GET',[(b'range',b'bytes=2-5')]),
    ('GET',[(b'range',b'bytes=-4')]),('GET',[(b'range',b'bytes=0-1,8-10')]),
    ('HEAD',[(b'range',b'bytes=0-1,8-10')]),('GET',[(b'range',b'bytes=1000-')]),
    ('GET',[(b'range',b'not-a-range')]),('GET',[(b'range',b'bytes=2-5'),(b'if-range',b'wrong-etag')]),
])
async def test_real_http_matches_unmodified_file_response(module, source, monkeypatch, method, headers):
    monkeypatch.setattr(starlette.responses, 'token_hex', lambda _: 'fixtureboundary')
    response = module.DescriptorFileResponse(source[1], media_type='video/webm'); fd = owned_fd(response)
    actual = await collect(response, scope(method, headers, {'http.response.pathsend':{}}))
    expected = await collect(FileResponse(source[0], media_type='video/webm'), scope(method, headers))
    assert actual == expected
    assert all(message['type'] != 'http.response.pathsend' for message in actual)
    assert_closed(fd); os.fstat(source[1])


@linux_proc
@pytest.mark.anyio
async def test_rename_and_same_name_replacement_cannot_change_opened_inode(module, source):
    original, fd = source
    response = module.DescriptorFileResponse(fd, media_type='video/webm'); owned = owned_fd(response)
    identity = os.fstat(owned)
    original.rename(original.with_name('renamed.webm')); original.write_bytes(b'REPLACEMENT')
    assert os.fstat(owned).st_ino == identity.st_ino
    messages = await collect(response)
    assert b''.join(message.get('body',b'') for message in messages) == b'0123456789abcdefghijklmnopqrstuvwxyz'
    assert_closed(owned)


@linux_proc
def test_real_directory_descriptor_is_rejected(module, tmp_path):
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(ValueError, match='not_regular'):
            module.DescriptorFileResponse(fd, media_type='video/webm')
        os.fstat(fd)
    finally:
        os.close(fd)


@linux_proc
@pytest.mark.anyio
async def test_real_disconnect_reaps_both_response_dup_and_library_file_handle(module, source):
    identity = os.fstat(source[1])
    def same_inode_fds():
        found = []
        for name in os.listdir('/proc/self/fd'):
            try:
                info = os.fstat(int(name))
                if (info.st_dev,info.st_ino)==(identity.st_dev,identity.st_ino): found.append(int(name))
            except OSError:
                pass
        return found
    initial = same_inode_fds(); started, disconnected = asyncio.Event(), asyncio.Event()
    response = module.DescriptorFileResponse(source[1], media_type='video/webm')
    async def send(message):
        if message['type']=='http.response.body': started.set(); await asyncio.Event().wait()
    async def receive():
        await disconnected.wait(); return {'type':'http.disconnect'}
    task=asyncio.create_task(response(scope(),receive,send)); await started.wait(); disconnected.set(); await asyncio.wait_for(task,1)
    assert same_inode_fds() == initial
