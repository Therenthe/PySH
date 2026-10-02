from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from services.backend.app import app, Hub


@pytest.fixture
def client(tmp_path):
    # Do not start hardware or external network services in HTTP boundary tests.
    hub = Hub(tmp_path)
    hub.device = SimpleNamespace(audio_set=AsyncMock(return_value={"available": False, "error":"unavailable"}))
    hub.player = SimpleNamespace(status=AsyncMock(return_value={"state":"idle"}), play=AsyncMock())
    app.state.hub = hub
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_session_and_preference_roundtrip(client):
    token = client.get('/api/session').json()['token']
    response = client.patch('/api/preferences', headers={'X-Hub-Token':token}, json={'language':'en'})
    assert response.status_code == 200
    assert client.get('/api/state').json()['preferences']['language'] == 'en'


@pytest.mark.parametrize('headers', [{'Origin':'https://evil.example'}, {'Host':'evil.example:8765'}, {'Sec-Fetch-Site':'cross-site'}])
def test_host_and_cross_site_boundary(client, headers):
    assert client.get('/api/session', headers=headers).status_code == 403


def test_mutation_requires_token(client):
    assert client.patch('/api/preferences', json={'language':'en'}).status_code == 403
    assert app.state.hub.store.value.language == 'ro'


def test_validation_never_reflects_submitted_credentials(client):
    token = client.get('/api/session').json()['token']
    secret = 'private-network-password-do-not-return'
    response = client.post('/api/network/connect', headers={'X-Hub-Token':token}, json={'ssid':'','password':secret})
    assert response.status_code == 422
    assert secret not in response.text
    assert response.json() == {'error':'invalid_request'}


def test_unknown_preferences_rejected_without_persistence(client):
    token = client.get('/api/session').json()['token']
    response = client.patch('/api/preferences', headers={'X-Hub-Token':token}, json={'command':'shell'})
    assert response.status_code == 422
    assert not app.state.hub.store.path.exists()


def test_diagnostics_do_not_expose_network_identifiers_or_token(client):
    hub = app.state.hub
    hub.snapshots['network'] = {'available':True, 'connection':'private-ssid', 'devices':[{'ip':'192.168.1.5'}]}
    response = client.get('/api/diagnostics')
    assert response.status_code == 200
    assert all(value not in response.text for value in ['private-ssid','192.168.1.5',hub.token])


def test_appliance_service_mode_stops_media_and_preserves_preferences(client):
    hub = app.state.hub
    hub.appliance = True
    hub.player.status = AsyncMock(return_value={"state": "playing"})
    hub.player.command = AsyncMock()
    hub.store.update({"language": "en", "setupComplete": True})
    before = hub.store.path.read_bytes()
    headers = {'X-Hub-Token': hub.token}
    response = client.post('/api/exit', headers=headers)
    assert response.json() == {'exiting': False, 'mode': 'service'}
    hub.player.command.assert_awaited_once_with('stop')
    assert client.get('/api/state').json()['serviceMode'] is True
    assert hub.store.path.read_bytes() == before
    assert not (hub.store.directory / 'exit-request').exists()
    assert client.post('/api/service/return', headers=headers).json() == {'mode': 'hub'}
    assert client.get('/api/state').json()['serviceMode'] is False
    assert hub.store.path.read_bytes() == before


def test_service_return_requires_token_and_appliance_mode(client):
    hub = app.state.hub
    hub.appliance = True
    hub.service_mode = True
    assert client.post('/api/service/return').status_code == 403
    assert hub.service_mode is True
    hub.appliance = False
    assert client.post('/api/service/return', headers={'X-Hub-Token': hub.token}).status_code == 409


def test_failed_media_stop_does_not_hide_controls_in_service_mode(client):
    from services.backend.player import PlayerError
    hub = app.state.hub
    hub.appliance = True
    hub.player.status = AsyncMock(return_value={"state": "playing"})
    hub.player.command = AsyncMock(side_effect=PlayerError("player_timeout", "timeout"))
    response = client.post('/api/exit', headers={'X-Hub-Token': hub.token})
    assert response.status_code == 409
    assert hub.service_mode is False


def test_unsupervised_desktop_exit_retains_existing_boundary(client, monkeypatch):
    monkeypatch.delenv('PI_HUB_SUPERVISED', raising=False)
    app.state.hub.appliance = False
    response = client.post('/api/exit', headers={'X-Hub-Token': app.state.hub.token})
    assert response.json() == {'error': 'desktop_exit_unavailable'}


def test_late_weather_cannot_replace_new_location(tmp_path):
    import asyncio
    async def scenario():
        hub = Hub(tmp_path)
        first_started, release_first = asyncio.Event(), asyncio.Event()
        async def weather(location):
            if location['name'] == 'Old':
                first_started.set()
                await release_first.wait()
            return {'city': location['name'], 'stale': False}
        hub.content.weather = weather
        hub.store.update({'location': {'name': 'Old', 'latitude': 1, 'longitude': 1}})
        old = asyncio.create_task(hub.refresh_weather())
        await first_started.wait()
        hub.store.update({'location': {'name': 'New', 'latitude': 2, 'longitude': 2}})
        await hub.refresh_weather()
        release_first.set()
        await old
        assert hub.weather['city'] == 'New'
        # Removing the location also invalidates an in-flight result.
        first_started.clear()
        release_first.clear()
        hub.store.update({'location': {'name': 'Old', 'latitude': 1, 'longitude': 1}})
        old = asyncio.create_task(hub.refresh_weather())
        await first_started.wait()
        hub.store.update({'location': None})
        await hub.refresh_weather()
        release_first.set()
        await old
        assert hub.weather is None
    asyncio.run(scenario())


def test_saved_audio_restores_once_and_after_reconnection(tmp_path):
    import asyncio
    async def scenario():
        hub = Hub(tmp_path)
        hub.store.update({'audioOutput': 'speaker', 'volume': 23, 'mute': True})
        outputs = [{'id': 'other', 'bluetooth': False}, {'id': 'speaker', 'bluetooth': True}]
        current = {'available': True, 'output': 'other', 'outputs': outputs, 'volume': 70, 'mute': False}
        async def audio_status(): return dict(current)
        async def audio_set(**values):
            current.update(output=values['output'], volume=values['volume'], mute=values['mute'])
            return dict(current)
        hub.device = SimpleNamespace(network_status=AsyncMock(return_value={}), bluetooth_status=AsyncMock(return_value={}), audio_status=audio_status, audio_set=AsyncMock(side_effect=audio_set))
        hub.player = SimpleNamespace(command=AsyncMock())
        await hub.refresh_device()
        assert hub.snapshots['audio']['volume'] == 23
        assert hub.snapshots['audio']['mute'] is True
        assert hub.snapshots['audio']['output'] == 'speaker'
        assert hub.audio_selected is True
        await hub.refresh_device()
        assert hub.device.audio_set.await_count == 1
        current.update(output='other', outputs=outputs[:1])
        await hub.refresh_device()
        hub.player.command.assert_awaited_once_with('pause')
        current.update(outputs=outputs)
        await hub.refresh_device()
        assert hub.device.audio_set.await_count == 2
        # The same persisted preferences restore through a new Hub instance.
        restarted = Hub(tmp_path)
        assert restarted.store.value.mute is True
        assert restarted.store.value.volume == 23
    asyncio.run(scenario())


def test_local_queue_boundaries_exposed_without_enabling_radio_queue(client):
    hub = app.state.hub
    hub.queue = [{'path': 'a'}, {'path': 'b'}]
    hub.queue_index = 0
    hub.player.status = AsyncMock(return_value={'kind': 'audio', 'url': '/a', 'state': 'playing'})
    status = client.get('/api/state').json()['player']
    assert status['canNext'] is True and status['canPrevious'] is False
    hub.queue_index = 1
    status = client.get('/api/state').json()['player']
    assert status['canPrevious'] is True and status['canNext'] is False
    hub.player.status = AsyncMock(return_value={'kind': 'radio', 'url': 'https://radio.example', 'state': 'playing'})
    status = client.get('/api/state').json()['player']
    assert status['canPrevious'] is False and status['canNext'] is False
