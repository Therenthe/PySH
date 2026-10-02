"""Small mpv JSON-IPC controller for real Linux playback."""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class PlayerError(Exception):
    """Playback error with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class Player:
    def __init__(self, *, mpv_path: str | None = None, socket_path: str | None = None, startup_timeout: float = 4.0):
        self.mpv_path = mpv_path
        self.socket_path = socket_path
        self._socket_directory: str | None = None
        self.startup_timeout = startup_timeout
        self._process: asyncio.subprocess.Process | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._request_id = 0
        self._lock = asyncio.Lock()
        self._kind = "radio"
        self._url = ""
        self._title = ""
        self._error: str | None = None
        self._connecting = False
        self._last_play_command = 0.0
        self._last_position: float | None = None

    async def start(self) -> None:
        if self._process and self._process.returncode is None and self._writer:
            return
        if not sys.platform.startswith("linux"):
            self._error = "player_unavailable"
            raise PlayerError("player_unavailable", "Playback is available on the Raspberry Pi Linux device.")
        executable = self.mpv_path or shutil.which("mpv")
        if not executable:
            self._error = "player_unavailable"
            raise PlayerError("player_unavailable", "mpv is not installed on this device.")
        if not self.socket_path:
            self._socket_directory = tempfile.mkdtemp(prefix="pi-hub-")
            self.socket_path = str(Path(self._socket_directory) / "mpv.sock")
        try:
            os.unlink(self.socket_path)
        except FileNotFoundError:
            pass
        args = [
            executable,
            "--idle=yes",
            "--no-terminal",
            "--no-video",
            "--audio-display=no",
            f"--input-ipc-server={self.socket_path}",
            "--no-config",
            "--audio-fallback-to-null=yes",
        ]
        try:
            self._process = await asyncio.create_subprocess_exec(
                *args, stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                env={**os.environ, "PIPEWIRE_PROPS": '{ "node.dont-reconnect": true }'},
            )
            deadline = time.monotonic() + self.startup_timeout
            while time.monotonic() < deadline:
                if self._process.returncode is not None:
                    self._error = "player_failed"
                    raise PlayerError("player_failed", "mpv could not start.")
                try:
                    self._reader, self._writer = await asyncio.open_unix_connection(self.socket_path)
                    return
                except (FileNotFoundError, ConnectionRefusedError, OSError):
                    await asyncio.sleep(0.05)
            self._error = "player_timeout"
            raise PlayerError("player_timeout", "mpv did not become ready.")
        except PlayerError:
            await self.close()
            raise
        except (OSError, asyncio.SubprocessError) as exc:
            self._error = "player_failed"
            await self.close()
            raise PlayerError("player_failed", "mpv could not start.") from exc

    async def close(self) -> None:
        writer, self._writer = self._writer, None
        self._reader = None
        if writer:
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass
        process, self._process = self._process, None
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        if self.socket_path:
            try:
                os.unlink(self.socket_path)
            except (FileNotFoundError, OSError):
                pass
        if self._socket_directory:
            try:
                os.rmdir(self._socket_directory)
            except OSError:
                pass
            self._socket_directory = None

    async def select_output(self, name: str) -> None:
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", name):
            raise PlayerError("invalid_output", "Choose an available audio output.")
        await self.start()
        await self._command(["set_property", "audio-device", "pipewire/" + name])

    async def play(self, url: str, title: str = "", kind: str = "radio") -> dict[str, Any]:
        await self.start()
        parsed = urlparse(url)
        if parsed.scheme and parsed.scheme not in {"http", "https", "rtsp", "rtmp", "file"}:
            raise PlayerError("invalid_media_url", "This media source is not supported.")
        if not url.strip():
            raise PlayerError("invalid_media_url", "Choose a media source first.")
        self._kind = "audio" if kind == "local" else kind if kind in {"radio", "audio", "video"} else "radio"
        self._url, self._title, self._error = url, title, None
        self._connecting = True
        self._last_play_command = time.monotonic()
        await self._command(["set_property", "pause", False])
        await self._command(["loadfile", url, "replace"])
        return await self.status()

    async def command(self, action: str, value: Any = None) -> dict[str, Any]:
        command_map: dict[str, list[Any]] = {
            "pause": ["set_property", "pause", True],
            "play": ["set_property", "pause", False],
            "resume": ["set_property", "pause", False],
            "toggle": ["cycle", "pause"],
            "stop": ["stop"],
            "next": ["playlist-next", "weak"],
            "previous": ["playlist-prev", "weak"],
            "mute": ["set_property", "mute", bool(value)],
        }
        if action == "seek":
            try:
                seconds = float(value)
            except (TypeError, ValueError) as exc:
                raise PlayerError("invalid_command", "Seek position must be a number.") from exc
            if not 0 <= seconds <= 864000:
                raise PlayerError("invalid_command", "Seek position is outside the allowed range.")
            command = ["seek", seconds, "absolute"]
        elif action == "volume":
            try:
                volume = float(value)
            except (TypeError, ValueError) as exc:
                raise PlayerError("invalid_command", "Volume must be a number.") from exc
            if not 0 <= volume <= 100:
                raise PlayerError("invalid_command", "Volume must be between 0 and 100.")
            command = ["set_property", "volume", volume]
        else:
            command = command_map.get(action)
            if command is None:
                raise PlayerError("invalid_command", "That playback control is unavailable.")
        await self.start()
        if action == "stop":
            self._connecting = False
            self._url = ""
            self._title = ""
            self._error = None
        await self._command(command)
        if action == "play":
            self._last_play_command = time.monotonic()
        return await self.status()

    async def status(self) -> dict[str, Any]:
        if self._process is None or self._process.returncode is not None:
            state = "error" if self._error else "idle"
            return self._status_value(state)
        props: dict[str, Any] = {}
        for name in ("pause", "time-pos", "duration", "volume", "mute", "media-title", "paused-for-cache", "idle-active"):
            try:
                props[name] = await self._command(["get_property", name])
            except PlayerError:
                pass
        if self._error:
            state = "error"
        elif not self._url or props.get("idle-active"):
            state = "idle"
            self._connecting = False
        elif props.get("pause"):
            state = "paused"
            self._connecting = False
        elif props.get("paused-for-cache"):
            state = "buffering"
        elif self._connecting:
            state = "connecting" if time.monotonic() - self._last_play_command < 12 else "buffering"
        else:
            state = "playing"
        position = props.get("time-pos")
        if position is not None:
            try:
                position = max(0.0, float(position))
            except (ValueError, TypeError):
                position = None
        if position is not None and self._last_position is not None and position > self._last_position:
            self._connecting = False
            if state in {"connecting", "buffering"}:
                state = "playing"
        self._last_position = position
        return self._status_value(
            state,
            title=props.get("media-title") or self._title,
            position=position,
            duration=_number_or_none(props.get("duration")),
            volume=_number_or_none(props.get("volume")),
            muted=props.get("mute"),
        )

    def _status_value(self, state: str, **overrides: Any) -> dict[str, Any]:
        result: dict[str, Any] = {
            "state": state,
            "url": self._url,
            "title": self._title,
            "kind": self._kind,
            "position": None,
            "duration": None,
            "volume": None,
            "muted": False,
            "error": self._error,
        }
        result.update(overrides)
        return result

    async def _command(self, command: list[Any]) -> Any:
        if not self._writer or not self._reader:
            raise PlayerError("player_unavailable", "Playback is not connected to mpv.")
        async with self._lock:
            self._request_id += 1
            request_id = self._request_id
            payload = json.dumps({"command": command, "request_id": request_id}, separators=(",", ":")) + "\n"
            self._writer.write(payload.encode("utf-8"))
            try:
                await self._writer.drain()
                while True:
                    line = await asyncio.wait_for(self._reader.readline(), timeout=2.0)
                    if not line:
                        raise ConnectionError("mpv closed IPC")
                    message = json.loads(line)
                    if message.get("event"):
                        self._handle_event(message)
                        continue
                    if message.get("request_id") != request_id:
                        continue
                    if message.get("error") != "success":
                        if message.get("error") in {"property unavailable", "property not found"}:
                            return None
                        raise PlayerError("playback_command_failed", "The playback command could not be completed.")
                    return message.get("data")
            except asyncio.TimeoutError as exc:
                raise PlayerError("player_timeout", "mpv did not respond to a playback command.") from exc
            except (ConnectionError, OSError, json.JSONDecodeError) as exc:
                self._error = "player_disconnected"
                raise PlayerError("player_disconnected", "mpv playback disconnected.") from exc

    def _handle_event(self, event: dict[str, Any]) -> None:
        name = event.get("event")
        data = event.get("data") or {}
        if name == "file-loaded":
            self._connecting = False
            self._error = None
        elif name == "end-file":
            reason = data.get("reason") if isinstance(data, dict) else data
            file_error = data.get("file_error") if isinstance(data, dict) else None
            if reason == "error" or file_error:
                self._error = "stream_failed"
                self._connecting = False
            elif reason == "stop":
                self._url = ""
                self._connecting = False


def _number_or_none(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
