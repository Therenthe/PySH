"""The LAN bridge is exercised independently of real hardware or user data."""
from http.client import HTTPSConnection
import hashlib
import json
from pathlib import Path
import shutil
import ssl
import subprocess
import threading
from unittest.mock import Mock

import pytest

from services.remote import gateway
from services.remote.gateway import DeviceStore, LanServer, LoopbackProxy, RateLimiter, RemoteError, certificate_pin, lan_address


@pytest.mark.parametrize("address", ["10.0.0.4", "172.16.4.2", "172.31.255.1", "192.168.1.50", "fd12:3456::2", "fe80::1"])
def test_lan_addresses(address):
    assert lan_address(address)


@pytest.mark.parametrize("address", ["0.0.0.0", "::", "127.0.0.1", "::1", "8.8.8.8", "1.1.1.1", "192.0.2.1", "203.0.113.1", "100.64.1.2", "172.32.0.1", "::ffff:192.168.1.2", "pysh.local", "https://192.168.1.1"])
def test_non_lan_addresses_refused(address):
    assert not lan_address(address)
    with pytest.raises(ValueError):
        LanServer(address, 8766, None, None)


def test_pairing_persistent_phone_and_immediate_revocation(tmp_path):
    store = DeviceStore(tmp_path)
    code = store.begin_pairing(now=1000)
    assert len(code) == 8 and code.isdigit()
    assert code not in store.path.read_text()
    phone = store.pair({"code": code, "name": "Telefon"}, now=1001)
    assert phone["token"] not in store.path.read_text()
    restarted = DeviceStore(tmp_path)
    assert restarted.authenticate("Bearer " + phone["token"])
    assert not restarted.authenticate(phone["token"])
    assert not restarted.authenticate("Bearer incorrect")
    with pytest.raises(RemoteError) as failure:
        restarted.pair({"code": code, "name": "Another"}, now=1002)
    assert failure.value.code == "pairing_expired"
    assert restarted.revoke(phone["deviceId"])
    assert not store.authenticate("Bearer " + phone["token"])


def test_pair_code_has_bounded_attempts_across_restarts(tmp_path):
    code = DeviceStore(tmp_path).begin_pairing(now=1000)
    invalid = "00000000" if code != "00000000" else "11111111"
    for _ in range(5):
        with pytest.raises(RemoteError) as failure:
            DeviceStore(tmp_path).pair({"code": invalid, "name": "Phone"}, now=1001)
        assert failure.value.code == "pairing_invalid"
    with pytest.raises(RemoteError) as failure:
        DeviceStore(tmp_path).pair({"code": code, "name": "Phone"}, now=1002)
    assert failure.value.code == "pairing_expired"


def test_pairing_expiration_replacement_and_strict_body(tmp_path):
    store = DeviceStore(tmp_path)
    code = store.begin_pairing(now=1000)
    with pytest.raises(RemoteError) as failure:
        store.pair({"code": code, "name": "Phone"}, now=1300)
    assert failure.value.code == "pairing_expired"
    new = store.begin_pairing(now=1400)
    for body in ({"code": new, "name": "Phone", "admin": True}, {"code": 12345678, "name": "Phone"}, {"code": new, "name": "\n"}, {"code": new, "name": ""}):
        with pytest.raises(RemoteError) as failure:
            store.pair(body, now=1401)
        assert failure.value.code == "invalid_request"
    assert store.pair({"code": new, "name": "Phone"}, now=1401)["name"] == "Phone"


def test_pairing_concurrent_code_consumed_once(tmp_path):
    store = DeviceStore(tmp_path)
    code = store.begin_pairing()
    outcomes = []
    def attempt():
        try:
            outcomes.append(store.pair({"code": code, "name": "Phone"}))
        except RemoteError as error:
            outcomes.append(error.code)
    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sum(isinstance(value, dict) for value in outcomes) == 1
    assert len(store.read()["devices"]) == 1


def test_rate_limit_expiry_and_peer_table_bound():
    limiter = RateLimiter(limit=2, window=60, max_peers=2)
    assert limiter.allow("a", 100)
    assert limiter.allow("a", 101)
    assert not limiter.allow("a", 102)
    assert limiter.allow("b", 103)
    assert not limiter.allow("c", 104)
    assert limiter.allow("c", 164)


def test_proxy_fixed_loopback_and_no_phone_headers(monkeypatch):
    response = Mock(status=200)
    response.read.return_value = b'{"ok":true}'
    response.getheader.return_value = "application/json"
    connection = Mock()
    connection.getresponse.return_value = response
    factory = Mock(return_value=connection)
    monkeypatch.setattr(gateway, "HTTPConnection", factory)
    proxy = LoopbackProxy()
    proxy.token = "local-session-only"
    assert proxy.forward("POST", "/api/audio", b'{"volume":40}') == (200, b'{"ok":true}')
    factory.assert_called_once_with("127.0.0.1", 8765, timeout=30)
    headers = connection.request.call_args.kwargs["headers"]
    assert headers["x-hub-token"] == "local-session-only"
    assert headers["Origin"] == "http://127.0.0.1:8765"
    assert "Authorization" not in headers


def test_session_restart_only_retries_boundary_denial():
    proxy = LoopbackProxy()
    proxy.token = "old-session"
    proxy.request = Mock(side_effect=[
        (403, b'{"error":"session_expired"}'),
        (200, b'{"token":"new-session-of-valid-length"}'),
        (200, b'{"ok":true}'),
    ])
    assert proxy.forward("POST", "/api/player", b"{}") == (200, b'{"ok":true}')
    assert proxy.token == "new-session-of-valid-length"
    assert proxy.request.call_count == 3
    proxy.request = Mock(return_value=(409, b'{"error":"operation_failed"}'))
    assert proxy.forward("POST", "/api/player", b"{}")[0] == 409
    assert proxy.request.call_count == 1


def test_pending_bluetooth_pair_allows_prompt_reply_concurrently():
    proxy = LoopbackProxy()
    proxy.token = "active-session"
    waiting, replied = threading.Event(), threading.Event()
    outcomes = []
    def upstream(method, path, body=b"", session_token=None):
        assert session_token == "active-session"
        if path == "/api/bluetooth/action":
            waiting.set()
            return (200, b'{"paired":true}') if replied.wait(timeout=2) else (409, b'{"error":"prompt_timeout"}')
        assert path == "/api/bluetooth/reply"
        replied.set()
        return 200, b'{"accepted":true}'
    proxy.request = upstream
    pending = threading.Thread(target=lambda: outcomes.append(proxy.forward("POST", "/api/bluetooth/action", b"{}")))
    pending.start()
    try:
        assert waiting.wait(timeout=1)
        assert proxy.forward("POST", "/api/bluetooth/reply", b"{}") == (200, b'{"accepted":true}')
    finally:
        replied.set()
        pending.join(timeout=3)
    assert outcomes == [(200, b'{"paired":true}')]


@pytest.mark.parametrize("status,payload,content_type,error", [
    (302, b"", "application/json", "upstream_redirect_blocked"),
    (200, b"<html>", "text/html", "upstream_invalid_response"),
    (200, b"x" * (gateway.MAX_RESPONSE + 1), "application/json", "upstream_response_too_large"),
], ids=["redirect", "html", "oversized"])
def test_upstream_boundaries(monkeypatch, status, payload, content_type, error):
    response = Mock(status=status)
    response.read.return_value = payload
    response.getheader.return_value = content_type
    connection = Mock()
    connection.getresponse.return_value = response
    monkeypatch.setattr(gateway, "HTTPConnection", Mock(return_value=connection))
    with pytest.raises(RemoteError) as failure:
        LoopbackProxy().request("GET", "/api/state")
    assert failure.value.code == error


@pytest.fixture
def tls_gateway(tmp_path, monkeypatch):
    openssl = shutil.which("openssl")
    if not openssl:
        candidate = Path("C:/Program Files/Git/usr/bin/openssl.exe")
        if candidate.exists():
            openssl = str(candidate)
    if not openssl:
        pytest.skip("OpenSSL needed for real TLS fixture")
    cert, key = tmp_path / "certificate.pem", tmp_path / "private-key.pem"
    subprocess.run([openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1", "-subj", "/CN=fixture", "-keyout", str(key), "-out", str(cert)], check=True, capture_output=True)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(cert, key)
    original = gateway.lan_address
    # Test-only loopback listener. Production policy has independent refusal tests.
    monkeypatch.setattr(gateway, "lan_address", lambda value: value == "127.0.0.1" or original(value))
    store = DeviceStore(tmp_path)
    proxy = Mock()
    proxy.forward.return_value = (200, b'{"preferences":{"language":"ro"}}')
    server = LanServer("127.0.0.1", 0, context, store, proxy)
    server.expected_host = f"127.0.0.1:{server.server_address[1]}"
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    worker.start()
    def request(method, path, body=None, headers=None):
        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_context.check_hostname = False
        client_context.verify_mode = ssl.CERT_NONE
        connection = HTTPSConnection("127.0.0.1", server.server_address[1], context=client_context, timeout=5)
        connection.connect()
        # Match Android's complete-certificate DER SHA256 pin format.
        assert hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest() == certificate_pin(cert)
        values = {"Host": server.expected_host, **(headers or {})}
        payload = json.dumps(body).encode() if body is not None else None
        if payload is not None:
            values = {"Content-Type": "application/json", **values}
        connection.request(method, path, body=payload, headers=values)
        response = connection.getresponse()
        data = json.loads(response.read())
        status = response.status
        connection.close()
        return status, data
    yield server, store, request
    server.shutdown()
    server.server_close()
    worker.join(timeout=2)


def test_real_https_health_pair_authenticated_api_and_revocation(tls_gateway):
    server, store, request = tls_gateway
    assert request("GET", "/remote/health") == (200, {"service": "pysh-remote", "version": 1})
    assert request("GET", "/api/state")[0] == 401
    code = store.begin_pairing()
    status, phone = request("POST", "/remote/pair", {"code": code, "name": "Telefon"})
    assert status == 200
    headers = {"Authorization": "Bearer " + phone["token"]}
    assert request("GET", "/api/state", headers=headers)[0] == 200
    assert request("PATCH", "/api/preferences", {"language": "en"}, headers)[0] == 200
    server.proxy.forward.assert_called_with("PATCH", "/api/preferences", b'{"language": "en"}')
    assert request("GET", "/api/external/preparation?job=fixture", headers=headers)[0] == 200
    for method, path in (("GET", "/api/session"), ("GET", "/api/media/file?path=a"), ("POST", "/api/external/report"), ("GET", "/"), ("PUT", "/api/preferences")):
        assert request(method, path, headers=headers)[0] == 404
    store.revoke(phone["deviceId"])
    assert request("GET", "/api/state", headers=headers)[0] == 401


@pytest.mark.parametrize("path", ["//public.example/api/state", "/api/%73tate", "/api/../state", "http://public.example/api/state", "/api/state#fragment"])
def test_https_rejects_path_confusion(tls_gateway, path):
    _, _, request = tls_gateway
    assert request("GET", path)[0] == 400


def test_https_browser_origin_host_and_body_limits(tls_gateway):
    _, _, request = tls_gateway
    assert request("GET", "/remote/health", headers={"Origin": "https://evil.example"})[0] == 403
    assert request("GET", "/remote/health", headers={"Host": "evil.example"})[0] == 403
    assert request("POST", "/remote/pair", {"code": "12345678", "name": "x"}, {"Content-Length": "65537"})[0] == 413
    assert request("POST", "/remote/pair", {"code": "12345678", "name": "x"}, {"Transfer-Encoding": "chunked"})[0] == 400


def test_https_rate_limiting(tls_gateway):
    server, _, request = tls_gateway
    server.limiter = RateLimiter(limit=1)
    assert request("GET", "/remote/health")[0] == 200
    assert request("GET", "/remote/health") == (429, {"error": "rate_limited"})


def test_https_phone_can_revoke_only_its_own_token(tls_gateway):
    _, store, request = tls_gateway
    code = store.begin_pairing()
    first = store.pair({"code": code, "name": "First"})
    code = store.begin_pairing()
    second = store.pair({"code": code, "name": "Second"})
    headers = {"Authorization": "Bearer " + first["token"]}
    assert request("POST", "/remote/revoke-self")[0] == 401
    assert request("POST", "/remote/revoke-self", {"deviceId": second["deviceId"]}, headers)[0] == 400
    assert store.authenticate("Bearer " + second["token"])
    assert request("POST", "/remote/revoke-self", {}, headers) == (200, {"revoked": True})
    assert request("GET", "/api/state", headers=headers)[0] == 401
    assert store.authenticate("Bearer " + second["token"])


def test_presence_only_authenticated_current_phone_and_state_poll(tls_gateway):
    server, store, request = tls_gateway
    phone = store.pair({'code':store.begin_pairing(), 'name':'Phone'})
    server.proxy.forward.assert_not_called()  # Pairing is not active presence.
    assert request('POST','/remote/heartbeat',{})[0] == 401
    headers = {'Authorization':'Bearer ' + phone['token']}
    assert request('POST','/remote/heartbeat',{'deviceId':'forged'},headers)[0] == 400
    assert request('POST','/api/remote/presence',{},headers)[0] == 404
    assert request('POST','/remote/heartbeat',{},headers)[0] == 200
    args = server.proxy.forward.call_args.args
    assert args[:2] == ('POST','/api/remote/presence')
    assert json.loads(args[2]) == {'deviceId':phone['deviceId'],'active':True}
    assert request('DELETE','/remote/heartbeat',headers=headers)[0] == 200
    assert json.loads(server.proxy.forward.call_args.args[2])['active'] is False
    server.proxy.forward.reset_mock()
    assert request('GET','/api/state',headers=headers)[0] == 200
    assert json.loads(server.proxy.forward.call_args_list[0].args[2]) == {'deviceId':phone['deviceId'],'active':True}


def test_proxy_allows_bounded_binary_only_on_known_artwork_route(monkeypatch):
    response = Mock(status=200)
    response.read.return_value = b'\x89PNG\r\n\x1a\nfixture'
    response.getheader.return_value = 'image/png'
    connection = Mock()
    connection.getresponse.return_value = response
    monkeypatch.setattr(gateway,'HTTPConnection',Mock(return_value=connection))
    status, payload = LoopbackProxy().forward('GET','/api/radio/artwork?station=current',b'')
    assert status == 200 and payload.mime == 'image/png'
    with pytest.raises(RemoteError):
        LoopbackProxy().forward('GET','/api/state',b'')
    response.read.return_value = b'x' * (256 * 1024 + 1)
    with pytest.raises(RemoteError) as failure:
        LoopbackProxy().forward('GET','/api/radio/artwork?station=current',b'')
    assert failure.value.code == 'upstream_response_too_large'
