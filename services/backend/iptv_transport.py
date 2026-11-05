"""A private, bounded MPEG-TS to HLS remux. FFmpeg never receives network URLs."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import tempfile
import threading
import time

SEGMENT = re.compile(r'^segment[0-9]{9}\.ts$')
MAX_FILE = 32 * 1024 * 1024
MAX_DIRECTORY = 96 * 1024 * 1024
MIN_FREE = 128 * 1024 * 1024
_CAPACITY = threading.BoundedSemaphore(3)  # One viewer and two independent recordings.


class TransportError(Exception):
    def __init__(self, code='iptv_stream_unavailable'):
        self.code = code
        super().__init__(code)


def is_transport(data: bytes) -> bool:
    """Require three aligned, unscrambled transport packet headers, not MIME alone."""
    return len(data) >= 564 and all(data[i] == 0x47 and not data[i + 1] & 0x80
                                  and not data[i + 3] & 0xc0 and data[i + 3] & 0x30
                                  for i in (0, 188, 376))


class DirectTransport:
    def __init__(self, response, connection, initial: bytes, url: str, source_socket=None, *, idle_timeout=120):
        self.response, self.connection, self.source_socket = response, connection, source_socket
        self.url, self.idle_timeout = url, idle_timeout
        self._stop, self._done = threading.Event(), threading.Event()
        self._touched = self._started = time.monotonic()
        self.error = None
        self._release_lock, self._released = threading.Lock(), False
        self.process = None
        self.directory = None
        if not is_transport(initial):
            raise TransportError('iptv_unsupported_stream')
        if not _CAPACITY.acquire(blocking=False):
            raise TransportError('iptv_stream_busy')
        try:
            if shutil.which('ffmpeg') is None:
                raise TransportError('recording_ffmpeg_unavailable')
            if shutil.disk_usage(tempfile.gettempdir()).free < MIN_FREE:
                raise TransportError('recording_disk_full')
            self.directory = Path(tempfile.mkdtemp(prefix='pysh-ts-'))
            self.process = subprocess.Popen([
                'ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostats',
                '-max_alloc', '67108864', '-probesize', '2097152', '-analyzeduration', '3000000',
                '-protocol_whitelist', 'pipe', '-format_whitelist', 'mpegts', '-f', 'mpegts', '-i', 'pipe:0',
                '-sn', '-dn', '-c', 'copy', '-f', 'hls', '-hls_time', '2', '-hls_list_size', '6',
                '-hls_delete_threshold', '2', '-hls_flags', 'delete_segments+temp_file+omit_endlist',
                '-hls_segment_filename', str(self.directory / 'segment%09d.ts'),
                str(self.directory / 'index.m3u8')], stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
            self._feeder = threading.Thread(target=self._feed, args=(initial,), daemon=True)
            self._monitor = threading.Thread(target=self._watch, daemon=True)
            self._feeder.start()
            self._monitor.start()
        except BaseException:
            self.close()
            self._cleanup()
            raise

    def _cleanup(self):
        with self._release_lock:
            if self._released:return
            self._released = True
        try:
            try:
                if self.process is not None:
                    try:self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=2)
            finally:
                try:
                    if hasattr(self, '_feeder') and self._feeder.ident is not None:
                        self._feeder.join(timeout=2)
                finally:
                    try:
                        self.response.close()
                    finally:
                        try:self.connection.close()
                        finally:
                            if self.source_socket is not None:self.source_socket.close()
        finally:
            try:
                if self.directory is not None:shutil.rmtree(self.directory, ignore_errors=True)
            finally:
                _CAPACITY.release()
                self._done.set()

    def touch(self):
        self._touched = time.monotonic()

    def close(self):
        """Nonblocking for the event loop; the watchdog owns reaping and cleanup."""
        self._stop.set()
        if self.source_socket is not None:
            try:self.source_socket.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        if self.process is not None and self.process.poll() is None:
            try:self.process.terminate()
            except OSError:pass

    def _feed(self, initial):
        sent, began = 0, time.monotonic()
        try:
            block = initial
            while block and not self._stop.is_set():
                self.process.stdin.write(block)
                self.process.stdin.flush()
                sent += len(block)
                # Bound both malicious input bandwidth and disk-limit overshoot.
                delay = sent / (8 * 1024 * 1024) - (time.monotonic() - began)
                if delay > 0 and self._stop.wait(delay):break
                block = self.response.read1(64 * 1024)
        except (OSError, ValueError):
            pass
        finally:
            try:self.process.stdin.close()
            except (OSError, ValueError):pass
            self.connection.close()

    def _watch(self):
        try:
            while not self._stop.wait(.1):
                now = time.monotonic()
                if now - self._touched > self.idle_timeout or now - self._started > 86400:
                    self.error = 'iptv_session_expired';break
                if self.process.poll() is not None:
                    self.error = 'iptv_stream_unavailable';break
                files = list(self.directory.iterdir())
                sizes = []
                for item in files:
                    try:sizes.append(item.stat().st_size)
                    except FileNotFoundError:pass  # FFmpeg retires old segments concurrently.
                if len(files) > 24 or sum(sizes) > MAX_DIRECTORY or any(size > MAX_FILE for size in sizes):
                    self.error = 'iptv_resource_too_large';break
                if shutil.disk_usage(self.directory).free < MIN_FREE:
                    self.error = 'recording_disk_full';break
        except OSError:
            self.error = 'iptv_stream_unavailable'
        finally:
            self.close()
            self._cleanup()

    def read(self, name):
        if name != 'index.m3u8' and not SEGMENT.fullmatch(name):
            raise TransportError('iptv_resource_expired')
        if self._stop.is_set() or self.error:
            raise TransportError(self.error or 'iptv_session_expired')
        self.touch()
        try:
            fd = os.open(self.directory / name, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                limit = 64 * 1024 if name == 'index.m3u8' else MAX_FILE
                if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
                    raise TransportError('iptv_resource_too_large')
                data = stream.read(limit + 1)
                if len(data) > limit:raise TransportError('iptv_resource_too_large')
                return data
        except OSError as exc:
            raise TransportError('iptv_resource_expired') from exc

    def manifest(self, timeout=15):
        deadline = time.monotonic() + timeout
        while not self._stop.is_set():
            try:
                data = self.read('index.m3u8')
                if data.startswith(b'#EXTM3U') and b'#EXTINF:' in data:return data
            except TransportError as exc:
                if exc.code != 'iptv_resource_expired':
                    self.error = exc.code
                    self.close()
                    raise
            if time.monotonic() >= deadline:
                self.error = 'iptv_stream_unavailable'
                self.close()
                raise TransportError()
            self._stop.wait(.1)
        raise TransportError(self.error or 'iptv_session_expired')
