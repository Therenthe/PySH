"""Hardware previews are observed, serialized and never saved per pointer move."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
import pytest

from services.backend.app import app, Hub, Audio, audio


@pytest.fixture
def scalar(tmp_path, monkeypatch):
    hub = Hub(tmp_path)
    hub.store.update({'audioOutput': 'speaker', 'volume': 30, 'screenBrightness': 80})
    current = {'available': True, 'volume': 30, 'mute': False, 'output': 'speaker',
               'outputs': [{'id': 'speaker', 'bluetooth': True, 'active': True}]}

    async def status():
        return deepcopy(current)

    async def set_audio(*, observed=None, **change):
        current.update(change)
        return deepcopy(current)

    hub.device = SimpleNamespace(audio_status=AsyncMock(side_effect=status), audio_set=AsyncMock(side_effect=set_audio),
                                network_status=AsyncMock(return_value={}), bluetooth_status=AsyncMock(return_value={}))
    hub.visualizer = SimpleNamespace(close=AsyncMock())
    hub.player = SimpleNamespace(command=AsyncMock())
    hub.snapshots['audio'] = {**deepcopy(current), 'ready': True}
    hub.audio_selected = True
    hub.last_output = hub._audio_restored = 'speaker'
    level = {'value': 80}

    async def brightness_status():
        return {'available': True, 'value': level['value']}

    async def brightness_set(value):
        level['value'] = value
        return await brightness_status()

    hub.power.backlight = SimpleNamespace(status=AsyncMock(side_effect=brightness_status), set=AsyncMock(side_effect=brightness_set))
    writes = Mock(wraps=hub.store._atomic)
    monkeypatch.setattr(hub.store, '_atomic', writes)
    monkeypatch.setattr(app.state, 'hub', hub, raising=False)
    client = TestClient(app, base_url='http://127.0.0.1:8765')
    return hub, client, {'X-Hub-Token': hub.token}, current, level, writes


def test_volume_previews_apply_actual_level_without_flash_or_monitor_restart(scalar):
    hub, client, headers, current, _, writes = scalar
    for value in [42, 63, 79]:
        reply = client.post('/api/audio', headers=headers, json={'volume': value, 'persist': False})
        assert reply.status_code == 200
        assert reply.json()['volume'] == current['volume'] == value
        assert reply.json()['ready'] is True
        assert hub.snapshots['audio']['volume'] == value
        assert hub.store.value.volume == 30
    writes.assert_not_called()
    hub.device.network_status.assert_not_awaited()
    hub.device.bluetooth_status.assert_not_awaited()
    hub.visualizer.close.assert_not_awaited()
    hub.player.command.assert_not_awaited()
    assert all(call.kwargs.keys() == {'volume', 'observed'} for call in hub.device.audio_set.await_args_list)
    final = client.post('/api/audio', headers=headers, json={'volume': 79})
    assert final.status_code == 200
    assert hub.store.value.volume == 79
    assert writes.call_count == 2  # One final preference transaction + backup.
    assert hub.snapshots['audio']['volume'] == 79


def test_brightness_preview_is_live_and_final_commit_is_the_only_saved_value(scalar):
    hub, client, headers, _, level, writes = scalar
    hub.power.error = 'brightness_unavailable'
    for value in [52, 37, 61]:
        reply = client.post('/api/power/brightness', headers=headers, json={'value': value, 'persist': False})
        assert reply.status_code == 200
        assert reply.json()['brightness']['value'] == level['value'] == value
        assert reply.json()['brightness']['desired'] == hub.store.value.screenBrightness == 80
        assert hub.power.error is None
    writes.assert_not_called()
    final = client.post('/api/power/brightness', headers=headers, json={'value': 61})
    assert final.status_code == 200
    assert final.json()['brightness']['value'] == final.json()['brightness']['desired'] == 61
    assert hub.store.value.screenBrightness == 61
    assert writes.call_count == 2


@pytest.mark.parametrize('payload', [
    {'persist': False}, {'mute': True, 'persist': False}, {'output': 'speaker', 'persist': False},
    {'volume': 50, 'mute': False, 'persist': False}, {'volume': 50, 'output': 'speaker', 'persist': False},
    {'volume': 50, 'persist': 0}, {'volume': 50, 'persist': 'false'},
])
def test_volume_preview_rejects_non_scalar_or_ambiguous_flags(scalar, payload):
    hub, client, headers, _, _, writes = scalar
    assert client.post('/api/audio', headers=headers, json=payload).status_code == 422
    hub.device.audio_set.assert_not_awaited()
    writes.assert_not_called()


@pytest.mark.parametrize('payload', [
    {'value': 0}, {'value': 101}, {'value': True}, {'value': 2.5}, {'value': '25'},
    {'value': 50, 'persist': 0}, {'value': 50, 'persist': 'false'}, {'value': 50, 'path': '/private'},
])
def test_brightness_route_rejects_untyped_values_and_extra_fields(scalar, payload):
    hub, client, headers, _, _, writes = scalar
    assert client.post('/api/power/brightness', headers=headers, json=payload).status_code == 422
    hub.power.backlight.set.assert_not_awaited()
    writes.assert_not_called()


@pytest.mark.parametrize('path,payload', [('/api/audio', {'volume': 50, 'persist': False}),
                                         ('/api/power/brightness', {'value': 50, 'persist': False})])
def test_preview_routes_keep_token_and_origin_boundaries(scalar, path, payload):
    hub, client, headers, _, _, writes = scalar
    assert client.post(path, json=payload).status_code == 403
    assert client.post(path, headers={**headers, 'Origin': 'https://outside.invalid'}, json=payload).status_code == 403
    assert client.post(path, headers={**headers, 'Sec-Fetch-Site': 'cross-site'}, json=payload).status_code == 403
    hub.device.audio_set.assert_not_awaited()
    hub.power.backlight.set.assert_not_awaited()
    writes.assert_not_called()


def test_preview_uses_fresh_output_readiness_instead_of_cached_green_state(scalar):
    hub, client, headers, current, _, writes = scalar
    current.update(output='missing', outputs=[])
    reply = client.post('/api/audio', headers=headers, json={'volume': 50, 'persist': False})
    assert reply.status_code == 409
    assert reply.json() == {'error': 'no_audio_output'}
    assert hub.audio_selected is False
    hub.device.audio_set.assert_not_awaited()
    writes.assert_not_called()


def test_volume_preview_serializes_with_other_previews_and_device_poll(scalar):
    hub, _, _, current, _, writes = scalar

    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()
        count = 0

        async def held(*, observed=None, **change):
            nonlocal count
            count += 1
            if count == 1:
                started.set()
                await release.wait()
            current.update(change)
            return deepcopy(current)

        hub.device.audio_set.side_effect = held
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(hub=hub)))
        first = asyncio.create_task(audio(request, Audio(volume=44, persist=False)))
        await started.wait()
        second = asyncio.create_task(audio(request, Audio(volume=69, persist=False)))
        poll = asyncio.create_task(hub.refresh_device())
        await asyncio.sleep(0)
        assert count == 1
        hub.device.network_status.assert_not_awaited()
        release.set()
        await asyncio.gather(first, second, poll)
        assert count == 2
        assert hub.snapshots['audio']['volume'] == current['volume'] == 69
        assert hub.store.value.volume == 30

    asyncio.run(scenario())
    writes.assert_not_called()


def test_slow_network_poll_does_not_block_volume_and_adopts_fresh_audio(scalar):
    hub, _, _, current, _, writes = scalar

    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()

        async def slow_network():
            started.set()
            await release.wait()
            return {'state': 'connected'}

        hub.device.network_status.side_effect = slow_network
        poll = asyncio.create_task(hub._poll_device())
        await started.wait()
        assert not hub._device_lock.locked()
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(hub=hub)))
        # The network gate remains shut; completion cannot depend on its delay.
        result = await asyncio.wait_for(audio(request, Audio(volume=57, persist=False)), timeout=.5)
        assert result['volume'] == current['volume'] == 57
        assert not poll.done()
        hub.device.audio_status.assert_awaited_once()
        hub.device.audio_set.assert_awaited_once_with(volume=57, observed=hub.device.audio_set.await_args.kwargs['observed'])
        assert hub.device.audio_set.await_args.kwargs['observed']['volume'] == 30
        release.set()
        await poll
        assert hub.snapshots['audio']['volume'] == 57
        assert hub.snapshots['network']['state'] == 'connected'

    asyncio.run(scenario())
    writes.assert_not_called()


def test_delayed_poll_cannot_overwrite_explicit_connection_refresh(scalar):
    hub, _, _, _, _, _ = scalar

    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()
        first = True

        async def network():
            nonlocal first
            if first:
                first = False
                started.set()
                await release.wait()
                return {'state': 'old'}
            return {'state': 'new'}

        hub.device.network_status.side_effect = network
        poll = asyncio.create_task(hub._poll_device())
        await started.wait()
        await hub.refresh_device()
        assert hub.snapshots['network']['state'] == 'new'
        release.set()
        await poll
        assert hub.snapshots['network']['state'] == 'new'

    asyncio.run(scenario())
