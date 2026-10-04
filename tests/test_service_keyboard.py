"""Keyboard bridge accepts controls only and reaps its own child on disconnect."""
import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from unittest.mock import Mock

import pytest


@pytest.fixture
def host():
    spec = importlib.util.spec_from_file_location("service_keyboard", Path(__file__).resolve().parents[1] / "scripts/service-keyboard-host.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame(body):
    payload = body if isinstance(body, bytes) else json.dumps(body).encode()
    return struct.pack("<I", len(payload)) + payload


@pytest.mark.parametrize("action", ["status", "show", "hide"])
def test_allowed_actions(host, action):
    assert host.read_message(io.BytesIO(frame({"action": action}))) == {"action": action}
    assert host.read_message(io.BytesIO()) is None


@pytest.mark.parametrize("body", [
    [], None, {"action": "type"}, {"action": "show", "text": "never_echo_this"},
    {"action": "status", "command": "/bin/sh"}, {"action": ["show"]},
    b'{"action":"show","action":"hide"}', b'\xff', b'not-json',
])
def test_rejects_non_control_or_duplicate_fields(host, body):
    with pytest.raises(host.ProtocolError):
        host.read_message(io.BytesIO(frame(body)))


@pytest.mark.parametrize("wire", [b'\x01', b'\x01\x00\x00', struct.pack("<I", 20) + b'{}', struct.pack("<I", 0), struct.pack("<I", 4097)])
def test_truncation_and_bounds(host, wire):
    with pytest.raises(host.ProtocolError):
        host.read_message(io.BytesIO(wire))


def test_partial_stream_reads(host):
    class Partial(io.BytesIO):
        def read(self, size=-1):
            return super().read(min(size, 1))
    assert host.read_message(Partial(frame({"action": "show"}))) == {"action": "show"}


def test_owned_keyboard_stdio_signals_and_cleanup(host, monkeypatch):
    child = Mock()
    child.poll.return_value = None
    spawn = Mock(return_value=child)
    monkeypatch.setattr(host.subprocess, "Popen", spawn)
    monkeypatch.setattr(host.Keyboard, "available", lambda self: True)
    monkeypatch.setattr(host.signal, "SIGUSR1", 10, raising=False)
    monkeypatch.setattr(host.signal, "SIGUSR2", 12, raising=False)
    keyboard = host.Keyboard()
    assert keyboard.handle("show") == {"ok": True}
    args, kwargs = spawn.call_args
    assert args[0] == ["/usr/bin/wvkbd-mobintl", "-H", "240", "-L", "240", "--fn", "DejaVu Sans 20"]
    assert kwargs == {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "close_fds": True}
    keyboard.handle("hide")
    keyboard.handle("show")
    assert spawn.call_count == 1
    assert [call.args[0] for call in child.send_signal.call_args_list] == [10, 12]
    keyboard.close()
    child.terminate.assert_called_once()
    child.wait.assert_called_once_with(timeout=2)
    assert keyboard.child is None


def test_cleanup_kills_unresponsive_owned_child(host):
    child = Mock()
    child.poll.return_value = None
    child.wait.side_effect = [subprocess.TimeoutExpired("wvkbd", 2), None]
    keyboard = host.Keyboard()
    keyboard.child = child
    keyboard.close()
    child.terminate.assert_called_once()
    child.kill.assert_called_once()
    assert child.wait.call_count == 2
    assert keyboard.child is None


def test_exited_child_reaped_and_replaced(host, monkeypatch):
    previous = Mock()
    previous.poll.return_value = 0
    fresh = Mock()
    monkeypatch.setattr(host.Keyboard, "available", lambda self: True)
    monkeypatch.setattr(host.subprocess, "Popen", Mock(return_value=fresh))
    keyboard = host.Keyboard()
    keyboard.child = previous
    assert keyboard.handle("show")["ok"]
    previous.wait.assert_called_once_with()
    assert keyboard.child is fresh


def test_eof_and_malformed_disconnect_cleanup(host):
    for wire, result in [(frame({"action": "show"}), 0), (frame({"action": "show", "text": "private_text"}), 1)]:
        keyboard = Mock()
        keyboard.handle.return_value = {"ok": True}
        output = io.BytesIO()
        assert host.serve(io.BytesIO(wire), output, keyboard) == result
        keyboard.close.assert_called_once()
        assert b"private_text" not in output.getvalue()


def test_broken_output_still_cleanup(host):
    class Broken(io.BytesIO):
        def write(self, data):
            raise BrokenPipeError
    keyboard = Mock()
    keyboard.handle.return_value = {"ok": True}
    with pytest.raises(BrokenPipeError):
        host.serve(io.BytesIO(frame({"action": "show"})), Broken(), keyboard)
    keyboard.close.assert_called_once()


def test_status_exposes_only_validated_language(host, monkeypatch, tmp_path):
    monkeypatch.setenv("PI_HUB_DATA", str(tmp_path))
    monkeypatch.setattr(host.Keyboard, "available", lambda self: True)
    path = tmp_path / "preferences.json"
    path.write_text(json.dumps({"language": "en", "password": "do_not_return"}))
    assert host.Keyboard().handle("status") == {"ok": True, "available": True, "language": "en"}
    for contents in ['{"language":"unknown"}', '[]', 'bad-json']:
        path.write_text(contents)
        assert host.preferred_language() == "ro"


def test_origin_uses_manifest_key_not_service_site(host, tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"key": base64.b64encode(b"known-test-public-key").decode()}))
    origin = host.allowed_origin(manifest)
    assert origin.startswith("chrome-extension://") and len(origin.split("//")[1].strip("/")) == 32
    monkeypatch.setattr(host, "allowed_origin", lambda: origin)
    monkeypatch.setattr(host.sys, "argv", ["host", "https://www.netflix.com/"])
    assert host.main() == 1
    monkeypatch.setattr(host.sys, "argv", ["host", origin, "--command=sh"])
    assert host.main() == 1


def test_unavailable_and_failure_are_sanitized(host, monkeypatch):
    keyboard = host.Keyboard()
    monkeypatch.setattr(host.Keyboard, "available", lambda self: False)
    assert keyboard.handle("show") == {"ok": False, "error": "keyboard_unavailable"}
    monkeypatch.setattr(host.Keyboard, "available", lambda self: True)
    monkeypatch.setattr(host.subprocess, "Popen", Mock(side_effect=OSError("secret-detail")))
    assert keyboard.handle("show") == {"ok": False, "error": "keyboard_failed"}


@pytest.mark.skipif(sys.platform != "linux", reason="Real owned Linux keyboard process")
def test_disconnect_reaps_real_child(host, monkeypatch, tmp_path):
    fake = tmp_path / "fake-keyboard"
    fake.write_text("#!" + sys.executable + "\nimport time\ntime.sleep(60)\n")
    fake.chmod(0o700)
    monkeypatch.setattr(host, "KEYBOARD", str(fake))
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-test")
    keyboard = host.Keyboard()
    assert keyboard.handle("show")["ok"]
    child = keyboard.child
    assert child.poll() is None
    assert host.serve(io.BytesIO(), io.BytesIO(), keyboard) == 0
    assert child.poll() is not None
    with pytest.raises(ProcessLookupError):
        os.kill(child.pid, 0)
