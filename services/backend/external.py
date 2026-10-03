"""Owned external browser with real, profile-specific protected-media preparation."""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import sys
import time
from urllib.parse import urlencode


URLS = {"youtube": "https://www.youtube.com", "netflix": "https://www.netflix.com", "spotify": "https://open.spotify.com"}


def _group_snapshot(pgid):
    """PID generations currently in a group, not a historical numeric PGID."""
    members = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rpartition(")")[2].split()
            if int(fields[2]) == pgid:
                status = (path.parent / "status").read_text()
                uid = int(next(line for line in status.splitlines() if line.startswith("Uid:")).split()[1])
                members[int(path.parent.name)] = (int(fields[19]), uid)
        except (OSError, ValueError, IndexError, StopIteration):
            pass
    return members


class ExternalError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class ExternalBrowser:
    def __init__(self, directory: Path, extension: Path, *, timeout=180, poll_interval=1):
        self.profile = Path(directory) / "services-browser"
        self.extension = Path(extension)
        self.timeout = timeout
        self.poll_interval = min(2, max(.01, poll_interval))
        self._lock = asyncio.Lock()
        self._process = None
        self._monitor = None
        self._job = None
        self._attempt = None
        self._state = "cancelled"
        self._service = None
        self._language = "en"
        self._theme = "ink"
        self._error = None
        self._restarted = False
        self._deadline = 0
        self._executable = None
        self._owned_members = {}

    def _owns_current_group(self, pid):
        current = _group_snapshot(pid)
        if not any(current.get(member) == generation for member, generation in self._owned_members.items()):
            return False
        self._owned_members.update(current)
        return True

    @property
    def running(self):
        return self._process is not None and self._process.returncode is None

    def _check_job(self, job_id, attempt=None):
        if not self._job or job_id != self._job or self._state == "cancelled":
            raise ExternalError("stale_preparation")
        if attempt is not None and attempt != self._attempt:
            raise ExternalError("stale_preparation")

    def _status(self):
        result = {"state": self._state, "service": self._service, "attempt": self._attempt,
                  "language": self._language, "theme": self._theme}
        if self._state == "ready":
            result["url"] = URLS[self._service]
        if self._error:
            result["error"] = self._error
        return result

    async def _cancel_monitor(self):
        monitor, self._monitor = self._monitor, None
        if monitor is not None:
            monitor.cancel()
            await asyncio.gather(monitor, return_exceptions=True)

    async def _spawn(self, preparing):
        self._attempt = secrets.token_urlsafe(24)
        url = "http://127.0.0.1:8765/service-prepare?" + urlencode({"job": self._job, "attempt": self._attempt, "lang": self._language, "theme": self._theme}) if preparing else URLS[self._service]
        try:
            self._process = await asyncio.create_subprocess_exec(
                self._executable, "--ozone-platform=wayland", "--no-first-run", "--disable-features=Translate", "--start-maximized",
                "--class=pysh-service", "--user-data-dir=" + str(self.profile),
                "--load-extension=" + str(self.extension), "--app=" + url,
                stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                **({"process_group": 0} if sys.platform == "linux" else {"start_new_session": True}),
            )
            self._owned_members = _group_snapshot(self._process.pid) if sys.platform == "linux" else {}
        except OSError:
            self._process = None
            self._state, self._error = "error", "browser_unavailable"
            raise ExternalError("browser_unavailable") from None

    async def _stop_process(self):
        process = self._process
        if process is None:
            return
        # A fresh group stays in the API-owned session for supervisor recovery.
        # Signal only if a saved PID generation still identifies this group.
        if sys.platform == "linux" and self._owns_current_group(process.pid):
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
        elif sys.platform != "linux" and process.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=3)
        except asyncio.TimeoutError:
            if sys.platform == "linux":
                if self._owns_current_group(process.pid):
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                else:
                    raise ExternalError("browser_cleanup_unavailable") from None
            else:
                with contextlib.suppress(ProcessLookupError):
                    process.kill()
            await process.wait()
        if sys.platform == "linux" and self._owns_current_group(process.pid):
            # Reap the leader above and stop any surviving members of its group.
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        self._owned_members = {}
        self._process = None

    def _component(self):
        """Observe only bounded CDM metadata; browser probe alone proves capability."""
        try:
            if self.profile.is_symlink():
                return None
            profile = self.profile.resolve()
            root = self.profile / "WidevineCdm"
            resolved_root = root.resolve()
            if not resolved_root.is_relative_to(profile):
                return None

            def load(path):
                canonical = path.resolve(strict=True)
                if not canonical.is_relative_to(resolved_root):
                    raise ValueError
                info = canonical.stat()
                if not stat.S_ISREG(info.st_mode) or info.st_size > 16384:
                    raise ValueError
                result = json.loads(canonical.read_text(encoding="utf-8"))
                if not isinstance(result, dict):
                    raise ValueError
                return result

            hint = load(root / "latest-component-updated-widevine-cdm")
            value = hint.get("Path")
            if not isinstance(value, str):
                return None
            path = Path(value)
            if not path.is_absolute() or not re.fullmatch(r"\d+(?:\.\d+){3}", path.name):
                return None
            canonical = path.resolve(strict=True)
            if canonical.parent != resolved_root:
                return None
            manifest = load(path / "manifest.json")
            if manifest.get("version") != path.name:
                return None
            library = path / "_platform_specific/linux_arm64/libwidevinecdm.so"
            canonical_library = library.resolve(strict=True)
            if not canonical_library.is_relative_to(canonical):
                return None
            info = canonical_library.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_size == 0:
                return None
            return (path.name, info.st_size, info.st_mtime_ns)
        except (OSError, ValueError, RuntimeError):
            return None

    async def start(self, service, executable, language="en", theme="ink"):
        if service not in URLS:
            raise ExternalError("invalid_request")
        async with self._lock:
            if self.running:
                raise ExternalError("service_already_open")
            await self._cancel_monitor()
            await self._stop_process()
            self._job = secrets.token_urlsafe(24)
            self._service, self._executable = service, executable
            self._language = language if language in ("en", "ro") else "en"
            self._theme = theme if theme in ("ink", "night") else "ink"
            self._error, self._restarted = None, False
            self._state = "opened" if service == "youtube" else "checking"
            self._deadline = time.monotonic() + self.timeout
            await self._spawn(service != "youtube")
            self._monitor = asyncio.create_task(self._watch(self._job))
            return {"opened": service == "youtube", "preparing": service != "youtube", "jobId": self._job, "service": service}

    async def status(self, job_id):
        async with self._lock:
            self._check_job(job_id)
            if not self.running:
                self._state, self._error = "error", "browser_closed"
            return self._status()

    async def report(self, job_id, attempt, ready):
        if type(ready) is not bool:
            raise ExternalError("invalid_request")
        async with self._lock:
            self._check_job(job_id, attempt)
            if not self.running or self._service == "youtube" or self._state not in {"checking", "waiting_component"}:
                raise ExternalError("stale_preparation")
            if ready:
                self._state, self._error = "ready", None
            elif self._restarted:
                self._state, self._error = "error", "protected_playback_unavailable"
            else:
                self._state = "waiting_component"
            return self._status()

    async def retry(self, job_id):
        async with self._lock:
            self._check_job(job_id)
            if not self.running or self._state != "error" or self._service == "youtube":
                raise ExternalError("stale_preparation")
            self._state, self._error = "checking", None
            self._deadline = time.monotonic() + self.timeout
            return self._status()

    async def cancel(self, job_id):
        async with self._lock:
            self._check_job(job_id)
            self._state, self._attempt, self._error = "cancelled", None, None
            await self._cancel_monitor()
            await self._stop_process()
            return self._status()

    async def close(self):
        async with self._lock:
            self._state, self._attempt, self._error = "cancelled", None, None
            await self._cancel_monitor()
            await self._stop_process()

    async def _watch(self, job):
        try:
            while True:
                await asyncio.sleep(self.poll_interval)
                async with self._lock:
                    if job != self._job or self._state == "cancelled":
                        return
                    if not self.running:
                        self._state, self._error = "error", "browser_closed"
                        return
                    if self._state == "waiting_component" and not self._restarted and self._component():
                        self._state, self._restarted = "restarting", True
                        await self._stop_process()
                        try:
                            await self._spawn(True)
                        except ExternalError:
                            return
                        self._state = "checking"
                        self._deadline = time.monotonic() + self.timeout
                    elif self._state in {"checking", "waiting_component"} and time.monotonic() >= self._deadline:
                        self._state, self._error = "error", "protected_playback_timeout"
        except asyncio.CancelledError:
            return
        except ExternalError as error:
            self._state, self._error = "error", error.code
