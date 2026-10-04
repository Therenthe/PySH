#!/usr/bin/python3
"""Bounded native messaging bridge; no site text or typed keys enter this host."""
import base64
import hashlib
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys

MAX_MESSAGE = 4096
KEYBOARD = "/usr/bin/wvkbd-mobintl"
ROOT = Path(__file__).resolve().parents[1]


class ProtocolError(ValueError):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("invalid_request")
        result[key] = value
    return result


def _read_exact(stream, size):
    parts = bytearray()
    while len(parts) < size:
        chunk = stream.read(size - len(parts))
        if not chunk:
            raise ProtocolError("truncated_message")
        parts.extend(chunk)
    return bytes(parts)


def read_message(stream):
    first = stream.read(1)
    if not first:
        return None
    length = struct.unpack("<I", first + _read_exact(stream, 3))[0]
    if not 0 < length <= MAX_MESSAGE:
        raise ProtocolError("invalid_message_size")
    try:
        message = json.loads(_read_exact(stream, length).decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError):
        raise ProtocolError("invalid_request") from None
    if not isinstance(message, dict) or set(message) != {"action"}:
        raise ProtocolError("invalid_request")
    if message["action"] not in ("status", "show", "hide"):
        raise ProtocolError("invalid_action")
    return message


def write_message(stream, message):
    payload = json.dumps(message, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    stream.write(struct.pack("<I", len(payload)) + payload)
    stream.flush()


def allowed_origin(manifest_path=ROOT / "app/browser-extension/manifest.json"):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    key = base64.b64decode(manifest["key"], validate=True)
    if not key:
        raise ValueError("missing_extension_key")
    digest = hashlib.sha256(key).hexdigest()[:32]
    extension_id = "".join(chr(ord("a") + int(character, 16)) for character in digest)
    return "chrome-extension://" + extension_id + "/"


def preferred_language():
    directory = Path(os.environ.get("PI_HUB_DATA", str(Path.home() / ".local/share/pi-smart-hub")))
    try:
        path = directory / "preferences.json"
        if path.stat().st_size > 1024 * 1024:
            return "ro"
        language = json.loads(path.read_text(encoding="utf-8")).get("language")
        return language if language in ("en", "ro") else "ro"
    except (OSError, ValueError, AttributeError):
        return "ro"


class Keyboard:
    def __init__(self):
        self.child = None

    def available(self):
        return os.access(KEYBOARD, os.X_OK) and bool(os.environ.get("WAYLAND_DISPLAY"))

    def handle(self, action):
        if self.child is not None and self.child.poll() is not None:
            self.child.wait()
            self.child = None
        if action == "status":
            return {"ok": True, "available": self.available(), "language": preferred_language()}
        if not self.available():
            return {"ok": False, "error": "keyboard_unavailable"}
        try:
            if action == "show":
                if self.child is None:
                    self.child = subprocess.Popen(
                        [KEYBOARD, "-H", "240", "-L", "240", "--fn", "DejaVu Sans 20"],
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        close_fds=True,
                    )
                else:
                    self.child.send_signal(signal.SIGUSR2)
            elif action == "hide" and self.child is not None:
                self.child.send_signal(signal.SIGUSR1)
            return {"ok": True}
        except OSError:
            return {"ok": False, "error": "keyboard_failed"}

    def close(self):
        if self.child is None:
            return
        try:
            if self.child.poll() is None:
                self.child.terminate()
            self.child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.wait()
        except ProcessLookupError:
            self.child.wait()
        finally:
            self.child = None


def serve(input_stream, output_stream, keyboard):
    try:
        while True:
            try:
                message = read_message(input_stream)
            except ProtocolError as error:
                write_message(output_stream, {"ok": False, "error": str(error)})
                return 1
            if message is None:
                return 0
            write_message(output_stream, keyboard.handle(message["action"]))
    finally:
        keyboard.close()


def main():
    try:
        if len(sys.argv) != 2 or sys.argv[1] != allowed_origin():
            return 1
    except (OSError, ValueError, KeyError, TypeError):
        return 1
    def stop(_signum, _frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        return serve(sys.stdin.buffer, sys.stdout.buffer, Keyboard())
    except (BrokenPipeError, OSError):
        return 1


if __name__ == "__main__":
    sys.exit(main())
