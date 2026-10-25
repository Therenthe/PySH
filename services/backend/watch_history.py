"""Bounded browser-video sessions and atomic private watch history.

Every public method is synchronous and MUST be called under the existing
hub.media_lock. Caller provides approved canonical paths/identities, regular
read-only FDs, and revalidation; this helper never opens a media pathname.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import time
from typing import Callable

TTL = 120.0
MAX_RECORDS = 40
MAX_BYTES = 262_144
MAX_DURATION = 864_000.0
MAX_SEQUENCE = 9_007_199_254_740_991


class WatchError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _fingerprint(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _readonly(fd):
    try:
        import fcntl
    except ImportError as exc:
        raise WatchError('readonly_not_verifiable') from exc
    return fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY


def _finite(value, *, positive=False, maximum=MAX_DURATION):
    if type(value) not in (int, float):
        raise WatchError('invalid_progress')
    try:
        valid = math.isfinite(value) and (value > 0 if positive else value >= 0) and value <= maximum
    except OverflowError:
        valid = False
    if not valid:
        raise WatchError('invalid_progress')
    return float(value)


def _coordinates(path, identity):
    # Canonical approval is the caller's responsibility; do not resolve/open.
    try:
        path_size = len(path.encode('utf8')) if isinstance(path, str) else 0
    except UnicodeError:
        path_size = 0
    if not isinstance(path, str) or not path_size or '\0' in path or path_size > 4096 or not Path(path).is_absolute() or str(Path(path)) != path or '..' in Path(path).parts:
        raise WatchError('invalid_approved_path')
    if not isinstance(identity, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}', identity):
        raise WatchError('invalid_identity')


def _progress(position, duration, ended):
    position, duration = _finite(position), _finite(duration, positive=True)
    if type(ended) is not bool or position > duration + 1:
        raise WatchError('invalid_progress')
    position = min(position, duration)
    complete = ended or duration - position <= min(30, duration * .05)
    return position, duration, position >= 10 and not complete


@dataclass
class _Session:
    token: str
    path: str
    identity: str
    fd: int
    fingerprint: tuple
    expires: float
    sequence: int = -1
    history_enabled: bool = True


class WatchHistory:
    def __init__(self, store_path: Path, *, validate: Callable[[str, str], bool],
                 writer=None, monotonic=time.monotonic, wall=time.time):
        """store_path is app-owned, validate checks current root+identity safely.

        validate must never trust arbitrary stored paths: validate confinement
        first. False or an OSError hides that record; no paths are opened here.
        writer is a test seam; production uses the existing atomic JSON writer.
        """
        if writer is None:
            from .content import _write_json_atomic
            writer = _write_json_atomic
        self.store_path, self.validate, self.writer = Path(store_path), validate, writer
        self.monotonic, self.wall = monotonic, wall
        self.active = None
        self.records = self._load()

    def _load(self):
        try:
            with self.store_path.open('rb') as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return {}
            document = json.loads(raw)
            if not isinstance(document, dict) or type(document.get('version')) is not int or document['version'] != 1 or not isinstance(document.get('records'), list) or len(document['records']) > MAX_RECORDS:
                return {}
            records = {}
            for entry in document['records']:
                if not isinstance(entry, dict) or set(entry) != {'path', 'identity', 'position_s', 'duration_s', 'updated_at'}:
                    return {}
                _coordinates(entry['path'], entry['identity'])
                position, duration, resumable = _progress(entry['position_s'], entry['duration_s'], False)
                updated = _finite(entry['updated_at'], maximum=32_503_680_000)
                if not resumable or entry['identity'] in records:
                    return {}
                records[entry['identity']] = dict(entry, position_s=position, duration_s=duration, updated_at=updated)
            return records
        except (OSError, ValueError, UnicodeError, RecursionError, WatchError):
            return {}

    @staticmethod
    def _document(records):
        return {'version': 1, 'records': sorted(records.values(), key=lambda r: r['updated_at'], reverse=True)}

    def _bounded(self, records):
        entries = self._document(records)['records'][:MAX_RECORDS]
        while len(json.dumps({'version': 1, 'records': entries}, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf8')) > MAX_BYTES:
            entries.pop()
        return {r['identity']: r for r in entries}

    def _persist(self, records):
        records = self._bounded(records)
        try:
            self.writer(self.store_path, self._document(records))
        except (OSError, ValueError) as exc:
            raise WatchError('history_write_failed') from exc
        self.records = records

    def _close_active(self):
        active, self.active = self.active, None
        if active:
            os.close(active.fd)

    def expire(self):
        if self.active and self.monotonic() >= self.active.expires:
            self._close_active()
            return True
        return False

    def _available(self, path, identity):
        try:
            return self.validate(path, identity) is True
        except OSError:
            return False

    def _live(self, token=None):
        self.expire()
        active = self.active
        if not active or token is not None and token != active.token:
            raise WatchError('stale_video_session')
        try:
            valid = _fingerprint(os.fstat(active.fd)) == active.fingerprint and self._available(active.path, active.identity)
        except OSError:
            valid = False
        if not valid:
            self._close_active()
            raise WatchError('media_changed')
        return active

    def start(self, canonical_path: str, approved_fd: int, identity: str):
        self.expire()
        _coordinates(canonical_path, identity)
        info = os.fstat(approved_fd)
        if not stat.S_ISREG(info.st_mode) or not _readonly(approved_fd):
            raise WatchError('not_readonly_regular')
        if not self._available(canonical_path, identity):
            raise WatchError('media_changed')
        duplicate = os.dup(approved_fd)
        try:
            if _fingerprint(os.fstat(duplicate)) != _fingerprint(info):
                raise WatchError('media_changed')
            token = secrets.token_urlsafe(24)
            replacement = _Session(token, canonical_path, identity, duplicate, _fingerprint(info), self.monotonic() + TTL)
        except BaseException:
            os.close(duplicate)
            raise
        self._close_active()
        self.active = replacement
        previous = self.records.get(identity)
        return {'session_id': token, 'resume_position_s': previous['position_s'] if previous and previous['path'] == canonical_path else 0}

    def _sequence(self, active, sequence):
        if type(sequence) is not int or not 0 <= sequence <= MAX_SEQUENCE or sequence <= active.sequence:
            raise WatchError('stale_video_sequence')

    def heartbeat(self, token: str, sequence: int):
        active = self._live(token)
        self._sequence(active, sequence)
        active.sequence, active.expires = sequence, self.monotonic() + TTL

    def update(self, token: str, sequence: int, position_s, duration_s, *, ended=False, final=False):
        active = self._live(token)
        self._sequence(active, sequence)
        if type(final) is not bool:
            raise WatchError('invalid_progress')
        position, duration, resumable = _progress(position_s, duration_s, ended)
        if active.history_enabled:
            proposed = {key: record for key, record in self.records.items() if record['path'] != active.path}
            if resumable:
                proposed[active.identity] = {'path': active.path, 'identity': active.identity,
                    'position_s': position, 'duration_s': duration,
                    'updated_at': _finite(self.wall(), maximum=32_503_680_000)}
            # Commit before changing session sequence/state or closing its FD.
            self._persist(proposed)
        active.sequence, active.expires = sequence, self.monotonic() + TTL
        if ended:
            active.history_enabled = False
        if final:
            self._close_active()

    def close(self, token: str):
        self.expire()
        if self.active and self.active.token == token:
            self._close_active()
            return True
        return False

    def clear(self, identity: str):
        self.expire()
        proposed = {key: record for key, record in self.records.items() if key != identity}
        self._persist(proposed)
        if self.active and self.active.identity == identity:
            self.active.history_enabled = False

    def continuing(self):
        self.expire()
        return [dict(record) for record in self._document(self.records)['records']
                if self._available(record['path'], record['identity'])][:12]

    def in_use(self, device: int, inode: int):
        try:
            return self._live().fingerprint[:2] == (device, inode)
        except WatchError:
            return False

    def after_unlink(self, canonical_path: str, identity: str):
        """Caller invokes ONLY after successful guarded unlink. No delete right.

        Best-effort persistence cannot turn completed unlink into a failure.
        Memory/session invalidation still prevents late progress resurrection.
        """
        self.expire()
        proposed = {key: record for key, record in self.records.items()
                    if not (key == identity and record['path'] == canonical_path)}
        if self.active and self.active.path == canonical_path and self.active.identity == identity:
            self._close_active()
        self.records = proposed
        try:
            self._persist(proposed)
            return True
        except WatchError:
            return False

    def shutdown(self):
        self._close_active()
