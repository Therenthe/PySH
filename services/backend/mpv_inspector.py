"""Bounded optional mpv inspection; no active Player IPC.

Caller owns root confinement, approved read-only regular FD and one shared
Semaphore(1). Revalidate path/root membership when accepting/caching the result.
Only the descriptor clone is closed; the caller's offset/flags stay untouched.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import sys
import tempfile
import unicodedata

TIMEOUT_S = 4.0
MAX_STDOUT = 16_384
MAX_STDERR = 8_192
MAX_JPEG = 262_144
SCRIPT_SHA256 = '4962dd93d543009eba60bc263fb230e389ddab0c48679cf479e480fc7e9ce79c'
MPV = Path('/usr/bin/mpv')
SCRIPT = Path(__file__).with_name('inspect.lua')
PREFIX = b'PYSH_MEDIA_V1 '
# A separate interpreter execs mpv in the same owned PID/group. This avoids
# Python preexec_fn in a multithreaded API process and adds no package dependency.
LAUNCHER = '''import os,resource,sys
os.nice(10)
resource.setrlimit(resource.RLIMIT_FSIZE,(262144,262144))
resource.setrlimit(resource.RLIMIT_AS,(402653184,402653184))
resource.setrlimit(resource.RLIMIT_CPU,(3,3))
os.execv(sys.argv[1],sys.argv[1:])
'''


class InspectionLimit(Exception):
    pass


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _trusted_inputs():
    binary = MPV.resolve(strict=True)
    info = binary.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022 or not os.access(binary, os.X_OK):
        raise ValueError('untrusted_tool')
    script = SCRIPT.resolve(strict=True)
    script_info = script.stat()
    if script.parent != Path(__file__).resolve().parent or not stat.S_ISREG(script_info.st_mode) or script_info.st_size > 16384 or script_info.st_mode & 0o022 or script_info.st_uid not in {0, os.geteuid()}:
        raise ValueError('untrusted_script')
    with script.open('rb') as stream:
        raw = stream.read(16385)
    if len(raw) > 16384 or hashlib.sha256(raw).hexdigest() != SCRIPT_SHA256:
        raise ValueError('untrusted_script')
    return binary, script


def build_argv(binary: Path, script: Path, descriptor: int, directory: Path):
    if type(descriptor) is not int or descriptor < 3:
        raise ValueError('invalid_descriptor')
    return [sys.executable, '-I', '-S', '-c', LAUNCHER, str(binary),
            '--no-config', '--load-scripts=no', '--script=' + str(script),
            '--osc=no', '--ytdl=no', '--load-stats-overlay=no', '--load-console=no',
            '--load-auto-profiles=no', '--load-select=no', '--load-positioning=no', '--load-commands=no',
            '--access-references=no', '--autoload-files=no', '--demuxer=lavf',
            '--demuxer-lavf-o=protocol_whitelist=pipe', '--demuxer-lavf-propagate-opts=yes',
            '--demuxer-lavf-probesize=1048576', '--demuxer-lavf-analyzeduration=1',
            '--cache=no', '--demuxer-max-bytes=1MiB', '--demuxer-max-back-bytes=0',
            '--input-terminal=no', '--msg-level=all=no', '--idle=no', '--keep-open=no',
            '--ao=null', '--mute=yes', '--volume=0', '--sid=no', '--hwdec=no',
            '--vd-lavc-threads=1', '--ad-lavc-threads=1', '--audio-display=embedded-first',
            '--vo=image', '--vo-image-format=jpg', '--vo-image-jpeg-quality=75',
            '--vo-image-outdir=' + str(directory),
            '--vf=lavfi=graph=[scale=w=320:h=180:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1]:o=[threads=1]',
            '--frames=1', '--length=0.1', '--', f'fd://{descriptor}']


async def _bounded_read(stream, cap):
    result = bytearray()
    while True:
        chunk = await stream.read(min(1024, cap + 1 - len(result)))
        if not chunk:
            return bytes(result)
        result.extend(chunk)
        if len(result) > cap:
            raise InspectionLimit('output_limit')


async def _stop(process):
    if process.returncode is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    await process.wait()


async def _run(argv, descriptor, directory):
    process = None
    collectors = []
    spawn = asyncio.create_task(asyncio.create_subprocess_exec(
        *argv, stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE, cwd=str(directory), pass_fds=(descriptor,),
        start_new_session=True, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
                                     'LC_ALL': 'C.UTF-8', 'HOME': str(directory)}))
    try:
        async with asyncio.timeout(TIMEOUT_S):
            process = await asyncio.shield(spawn)
            collectors = [asyncio.create_task(_bounded_read(process.stdout, MAX_STDOUT)),
                          asyncio.create_task(_bounded_read(process.stderr, MAX_STDERR)),
                          asyncio.create_task(process.wait())]
            stdout, _stderr, code = await asyncio.gather(*collectors)
            return stdout, code
    except BaseException:
        # Cover cancellation during process creation as well as during decoding.
        if process is None:
            while not spawn.done():
                try:
                    await asyncio.shield(spawn)
                except asyncio.CancelledError:
                    continue
                except (OSError, ValueError):
                    break
            try:
                process = spawn.result()
            except (OSError, ValueError):
                pass
        if process is not None:
            async def finish():
                try:
                    await _stop(process)
                finally:
                    for task in collectors:
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(*collectors, return_exceptions=True)
            cleanup = asyncio.create_task(finish())
            while not cleanup.done():
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    continue
            cleanup.result()
        raise


def _text(value):
    if not isinstance(value, str):
        return None
    value = ''.join(c for c in value if unicodedata.category(c) not in {'Cc', 'Cf'}).strip()[:240]
    if not value or re.search(r'[a-zA-Z][a-zA-Z0-9+.-]*://|^(?:[/\\]|[a-zA-Z]:[/\\])', value):
        return None
    return value


def parse_metadata(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_STDOUT:
        return None
    records = [line[len(PREFIX):] for line in raw.splitlines() if line.startswith(PREFIX)]
    if len(records) != 1 or len(records[0]) > 8192:
        return None
    try:
        data = json.loads(records[0])
    except (ValueError, UnicodeError, RecursionError):
        return None
    if not isinstance(data, dict):
        return None
    duration = data.get('duration_s')
    try:
        finite_duration = isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(duration)
    except OverflowError:
        finite_duration = False
    if not finite_duration or not 0 < duration <= 864000:
        duration = None
    tracks = data.get('tracks') if isinstance(data.get('tracks'), list) else []
    tracks = [{'type': t['type'], 'albumart': t.get('albumart') is True}
              for t in tracks[:16] if isinstance(t, dict) and t.get('type') in ('audio', 'video')]
    return {'duration_s': duration, 'title': _text(data.get('title')),
            'artist': _text(data.get('artist')), 'album': _text(data.get('album')), 'tracks': tracks}


def jpeg_dimensions(raw):
    """Header bounds, not a general JPEG decoder; encoder is the trusted mpv VO."""
    if not 4 <= len(raw) <= MAX_JPEG or raw[:2] != b'\xff\xd8' or raw[-2:] != b'\xff\xd9':
        return None
    offset = 2
    while offset + 4 <= len(raw):
        if raw[offset] != 255:
            return None
        marker = raw[offset + 1]
        length = int.from_bytes(raw[offset + 2:offset + 4], 'big')
        if length < 2 or offset + 2 + length > len(raw):
            return None
        if marker in {0xC0, 0xC1, 0xC2} and length >= 8:
            height = int.from_bytes(raw[offset + 5:offset + 7], 'big')
            width = int.from_bytes(raw[offset + 7:offset + 9], 'big')
            return (width, height) if raw[offset + 4] == 8 and 0 < width <= 320 and 0 < height <= 180 else None
        offset += 2 + length
    return None


async def inspect_fd(approved_fd: int, *, gate: asyncio.Semaphore, private_dir: Path):
    """Return sanitized metadata/real JPEG or absence; cancellation propagates.

    private_dir is an app-owned existing directory, never client input. Caller
    must retain the approved FD and hold a single shared gate across all jobs.
    No persistent cache, scheduling, API or resume behavior is implemented here.
    """
    absent = {'state': 'unavailable', 'metadata': None, 'poster_jpeg': None}
    if sys.platform != 'linux':
        return absent | {'reason': 'unsupported_platform'}
    async with gate:
        duplicate = None
        try:
            before = os.fstat(approved_fd)
            if not stat.S_ISREG(before.st_mode):
                return absent | {'reason': 'not_regular'}
            binary, script = _trusted_inputs()
            # os.dup shares seek position/flags. Reopen the pinned regular inode
            # through proc instead, then check that this really is the same file.
            duplicate = os.open(f'/proc/self/fd/{approved_fd}', os.O_RDONLY | os.O_CLOEXEC)
            if _identity(os.fstat(duplicate)) != _identity(before):
                return absent | {'reason': 'media_changed'}
            base = private_dir.resolve(strict=True)
            if not base.is_dir():
                return absent | {'reason': 'invalid_private_directory'}
            with tempfile.TemporaryDirectory(prefix='.pysh-inspect-', dir=base) as created:
                directory = Path(created)
                if directory.parent.resolve() != base or not directory.name.startswith('.pysh-inspect-'):
                    raise ValueError('private_directory_escape')
                raw, code = await _run(build_argv(binary, script, duplicate, directory), duplicate, directory)
                if _identity(os.fstat(approved_fd)) != _identity(before) or _identity(os.fstat(duplicate)) != _identity(before):
                    return absent | {'reason': 'media_changed'}
                metadata = parse_metadata(raw)
                if code != 0 or metadata is None:
                    return absent | {'reason': 'inspection_failed'}
                files = list(directory.iterdir())
                poster = None
                if len(files) == 1 and re.fullmatch(r'[0-9]+\.jpg', files[0].name) and not files[0].is_symlink():
                    with files[0].open('rb') as stream:
                        pixels = stream.read(MAX_JPEG + 1)
                    if jpeg_dimensions(pixels):
                        poster = pixels
                return {'state': 'ready', 'metadata': metadata, 'poster_jpeg': poster}
        except asyncio.CancelledError:
            raise
        except (OSError, ValueError, InspectionLimit, TimeoutError):
            return absent | {'reason': 'inspection_unavailable'}
        finally:
            if duplicate is not None:
                os.close(duplicate)
