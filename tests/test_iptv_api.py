"""IPTV route composition and ownership; no browser, network or device changes."""
import asyncio
import hashlib
import os
from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import pytest

from services.backend.content import ContentError
from services.backend.iptv_api import (router, refresh, sources, view, recorded_media,
                                       catalogue, recordings, Channel, Sources)
from services.backend.iptv_catalog import IPTVError
from services.backend.iptv_recorder import RecorderError
from services.backend.iptv_stream import IPTVStream, IPTVStreamError


URL = 'https://streams.example/live.m3u8'


def hub_fixture():
    hub = SimpleNamespace(
        iptv=SimpleNamespace(resolve=lambda channel_id: {'id': channel_id, 'url': URL}),
        iptv_stream=IPTVStream(idle_timeout=120),
        media_lock=asyncio.Lock(),
        local_media=SimpleNamespace(watch=SimpleNamespace(active=None, expire=lambda: None)),
        power=SimpleNamespace(standby=False), service_mode=False,
        player=SimpleNamespace(command=AsyncMock(return_value={'state': 'idle'})),
        visualizer=SimpleNamespace(close=AsyncMock()),
        cache_playback=lambda value: value,
        iptv_refreshing=set(), tasks=[],
    )
    hub.background = lambda operation: hub.tasks.append(asyncio.create_task(operation))
    return hub


def request_for(hub):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(hub=hub)))


def client_for(hub):
    app = FastAPI()
    app.state.hub = hub
    app.include_router(router)
    for error in (ContentError, IPTVStreamError, IPTVError, RecorderError):
        async def failure(_request, exc):
            return JSONResponse({'error': exc.code}, status_code=409)
        app.add_exception_handler(error, failure)
    return TestClient(app)


def test_view_stops_previous_mpv_before_acquiring_tv_decoder():
    async def scenario():
        hub = hub_fixture()
        trace = []
        async def stop(action):
            trace.append(action)
            assert not hub.iptv_stream.active()
        async def close_visualizer():
            trace.append('visualizer')
            assert not hub.iptv_stream.active()
        hub.player.command = stop
        hub.visualizer.close = close_visualizer
        result = await view(request_for(hub), Channel(channel_id='tv_one'))
        assert trace == ['stop', 'visualizer']
        assert result['channel_id'] == 'tv_one'
        assert hub.iptv_stream.active()
        assert not hub.media_lock.locked()
    asyncio.run(scenario())


@pytest.mark.parametrize('blocker,code', [('standby', 'standby_active'), ('service', 'service_mode'),
                                          ('local', 'media_in_use'), ('tv', 'media_in_use')])
def test_view_respects_existing_owners_and_power(blocker, code):
    async def scenario():
        hub = hub_fixture()
        if blocker == 'standby':
            hub.power.standby = True
        elif blocker == 'service':
            hub.service_mode = True
        elif blocker == 'local':
            hub.local_media.watch.active = object()
        else:
            hub.iptv_stream.start('existing', URL)
        with pytest.raises(ContentError) as caught:
            await view(request_for(hub), Channel(channel_id='new'))
        assert caught.value.code == code
        hub.player.command.assert_not_awaited()
        hub.visualizer.close.assert_not_awaited()
    asyncio.run(scenario())


def test_view_dns_resolution_does_not_hold_media_lock():
    async def scenario():
        hub = hub_fixture()
        entered, release = threading.Event(), threading.Event()
        def resolve(channel_id):
            entered.set()
            assert release.wait(3)
            return {'id': channel_id, 'url': URL}
        hub.iptv.resolve = resolve
        task = asyncio.create_task(view(request_for(hub), Channel(channel_id='one')))
        assert await asyncio.to_thread(entered.wait, 3)
        assert not hub.media_lock.locked()
        hub.power.standby = True
        release.set()
        with pytest.raises(ContentError) as caught:
            await task
        assert caught.value.code == 'standby_active'
        assert not hub.iptv_stream.active()
    asyncio.run(scenario())


def test_cancelled_view_transition_keeps_lock_until_exact_session_is_released():
    async def scenario():
        hub = hub_fixture()
        entered, release = asyncio.Event(), asyncio.Event()
        async def stop(_action):
            entered.set()
            await release.wait()
        hub.player.command = stop
        task = asyncio.create_task(view(request_for(hub), Channel(channel_id='one')))
        await asyncio.wait_for(entered.wait(), 3)
        task.cancel()
        await asyncio.sleep(0)
        assert hub.media_lock.locked()
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not hub.iptv_stream.active()
        assert not hub.media_lock.locked()
    asyncio.run(scenario())


def test_heartbeat_renews_only_exact_owner_and_has_strict_body():
    now = [0.0]
    hub = hub_fixture()
    hub.iptv_stream = IPTVStream(clock=lambda: now[0], idle_timeout=120)
    started = hub.iptv_stream.start('one', URL)
    client = client_for(hub)
    path = '/api/iptv/view/' + started['session_id']
    now[0] = 110
    assert client.patch(path, json={}).json() == {'active': True}
    now[0] = 200
    assert hub.iptv_stream.active()
    assert client.patch(path, json={'unexpected': True}).status_code == 422
    assert client.patch('/api/iptv/view/' + 'x' * 32, json={}).json() == {'error': 'iptv_session_expired'}
    now[0] = 231
    assert client.patch(path, json={}).json() == {'error': 'iptv_session_expired'}


def test_stale_delete_does_not_close_replacement_session():
    hub = hub_fixture()
    old = hub.iptv_stream.start('old', URL)
    latest = hub.iptv_stream.start('new', URL)
    client = client_for(hub)
    assert client.delete('/api/iptv/view/' + old['session_id']).json() == {'closed': False}
    assert hub.iptv_stream.active()
    assert client.delete('/api/iptv/view/' + latest['session_id']).json() == {'closed': True}
    assert not hub.iptv_stream.active()


def test_catalogue_does_not_publish_resolved_stream_locations_or_backend_matching_fields():
    async def scenario():
        hub = hub_fixture()
        hub.iptv.catalogue = lambda: {'channels': [{'id': 'one', 'name': 'Synthetic TV', 'logo': '',
                                                  'group': 'Tests', 'favorite': True, 'url': URL,
                                                  'tvg_id': 'one.ro', 'tvg_name': 'Matching alias',
                                                  'sources': ['https://source.example/list.m3u']}],
                                       'sources': {'playlists': ['https://source.example/list.m3u'], 'xmltv': []}}
        response = await catalogue(request_for(hub))
        assert response['channels'] == [{'id': 'one', 'name': 'Synthetic TV', 'logo': '', 'group': 'Tests', 'favorite': True}]
        assert response['sources']['playlists'] == ['https://source.example/list.m3u']
    asyncio.run(scenario())


def test_lazy_recorder_initialization_runs_in_a_worker_not_the_api_event_loop():
    async def scenario():
        event_thread = threading.get_ident()
        class LazyHub:
            @property
            def recorder(self):
                assert threading.get_ident() != event_thread
                return SimpleNamespace(list=lambda: [], status=lambda: {'service_active': False})
        response = await recordings(request_for(LazyHub()))
        assert response == {'items': [], 'service': {'service_active': False, 'active': False}}
    asyncio.run(scenario())


def test_source_change_during_fetch_is_coalesced_and_imported_without_periodic_wait():
    async def scenario():
        hub = hub_fixture()
        entered, release = threading.Event(), threading.Event()
        generation = [0]
        observed = []
        def fetch_guide():
            current = generation[0]
            observed.append(current)
            if len(observed) == 1:
                entered.set()
                assert release.wait(3)
            if current != generation[0]:
                raise IPTVError('iptv_sources_changed')
        def set_sources(kind, urls):
            assert kind == 'xmltv'
            assert urls == ['https://guide.example/new.xml']
            generation[0] += 1
        hub.iptv.refresh_guide = fetch_guide
        hub.iptv.set_sources = set_sources
        task = asyncio.create_task(refresh(hub, 'guide'))
        assert await asyncio.to_thread(entered.wait, 3)
        result = await sources(request_for(hub), Sources(kind='xmltv', urls=['https://guide.example/new.xml']))
        assert result == {'saved': True}
        await asyncio.sleep(0)
        assert 'guide' in hub.iptv_refreshing
        release.set()
        await asyncio.wait_for(task, 3)
        await asyncio.gather(*hub.tasks)
        assert observed == [0, 1]
        assert not hub.iptv_refreshing
        assert not hub.iptv_refresh_pending
        assert hub.iptv_refresh_worker is None
    asyncio.run(scenario())


def test_cross_kind_refresh_is_serial_and_duplicate_requests_coalesce():
    async def scenario():
        hub = hub_fixture()
        entered, release = threading.Event(), threading.Event()
        calls = []
        def playlists():
            calls.append('playlists')
            entered.set()
            assert release.wait(3)
        def guide():
            calls.append('guide')
        hub.iptv.refresh_playlists = playlists
        hub.iptv.refresh_guide = guide
        task = asyncio.create_task(refresh(hub, 'playlists'))
        assert await asyncio.to_thread(entered.wait, 3)
        await asyncio.gather(*(refresh(hub, 'guide') for _ in range(8)))
        assert calls == ['playlists']
        assert hub.iptv_refreshing == {'playlists', 'guide'}
        release.set()
        await asyncio.wait_for(task, 3)
        assert calls == ['playlists', 'guide']
        assert not hub.iptv_refreshing
    asyncio.run(scenario())


def test_refresh_busy_retries_and_ordinary_failure_does_not_spin():
    async def scenario():
        hub = hub_fixture()
        calls = []
        def guide():
            calls.append('guide')
            if len(calls) == 1:
                raise IPTVError('iptv_refresh_busy')
            raise IPTVError('iptv_source_unavailable')
        hub.iptv.refresh_guide = guide
        await refresh(hub, 'guide')
        assert calls == ['guide', 'guide']
        assert not hub.iptv_refreshing
    asyncio.run(scenario())


def test_cancelled_refresh_drains_worker_and_clears_queue():
    async def scenario():
        hub = hub_fixture()
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        def guide():
            entered.set()
            assert release.wait(3)
            finished.set()
        hub.iptv.refresh_guide = guide
        task = asyncio.create_task(refresh(hub, 'guide'))
        assert await asyncio.to_thread(entered.wait, 3)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert finished.is_set()
        assert not hub.iptv_refreshing
        assert not hub.iptv_refresh_pending
        assert hub.iptv_refresh_worker is None
    asyncio.run(scenario())


def test_record_creation_requires_stable_request_identity_and_strict_payload():
    hub = hub_fixture()
    received = []
    def create(*args, **kwargs):
        received.append(kwargs['request_id'])
        return {'id': 'created'}
    hub.recorder = SimpleNamespace(create=create)
    client = client_for(hub)
    body = {'channel_id': 'one', 'title': 'Synthetic show', 'start_at': '2026-11-05T12:00:00Z',
            'end_at': '2026-11-05T13:00:00Z', 'before_minutes': 0, 'after_minutes': 60}
    assert client.post('/api/iptv/recordings', json=body).status_code == 422
    body['request_id'] = '0c3da976-4e63-4cbf-af6b-56281c849276'
    assert client.post('/api/iptv/recordings', json=body).json() == {'id': 'created'}
    assert client.post('/api/iptv/recordings', json={**body, 'after_minutes': 61}).status_code == 422
    assert client.post('/api/iptv/recordings', json={**body, 'before_minutes': True}).status_code == 422
    assert client.post('/api/iptv/recordings', json={**body, 'output_path': '/not/allowed'}).status_code == 422
    assert received == [body['request_id']]


def test_recorded_media_requires_terminal_owned_inode_and_revalidated_identity(tmp_path):
    async def scenario():
        path = tmp_path / 'owned.mkv'
        path.write_bytes(b'synthetic video bytes')
        hub = hub_fixture()
        descriptors = []
        def open_recording(_job_id):
            descriptor = os.open(path, os.O_RDONLY)
            descriptors.append(descriptor)
            return descriptor
        def identity(_path, info):
            return hashlib.sha256(f'{info.st_dev}:{info.st_ino}:{info.st_size}:{info.st_mtime_ns}'.encode()).hexdigest()
        async def listing(_parent):
            return {'items': [{'path': str(path), 'media_identity': identity(path, path.stat()), 'name': path.name}]}
        hub.recorder = SimpleNamespace(open_recording=open_recording, recording_path=lambda _job: path)
        hub.content = SimpleNamespace(media_list=listing, media_identity=identity)
        hub.local_media.enrich = lambda value: value
        result = await recorded_media(request_for(hub), 'fixture-job')
        assert result['path'] == str(path)
        with pytest.raises(OSError):
            os.fstat(descriptors[-1])
        async def replaced(_parent):
            return {'items': [{'path': str(path), 'media_identity': 'different-inode-version'}]}
        hub.content.media_list = replaced
        with pytest.raises(ContentError) as caught:
            await recorded_media(request_for(hub), 'fixture-job')
        assert caught.value.code == 'media_not_found'
        with pytest.raises(OSError):
            os.fstat(descriptors[-1])
        def active(_job):
            raise RecorderError('recording_active')
        hub.recorder.open_recording = active
        with pytest.raises(RecorderError, match='recording_active'):
            await recorded_media(request_for(hub), 'fixture-job')
    asyncio.run(scenario())
