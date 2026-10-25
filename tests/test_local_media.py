"""Production API composition with synthetic files and mocked native boundaries."""
import ast
import asyncio
import importlib
import json
import os
from pathlib import Path
import sys
import time
import threading
import weakref
import anyio
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from starlette.responses import Response

api = importlib.import_module('services.backend.app')
local = importlib.import_module('services.backend.local_media')
watch = importlib.import_module('services.backend.watch_history')

@pytest.fixture
def env(tmp_path, monkeypatch):
    folder = tmp_path / 'Videos'
    folder.mkdir()
    movie = folder / 'synthetic.mp4'
    movie.write_bytes(b'synthetic undecoded fixture')
    hub = api.Hub(tmp_path / 'data')
    hub.content._media_roots = lambda: [folder]
    if sys.platform == 'win32':
        # Windows Path.stat/fstat report inconsistent legacy ctime semantics.
        # This is already a mocked native-open harness, not Linux identity proof.
        original_identity = hub.content.media_identity
        def fixture_identity(path, info):
            normalized = SimpleNamespace(**{key: getattr(info, key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns')},
                                         st_ctime_ns=getattr(info, 'st_birthtime_ns', 0))
            return original_identity(path, normalized)
        monkeypatch.setattr(hub.content, 'media_identity', fixture_identity)
    hub.player = SimpleNamespace(status=AsyncMock(return_value={'state': 'idle'}))
    api.app.state.hub = hub
    monkeypatch.setattr(watch, '_readonly', lambda fd: True)
    def open_fixture(path, expected=None):
        canonical = hub.content.resolve_media(path)
        fd = os.open(canonical, os.O_RDONLY)
        identity = hub.content.media_identity(canonical, os.fstat(fd))
        if expected is not None and expected != identity:
            os.close(fd)
            raise api.ContentError('media_changed')
        return str(canonical), fd, identity
    monkeypatch.setattr(hub.local_media, 'open_approved', open_fixture)
    pinned = []
    def response(fd, *, media_type):
        pinned.append(os.fstat(fd).st_ino)
        return Response(b'mocked pinned descriptor body', media_type=media_type)
    monkeypatch.setattr(local, 'DescriptorFileResponse', response)
    extraction = AsyncMock(return_value={'state': 'ready', 'metadata': {'title': 'Fixture title', 'duration_s': 100, 'tracks': []}, 'poster_jpeg': None})
    monkeypatch.setattr(local, 'inspect_fd', extraction)
    identity = hub.content.media_identity(movie.resolve(), movie.stat())
    client = TestClient(api.app, base_url='http://127.0.0.1:8765')
    yield SimpleNamespace(hub=hub, client=client, movie=movie, folder=folder, identity=identity,
                          headers={'X-Hub-Token': hub.token}, extraction=extraction, pinned=pinned)
    hub.local_media.watch.shutdown()


def create(e, resume=False):
    return e.client.post('/api/media/video-session', headers=e.headers,
                          json={'path': str(e.movie), 'media_identity': e.identity, 'resume': resume})


def test_new_mutations_keep_origin_token_and_strict_body(env):
    e = env
    body = {'path': str(e.movie), 'media_identity': e.identity}
    assert e.client.post('/api/media/video-session', json=body).status_code == 403
    assert e.client.post('/api/media/video-session', headers={**e.headers, 'Origin': 'https://evil.example'}, json=body).status_code == 403
    for bad in [dict(body, extra=True), dict(body, resume=1), dict(body, media_identity='bad'), dict(body, path=False)]:
        assert e.client.post('/api/media/video-session', headers=e.headers, json=bad).status_code == 422
    outside = e.movie.parent.parent / 'not-approved.mp4'
    outside.write_bytes(b'synthetic outside approved root')
    assert e.client.post('/api/media/video-session', headers=e.headers, json={'path': str(outside), 'media_identity': e.identity}).status_code == 409
    assert not env.extraction.await_count


def test_listing_identity_opaque_no_ns_and_metadata_is_optional(env):
    e = env
    item = e.client.get('/api/media', params={'path': str(e.folder)}).json()['items'][0]
    assert item['media_identity'] == e.identity
    assert 'modified_ns' not in item and item['metadata'] is None and not item['artwork_available']
    assert e.client.post('/api/media/inspect', headers=e.headers, json={'path': str(e.movie), 'media_identity': e.identity}).json()['metadata']['title'] == 'Fixture title'
    again = e.client.get('/api/media', params={'path': str(e.folder)}).json()['items'][0]
    assert again['metadata']['duration_s'] == 100
    assert e.client.get('/api/media/artwork', params={'path': str(e.movie), 'media_identity': e.identity}).status_code == 409
    assert e.client.post('/api/media/inspect', headers=e.headers, json={'path': str(e.movie), 'media_identity': e.identity}).status_code == 200
    assert e.extraction.await_count == 1


def test_start_progress_resume_stream_binding_and_stale_owner(env):
    e = env
    result = create(e)
    assert result.status_code == 200
    first = result.json()
    sid = first['session_id']
    assert len(sid) == 32 and first['stream_url'] == '/api/media/file?session_id=' + sid
    assert first['media_identity'] == e.identity and first['resume_position_s'] == 0
    assert e.client.get(first['stream_url']).status_code == 200
    assert e.client.head(first['stream_url']).status_code == 200
    assert e.pinned[-1] == e.movie.stat().st_ino
    assert e.client.get('/api/media/file', params={'session_id': sid, 'path': str(e.movie)+'-wrong'}).status_code == 409
    assert e.client.get('/api/media/file', params={'path': str(e.movie)}).status_code == 409
    assert e.client.patch('/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 0, 'heartbeat': True}).status_code == 200
    assert e.client.patch('/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 1, 'position_s': 25, 'duration_s': 100}).status_code == 200
    assert e.client.patch('/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 1, 'position_s': 30, 'duration_s': 100}).status_code == 409
    assert e.client.request('DELETE', '/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 2, 'position_s': 35, 'duration_s': 100}).json() == {'closed': True}
    assert e.client.get(first['stream_url']).status_code == 409
    assert create(e, resume=True).json()['resume_position_s'] == 35
    assert e.client.patch('/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 3, 'heartbeat': True}).status_code == 409
    assert e.client.request('DELETE', '/api/media/video-session/'+sid, headers=e.headers).json() == {'closed': False}


def test_observations_reject_bools_nan_and_ambiguous_heartbeat(env):
    e = env
    sid = create(e).json()['session_id']
    for bad in [{'sequence': True, 'heartbeat': True}, {'sequence': 0, 'position_s': True, 'duration_s': 100}, {'sequence': 0, 'position_s': 20}, {'sequence': 0, 'heartbeat': True, 'position_s': 20, 'duration_s': 100}]:
        assert e.client.patch('/api/media/video-session/'+sid, headers=e.headers, json=bad).status_code == 422
    assert e.client.patch('/api/media/video-session/'+sid, headers={**e.headers, 'Content-Type': 'application/json'}, content=b'{"sequence":0,"position_s":NaN,"duration_s":100}').status_code == 422
    assert e.client.request('DELETE', '/api/media/video-session/'+sid, headers=e.headers).status_code == 200
    assert e.hub.local_media.watch.active is None


def test_continue_clear_final_close_cannot_resurrect_or_delete(env):
    e = env
    sid = create(e).json()['session_id']
    e.client.patch('/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 0, 'position_s': 20, 'duration_s': 100})
    item = e.client.get('/api/media/continue').json()['items'][0]
    assert item['media_identity'] == e.identity and item['name'] == e.movie.name
    assert e.client.request('DELETE', '/api/media/continue', headers=e.headers, json={'path': str(e.movie), 'media_identity': e.identity}).json() == {'cleared': True}
    assert e.client.request('DELETE', '/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 1, 'position_s': 30, 'duration_s': 100}).status_code == 200
    assert e.client.get('/api/media/continue').json() == {'items': []}
    assert e.movie.exists()


def test_live_video_blocks_existing_delete_and_success_invalidates_only_after_unlink(env, monkeypatch):
    e = env
    sid = create(e).json()['session_id']
    deleting = AsyncMock(return_value=str(e.movie))
    monkeypatch.setattr(e.hub.content, 'delete_media', deleting)
    body = {'path': str(e.movie), 'token': 'a'*64}
    assert e.client.request('DELETE', '/api/media', headers=e.headers, json=body).json() == {'error': 'media_in_use'}
    deleting.assert_not_awaited()
    assert e.client.request('DELETE', '/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 0, 'position_s': 25, 'duration_s': 100}).status_code == 200
    e.hub.local_media._remember(str(e.movie), e.identity, {'state': 'ready', 'metadata': {'title': 'Fixture'}})
    deleting.side_effect = api.ContentError('media_delete_failed')
    assert e.client.request('DELETE', '/api/media', headers=e.headers, json=body).status_code == 409
    assert e.identity in e.hub.local_media.watch.records and e.identity in e.hub.local_media.cache
    deleting.side_effect = None
    assert e.client.request('DELETE', '/api/media', headers=e.headers, json=body).json() == {'deleted': True}
    assert e.identity not in e.hub.local_media.watch.records and e.identity not in e.hub.local_media.cache
    assert e.movie.exists()  # mocked authority, no physical deletion claimed


def test_player_not_stopped_cannot_start_parallel_video(env):
    e = env
    e.hub.player.status.return_value = {'state': 'playing', 'kind': 'radio'}
    assert create(e).json() == {'error': 'media_in_use'}
    assert e.hub.local_media.watch.active is None


def test_cache_limits_and_bad_artwork_fallback(env):
    e = env
    for i in range(70):
        e.hub.local_media._remember(str(e.movie), f'm1_{i:064x}', {'state': 'ready', 'metadata': {'title': 'bounded'}, 'poster_jpeg': b'not jpeg'})
    assert len(e.hub.local_media.cache) == 64
    assert sum(x['bytes'] for x in e.hub.local_media.cache.values()) <= 8*1024*1024
    assert all(not x['poster'] for x in e.hub.local_media.cache.values())


def test_cache_byte_budget_includes_real_payload_weight(env):
    e = env
    # Synthetic JPEG header shape only; no decode/poster-quality claim.
    poster = b'\xff\xd8\xff\xc0\x00\x08\x08\x00\xb4\x01\x40\x03' + b'\0' * 250000 + b'\xff\xd9'
    for i in range(40):
        e.hub.local_media._remember(str(e.movie), f'm1_{i:064x}', {'state': 'ready', 'metadata': {'title': 'bounded'}, 'poster_jpeg': poster})
    assert len(e.hub.local_media.cache) < 40
    assert sum(x['bytes'] for x in e.hub.local_media.cache.values()) <= 8*1024*1024


def test_identity_includes_each_observed_field_without_exposing_ns():
    fields = {'st_dev': 1, 'st_ino': 2, 'st_size': 3, 'st_mtime_ns': 1792885500883612400, 'st_ctime_ns': 1792885500884619600}
    identity = api.Content.media_identity(Path('/approved/synthetic.mp4'), SimpleNamespace(**fields))
    assert len(identity) == 67 and identity.startswith('m1_')
    for key in fields:
        changed = {**fields, key: fields[key]+1}
        assert api.Content.media_identity(Path('/approved/synthetic.mp4'), SimpleNamespace(**changed)) != identity


def test_inspection_coalesces_and_revalidation_prevents_changed_cache(env, monkeypatch):
    e = env
    async def run():
        entered, finish = asyncio.Event(), asyncio.Event()
        async def inspect(*args, **kwargs):
            entered.set()
            await finish.wait()
            return {'state': 'ready', 'metadata': {'title': 'actual mock observation'}}
        mocked = AsyncMock(side_effect=inspect)
        monkeypatch.setattr(local, 'inspect_fd', mocked)
        first = asyncio.create_task(e.hub.local_media.inspect(str(e.movie), e.identity))
        await asyncio.wait_for(entered.wait(), 2)
        second = asyncio.create_task(e.hub.local_media.inspect(str(e.movie), e.identity))
        await asyncio.sleep(.01)
        finish.set()
        assert (await asyncio.wait_for(first, 2))['state'] == 'ready' and (await asyncio.wait_for(second, 2))['state'] == 'ready'
        assert mocked.await_count == 1 and not e.hub.local_media.jobs
        e.hub.local_media.cache.clear()
        async def changed(*args, **kwargs):
            e.movie.write_bytes(b'changed synthetic file')
            return {'state': 'ready', 'metadata': {'title': 'must not cache'}}
        monkeypatch.setattr(local, 'inspect_fd', changed)
        with pytest.raises(api.ContentError):
            await e.hub.local_media.inspect(str(e.movie), e.identity)
        assert e.identity not in e.hub.local_media.cache
    asyncio.run(run())


def test_cancel_during_threaded_open_reclaims_descriptor(env, monkeypatch):
    e = env
    original = e.hub.local_media.open_approved
    opened = []
    def slow_open(*args):
        time.sleep(.03)
        value = original(*args)
        opened.append(value[1])
        return value
    monkeypatch.setattr(e.hub.local_media, 'open_approved', slow_open)
    async def run():
        task = asyncio.create_task(e.hub.local_media.inspect(str(e.movie), e.identity))
        await asyncio.sleep(.005)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(run())
    assert len(opened) == 1
    with pytest.raises(OSError):
        os.fstat(opened[0])
    assert not e.hub.local_media.jobs
    e.extraction.assert_not_awaited()


def test_housekeeping_expiry_and_cache_shutdown(env):
    e = env
    sid = create(e).json()['session_id']
    active = e.hub.local_media.watch.active
    descriptor = active.fd
    e.hub.local_media.watch.monotonic = lambda: active.expires
    assert e.client.get('/api/media/file', params={'session_id': sid}).status_code == 409
    with pytest.raises(OSError):
        os.fstat(descriptor)
    asyncio.run(e.hub.local_media.close())
    assert not e.hub.local_media.cache and not e.hub.local_media.jobs


def test_postunlink_unknown_observation_still_invalidates_saved_path(env):
    e = env
    sid = create(e).json()['session_id']
    assert e.client.request('DELETE', '/api/media/video-session/'+sid, headers=e.headers, json={'sequence': 0, 'position_s': 25, 'duration_s': 100}).status_code == 200
    assert e.identity in e.hub.local_media.watch.records
    e.hub.local_media.after_delete(str(e.movie), None)
    assert e.identity not in e.hub.local_media.watch.records
    assert e.movie.exists()


def test_final_progress_write_failure_keeps_retryable_session(env):
    e = env
    sid = create(e).json()['session_id']
    before = e.hub.local_media.watch.writer
    def failed(*args):
        raise OSError('synthetic private store failure')
    e.hub.local_media.watch.writer = failed
    body = {'sequence': 0, 'position_s': 25, 'duration_s': 100}
    response = e.client.request('DELETE', '/api/media/video-session/'+sid, headers=e.headers, json=body)
    assert response.status_code == 409 and response.json() == {'error': 'history_write_failed'}
    assert e.hub.local_media.watch.active.token == sid and e.hub.local_media.watch.active.sequence == -1
    e.hub.local_media.watch.writer = before
    assert e.client.request('DELETE', '/api/media/video-session/'+sid, headers=e.headers, json=body).status_code == 200
    assert e.client.get('/api/media/continue').json()['items'][0]['position_s'] == 25


async def entered(event):
    for _ in range(2000):
        if event.is_set():
            return
        await asyncio.sleep(.001)
    raise AssertionError('mock worker did not start')


def test_cancelled_thread_mutator_keeps_lock_until_completion():
    async def run():
        lock = asyncio.Lock()
        began, release = threading.Event(), threading.Event()
        values = []
        def worker():
            began.set()
            assert release.wait(2)
            values.append('committed')
        async def owner():
            async with lock:
                await local.media_thread(worker)
        async def next_owner():
            async with lock:
                assert values == ['committed']
                values.append('next')
        first = asyncio.create_task(owner())
        await entered(began)
        second = asyncio.create_task(next_owner())
        first.cancel()
        await asyncio.sleep(.01)
        assert lock.locked() and not first.done() and not second.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await first
        await second
        assert values == ['committed', 'next']
    asyncio.run(run())


@pytest.mark.parametrize('action', ['progress', 'clear'])
def test_cancelled_api_mutator_drains_before_next_owner(env, monkeypatch, action):
    e = env
    async def run():
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(hub=e.hub)))
        async with e.hub.media_lock:
            sid = e.hub.local_media.start(str(e.movie), e.identity, False)['session_id']
            e.hub.local_media.watch.update(sid, 0, 20, 100)
        began, release = threading.Event(), threading.Event()
        original = e.hub.local_media.watch.update if action == 'progress' else e.hub.local_media.clear
        def delayed(*args, **kwargs):
            began.set()
            assert release.wait(2)
            return original(*args, **kwargs)
        if action == 'progress':
            monkeypatch.setattr(e.hub.local_media.watch, 'update', delayed)
            operation = api.update_video(request, sid, api.VideoObservation(sequence=1, position_s=30, duration_s=100))
        else:
            monkeypatch.setattr(e.hub.local_media, 'clear', delayed)
            operation = api.clear_continue(request, api.MediaReference(path=str(e.movie), media_identity=e.identity))
        first = asyncio.create_task(operation)
        await entered(began)
        async def next_owner():
            async with e.hub.media_lock:
                if action == 'progress':
                    assert e.hub.local_media.watch.records[e.identity]['position_s'] == 30
                else:
                    assert e.identity not in e.hub.local_media.watch.records
                    assert e.hub.local_media.watch.active.history_enabled is False
        second = asyncio.create_task(next_owner())
        first.cancel()
        await asyncio.sleep(.01)
        assert not first.done() and not second.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await first
        await second
    asyncio.run(run())


def test_cancelled_start_closes_only_returned_session_before_unlock(env, monkeypatch):
    e = env
    async def run():
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(hub=e.hub)))
        began, release = threading.Event(), threading.Event()
        original = e.hub.local_media.start
        created = []
        def delayed(*args):
            result = original(*args)
            created.append((result['session_id'], e.hub.local_media.watch.active.fd))
            began.set()
            assert release.wait(2)
            return result
        monkeypatch.setattr(e.hub.local_media, 'start', delayed)
        first = asyncio.create_task(api.start_video(request, api.VideoStart(path=str(e.movie), media_identity=e.identity)))
        await entered(began)
        async def next_owner():
            async with e.hub.media_lock:
                assert e.hub.local_media.watch.active is None
                with pytest.raises(OSError):
                    os.fstat(created[0][1])
                return original(str(e.movie), e.identity, False)['session_id']
        second = asyncio.create_task(next_owner())
        first.cancel()
        await asyncio.sleep(.01)
        assert not second.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await first
        replacement = await second
        assert replacement != created[0][0] and e.hub.local_media.watch.active.token == replacement
    asyncio.run(run())


def test_cancelled_stream_releases_unused_response_without_gc(env, monkeypatch):
    e = env
    descriptor_module = importlib.import_module('services.backend.descriptor_response')
    async def run():
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(hub=e.hub)))
        began, release = threading.Event(), threading.Event()
        captured = []
        def delayed(*args):
            _, fd, _ = e.hub.local_media.open_approved(str(e.movie), e.identity)
            response = object.__new__(descriptor_module.DescriptorFileResponse)
            response._release = weakref.finalize(response, os.close, fd)
            captured.append((response, fd))  # Keep a strong reference: no GC proof.
            began.set()
            assert release.wait(2)
            return response
        monkeypatch.setattr(e.hub.local_media, 'stream', delayed)
        first = asyncio.create_task(api.media_file(request, path=str(e.movie)))
        await entered(began)
        first.cancel()
        await asyncio.sleep(.01)
        assert not first.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await first
        assert captured[0][0]._release.alive is False
        with pytest.raises(OSError):
            os.fstat(captured[0][1])
    asyncio.run(run())


def test_cancelled_delete_keeps_lock_through_unlink_and_postcleanup(env, monkeypatch):
    e = env
    async def run():
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(hub=e.hub)))
        async with e.hub.media_lock:
            sid = e.hub.local_media.start(str(e.movie), e.identity, False)['session_id']
            e.hub.local_media.watch.update(sid, 0, 25, 100, final=True)
        e.hub.queue = [{'path': str(e.movie), 'name': e.movie.name}]
        e.hub.queue_index = 0
        e.hub.local_media._remember(str(e.movie), e.identity, {'state': 'ready', 'metadata': {'title': 'fixture'}})
        began, release = threading.Event(), threading.Event()
        def unlink_worker():
            began.set()
            assert release.wait(2)
            return str(e.movie)  # Authority mocked; no physical unlink claimed.
        async def unlink(*args):
            return await asyncio.to_thread(unlink_worker)
        monkeypatch.setattr(e.hub.content, 'delete_media', unlink)
        first = asyncio.create_task(api.delete_media(request, api.MediaDelete(path=str(e.movie), token='a'*64)))
        await entered(began)
        async def next_owner():
            async with e.hub.media_lock:
                assert not e.hub.queue and e.hub.queue_index == -1
                assert e.identity not in e.hub.local_media.cache
                assert e.identity not in e.hub.local_media.watch.records
        second = asyncio.create_task(next_owner())
        first.cancel()
        await asyncio.sleep(.01)
        assert not first.done() and not second.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await first
        await second
    asyncio.run(run())


def test_anyio_parent_cancellation_drains_media_worker():
    async def run():
        lock = asyncio.Lock()
        began, release = threading.Event(), threading.Event()
        state = []
        def work():
            began.set()
            assert release.wait(2)
            state.append('finished')
        async def owner():
            async with lock:
                await local.media_thread(work)
        async with anyio.create_task_group() as group:
            group.start_soon(owner)
            await entered(began)
            group.cancel_scope.cancel()
            release.set()
        assert state == ['finished'] and not lock.locked()
    asyncio.run(run())
