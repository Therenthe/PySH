"""A narrow native-phone bridge to the fixed loopback PySH API.

No browser CORS, URL forwarding, session export, remote shell or WAN listener.
Runtime dependencies are Python's standard library; certificate setup uses OpenSSL.
"""
from collections import defaultdict, deque
from contextlib import contextmanager
import hashlib
import hmac
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, HTTPServer
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
from socketserver import ThreadingMixIn
import ssl
import threading
import time
from urllib.parse import urlsplit
import uuid
import base64
import subprocess
import tempfile
import re
import unicodedata

MAX_BODY = 65536
MAX_RESPONSE = 2 * 1024 * 1024
LAN_NETWORKS = tuple(ipaddress.ip_network(item) for item in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7", "fe80::/10"))
ROUTES = {
    "GET": {"/api/state", "/api/radio", "/api/radio/artwork", "/api/power", "/api/media", "/api/geocode",
            "/api/audio/visualization", "/api/diagnostics", "/api/external/preparation"},
    "PATCH": {"/api/preferences"},
    "DELETE": {"/api/media"},
    "POST": {"/api/audio", "/api/power", "/api/power/timer", "/api/bluetooth/power", "/api/bluetooth/scan",
             "/api/bluetooth/action", "/api/bluetooth/reply", "/api/network/scan",
             "/api/network/connect", "/api/network/forget", "/api/weather/refresh",
             "/api/favorites", "/api/play", "/api/player", "/api/documentation",
             "/api/external", "/api/external/retry", "/api/external/cancel",
             "/api/exit", "/api/service/return"},
}


def lan_address(value):
    """Require actual RFC1918/ULA/link-local addresses, never wildcard/public."""
    try:
        address = ipaddress.ip_address(value)
        return any(address.version == net.version and address in net for net in LAN_NETWORKS)
    except ValueError:
        return False


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def certificate_pin(path):
    der = ssl.PEM_cert_to_DER_cert(Path(path).read_text(encoding="ascii"))
    return hashlib.sha256(der).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class RemoteError(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status


def validate_public_key(encoded):
    if not isinstance(encoded, str) or len(encoded) > 800:
        raise RemoteError('invalid_request')
    try:
        key = base64.b64decode(encoded, validate=True)
        if len(key) != 422:
            raise ValueError()
        result = subprocess.run(['openssl', 'pkey', '-pubin', '-inform', 'DER', '-text', '-noout'], input=key, capture_output=True, timeout=3, check=True)
        if b'Public-Key: (3072 bit)' not in result.stdout or b'Exponent: 65537 ' not in result.stdout:
            raise ValueError()
        canonical = subprocess.run(['openssl', 'pkey', '-pubin', '-inform', 'DER', '-outform', 'DER'], input=key, capture_output=True, timeout=3, check=True).stdout
        if canonical != key:
            raise ValueError()
        return key
    except (ValueError, OSError, subprocess.SubprocessError):
        raise RemoteError('invalid_public_key')


def encrypt_result(key, payload):
    plaintext = json.dumps(payload, separators=(',', ':')).encode()
    if len(plaintext) > 318:
        raise RemoteError('pairing_failed', 503)
    try:
        with tempfile.TemporaryDirectory(prefix='pysh-public-key-') as directory:
            path = Path(directory) / 'public.der'
            path.write_bytes(key)
            result = subprocess.run(['openssl', 'pkeyutl', '-encrypt', '-pubin', '-inkey', str(path), '-keyform', 'DER', '-pkeyopt', 'rsa_padding_mode:oaep', '-pkeyopt', 'rsa_oaep_md:sha256', '-pkeyopt', 'rsa_mgf1_md:sha256'], input=plaintext, capture_output=True, timeout=3, check=True)
            if len(result.stdout) != 384:
                raise ValueError()
            return base64.b64encode(result.stdout).decode()
    except (ValueError, OSError, subprocess.SubprocessError):
        raise RemoteError('pairing_failed', 503)


class DeviceStore:
    """Phone hashes only; one-time pairing never writes its plaintext code."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "devices.json"
        self.lock = threading.Lock()

    def read(self):
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"devices": []}

    def enabled(self):
        return self.read().get('enabled', True) is True

    def hub_id(self):
        with self.transaction() as state:
            state.setdefault('hubId', str(uuid.uuid4()))
            return state['hubId']

    def set_enabled(self, enabled):
        with self.transaction() as state:
            state['enabled'] = enabled
            if not enabled:
                state.pop('requests', None)
                state.pop('pairing', None)

    @staticmethod
    def prune(state, now):
        state['requests'] = [r for r in state.get('requests', []) if r['expires'] > now]

    def request_pair(self, body, pin, now=None):
        now = time.time() if now is None else now
        if not isinstance(body, dict) or set(body) != {'name', 'publicKey'}:
            raise RemoteError('invalid_request')
        name = body['name']
        if not isinstance(name, str) or not name.strip() or len(name) > 80 or any(unicodedata.category(c) in {'Cc', 'Cf', 'Zl', 'Zp'} for c in name):
            raise RemoteError('invalid_request')
        key = validate_public_key(body['publicKey'])
        with self.transaction() as state:
            if state.get('enabled', True) is not True:
                raise RemoteError('control_disabled', 503)
            self.prune(state, now)
            if len(state['requests']) >= 4:
                raise RemoteError('pairing_busy', 429)
            identity, secret = str(uuid.uuid4()), secrets.token_urlsafe(32)
            state.setdefault('hubId', str(uuid.uuid4()))
            state['requests'].append({'requestId': identity, 'secretHash': digest(secret), 'name': name.strip(), 'publicKey': base64.b64encode(key).decode(), 'certificateSha256': pin, 'expires': now + 120, 'status': 'pending'})
        return {'requestId': identity, 'requestSecret': secret, 'expiresIn': 120}

    def pair_status(self, body, cancel=False, now=None):
        now = time.time() if now is None else now
        if not isinstance(body, dict) or set(body) != {'requestId', 'requestSecret'} or not isinstance(body['requestSecret'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', body['requestSecret']) or not isinstance(body['requestId'], str):
            raise RemoteError('invalid_request')
        with self.transaction() as state:
            request = next((r for r in state.get('requests', []) if r['requestId'] == body['requestId']), None)
            if request is None or not hmac.compare_digest(request['secretHash'], digest(body['requestSecret'])):
                raise RemoteError('pairing_expired', 403)
            if request['expires'] <= now or state.get('enabled', True) is not True:
                return {'status': 'expired'}
            if cancel:
                state['requests'].remove(request)
                state['devices'] = [d for d in state['devices'] if d['deviceId'] != request.get('deviceId')]
                return {'status': 'cancelled'}
            result = {'status': request['status']}
            if request['status'] == 'approved':
                result['encryptedResult'] = request['encryptedResult']
            return result

    def approve(self, identity, accept, now=None):
        now = time.time() if now is None else now
        with self.transaction() as state:
            self.prune(state, now)
            request = next((r for r in state['requests'] if r['requestId'] == identity and r['status'] == 'pending'), None)
            if request is None or state.get('enabled', True) is not True:
                raise RemoteError('pairing_expired', 409)
            if not accept:
                request['status'] = 'denied'
            else:
                if len(state['devices']) >= 16:
                    raise RemoteError('device_limit', 409)
                token = secrets.token_urlsafe(32)
                device = {'deviceId': str(uuid.uuid4()), 'name': request['name'], 'hash': digest(token)}
                payload = {'token': token, 'deviceId': device['deviceId'], 'hubId': state['hubId'], 'certificateSha256': request['certificateSha256']}
                encrypted = encrypt_result(base64.b64decode(request['publicKey']), payload)
                state['devices'].append(device)
                request.update(status='approved', encryptedResult=encrypted, deviceId=device['deviceId'])
            return {'requestId': identity, 'accepted': accept}

    @contextmanager
    def transaction(self):
        with self.lock:
            lock_path = self.directory / "devices.lock"
            descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
            with os.fdopen(descriptor, "r+b") as handle:
                if os.name == "nt":
                    import msvcrt
                    if os.fstat(handle.fileno()).st_size == 0:
                        handle.write(b"0")
                        handle.flush()
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX)
                try:
                    state = self.read()
                    yield state
                    atomic_json(self.path, state)
                finally:
                    if os.name == "nt":
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(handle, fcntl.LOCK_UN)

    def begin_pairing(self, now=None):
        code = f"{secrets.randbelow(100000000):08d}"
        with self.transaction() as state:
            state["pairing"] = {"hash": digest(code), "expires": (time.time() if now is None else now) + 300, "attempts": 0}
        return code

    def pair(self, body, now=None):
        if not isinstance(body, dict) or set(body) != {"code", "name"}:
            raise RemoteError("invalid_request")
        code, name = body["code"], body["name"]
        if not isinstance(code, str) or len(code) != 8 or not code.isascii() or not code.isdigit():
            raise RemoteError("invalid_request")
        if not isinstance(name, str) or not name.strip() or len(name) > 80 or any(ord(c) < 32 for c in name):
            raise RemoteError("invalid_request")
        error = None
        result = None
        with self.transaction() as state:
            pairing = state.get("pairing", {})
            if pairing.get("expires", 0) <= (time.time() if now is None else now) or pairing.get("attempts", 5) >= 5:
                error = RemoteError("pairing_expired", 403)
            elif not hmac.compare_digest(pairing["hash"], digest(code)):
                pairing["attempts"] += 1
                error = RemoteError("pairing_invalid", 403)
            elif len(state["devices"]) >= 16:
                error = RemoteError("device_limit", 409)
            else:
                token = secrets.token_urlsafe(32)
                device = {"deviceId": str(uuid.uuid4()), "name": name.strip(), "hash": digest(token)}
                state["devices"].append(device)
                state.pop("pairing", None)
                result = {"token": token, "deviceId": device["deviceId"], "name": device["name"]}
        if error:
            raise error
        return result

    def authenticate(self, authorization):
        return self.identity(authorization) is not None

    def identity(self, authorization):
        if not authorization.startswith("Bearer ") or len(authorization) > 256:
            return None
        submitted = digest(authorization[7:])
        return next((device['deviceId'] for device in self.read()['devices'] if hmac.compare_digest(submitted, device['hash'])), None)

    def revoke(self, identity):
        with self.transaction() as state:
            old = len(state["devices"])
            state["devices"] = [item for item in state["devices"] if item["deviceId"] != identity]
            return old != len(state["devices"])

    def revoke_token(self, authorization):
        submitted = digest(authorization[7:])
        with self.transaction() as state:
            state["devices"] = [item for item in state["devices"] if not hmac.compare_digest(item["hash"], submitted)]


class RateLimiter:
    def __init__(self, limit=120, window=60, max_peers=256):
        self.limit, self.window, self.max_peers = limit, window, max_peers
        self.events = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, peer, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            for key in list(self.events):
                events = self.events[key]
                while events and events[0] <= now - self.window:
                    events.popleft()
                if not events:
                    del self.events[key]
            if peer not in self.events and len(self.events) >= self.max_peers:
                return False
            queue = self.events[peer]
            if len(queue) >= self.limit:
                return False
            queue.append(now)
            return True


class ImagePayload(bytes):
    def __new__(cls, payload, mime):
        result = super().__new__(cls, payload)
        result.mime = mime
        return result


class LoopbackProxy:
    def __init__(self):
        self.token = ""
        self.lock = threading.Lock()

    def request(self, method, path, body=b"", session_token=None):
        # This target is a constant; urllib/environment proxies are never consulted.
        connection = HTTPConnection("127.0.0.1", 8765, timeout=30)
        try:
            headers = {"Content-Type": "application/json", "Origin": "http://127.0.0.1:8765"}
            if method != "GET":
                headers["x-hub-token"] = self.token if session_token is None else session_token
            connection.request(method, path, body=body or None, headers=headers)
            response = connection.getresponse()
            payload = response.read(MAX_RESPONSE + 1)
            if len(payload) > MAX_RESPONSE:
                raise RemoteError("upstream_response_too_large", 502)
            if 300 <= response.status < 400:
                raise RemoteError("upstream_redirect_blocked", 502)
            mime = response.getheader('Content-Type', '').split(';')[0]
            if urlsplit(path).path == '/api/radio/artwork' and response.status == 200 and mime in {'image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/x-icon', 'image/vnd.microsoft.icon'}:
                if len(payload) > 256 * 1024:
                    raise RemoteError('upstream_response_too_large', 502)
                return response.status, ImagePayload(payload, mime)
            if mime != "application/json":
                raise RemoteError("upstream_invalid_response", 502)
            return response.status, payload
        except (OSError, TimeoutError) as error:
            raise RemoteError("upstream_unavailable", 503) from error
        finally:
            connection.close()

    def refresh_session(self):
        status, body = self.request("GET", "/api/session")
        try:
            token = json.loads(body)["token"]
            if status != 200 or not isinstance(token, str) or not 16 <= len(token) <= 256:
                raise ValueError()
        except (ValueError, KeyError, TypeError) as error:
            raise RemoteError("upstream_unavailable", 503) from error
        self.token = token

    def forward(self, method, path, body):
        if method == "GET":
            return self.request(method, path, body)
        with self.lock:
            if not self.token:
                self.refresh_session()
            token = self.token
        # A Bluetooth pair request can await a separate prompt reply. Never hold
        # the session lock during mutations: that reply must be able to proceed.
        status, payload = self.request(method, path, body, session_token=token)
        if status == 403 and json.loads(payload).get("error") == "session_expired":
            # The boundary denied this mutation before execution; only this case is retryable.
            with self.lock:
                if self.token == token:
                    self.refresh_session()
                token = self.token
            status, payload = self.request(method, path, body, session_token=token)
        return status, payload


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "PySH-Remote"
    sys_version = ""

    def log_message(self, *_):
        pass  # Never log paths, submitted secrets, names or Wi-Fi credentials.

    def reply(self, status, body):
        payload = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", getattr(body, 'mime', 'application/json; charset=utf-8'))
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        if status == 429:
            self.send_header("Retry-After", "60")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def dispatch(self):
        try:
            peer = self.client_address[0]
            if not lan_address(peer):
                raise RemoteError("lan_required", 403)
            if not self.server.limiter.allow(peer) or not self.server.global_limiter.allow("all"):
                raise RemoteError("rate_limited", 429)
            if self.headers.get("Host") != self.server.expected_host or self.headers.get("Origin") is not None:
                raise RemoteError("forbidden_origin", 403)
            # BaseHTTPRequestHandler normalizes a leading //; inspect the original target.
            raw_target = self.requestline.split()[1]
            if raw_target.startswith("//"):
                raise RemoteError("invalid_request")
            if len(self.path) > 8192 or not self.path.startswith("/") or self.path.startswith("//") or "\\" in self.path or any(ord(c) < 32 for c in self.path):
                raise RemoteError("invalid_request")
            parsed = urlsplit(self.path)
            if parsed.scheme or parsed.netloc or parsed.fragment or "%" in parsed.path or ".." in parsed.path:
                raise RemoteError("invalid_request")
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) > 1:
                raise RemoteError("invalid_request")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise RemoteError("invalid_request")
            if not 0 <= length <= MAX_BODY:
                raise RemoteError("request_too_large", 413)
            if self.command == "GET" and length:
                raise RemoteError("invalid_request")
            pairing = self.command == "POST" and parsed.path == "/remote/pair" and not parsed.query
            health = self.command == "GET" and self.path == "/remote/health"
            identity = self.command == 'GET' and self.path == '/remote/identity'
            pairing_request = self.command == 'POST' and self.path in {'/remote/pair/request', '/remote/pair/status', '/remote/pair/cancel'}
            revoke_self = self.command == "POST" and self.path == "/remote/revoke-self"
            heartbeat = self.command in {'POST', 'DELETE'} and self.path == '/remote/heartbeat'
            device_id = None
            if not health and not identity and not self.server.devices.enabled():
                raise RemoteError('control_disabled', 503)
            if not pairing and not health and not identity and not pairing_request:
                device_id = self.server.devices.identity(self.headers.get("Authorization", ""))
                if device_id is None:
                    raise RemoteError("unauthorized", 401)
                if not revoke_self and not heartbeat and parsed.path not in ROUTES.get(self.command, set()):
                    raise RemoteError("route_not_allowed", 404)
            if length and self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise RemoteError("invalid_request")
            body = self.rfile.read(length)
            if len(body) != length:
                raise RemoteError("invalid_request")
            if health:
                self.reply(200, {"service": "pysh-remote", "version": 1})
            elif identity:
                self.reply(200, {'hubId': self.server.devices.hub_id(), 'name': 'PySH', 'protocol': 2, 'enabled': self.server.devices.enabled(), 'certificateSha256': self.server.pin})
            elif pairing_request:
                try:
                    decoded = json.loads(body)
                except (ValueError, UnicodeError):
                    raise RemoteError('invalid_request')
                if self.path == '/remote/pair/request':
                    if not self.server.pair_limiter.allow(peer):
                        raise RemoteError('rate_limited', 429)
                    self.reply(200, self.server.devices.request_pair(decoded, self.server.pin))
                else:
                    self.reply(200, self.server.devices.pair_status(decoded, cancel=self.path.endswith('/cancel')))
            elif pairing:
                if not self.server.pair_limiter.allow(peer):
                    raise RemoteError("rate_limited", 429)
                try:
                    decoded = json.loads(body)
                except (ValueError, UnicodeError):
                    raise RemoteError("invalid_request")
                self.reply(200, self.server.devices.pair(decoded))
            elif revoke_self:
                if body and body.strip() != b"{}":
                    raise RemoteError("invalid_request")
                self.server.devices.revoke_token(self.headers.get("Authorization", ""))
                try:
                    self.server.proxy.forward('POST', '/api/remote/presence', json.dumps({'deviceId': device_id, 'active': False}).encode())
                except RemoteError:
                    pass
                self.reply(200, {"revoked": True})
            elif heartbeat:
                if body and body.strip() != b'{}':
                    raise RemoteError('invalid_request')
                status, payload = self.server.proxy.forward('POST', '/api/remote/presence', json.dumps({'deviceId': device_id, 'active': self.command == 'POST'}).encode())
                self.reply(status, payload)
            else:
                if self.command == 'GET' and parsed.path == '/api/state':
                    try:
                        self.server.proxy.forward('POST', '/api/remote/presence', json.dumps({'deviceId': device_id, 'active': True}).encode())
                    except RemoteError:
                        pass
                status, payload = self.server.proxy.forward(self.command, self.path, body)
                self.reply(status, payload)
        except RemoteError as error:
            self.reply(error.status, {"error": error.code})
        except (OSError, TimeoutError):
            self.close_connection = True
        except Exception:
            self.reply(500, {"error": "operation_failed"})

    do_GET = do_POST = do_PATCH = do_DELETE = do_PUT = do_OPTIONS = do_HEAD = dispatch


class LanServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    request_queue_size = 16
    allow_reuse_address = True

    def __init__(self, host, port, context, devices, proxy=None, pin=''):
        if not lan_address(host):
            raise ValueError("An explicit private LAN IP is required; wildcard/public/loopback binding refused")
        self.address_family = socket.AF_INET6 if ":" in host else socket.AF_INET
        self.expected_host = f"[{host}]:{port}" if ":" in host else f"{host}:{port}"
        self.context, self.devices, self.proxy = context, devices, proxy or LoopbackProxy()
        self.pin = pin
        self.limiter = RateLimiter()
        self.global_limiter = RateLimiter(limit=600)
        self.pair_limiter = RateLimiter(limit=5)
        self.slots = threading.BoundedSemaphore(16)
        super().__init__((host, port), Handler)

    def process_request(self, request, client_address):
        if not lan_address(client_address[0]) or not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        secured = request
        try:
            request.settimeout(5)
            secured = self.context.wrap_socket(request, server_side=True)
            secured.settimeout(10)
            self.finish_request(secured, client_address)
        except (OSError, ssl.SSLError):
            pass
        finally:
            self.shutdown_request(secured)
            self.slots.release()
