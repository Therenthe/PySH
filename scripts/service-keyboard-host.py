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
import urllib.error
import urllib.request

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
    if not isinstance(message, dict) or not isinstance(message.get("action"), str):
        raise ProtocolError("invalid_request")
    action = message["action"]
    if action in ("status", "show", "hide", "home", "radio", "media", "controls-status"):
        if set(message) != {"action"}:
            raise ProtocolError("invalid_request")
    elif action in ("controls-volume", "controls-mute", "controls-brightness", "controls-output"):
        if set(message) != {"action", "value"}:
            raise ProtocolError("invalid_request")
        value = message["value"]
        if action == "controls-mute":
            valid = type(value) is bool
        elif action == "controls-output":
            valid = isinstance(value, str) and 1 <= len(value) <= 200 and value.isprintable()
        else:
            valid = type(value) is int and (1 if action == "controls-brightness" else 0) <= value <= 100
        if not valid:
            raise ProtocolError("invalid_request")
    else:
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


def presentation():
    # Return only two public UI enums, never preferences, account or network data.
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        request = urllib.request.Request("http://127.0.0.1:8765/api/external/context",
                                         headers={"Origin": "http://127.0.0.1:8765"})
        with opener.open(request, timeout=2) as response:
            value = json.loads(response.read(1025))
        if value.get("language") in ("en", "ro") and value.get("theme") in ("ink", "night"):
            return {"language": value["language"], "theme": value["theme"]}
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return {"language": preferred_language()}



def owner_json(path, body=None, method="GET"):
    # All callers use fixed paths; the message never supplies a URL or header.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    headers = {"Origin": "http://127.0.0.1:8765"}
    if body is not None:
        with opener.open(urllib.request.Request("http://127.0.0.1:8765/api/session", headers=headers), timeout=2) as response:
            token = json.loads(response.read(4096))["token"]
        if not isinstance(token, str) or not 1 <= len(token) <= 512:
            raise ValueError("invalid_session")
        headers.update({"X-Hub-Token": token, "Content-Type": "application/json"})
    request = urllib.request.Request("http://127.0.0.1:8765" + path,
        data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
    with opener.open(request, timeout=2) as response:
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError("response_too_large")
    return json.loads(raw)


def controls_snapshot():
    value = owner_json("/api/external/controls")
    if not isinstance(value, dict) or value.get("language") not in ("en", "ro") or value.get("theme") not in ("ink", "night"):
        raise ValueError("invalid_controls")
    audio, brightness = value.get("audio"), value.get("brightness")
    if not isinstance(audio, dict) or not isinstance(brightness, dict) or type(value.get("busy")) is not bool:
        raise ValueError("invalid_controls")
    volume, mute, level = audio.get("volume"), audio.get("mute"), brightness.get("value")
    if volume is not None and (type(volume) is not int or not 0 <= volume <= 100):
        raise ValueError("invalid_controls")
    if mute is not None and type(mute) is not bool or level is not None and (type(level) is not int or not 1 <= level <= 100):
        raise ValueError("invalid_controls")
    outputs = audio.get("outputs")
    if not isinstance(outputs, list) or len(outputs) > 32:
        raise ValueError("invalid_controls")
    safe_outputs = []
    for item in outputs:
        if not isinstance(item, dict):
            raise ValueError("invalid_controls")
        identifier, label = item.get("id"), item.get("label")
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 200 or not identifier.isprintable() or not isinstance(label, str) or len(label) > 300:
            raise ValueError("invalid_controls")
        safe_outputs.append({"id": identifier, "label": label, "active": item.get("active") is True})
    # Rebuild every field: accidental future backend data must not reach a site.
    return {"language": value["language"], "theme": value["theme"], "busy": value["busy"],
        "audio": {"available": audio.get("available") is True, "ready": audio.get("ready") is True,
            "volume": volume, "mute": mute, "outputs": safe_outputs},
        "brightness": {"available": brightness.get("available") is True, "value": level}}


def control(action, value=None):
    try:
        before = controls_snapshot()
    except (OSError, ValueError, KeyError, TypeError):
        return {"ok": False, "error": "controls_unavailable"}
    if action == "controls-status":
        return {"ok": True, "controls": before}
    if before["busy"]:
        return {"ok": False, "error": "controls_busy", "definite": True, "controls": before}
    if action == "controls-brightness":
        if not before["brightness"]["available"]:
            return {"ok": False, "error": "controls_unavailable", "definite": True, "controls": before}
        path, body, method = "/api/preferences", {"screenBrightness": value}, "PATCH"
    else:
        if not before["audio"]["available"]:
            return {"ok": False, "error": "controls_unavailable", "definite": True, "controls": before}
        if action != "controls-output" and not before["audio"]["ready"]:
            return {"ok": False, "error": "controls_unavailable", "definite": True, "controls": before}
        if action == "controls-output" and value not in {item["id"] for item in before["audio"]["outputs"]}:
            return {"ok": False, "error": "output_unavailable", "definite": True, "controls": before}
        path, body, method = "/api/audio", {action.removeprefix("controls-"): value}, "POST"
    try:
        owner_json(path, body, method)
    except urllib.error.HTTPError as error:
        # Integration409 can follow a device write and a failed rollback.
        if error.code in (400,401,403,404,405,413,422):
            return {"ok": False, "error": "controls_unavailable", "definite": True}
        return {"ok": False, "error": "controls_unverified", "uncertain": True}
    except (OSError, ValueError, KeyError, TypeError):
        return {"ok": False, "error": "controls_unverified", "uncertain": True}
    try:
        after = controls_snapshot()
        key = action.removeprefix("controls-")
        actual = after["brightness"]["value"] if key == "brightness" else next((item["id"] for item in after["audio"]["outputs"] if item["active"]), None) if key == "output" else after["audio"].get(key)
        if after["busy"] or actual != value:
            raise ValueError("still_applying")
        return {"ok": True, "controls": after}
    except (OSError, ValueError, KeyError, TypeError):
        # An accepted write is never replayed just because readback was lost.
        return {"ok": False, "error": "controls_unverified", "uncertain": True}


class Keyboard:
    def __init__(self):
        self.child = None

    def available(self):
        return os.access(KEYBOARD, os.X_OK) and bool(os.environ.get("WAYLAND_DISPLAY"))

    def handle(self, action, value=None):
        if action.startswith("controls-"):
            return control(action, value)
        if action in ("home", "radio", "media"):
            # Fixed loopback owner API, no page URLs, cookies or typed values.
            # A native message cannot choose another host, path or command.
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                headers = {"Origin": "http://127.0.0.1:8765"}
                with opener.open(urllib.request.Request("http://127.0.0.1:8765/api/session", headers=headers), timeout=2) as response:
                    token = json.loads(response.read(4096))["token"]
                body = json.dumps({"target": action}).encode()
                request = urllib.request.Request("http://127.0.0.1:8765/api/external/navigation", data=body,
                    headers={**headers, "Content-Type": "application/json", "X-Hub-Token": token}, method="POST")
                with opener.open(request, timeout=2) as response:
                    if json.loads(response.read(4096)).get("accepted") is not True:
                        raise ValueError("navigation_unavailable")
                return {"ok": True}
            except (OSError, ValueError, KeyError, TypeError):
                return {"ok": False, "error": "return_unavailable"}
        if self.child is not None and self.child.poll() is not None:
            self.child.wait()
            self.child = None
        if action == "status":
            return {"ok": True, "available": self.available(), **presentation()}
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
            write_message(output_stream, keyboard.handle(message["action"], message["value"]) if "value" in message else keyboard.handle(message["action"]))
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
