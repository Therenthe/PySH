"""Durable, local IPTV recording jobs and their independent service process.

Only this daemon owns FFmpeg children. The Hub writes SQLite commands; closing
Chromium or restarting the Hub does not stop a recording. No network listener is
exposed: the temporary HLS relay binds loopback and uses opaque resource tokens.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socketserver
import sqlite3
import stat
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any
import uuid


ACTIVE = ('starting', 'recording', 'stopping')
TERMINAL = ('completed', 'stopped', 'cancelled', 'failed', 'interrupted', 'missed', 'deleted')
MIN_FREE = 256 * 1024 * 1024
STOP_FREE = 128 * 1024 * 1024
MAX_JOBS = 2000
MAX_CONCURRENT = 2


class RecorderError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _iso(value: float | None) -> str | None:
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def _timestamp(value: str) -> float:
    try:
        if not isinstance(value, str) or len(value) > 40:
            raise ValueError()
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError()
        result = parsed.timestamp()
        if not 0 < result < 4102444800:
            raise ValueError()
        return result
    except (ValueError, TypeError, OverflowError) as exc:
        raise RecorderError('recording_invalid_time') from exc


def _text(value: Any, maximum: int = 200) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise RecorderError('recording_invalid_request')
    return value.strip()


def _directory(path: Path) -> Path:
    """Private state and generated output must not traverse symlink directories."""
    path = path.expanduser().absolute()
    for ancestor in reversed((path, *path.parents)):
        if ancestor.is_symlink():
            raise RecorderError('recording_unsafe_directory')
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.is_dir():
        raise RecorderError('recording_unsafe_directory')
    return path


class RecorderStore:
    def __init__(self, data_dir: str | Path, output_dir: str | Path | None = None, *, clock=time.time):
        self.directory = _directory(Path(data_dir) / 'iptv-recordings')
        self.database = self.directory / 'jobs.sqlite3'
        self.clock = clock
        if self.database.is_symlink():
            raise RecorderError('recording_unsafe_directory')
        with self._db(write=True) as db:
            db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('''CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, channel_id TEXT NOT NULL, channel_name TEXT NOT NULL,
              url TEXT NOT NULL, title TEXT NOT NULL, start REAL NOT NULL, end REAL NOT NULL,
              before_minutes INTEGER NOT NULL, after_minutes INTEGER NOT NULL,
              state TEXT NOT NULL, error TEXT, stop_requested INTEGER NOT NULL DEFAULT 0,
              filename TEXT NOT NULL, device TEXT, inode TEXT, created REAL NOT NULL,
              updated REAL NOT NULL, started REAL, finished REAL, version INTEGER NOT NULL DEFAULT 1)''')
            if 'request_key' not in {column['name'] for column in db.execute('PRAGMA table_info(jobs)')}:
                db.execute('ALTER TABLE jobs ADD COLUMN request_key TEXT')
            if 'request_fingerprint' not in {column['name'] for column in db.execute('PRAGMA table_info(jobs)')}:
                db.execute('ALTER TABLE jobs ADD COLUMN request_fingerprint TEXT')
            db.execute('CREATE UNIQUE INDEX IF NOT EXISTS recording_request_key ON jobs(request_key)')
            stored = db.execute("SELECT value FROM meta WHERE key='output_dir'").fetchone()
            chosen = Path(output_dir) if output_dir is not None else Path(stored['value']) if stored else Path.home() / 'Videos' / 'MediaTool'
            self.output_dir = _directory(chosen)
            if stored and Path(stored['value']) != self.output_dir:
                raise RecorderError('recording_output_changed')
            db.execute("INSERT OR IGNORE INTO meta VALUES ('output_dir', ?)", (str(self.output_dir),))
        try:
            self.database.chmod(0o600)
        except OSError:
            pass

    @contextlib.contextmanager
    def _db(self, *, write=False):
        db = sqlite3.connect(self.database, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA busy_timeout=5000')
            db.execute('PRAGMA journal_mode=WAL')
            if write:
                db.execute('BEGIN IMMEDIATE')
            yield db
            if write:
                db.commit()
        except BaseException:
            if write:
                db.rollback()
            raise
        finally:
            db.close()

    def _row(self, db, job_id: str):
        if not isinstance(job_id, str) or not re.fullmatch('[0-9a-f]{32}', job_id):
            raise RecorderError('recording_not_found')
        row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
        if row is None or row['state'] == 'deleted':
            raise RecorderError('recording_not_found')
        return row

    def _interval(self, start_at, end_at, before_minutes, after_minutes, *, repeated=False):
        start, end = _timestamp(start_at), _timestamp(end_at)
        if any(type(n) is not int or not 0 <= n <= 60 for n in (before_minutes, after_minutes)):
            raise RecorderError('recording_invalid_padding')
        now = self.clock()
        if end <= start or end - start > 86400 or not repeated and (end + after_minutes * 60 <= now or start > now + 31 * 86400):
            raise RecorderError('recording_invalid_time')
        return start, end

    def _capacity(self, db, start: float, end: float, exclude=''):
        intervals = db.execute("SELECT start-before_minutes*60 AS a,end+after_minutes*60 AS b FROM jobs WHERE id!=? AND state IN ('scheduled','starting','recording','stopping') AND end+after_minutes*60>? AND start-before_minutes*60<?", (exclude, start, end)).fetchall()
        events = [(start, 1), (end, -1)]
        for item in intervals:
            events.extend(((max(start, item['a']), 1), (min(end, item['b']), -1)))
        count = 0
        for _, delta in sorted(events):
            count += delta
            if count > MAX_CONCURRENT:
                raise RecorderError('recording_capacity')

    def create(self, channel: dict, title: str, start_at: str, end_at: str, before_minutes=0, after_minutes=0, request_id=None):
        from .iptv_catalog import public_url, verify_public_url
        if not isinstance(channel, dict):
            raise RecorderError('recording_invalid_request')
        channel_id, channel_name = _text(channel.get('id'), 160), _text(channel.get('name'), 240)
        # FFmpeg never sees this external URL: every HLS resource uses the safe relay.
        url = public_url(_text(channel.get('url'), 4096))
        title = _text(title)
        start, end = self._interval(start_at, end_at, before_minutes, after_minutes, repeated=True)
        try:
            request_key = str(uuid.UUID(request_id)) if request_id is not None else None
        except (ValueError, TypeError, AttributeError) as exc:
            raise RecorderError('recording_invalid_request') from exc
        values = (channel_id, channel_name, url, title, start, end, before_minutes, after_minutes)
        fingerprint = hashlib.sha256(json.dumps(values, ensure_ascii=False, separators=(',', ':')).encode('utf8')).hexdigest()
        def repeated(db):
            old = db.execute('SELECT * FROM jobs WHERE request_key=?', (request_key,)).fetchone() if request_key else None
            if old is not None:
                original = old['request_fingerprint'] or hashlib.sha256(json.dumps(
                    tuple(old[key] for key in ('channel_id', 'channel_name', 'url', 'title', 'start', 'end', 'before_minutes', 'after_minutes')),
                    ensure_ascii=False, separators=(',', ':')).encode('utf8')).hexdigest()
                if original != fingerprint:
                    raise RecorderError('recording_request_conflict')
                return self._public(old)
            return None
        with self._db() as db:
            old = repeated(db)
            if old is not None:
                return old
        self._interval(start_at, end_at, before_minutes, after_minutes)
        verify_public_url(url)
        now, job_id = self.clock(), uuid.uuid4().hex
        with self._db(write=True) as db:
            old = repeated(db)
            if old is not None:
                return old
            # Keep deletion tombstones through their whole scheduled window;
            # afterwards an old POST is already rejected as a past interval.
            db.execute("DELETE FROM jobs WHERE state='deleted' AND end+after_minutes*60<?", (now - 86400,))
            if db.execute('SELECT count(*) FROM jobs').fetchone()[0] >= MAX_JOBS:
                raise RecorderError('recording_limit')
            self._capacity(db, start - before_minutes * 60, end + after_minutes * 60)
            db.execute('''INSERT INTO jobs (id,channel_id,channel_name,url,title,start,end,before_minutes,after_minutes,state,filename,created,updated,request_key,request_fingerprint)
                       VALUES (?,?,?,?,?,?,?,?,?,'scheduled',?,?,?,?,?)''',
                       (job_id, *values, job_id + '.mkv', now, now, request_key, fingerprint))
        return self.get(job_id)

    def edit(self, job_id: str, **changes):
        if not changes or set(changes) - {'title', 'start_at', 'end_at', 'before_minutes', 'after_minutes'}:
            raise RecorderError('recording_invalid_request')
        with self._db(write=True) as db:
            row = self._row(db, job_id)
            if row['state'] != 'scheduled':
                raise RecorderError('recording_not_editable')
            before, after = changes.get('before_minutes', row['before_minutes']), changes.get('after_minutes', row['after_minutes'])
            start, end = self._interval(changes.get('start_at', _iso(row['start'])), changes.get('end_at', _iso(row['end'])), before, after)
            self._capacity(db, start - before * 60, end + after * 60, job_id)
            db.execute('UPDATE jobs SET title=?,start=?,end=?,before_minutes=?,after_minutes=?,updated=?,version=version+1 WHERE id=?',
                       (_text(changes.get('title', row['title'])), start, end, before, after, self.clock(), job_id))
        return self.get(job_id)

    def cancel(self, job_id):
        with self._db(write=True) as db:
            row = self._row(db, job_id)
            if row['state'] != 'scheduled':
                raise RecorderError('recording_not_editable')
            db.execute("UPDATE jobs SET state='cancelled',finished=?,updated=?,version=version+1 WHERE id=?", (self.clock(), self.clock(), job_id))
        return self.get(job_id)

    def stop(self, job_id):
        with self._db(write=True) as db:
            row = self._row(db, job_id)
            if row['state'] not in ACTIVE:
                raise RecorderError('recording_not_active')
            db.execute('UPDATE jobs SET stop_requested=1,updated=?,version=version+1 WHERE id=?', (self.clock(), job_id))
        return self.get(job_id)

    def _file(self, row):
        if row['filename'] != row['id'] + '.mkv' or self.output_dir.is_symlink():
            raise RecorderError('recording_file_changed')
        return self.output_dir / row['filename']

    @contextlib.contextmanager
    def _output_parent(self):
        parent = None
        try:
            if sys.platform.startswith('linux'):
                parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                for component in self.output_dir.parts[1:]:
                    following = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                    os.close(parent)
                    parent = following
                if Path('/proc/self/fd', str(parent)).resolve() != self.output_dir:
                    raise RecorderError('recording_unsafe_directory')
            else:
                _directory(self.output_dir)
            yield parent
        finally:
            if parent is not None:
                os.close(parent)

    def _open(self, row, flags):
        path = self._file(row)
        with self._output_parent() as parent:
            return os.open(path.name if parent is not None else path,
                           flags | getattr(os, 'O_NOFOLLOW', 0), 0o600,
                           **({'dir_fd': parent} if parent is not None else {}))

    def _stat(self, row):
        try:
            info = self._file(row).lstat()
            if not stat.S_ISREG(info.st_mode) or (str(info.st_dev), str(info.st_ino)) != (row['device'], row['inode']):
                return None
            return info
        except OSError:
            return None

    def _public(self, row):
        info = self._stat(row)
        return {'id': row['id'], 'channel_id': row['channel_id'], 'channel_name': row['channel_name'],
                'title': row['title'], 'start_at': _iso(row['start']), 'end_at': _iso(row['end']),
                'record_start_at': _iso(row['start'] - row['before_minutes'] * 60),
                'record_end_at': _iso(row['end'] + row['after_minutes'] * 60),
                'before_minutes': row['before_minutes'], 'after_minutes': row['after_minutes'],
                'state': row['state'], 'error': row['error'], 'stop_requested': bool(row['stop_requested']),
                'created_at': _iso(row['created']), 'started_at': _iso(row['started']), 'finished_at': _iso(row['finished']),
                'has_file': info is not None and info.st_size > 0, 'size': info.st_size if info else 0,
                'version': row['version']}

    def get(self, job_id):
        with self._db() as db:
            return self._public(self._row(db, job_id))

    def list(self):
        with self._db() as db:
            return [self._public(row) for row in db.execute("SELECT * FROM jobs WHERE state!='deleted' ORDER BY created DESC LIMIT ?", (MAX_JOBS,))]

    def status(self):
        with self._db() as db:
            heartbeat = db.execute("SELECT value FROM meta WHERE key='heartbeat'").fetchone()
            active = db.execute("SELECT count(*) FROM jobs WHERE state IN ('starting','recording','stopping')").fetchone()[0]
        return {'service_active': bool(heartbeat and 0 <= self.clock() - float(heartbeat['value']) < 10),
                'ffmpeg_available': shutil.which('ffmpeg') is not None, 'output_directory': str(self.output_dir),
                'free_bytes': shutil.disk_usage(self.output_dir).free, 'minimum_free_bytes': MIN_FREE,
                'max_concurrent': MAX_CONCURRENT, 'active_count': active}

    def in_use(self, path: str | Path) -> bool:
        """Shared Media must protect the daemon's files too, including start-up."""
        try:
            candidate = Path(path).expanduser().absolute()
            try:
                info = candidate.stat()
                identity = (str(info.st_dev), str(info.st_ino))
            except OSError:
                identity = None
            with self._db() as db:
                rows = db.execute("SELECT * FROM jobs WHERE state IN ('starting','recording','stopping')").fetchall()
            return any(candidate == self._file(row) or identity is not None and identity == (row['device'], row['inode'])
                       for row in rows)
        except (ValueError, TypeError, OSError):
            return False

    def open_recording(self, job_id) -> int:
        """Caller owns fd; never re-open the returned display path for streaming."""
        with self._db() as db:
            row = self._row(db, job_id)
            if row['state'] in ACTIVE:
                raise RecorderError('recording_active')
            try:
                fd = self._open(row, os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0))
            except OSError as exc:
                raise RecorderError('recording_file_unavailable') from exc
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size <= 0 or (str(info.st_dev), str(info.st_ino)) != (row['device'], row['inode']):
                os.close(fd)
                raise RecorderError('recording_file_changed')
            return fd

    def recording_path(self, job_id):
        with self._db() as db:
            row = self._row(db, job_id)
            if not self._stat(row):
                raise RecorderError('recording_file_unavailable')
            return self._file(row)

    def delete(self, job_id):
        with self._db(write=True) as db:
            row = self._row(db, job_id)
            if row['state'] in ACTIVE or row['state'] == 'scheduled':
                raise RecorderError('recording_active')
            path = self._file(row)
            if path.exists() or path.is_symlink():
                info = self._stat(row)
                if info is None:
                    raise RecorderError('recording_file_changed')
                # Reuse the Hub's atomic quarantine/identity-checked unlink.
                # A raced replacement is restored without overwriting a new name.
                from .content import Content, ContentError
                content = Content(self.directory)
                content._media_roots = lambda: [self.output_dir]
                try:
                    content._delete_media(str(path), Content._delete_token(path, info))
                except ContentError as exc:
                    mapping = {'media_changed': 'recording_file_changed',
                               'media_delete_unavailable': 'recording_delete_unavailable',
                               'media_delete_recovery_required': 'recording_delete_recovery_required'}
                    raise RecorderError(mapping.get(exc.code, 'recording_delete_failed')) from exc
            db.execute("UPDATE jobs SET state='deleted',updated=?,version=version+1 WHERE id=?", (self.clock(), job_id))
        return {'deleted': True}


class _RelayServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self):
        self.proxies = {}
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(('127.0.0.1', 0), _RelayHandler)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class _RelayHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass  # No stream URLs/tokens in journald.

    def do_GET(self):
        match = re.fullmatch(r'/r/([0-9a-f]{32})/([^/?]+)/([^/?]+)', self.path)
        if not match or self.headers.get('Host') != '127.0.0.1:' + str(self.server.server_port):
            self.send_error(404)
            return
        proxy = self.server.proxies.get(match.group(1))
        if proxy is None:
            self.send_error(404)
            return
        try:
            result = proxy.fetch(match.group(2), match.group(3), self.headers.get('Range'))
            self.send_response(result.status_code)
            self.send_header('Content-Type', result.media_type)
            self.send_header('Content-Length', str(len(result.data)))
            self.send_header('Cache-Control', 'no-store')
            for key, value in result.headers.items():
                if key.lower() in {'content-range', 'accept-ranges'}:
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(result.data)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.send_error(502, 'Stream unavailable')


class RecorderDaemon:
    def __init__(self, store: RecorderStore, *, popen=subprocess.Popen, disk_free=None, proxy_factory=None):
        self.store, self.popen = store, popen
        self.disk_free = disk_free or (lambda: shutil.disk_usage(store.output_dir).free)
        self.proxy_factory = proxy_factory
        self.running = {}
        self.relay = None
        self.closed = False
        self._opaque_hls_options = None

    def _hls_options(self):
        if self._opaque_hls_options is None:
            self._opaque_hls_options = []
            if self.popen is subprocess.Popen:
                # Patched FFmpeg versions additionally enforce filename suffixes.
                # The relay deliberately uses opaque paths and validates bytes;
                # its strict demuxer whitelist remains enabled below.
                try:
                    help_text = subprocess.run(['ffmpeg', '-hide_banner', '-h', 'demuxer=hls'],
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=True).stdout
                    if b'extension_picky' in help_text:
                        self._opaque_hls_options = ['-extension_picky', '0']
                except (OSError, subprocess.SubprocessError):
                    pass
        return self._opaque_hls_options

    def _set(self, job_id, **changes):
        allowed = {'state', 'error', 'device', 'inode', 'started', 'finished'}
        if set(changes) - allowed:
            raise ValueError('invalid_recorder_update')
        with self.store._db(write=True) as db:
            columns = ','.join(key + '=?' for key in changes)
            db.execute(f'UPDATE jobs SET {columns},updated=?,version=version+1 WHERE id=?', (*changes.values(), self.store.clock(), job_id))

    def recover(self):
        with self.store._db(write=True) as db:
            db.execute("UPDATE jobs SET state='interrupted',error='recording_service_interrupted',finished=?,updated=?,version=version+1 WHERE state IN ('starting','recording','stopping')", (self.store.clock(), self.store.clock()))

    def _source(self, row):
        if self.proxy_factory is None:
            from .iptv_stream import IPTVStream
            factory = IPTVStream
        else:
            factory = self.proxy_factory
        if self.relay is None:
            self.relay = _RelayServer()
            threading.Thread(target=self.relay.serve_forever, name='iptv-recorder-relay', daemon=True).start()
        proxy = factory(path_prefix='/r/' + row['id'])
        session = proxy.start(row['channel_id'], row['url'])
        self.relay.proxies[row['id']] = proxy
        return proxy, session, 'http://127.0.0.1:' + str(self.relay.server_port) + session['stream_url']

    def _start(self, row):
        if self.disk_free() < MIN_FREE:
            self._set(row['id'], state='failed', error='recording_disk_full', finished=self.store.clock())
            return
        if shutil.which('ffmpeg') is None and self.popen is subprocess.Popen:
            self._set(row['id'], state='failed', error='recording_ffmpeg_unavailable', finished=self.store.clock())
            return
        proxy = session = None
        fd = None
        try:
            proxy, session, source = self._source(row)
            fd = self.store._open(row, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            info = os.fstat(fd)
            self._set(row['id'], device=str(info.st_dev), inode=str(info.st_ino))
            with os.fdopen(fd, 'wb') as output:
                fd = None
                process = self.popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostats',
                    '-protocol_whitelist', 'http,tcp,crypto', '-rw_timeout', '15000000',
                    '-format_whitelist', 'hls,mpegts,mov,aac,mp3,ac3,eac3,webvtt',
                    '-allowed_extensions', 'ALL', '-seg_format_options', 'enable_drefs=0:use_absolute_path=0',
                    *self._hls_options(), '-f', 'hls', '-i', source,
                    '-map', '0:v?', '-map', '0:a?', '-sn', '-dn', '-c', 'copy',
                    # fd: keeps this owned regular descriptor seekable. pipe:
                    # forbids Matroska's deferred AAC header/trailer updates.
                    '-max_interleave_delta', '1000000', '-max_muxing_queue_size', '1024', '-f', 'matroska', 'fd:'],
                    stdin=subprocess.PIPE, stdout=output, stderr=subprocess.DEVNULL, close_fds=True)
            self.running[row['id']] = {'process': process, 'proxy': proxy, 'session': session['session_id'], 'stop_at': None, 'stop_reason': None, 'kill_at': None}
            self._set(row['id'], state='recording', started=self.store.clock(), error=None)
        except Exception:
            if fd is not None:
                os.close(fd)
            if proxy is not None and session is not None:
                with contextlib.suppress(Exception):
                    proxy.close(session['session_id'])
            if self.relay is not None:
                self.relay.proxies.pop(row['id'], None)
            self._set(row['id'], state='failed', error='recording_start_failed', finished=self.store.clock())

    def _request_stop(self, job_id, item, reason):
        if item['stop_at'] is not None:
            return
        item['stop_at'], item['stop_reason'] = time.monotonic(), reason
        self._set(job_id, state='stopping')
        try:
            item['process'].stdin.write(b'q\n')
            item['process'].stdin.flush()
        except (OSError, ValueError, AttributeError):
            pass

    def _finish(self, job_id, item, code):
        reason = item['stop_reason']
        if reason == 'disk':
            state, error = 'stopped', 'recording_disk_full'
        elif reason == 'user':
            state, error = 'stopped', None if code == 0 else 'recording_finalization_failed'
        elif reason == 'schedule' and code == 0:
            state, error = 'completed', None
        elif reason == 'shutdown':
            state, error = 'interrupted', 'recording_service_interrupted'
        else:
            state, error = 'failed', 'recording_stream_ended' if code == 0 else 'recording_stream_failed'
        self._set(job_id, state=state, error=error, finished=self.store.clock())
        try:
            if item['process'].stdin:
                item['process'].stdin.close()
        finally:
            with contextlib.suppress(Exception):
                item['proxy'].close(item['session'])
            if self.relay is not None:
                self.relay.proxies.pop(job_id, None)
            del self.running[job_id]

    def tick(self):
        now = self.store.clock()
        with self.store._db(write=True) as db:
            db.execute("INSERT OR REPLACE INTO meta VALUES ('heartbeat',?)", (str(now),))
            for job_id, item in tuple(self.running.items()):
                row = self.store._row(db, job_id)
                code = item['process'].poll()
                if code is not None:
                    # Update outside this write transaction to avoid self-deadlock.
                    continue
                if row['stop_requested']:
                    item['pending_reason'] = 'user'
                elif now >= row['end'] + row['after_minutes'] * 60:
                    item['pending_reason'] = 'schedule'
                elif self.disk_free() < STOP_FREE:
                    item['pending_reason'] = 'disk'
            db.execute("UPDATE jobs SET state='missed',error='recording_missed',finished=?,updated=?,version=version+1 WHERE state='scheduled' AND end+after_minutes*60<=?", (now, now, now))
            due = db.execute("SELECT * FROM jobs WHERE state='scheduled' AND start-before_minutes*60<=? ORDER BY start LIMIT ?", (now, MAX_CONCURRENT - len(self.running))).fetchall()
            for row in due:
                db.execute("UPDATE jobs SET state='starting',updated=?,version=version+1 WHERE id=?", (now, row['id']))
        for job_id, item in tuple(self.running.items()):
            code = item['process'].poll()
            if code is not None:
                self._finish(job_id, item, code)
                continue
            reason = item.pop('pending_reason', None)
            if reason:
                self._request_stop(job_id, item, reason)
            elapsed = time.monotonic() - item['stop_at'] if item['stop_at'] is not None else 0
            if elapsed > 13:
                item['process'].kill()
            elif elapsed > 8 and item['kill_at'] is None:
                item['process'].terminate()
                item['kill_at'] = time.monotonic()
        for row in due:
            self._start(row)

    def close(self):
        if self.closed:
            return
        self.closed = True
        for job_id, item in tuple(self.running.items()):
            self._request_stop(job_id, item, 'shutdown')
        deadline = time.monotonic() + 13
        while self.running and time.monotonic() < deadline:
            for job_id, item in tuple(self.running.items()):
                code = item['process'].poll()
                if code is not None:
                    self._finish(job_id, item, code)
                elif time.monotonic() - item['stop_at'] > 8:
                    item['process'].terminate()
            if self.running:
                time.sleep(0.1)
        for job_id, item in tuple(self.running.items()):
            item['process'].kill()
            try:
                item['process'].wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
            self._finish(job_id, item, -9)
        if self.relay is not None:
            self.relay.shutdown()
            self.relay.server_close()
        with self.store._db(write=True) as db:
            db.execute("INSERT OR REPLACE INTO meta VALUES ('heartbeat','0')")


def main():
    parser = argparse.ArgumentParser(description='PySH independent local IPTV recording service')
    parser.add_argument('--daemon', action='store_true', required=True)
    parser.add_argument('--data-dir', default=os.environ.get('PI_HUB_DATA', str(Path.home() / '.local/share/pi-smart-hub')))
    arguments = parser.parse_args()
    store = RecorderStore(arguments.data_dir)
    if not sys.platform.startswith('linux'):
        raise SystemExit('The recording service requires Linux.')
    import fcntl
    descriptor = os.open(store.directory / 'daemon.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('The recording service is already running.')
        stopped = threading.Event()
        signal.signal(signal.SIGTERM, lambda *_: stopped.set())
        signal.signal(signal.SIGINT, lambda *_: stopped.set())
        daemon = RecorderDaemon(store)
        try:
            daemon.recover()
            while not stopped.is_set():
                daemon.tick()
                stopped.wait(1)
        finally:
            daemon.close()


if __name__ == '__main__':
    main()
