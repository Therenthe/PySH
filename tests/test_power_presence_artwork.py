import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from services.backend.app import app, Hub
from services.backend.artwork import Artwork, MAX_ARTWORK
from services.backend.content import ContentError
from services.backend.device import DeviceError
from services.backend.power import Backlight, PowerController, RemotePresence
from services.backend.preferences import PreferenceStore


class BacklightFixture:
    def __init__(self):
        self.value = 100
        self.failure = False
    async def status(self):
        return {'available': True, 'value': self.value}
    async def set(self, value):
        if self.failure:
            raise DeviceError('brightness_permission_denied')
        self.value = value
        return await self.status()


def controller(tmp_path, now='2026-10-13T18:00:00+00:00'):
    clock = {'monotonic': 100, 'wall': datetime.fromisoformat(now)}
    hub = SimpleNamespace(store=PreferenceStore(tmp_path), device=None, media_lock=asyncio.Lock(),
                          player=SimpleNamespace(status=AsyncMock(return_value={'state': 'playing'}), command=AsyncMock(return_value={'state': 'paused'})),
                          visualizer=SimpleNamespace(close=AsyncMock()), external=SimpleNamespace(close=AsyncMock()), cache_playback=lambda value:value)
    backlight = BacklightFixture()
    power = PowerController(hub, backlight, lambda:clock['monotonic'], lambda:clock['wall'])
    return hub, power, backlight, clock


def test_standby_pauses_closes_and_restores_desired_brightness(tmp_path):
    hub, power, light, _ = controller(tmp_path)
    hub.store.update({'screenBrightness': 63})
    result = asyncio.run(power.change(True))
    assert result['standby'] and light.value == 0
    hub.player.command.assert_awaited_once_with('pause')
    hub.external.close.assert_awaited_once()
    assert hub.store.value.screenBrightness == 63
    asyncio.run(power.brightness(42))
    assert light.value == 0 and hub.store.value.screenBrightness == 42
    assert not asyncio.run(power.change(False))['standby'] and light.value == 42
    assert hub.player.command.await_count == 1  # Wake never resumes audio implicitly.
    assert not PowerController(hub, light).standby


def test_pause_failure_does_not_claim_standby_or_dim(tmp_path):
    hub, power, light, _ = controller(tmp_path)
    hub.player.command.side_effect = DeviceError('audio_unavailable')
    with pytest.raises(DeviceError):
        asyncio.run(power.change(True))
    assert not power.standby and light.value == 100


def test_backlight_failure_is_honest_and_wake_remains_available(tmp_path):
    hub, power, light, _ = controller(tmp_path)
    light.failure = True
    before = hub.store.value.screenBrightness
    with pytest.raises(DeviceError):
        asyncio.run(power.brightness(23))
    assert hub.store.value.screenBrightness == before
    state = asyncio.run(power.change(True))
    assert state['standby'] and state['error'] == 'brightness_permission_denied'
    assert not asyncio.run(power.change(False))['standby']


def test_timer_is_monotonic_wall_clock_jump_and_cancel(tmp_path):
    _, power, _, clock = controller(tmp_path)
    asyncio.run(power.timer(2))
    clock['wall'] = datetime(2040, 1, 1, tzinfo=timezone.utc)
    clock['monotonic'] += 119
    asyncio.run(power.tick())
    assert not power.standby
    assert asyncio.run(power.snapshot())['timer']['remainingSeconds'] == 1
    clock['monotonic'] += 1
    asyncio.run(power.tick())
    assert power.standby and power.deadline is None
    asyncio.run(power.change(False))
    asyncio.run(power.timer(1))
    asyncio.run(power.timer(0))
    clock['monotonic'] += 60
    asyncio.run(power.tick())
    assert not power.standby


def test_timer_cancellation_invalidates_due_tick_waiting_for_media(tmp_path):
    _, power, _, clock = controller(tmp_path)
    async def scenario():
        await power.timer(1)
        clock['monotonic'] += 60
        await power.hub.media_lock.acquire()
        due = asyncio.create_task(power.tick())
        await asyncio.sleep(0)
        await power.timer(0)
        power.hub.media_lock.release()
        await due
        assert not power.standby and power.deadline is None
    asyncio.run(scenario())


def test_brightness_pending_write_commits_whole_patch_before_standby(tmp_path):
    hub, power, light, _ = controller(tmp_path)
    async def scenario():
        entered, finish = asyncio.Event(), asyncio.Event()
        original = light.set
        async def pending(value):
            if value == 41:
                entered.set()
                await finish.wait()
            return await original(value)
        light.set = pending
        save = asyncio.create_task(power.update_preferences({'screenBrightness':41,'dailyStandbyTime':'22:22'}))
        await entered.wait()
        sleep = asyncio.create_task(power.change(True))
        await asyncio.sleep(0)
        assert hub.store.value.screenBrightness == 100
        finish.set()
        await save
        await sleep
        assert hub.store.value.screenBrightness == 41 and hub.store.value.dailyStandbyTime == '22:22'
        assert light.value == 0 and power.standby
        await power.change(False)
        assert light.value == 41
    asyncio.run(scenario())


@pytest.mark.parametrize('start,end', [
    ('2026-03-29T00:59:00+00:00', '2026-03-29T01:01:00+00:00'),
    ('2026-10-25T00:29:00+00:00', '2026-10-25T00:31:00+00:00'),
])
def test_daily_dst_gap_and_repeat_once_per_date(tmp_path, start, end):
    hub, power, _, clock = controller(tmp_path, start)
    hub.store.update({'dailyStandbyEnabled': True, 'dailyStandbyTime': '03:30'})
    asyncio.run(power.tick())
    clock['wall'] = datetime.fromisoformat(end)
    asyncio.run(power.tick())
    assert power.standby
    asyncio.run(power.change(False))
    clock['wall'] = datetime.fromisoformat('2026-10-25T01:31:00+00:00') if '10-25' in end else clock['wall']
    asyncio.run(power.tick())
    assert not power.standby


def test_restart_after_daily_time_stays_awake(tmp_path):
    hub, power, _, _ = controller(tmp_path, '2026-10-13T22:01:00+00:00')
    hub.store.update({'dailyStandbyEnabled': True, 'dailyStandbyTime': '23:00'})
    asyncio.run(power.tick())
    assert not power.standby


def test_disabled_schedule_and_manual_wake_do_not_consume_later_enabled_event(tmp_path):
    hub, power, _, clock = controller(tmp_path, '2026-10-13T20:58:00+00:00')
    # 23:58 local: a disabled default 23:00 event did not happen.
    asyncio.run(power.tick())
    asyncio.run(power.change(False))
    asyncio.run(power.update_preferences({'dailyStandbyEnabled': True, 'dailyStandbyTime': '23:59'}))
    asyncio.run(power.tick())
    assert not power.standby
    clock['wall'] = datetime.fromisoformat('2026-10-13T20:59:00+00:00')
    asyncio.run(power.tick())
    assert power.standby


def test_presence_ttl_counts_current_sessions_and_revocation():
    clock = [100]
    presence = RemotePresence(lambda:clock[0])
    assert presence.snapshot() == {'connected': False, 'count': 0}
    presence.update('phone-a', True)
    presence.update('phone-a', True)
    presence.update('phone-b', True)
    assert presence.snapshot() == {'connected': True, 'count': 2}
    presence.update('phone-a', False)
    assert presence.snapshot()['count'] == 1
    clock[0] += 15
    assert presence.snapshot() == {'connected': False, 'count': 0}


def test_backlight_reads_real_files_and_uses_only_active_user_seat(tmp_path, monkeypatch):
    from pathlib import Path
    import services.backend.power as module
    target = tmp_path / '10-0045'
    target.mkdir()
    (target / 'max_brightness').write_text('255')
    (target / 'actual_brightness').write_text('255')
    (target / 'brightness').write_text('255')
    monkeypatch.setattr(module.platform, 'system', lambda:'Linux')
    monkeypatch.setattr(module.os, 'getuid', lambda:1000, raising=False)
    original = Path.write_text
    def protected_write(path, value, *args, **kwargs):
        if path == target / 'brightness':
            raise PermissionError()
        return original(path, value, *args, **kwargs)
    monkeypatch.setattr(Path, 'write_text', protected_write)
    manager = SimpleNamespace(call_list_sessions=AsyncMock(return_value=[('1',1000,'pysh','seat0','/active'), ('2',1000,'pysh','','/manager'), ('3',1001,'other','seat1','/other')]))
    async def brightness(subsystem, name, value):
        assert subsystem == 'backlight' and name == '10-0045'
        original(target / 'actual_brightness', str(value))
    session = SimpleNamespace(call_set_brightness=AsyncMock(side_effect=brightness))
    async def proxy(service, path, interface):
        return manager if path == '/org/freedesktop/login1' else session
    device = SimpleNamespace(_proxy=AsyncMock(side_effect=proxy), _get=AsyncMock(return_value=True))
    adapter = Backlight(device, tmp_path)
    assert asyncio.run(adapter.status()) == {'available':True,'value':100}
    assert asyncio.run(adapter.set(25))['value'] == 25
    session.call_set_brightness.assert_awaited_once_with('backlight','10-0045',64)
    assert device._get.call_args.args[1] == '/active'
    assert asyncio.run(adapter.set(0))['value'] == 0
    assert (target / 'brightness').read_text() == '255'  # No permission mutation.


@pytest.fixture
def client(tmp_path):
    hub = Hub(tmp_path)
    hub.player = SimpleNamespace(status=AsyncMock(return_value={'state':'playing', 'kind':'radio', 'url':'https://stream.example/radio'}), command=AsyncMock(return_value={'state':'paused'}))
    hub.external.close = AsyncMock()
    hub.power.backlight = BacklightFixture()
    app.state.hub = hub
    return TestClient(app, base_url='http://127.0.0.1:8765')


def test_api_power_presence_requires_mutation_token(client):
    for path, body in [('/api/power', {'standby':True}), ('/api/power/timer', {'minutes':20}), ('/api/remote/presence', {'deviceId':'a'*36,'active':True})]:
        assert client.post(path, json=body).status_code == 403
    headers = {'x-hub-token': app.state.hub.token}
    assert client.post('/api/power/timer', headers=headers, json={'minutes':721}).status_code == 422
    assert client.post('/api/power', headers=headers, json={'standby':True}).json()['standby']
    assert client.post('/api/play', headers=headers, json={'source':'radio', 'url':'https://example.org'}).json()['error'] == 'standby_active'
    assert client.post('/api/player', headers=headers, json={'action':'resume'}).json()['error'] == 'standby_active'
    assert not client.post('/api/power', headers=headers, json={'standby':False}).json()['standby']
    assert client.post('/api/remote/presence', headers=headers, json={'deviceId':'a'*36,'active':True}).json()['count'] == 1
    state = client.get('/api/state').json()
    assert 'power' in state and state['remote'] == {'connected':True,'count':1}


def test_brightness_api_write_and_persistence_failure(client):
    headers = {'x-hub-token': app.state.hub.token}
    response = client.patch('/api/preferences', headers=headers, json={'screenBrightness':53,'dailyStandbyEnabled':True,'dailyStandbyTime':'22:15'})
    assert response.status_code == 200 and response.json()['screenBrightness'] == 53
    assert app.state.hub.power.backlight.value == 53
    app.state.hub.power.backlight.failure = True
    response = client.patch('/api/preferences', headers=headers, json={'screenBrightness':20})
    assert response.status_code == 409
    assert app.state.hub.store.value.screenBrightness == 53
    assert client.patch('/api/preferences', headers=headers, json={'screenBrightness':False}).status_code == 422


@pytest.mark.parametrize('url,address', [
    ('http://localhost/image.png','127.0.0.1'), ('https://private.example/a','192.168.1.1'),
    ('http://link.example/a','169.254.169.254'), ('https://v6.example/a','::1'),
    ('https://v6.example/a','fd00::1'), ('https://docs.example/a','192.0.2.1'),
    ('https://multicast.example/a','224.0.0.1'), ('https://multicast.example/a','ff02::1'),
])
def test_artwork_private_dns_ssrf_refused(monkeypatch, url, address):
    monkeypatch.setattr('services.backend.artwork.socket.getaddrinfo', lambda *args, **kwargs:[(2,1,6,'',(address,443))])
    factory = Mock()
    monkeypatch.setattr('services.backend.artwork.HTTPSConnection', factory)
    monkeypatch.setattr('services.backend.artwork.HTTPConnection', factory)
    with pytest.raises(ContentError):
        Artwork.fetch(url)
    factory.assert_not_called()


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'https://user:password@example.org/a', 'https://example.org:8765/a', 'https://example.org/a\nsecret'])
def test_artwork_url_protocol_and_credentials_refused(url):
    with pytest.raises(ContentError):
        Artwork.fetch(url)


@pytest.mark.parametrize('kind', ['redirect','oversize','svg','badmagic','mixed_dns'])
def test_artwork_bounded_image_and_no_redirect(monkeypatch, kind):
    addresses = [(2,1,6,'',('8.8.8.8',443))]
    if kind == 'mixed_dns':
        addresses += [(2,1,6,'',('10.0.0.1',443))]
    monkeypatch.setattr('services.backend.artwork.socket.getaddrinfo', lambda *args,**kwargs:addresses)
    response = Mock(status=302 if kind == 'redirect' else 200)
    response.getheader.return_value = 'image/svg+xml' if kind == 'svg' else 'image/png'
    response.read.return_value = b'\x89PNG\r\n\x1a\n' + b'x' * MAX_ARTWORK if kind == 'oversize' else b'html'
    connection = Mock()
    connection.getresponse.return_value = response
    monkeypatch.setattr('services.backend.artwork.HTTPSConnection', Mock(return_value=connection))
    with pytest.raises(ContentError):
        Artwork.fetch('https://logo.example/image.png')


def test_artwork_public_address_pinned_and_known_metadata_only(monkeypatch, client):
    monkeypatch.setattr('services.backend.artwork.socket.getaddrinfo', lambda *args,**kwargs:[(2,1,6,'',('8.8.8.8',443))])
    response = Mock(status=200)
    response.getheader.return_value = 'image/png'
    response.read.return_value = b'\x89PNG\r\n\x1a\nfixture'
    connection = Mock()
    connection.getresponse.return_value = response
    monkeypatch.setattr('services.backend.artwork.HTTPSConnection', Mock(return_value=connection))
    assert Artwork.fetch('https://logo.example/a')[1] == 'image/png'
    connect = Mock()
    monkeypatch.setattr('services.backend.artwork.socket.create_connection', connect)
    connection._create_connection(('logo.example',443),5)
    connect.assert_called_once_with(('8.8.8.8',443),5,None)
    assert client.get('/api/radio/artwork?station=https://evil.example/image').status_code == 404
    app.state.hub.store.update({'lastStation': {'uuid':'known','name':'Fixture','url':'https://stream.example/radio','favicon':'https://logo.example/a'}})
    app.state.hub.artwork.get = AsyncMock(return_value=(b'png','image/png'))
    result = client.get('/api/radio/artwork?station=current')
    assert result.status_code == 200 and result.headers['content-type'] == 'image/png'
    app.state.hub.artwork.get.assert_awaited_once_with('https://logo.example/a')


def test_current_artwork_uses_matching_favorite_then_known_homepage(client):
    hub = app.state.hub
    hub.store.update({'lastStation': {'uuid': 'last', 'name': 'Fixture', 'url': 'https://stream.example/radio'},
                      'favorites': [{'uuid': 'favorite', 'name': 'Fixture', 'url': 'https://stream.example/radio', 'favicon': 'https://logo.example/a', 'homepage': 'https://radio.example/'}]})
    hub.artwork.get = AsyncMock(return_value=(b'png', 'image/png'))
    assert client.get('/api/radio/artwork?station=current').status_code == 200
    hub.artwork.get.assert_awaited_once_with('https://logo.example/a')
    hub.artwork.get.side_effect = ContentError('artwork_unavailable')
    hub.artwork.homepage = AsyncMock(return_value=(b'png', 'image/png'))
    assert client.get('/api/radio/artwork?station=current').status_code == 200
    hub.artwork.homepage.assert_awaited_once_with('https://radio.example/')
    assert hub.store.value.lastStation.favicon == ''  # Reading artwork preserves preferences.


def test_homepage_prefers_known_png_icon_without_fetching_other_page_resources(monkeypatch):
    monkeypatch.setattr(Artwork, 'request', Mock(return_value=(b'<script src="secret"></script><link rel="icon" href="/old.ico"><link rel="apple-touch-icon" href="/brand.png">', 'text/html', 'https://radio.example/')))
    fetch = Mock(return_value=(b'png', 'image/png'))
    monkeypatch.setattr(Artwork, 'fetch', fetch)
    assert Artwork.fetch_homepage('https://radio.example/') == (b'png', 'image/png')
    assert fetch.call_args.args == ('https://radio.example/brand.png',)
    assert fetch.call_count == 1


@pytest.mark.parametrize('private', [False, True])
def test_artwork_redirect_revalidates_public_dns_without_forwarding_credentials(monkeypatch, private):
    addresses = [[(2, 1, 6, '', ('8.8.8.8', 443))], [(2, 1, 6, '', ('10.0.0.1' if private else '8.8.4.4', 443))]]
    monkeypatch.setattr('services.backend.artwork.socket.getaddrinfo', Mock(side_effect=addresses))
    redirect = Mock(status=302)
    redirect.getheader.side_effect = lambda name, default='': 'https://cdn.example/icon.png' if name == 'Location' else ''
    image = Mock(status=200)
    image.getheader.return_value = 'image/png'
    image.read.return_value = b'\x89PNG\r\n\x1a\nfixture'
    first, second = Mock(), Mock()
    first.getresponse.return_value = redirect
    second.getresponse.return_value = image
    connections = Mock(side_effect=[first, second])
    monkeypatch.setattr('services.backend.artwork.HTTPSConnection', connections)
    if private:
        with pytest.raises(ContentError): Artwork.fetch('https://radio.example/icon.png')
        assert connections.call_count == 1
    else:
        assert Artwork.fetch('https://radio.example/icon.png')[1] == 'image/png'
        assert connections.call_count == 2
        assert 'Authorization' not in second.request.call_args.kwargs['headers']
    first.close.assert_called_once()


def test_disabling_daily_schedule_invalidates_pending_transition(tmp_path):
    hub, power, _, clock = controller(tmp_path, '2026-10-13T19:59:00+00:00')
    hub.store.update({'dailyStandbyEnabled':True,'dailyStandbyTime':'23:00'})
    async def scenario():
        await power.tick()
        clock['wall'] = datetime.fromisoformat('2026-10-13T20:00:00+00:00')
        await hub.media_lock.acquire()
        pending = asyncio.create_task(power.tick())
        await asyncio.sleep(0)
        await power.update_preferences({'dailyStandbyEnabled':False})
        hub.media_lock.release()
        await pending
        assert not power.standby
    asyncio.run(scenario())


def test_brightness_disk_failure_restores_previous_hardware_level(tmp_path):
    hub, power, light, _ = controller(tmp_path)
    hub.store.update = Mock(side_effect=OSError('fixture read-only'))
    with pytest.raises(DeviceError) as failure:
        asyncio.run(power.update_preferences({'screenBrightness':20}))
    assert failure.value.code == 'preferences_write_failed'
    assert light.value == 100 and hub.store.value.screenBrightness == 100
