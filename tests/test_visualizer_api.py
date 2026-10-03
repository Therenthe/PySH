import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.backend.app import Hub, app
from services.backend.preferences import PreferenceStore


@pytest.fixture
def client(tmp_path):
    hub = Hub(tmp_path)
    hub.player = SimpleNamespace(status=AsyncMock(return_value={'state': 'playing', 'kind': 'radio', 'volume': 80}), command=AsyncMock(return_value={'state': 'paused', 'kind': 'radio'}), close=AsyncMock())
    hub.device = SimpleNamespace(close=AsyncMock())
    hub.external = SimpleNamespace(close=AsyncMock())
    hub.visualizer = SimpleNamespace(snapshot=AsyncMock(return_value={'available': False, 'status': 'inactive'}), close=AsyncMock())
    app.state.hub = hub
    return TestClient(app, base_url='http://127.0.0.1:8765')


def test_default_off_and_styles_persist(tmp_path):
    store = PreferenceStore(tmp_path)
    assert store.value.visualizerStyle == 'off'
    for style in ('wave', 'bars', 'orbit', 'off'):
        store.update({'visualizerStyle': style})
        assert PreferenceStore(tmp_path).value.visualizerStyle == style
    before = store.path.read_bytes()
    with pytest.raises(ValidationError):
        store.update({'visualizerStyle': 'microphone'})
    assert store.path.read_bytes() == before


def test_endpoint_is_cached_no_store_and_preference_gated(client):
    hub = app.state.hub
    response = client.get('/api/audio/visualization')
    assert response.status_code == 200 and response.headers['Cache-Control'] == 'no-store'
    hub.visualizer.snapshot.assert_awaited_once_with(enabled=False)
    hub.visualizer.snapshot.reset_mock()
    hub.store.update({'visualizerStyle': 'bars'})
    for _ in range(10):
        assert client.get('/api/audio/visualization').status_code == 200
    hub.player.status.assert_not_awaited()
    assert hub.visualizer.snapshot.await_count == 10
    assert hub.visualizer.snapshot.await_args.kwargs == {'enabled': True}
    hub.service_mode = True
    client.get('/api/audio/visualization')
    assert hub.visualizer.snapshot.await_args.kwargs == {'enabled': False}


@pytest.mark.parametrize('headers', [{'Origin': 'https://evil.example'}, {'Host': 'evil.example:8765'}, {'Sec-Fetch-Site': 'cross-site'}])
def test_signal_boundary_rejects_remote_pages(client, headers):
    assert client.get('/api/audio/visualization', headers=headers).status_code == 403
    app.state.hub.visualizer.snapshot.assert_not_awaited()


def test_cache_requires_fresh_normal_state_and_audible_player(client, monkeypatch):
    hub = app.state.hub
    hub.store.update({'visualizerStyle': 'wave'})
    hub.snapshots['audio'] = {'ready': True, 'volume': 50, 'mute': False}
    assert hub.visualizer_context() == ({}, {})
    client.get('/api/state')
    assert hub.visualizer_context()[1]['state'] == 'playing'
    sampled = hub._playback_sampled
    monkeypatch.setattr('services.backend.app.time.monotonic', lambda: sampled + 3.1)
    assert hub.visualizer_context() == ({}, {})
    monkeypatch.setattr('services.backend.app.time.monotonic', lambda: sampled + 1)
    hub.cache_playback({'state': 'playing', 'kind': 'radio', 'muted': True})
    assert hub.visualizer_context() == ({}, {})
    hub.cache_playback({'state': 'playing', 'kind': 'radio', 'volume': 0})
    assert hub.visualizer_context() == ({}, {})


def test_pause_and_switch_off_close_capture_immediately(client):
    hub = app.state.hub
    hub.store.update({'visualizerStyle': 'bars'})
    token = {'X-Hub-Token': hub.token}
    assert client.post('/api/player', headers=token, json={'action': 'pause'}).status_code == 200
    assert hub._playback_snapshot['state'] == 'paused'
    assert hub.visualizer.close.await_count == 1
    assert client.patch('/api/preferences', headers=token, json={'visualizerStyle': 'off'}).status_code == 200
    assert hub.visualizer.close.await_count == 2


def test_hub_shutdown_closes_capture_before_runtime(client):
    hub = app.state.hub
    order = []
    async def capture_close(): order.append('capture')
    async def player_close(): order.append('player')
    hub.visualizer.close = capture_close
    hub.player.close = player_close
    asyncio.run(hub.close())
    assert order == ['capture', 'player']


def test_routing_change_blocks_concurrent_cache_refresh_and_recovers_after_failure(client):
    hub = app.state.hub
    hub.store.update({'visualizerStyle': 'wave'})
    hub.snapshots['audio'] = {'ready': True}
    async def scenario():
        with pytest.raises(RuntimeError):
            async with hub.changing_audio():
                hub.cache_playback({'state': 'playing', 'kind': 'radio'})
                assert hub.visualizer_context() == ({}, {})
                raise RuntimeError('routing unavailable')
        assert hub._visualizer_suspended == 0
        assert hub.visualizer_context()[1]['state'] == 'playing'
    asyncio.run(scenario())
