"""Approval, ciphertext, discovery and loopback boundary properties."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from services.remote.gateway import DeviceStore, RemoteError, ROUTES, validate_public_key
from services.remote.discovery import private_interface
from services.backend.remote_control import AndroidControl
from services.backend.app import Hub, app
from test_remote_gateway import tls_gateway


@pytest.fixture(scope='module')
def phone_key(tmp_path_factory):
    executable = shutil.which('openssl') or 'C:/Program Files/Git/usr/bin/openssl.exe'
    if not Path(executable).is_file() and not shutil.which(executable):
        pytest.skip('OpenSSL unavailable')
    directory = Path(__file__).parents[1] / '.runtime' / 'test-data' / ('rsa-' + str(os.getpid()))
    directory.mkdir(parents=True, exist_ok=True)
    private = directory / 'phone.pem'
    subprocess.run([executable, 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:3072', '-out', str(private)], check=True, capture_output=True)
    public = subprocess.run([executable, 'pkey', '-in', str(private), '-pubout', '-outform', 'DER'], check=True, capture_output=True).stdout
    return executable, private, base64.b64encode(public).decode()


@pytest.fixture
def openssl_path(phone_key, monkeypatch):
    monkeypatch.setenv('PATH', str(Path(phone_key[0]).parent) + os.pathsep + os.environ['PATH'])
    return phone_key


def poll_body(request):
    return {k: request[k] for k in ('requestId', 'requestSecret')}


def test_explicit_approval_encrypts_token_bound_to_actual_hub_and_cert(tmp_path, openssl_path):
    executable, private, public = openssl_path
    store = DeviceStore(tmp_path)
    request = store.request_pair({'name': 'Samsung Note10', 'publicKey': public}, 'a' * 64, now=100)
    assert store.read()['devices'] == []
    assert request['requestSecret'] not in store.path.read_text()
    assert store.pair_status(poll_body(request), now=101) == {'status': 'pending'}
    store.approve(request['requestId'], True, now=102)
    status = store.pair_status(poll_body(request), now=103)
    assert status['status'] == 'approved' and 'token' not in status
    cipher = base64.b64decode(status['encryptedResult'])
    plaintext = subprocess.run([executable, 'pkeyutl', '-decrypt', '-inkey', str(private), '-pkeyopt', 'rsa_padding_mode:oaep', '-pkeyopt', 'rsa_oaep_md:sha256', '-pkeyopt', 'rsa_mgf1_md:sha256'], input=cipher, check=True, capture_output=True).stdout
    credentials = json.loads(plaintext)
    assert credentials['hubId'] == store.hub_id()
    assert credentials['certificateSha256'] == 'a' * 64
    assert store.authenticate('Bearer ' + credentials['token'])
    assert credentials['token'] not in store.path.read_text()
    with pytest.raises(RemoteError):
        store.approve(request['requestId'], True, now=104)
    assert len(store.read()['devices']) == 1
    assert store.pair_status(poll_body(request), cancel=True, now=105) == {'status': 'cancelled'}
    assert not store.authenticate('Bearer ' + credentials['token'])


def test_denial_expiry_cancel_and_disable_never_issue_credentials(tmp_path, openssl_path):
    store = DeviceStore(tmp_path)
    first = store.request_pair({'name': 'Phone', 'publicKey': openssl_path[2]}, 'a' * 64, now=100)
    store.approve(first['requestId'], False, now=101)
    assert store.pair_status(poll_body(first), now=102) == {'status': 'denied'}
    second = store.request_pair({'name': 'Phone', 'publicKey': openssl_path[2]}, 'a' * 64, now=110)
    assert store.pair_status(poll_body(second), now=230) == {'status': 'expired'}
    with pytest.raises(RemoteError):
        store.approve(second['requestId'], True, now=230)
    third = store.request_pair({'name': 'Phone', 'publicKey': openssl_path[2]}, 'a' * 64, now=240)
    store.set_enabled(False)
    with pytest.raises(RemoteError):
        store.approve(third['requestId'], True, now=241)
    with pytest.raises(RemoteError) as failure:
        store.request_pair({'name': 'Phone', 'publicKey': openssl_path[2]}, 'a' * 64, now=242)
    assert failure.value.code == 'control_disabled'
    assert store.read()['devices'] == []


def test_queue_bounded_and_unknown_poll_secret_denied(tmp_path, openssl_path):
    store = DeviceStore(tmp_path)
    for _ in range(4):
        request = store.request_pair({'name': 'Phone', 'publicKey': openssl_path[2]}, 'a' * 64, now=100)
    with pytest.raises(RemoteError) as failure:
        store.request_pair({'name': 'Phone', 'publicKey': openssl_path[2]}, 'a' * 64, now=101)
    assert failure.value.code == 'pairing_busy'
    wrong = {**poll_body(request), 'requestSecret': 'b' * 43}
    with pytest.raises(RemoteError):
        store.pair_status(wrong, now=101)
    store.request_pair({'name': 'Phone', 'publicKey': openssl_path[2]}, 'a' * 64, now=220)
    assert len(store.read()['requests']) == 1


@pytest.mark.parametrize('body', [{'name':'Phone','publicKey':'abc'}, {'name':'Phone','publicKey':100}, {'name':'\u202eevil','publicKey':'abc'}, {'name':'Phone','publicKey':'abc','accept':True}, {'name':'','publicKey':'abc'}])
def test_untrusted_request_has_strict_schema(tmp_path, body):
    with pytest.raises(RemoteError):
        DeviceStore(tmp_path).request_pair(body, 'a' * 64)


def test_valid_rsa_key_rejects_trailing_der_and_ec(openssl_path):
    assert len(validate_public_key(openssl_path[2])) == 422
    with pytest.raises(RemoteError):
        validate_public_key(base64.b64encode(base64.b64decode(openssl_path[2]) + b'x').decode())


def test_current_private_interface_changes_without_wildcard_or_public(monkeypatch):
    from services.remote import discovery
    def command(arguments, **kwargs):
        if 'addr' in arguments:
            return SimpleNamespace(stdout=json.dumps([{'ifname':'eth0','ifindex':2,'flags':['UP'],'addr_info':[{'family':'inet','local':'192.168.100.200'}]}, {'ifname':'eth1','ifindex':3,'flags':['UP'],'addr_info':[{'family':'inet','local':'8.8.8.8'}]}]).encode())
        return SimpleNamespace(stdout=b'[{"dev":"eth0"}]')
    monkeypatch.setattr(discovery.subprocess, 'run', command)
    assert private_interface('192.168.100.127') == ('192.168.100.200', 2)


def test_control_marker_truth_and_preexisting_tokens_preserved(tmp_path):
    control = AndroidControl(tmp_path)
    assert not control.snapshot()['available']
    control.directory.mkdir()
    (control.directory / 'config.json').write_text('{}')
    old = control.devices.pair({'code': control.devices.begin_pairing(), 'name':'Old phone'})
    (control.directory / 'runtime.json').write_text(json.dumps({'ready':True,'discovery':True,'updated':time.time()}))
    assert control.snapshot()['available']
    control.enable(False)
    assert control.devices.authenticate('Bearer ' + old['token'])
    assert not control.snapshot()['enabled']
    control.enable(True)
    assert control.snapshot()['enabled']
    (control.directory / 'runtime.json').write_text(json.dumps({'ready':True,'updated':time.time()-20}))
    assert not control.snapshot()['available']
    serialized = json.dumps(control.snapshot())
    assert old['token'] not in serialized and 'hash' not in serialized


def test_physical_mutations_not_exposed_on_lan_allowlist(tmp_path):
    for method, path in (('PATCH','/api/android-control'), ('POST','/api/android-control/pairing'), ('DELETE','/api/android-control/devices/a')):
        assert path not in ROUTES.get(method, set())
    hub = Hub(tmp_path)
    app.state.hub = hub
    client = TestClient(app, base_url='http://127.0.0.1:8765')
    body = {'requestId':'b853877d-d21c-4ce2-afdb-4d52e6e6b6ca','accept':True}
    assert client.post('/api/android-control/pairing', json=body).status_code == 403
    assert client.post('/api/android-control/pairing', headers={'X-Hub-Token':hub.token,'Origin':'https://evil.example'}, json=body).status_code == 403
    assert client.patch('/api/android-control', headers={'X-Hub-Token':hub.token},json={'enabled':'true'}).status_code == 422
    assert client.patch('/api/android-control', headers={'X-Hub-Token':hub.token},json={'enabled':True}).json()['error'] == 'control_unavailable'


def test_real_https_pairing_requests_need_physical_approval_and_secret(tls_gateway, openssl_path):
    server, store, request = tls_gateway
    server.pin = 'a' * 64
    identity = request('GET', '/remote/identity')[1]
    assert identity['protocol'] == 2 and identity['certificateSha256'] == server.pin
    status, pending = request('POST', '/remote/pair/request', {'name':'New phone','publicKey':openssl_path[2]})
    assert status == 200 and len(pending['requestSecret']) == 43
    assert request('POST', '/remote/pair/status', poll_body(pending)) == (200, {'status':'pending'})
    assert request('POST', '/api/android-control/pairing', {'requestId':pending['requestId'],'accept':True})[0] == 401
    assert not store.read()['devices']
    store.approve(pending['requestId'], True)
    status, approved = request('POST', '/remote/pair/status', poll_body(pending))
    assert status == 200 and approved['status'] == 'approved' and 'token' not in approved
    assert request('POST', '/remote/pair/cancel', poll_body(pending)) == (200, {'status':'cancelled'})
    assert store.read()['devices'] == []
    server.proxy.forward.assert_not_called()


def test_disabled_control_refuses_old_token_and_new_pair_but_identity_reports(tls_gateway, openssl_path):
    server, store, request = tls_gateway
    phone = store.pair({'code':store.begin_pairing(),'name':'Old phone'})
    store.set_enabled(False)
    headers = {'Authorization':'Bearer ' + phone['token']}
    assert request('GET', '/api/state', headers=headers) == (503, {'error':'control_disabled'})
    assert request('POST', '/remote/pair/request', {'name':'New','publicKey':openssl_path[2]}) == (503, {'error':'control_disabled'})
    assert request('GET', '/remote/identity')[1]['enabled'] is False
    store.set_enabled(True)
    for method, path in (('PATCH','/api/android-control'), ('POST','/api/android-control/pairing'), ('DELETE','/api/android-control/devices/' + phone['deviceId'])):
        assert request(method, path, {}, headers)[0] == 404
    assert request('GET','/api/state',headers=headers)[0] == 200


def test_supervisor_rebinds_on_address_change_and_closes_when_disabled(tmp_path, monkeypatch):
    import asyncio
    from services.remote import discovery
    events, runtime = [], []
    interfaces = iter([('192.168.1.2', 2), ('192.168.1.3', 2), ('192.168.1.3', 2)])
    enabled = iter([True, True, False])
    devices = SimpleNamespace(hub_id=lambda:'a' * 36, enabled=lambda:next(enabled))
    class Server:
        def __init__(self, host, port, *args, **kwargs):
            self.host = host;events.append(('open',host))
        def serve_forever(self):pass
        def shutdown(self):events.append(('shutdown',self.host))
        def server_close(self):events.append(('close',self.host))
    class Thread:
        def __init__(self, **kwargs):pass
        def start(self):pass
        def join(self, *args):pass
        def is_alive(self):return True
    class Advert:
        def __init__(self):self.group=SimpleNamespace(call_get_state=AsyncMock(return_value=2))
        async def close(self):events.append(('unpublish',))
        async def publish(self,*args):events.append(('publish',args[0]))
    sleeps = 0
    async def sleep(seconds):
        nonlocal sleeps
        sleeps += 1
        if sleeps >= 3:raise asyncio.CancelledError()
    monkeypatch.setattr(discovery, 'private_interface', lambda preferred:next(interfaces))
    monkeypatch.setattr(discovery, 'LanServer', Server)
    monkeypatch.setattr(discovery.threading, 'Thread', Thread)
    monkeypatch.setattr(discovery, 'Advertisement', Advert)
    monkeypatch.setattr(discovery, 'atomic_json', lambda p, v:runtime.append(v))
    monkeypatch.setattr(asyncio, 'sleep', sleep)
    # Keep execution deterministic and do not replace asyncio's global worker thread.
    async def call(function,*args):return function(*args)
    monkeypatch.setattr(asyncio, 'to_thread', call)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(discovery.serve_dynamic({'host':'192.168.1.2','port':8766},tmp_path,None,devices,'a'*64))
    assert ('open','192.168.1.2') in events and ('open','192.168.1.3') in events
    assert events.index(('close','192.168.1.2')) < events.index(('open','192.168.1.3'))
    assert events.count(('close','192.168.1.3')) == 1
    assert runtime[2]['ready'] is True and runtime[2]['host'] == ''
    assert runtime[-1]['ready'] is False
