"""Bounded local media composition; uses the existing Hub media lock only."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
import contextlib
import json
import mimetypes
import os
from pathlib import Path
import re
import stat
import sys
import time
from anyio import CancelScope

from .content import ContentError
from .descriptor_response import DescriptorFileResponse, DescriptorResponseUnavailable
from .mpv_inspector import inspect_fd, jpeg_dimensions
from .watch_history import WatchHistory, WatchError

IDENTITY = r'm1_[0-9a-f]{64}'
SESSION = r'[A-Za-z0-9_-]{32}'


async def media_await(operation, *, on_cancel=None):
    """Drain an owned operation before its caller releases media_lock.

    Cancellation changes acknowledgement, not whether a started worker finishes.
    The optional synchronous cleanup receives only a successful owned result.
    """
    async def owned():
        with CancelScope(shield=True):
            return await operation
    work = asyncio.create_task(owned())
    try:
        return await asyncio.shield(work)
    except asyncio.CancelledError:
        with CancelScope(shield=True):
            while not work.done():
                try:
                    await asyncio.shield(work)
                except asyncio.CancelledError:
                    continue
                except Exception:
                    break
            try:
                result = work.result()
            except (Exception, asyncio.CancelledError):
                pass
            else:
                if on_cancel is not None:
                    on_cancel(result)
        raise


async def media_thread(function, *args, on_cancel=None, **kwargs):
    return await media_await(asyncio.to_thread(function, *args, **kwargs), on_cancel=on_cancel)


def release_unused_response(response):
    response.close_owned()


class LocalMedia:
    def __init__(self, directory: Path, content, lock: asyncio.Lock):
        self.content, self.lock = content, lock
        self.directory = directory / 'local-media'
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.watch = WatchHistory(self.directory / 'watch.json', validate=self.available)
        self.cache = OrderedDict()
        self.jobs = {}
        self.inspector_gate = asyncio.Semaphore(1)

    def open_approved(self, path: str, expected: str | None = None):
        """Confine first, hold nofollow ancestors and pin the observed inode."""
        if not sys.platform.startswith('linux') or not Path('/proc/self/fd').is_dir():
            raise ContentError('media_descriptor_unavailable')
        canonical = self.content.resolve_media(path)
        if canonical.suffix.lower() not in self.content.AUDIO_EXTENSIONS | self.content.VIDEO_EXTENSIONS:
            raise ContentError('media_not_supported')
        parent = descriptor = None
        try:
            parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            for component in canonical.parent.parts[1:]:
                following = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                os.close(parent)
                parent = following
            descriptor = os.open(canonical.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            observed = os.fstat(descriptor)
            if not stat.S_ISREG(observed.st_mode):
                raise ContentError('media_not_file')
            if Path('/proc/self/fd', str(parent)).resolve() != canonical.parent or Path('/proc/self/fd', str(descriptor)).resolve() != canonical:
                raise ContentError('media_changed')
            # Recheck current root membership and name identity after the open.
            if self.content.resolve_media(canonical) != canonical:
                raise ContentError('media_changed')
            current = canonical.stat(follow_symlinks=False)
            identity = self.content.media_identity(canonical, observed)
            if self.content.media_identity(canonical, current) != identity or expected is not None and expected != identity:
                raise ContentError('media_changed')
            result, descriptor = descriptor, None
            return str(canonical), result, identity
        except (OSError, RuntimeError) as exc:
            raise ContentError('media_unavailable') from exc
        finally:
            for value in (descriptor, parent):
                if value is not None:
                    os.close(value)

    def available(self, path, identity):
        try:
            _, descriptor, _ = self.open_approved(path, identity)
            os.close(descriptor)
            return True
        except ContentError:
            return False

    def _cached(self, path, identity):
        entry = self.cache.get(identity)
        if not entry or entry['path'] != path:
            return None
        if entry['state'] == 'unavailable' and time.monotonic() - entry['at'] > 600:
            self.cache.pop(identity, None)
            return None
        self.cache.move_to_end(identity)
        return entry

    @staticmethod
    def _summary(entry):
        return {'state': entry['state'], 'metadata': entry['metadata'], 'artwork_available': bool(entry['poster'])}

    def enrich(self, listing):
        for item in listing.get('items', []):
            identity = item.get('media_identity')
            entry = self._cached(item['path'], identity) if identity else None
            item['metadata'] = entry['metadata'] if entry else None
            item['artwork_available'] = bool(entry and entry['poster'])
        return listing

    def _remember(self, path, identity, result):
        poster = result.get('poster_jpeg')
        if not isinstance(poster, bytes) or not jpeg_dimensions(poster):
            poster = None
        metadata = result.get('metadata')
        try:
            metadata_bytes = json.dumps(metadata, ensure_ascii=False, allow_nan=False).encode('utf8')
            if not isinstance(metadata, dict) or len(metadata_bytes) > 16384:
                metadata = None
                metadata_bytes = b''
        except (ValueError, TypeError, UnicodeError):
            metadata, metadata_bytes = None, b''
        self.cache[identity] = {'path': path, 'state': result.get('state') if result.get('state') == 'ready' else 'unavailable',
                                'metadata': metadata, 'poster': poster, 'at': time.monotonic(),
                                'bytes': len(poster or b'') + len(metadata_bytes) + len(path.encode('utf8')) + len(identity)}
        self.cache.move_to_end(identity)
        while len(self.cache) > 64 or sum(entry['bytes'] for entry in self.cache.values()) > 8 * 1024 * 1024:
            self.cache.popitem(last=False)

    async def _open_for_inspection(self, path, identity):
        return await media_thread(self.open_approved, path, identity,
                                  on_cancel=lambda opened: os.close(opened[1]))

    async def inspect(self, path, identity):
        async with self.lock:
            canonical, descriptor, actual = await self._open_for_inspection(path, identity)
            entry = self._cached(canonical, actual)
            if entry:
                os.close(descriptor)
                return self._summary(entry)
            task = self.jobs.get(actual)
            if task:
                os.close(descriptor)
            elif len(self.jobs) >= 8:
                os.close(descriptor)
                raise ContentError('media_inspection_busy')
            else:
                task = asyncio.create_task(self._inspect_owned(canonical, descriptor, actual))
                self.jobs[actual] = task
        # Request cancellation cancels/reaps its owned inspector, never Player.
        return await task

    async def _inspect_owned(self, path, descriptor, identity):
        try:
            result = await inspect_fd(descriptor, gate=self.inspector_gate, private_dir=self.directory)
            async with self.lock:
                if not await media_thread(self.available, path, identity):
                    raise ContentError('media_changed')
                self._remember(path, identity, result)
                return self._summary(self.cache[identity])
        finally:
            os.close(descriptor)
            if self.jobs.get(identity) is asyncio.current_task():
                self.jobs.pop(identity, None)

    def start(self, path, identity, resume):
        canonical, descriptor, actual = self.open_approved(path, identity)
        try:
            if Path(canonical).suffix.lower() not in self.content.VIDEO_EXTENSIONS:
                raise ContentError('media_not_video')
            if not resume and actual in self.watch.records:
                self.watch.clear(actual)
            result = self.watch.start(canonical, descriptor, actual)
            previous = self.watch.records.get(actual)
            return {'session_id': result['session_id'], 'media_identity': actual,
                    'resume_position_s': result['resume_position_s'] if resume else 0,
                    'duration_s': previous['duration_s'] if previous else None,
                    'stream_url': '/api/media/file?session_id=' + result['session_id']}
        finally:
            os.close(descriptor)

    def cancel_started(self, result):
        # Still under media_lock: never close any later replacement session.
        self.watch.close(result['session_id'])

    def stream(self, path=None, identity=None, session_id=None):
        if session_id:
            if not re.fullmatch(SESSION, session_id):
                raise WatchError('stale_video_session')
            active = self.watch._live(session_id)
            if path is not None and path != active.path or identity is not None and identity != active.identity:
                raise ContentError('media_changed')
            descriptor, canonical, owned = active.fd, active.path, False
        else:
            self.watch.expire()
            if self.watch.active:
                raise ContentError('media_session_required')
            if not path:
                raise ContentError('media_not_found')
            canonical, descriptor, _ = self.open_approved(path, identity)
            owned = True
        try:
            return DescriptorFileResponse(descriptor, media_type=mimetypes.guess_type(canonical)[0] or 'application/octet-stream')
        except DescriptorResponseUnavailable as exc:
            raise ContentError('media_descriptor_unavailable') from exc
        finally:
            if owned:
                os.close(descriptor)

    def continuing(self):
        items = []
        for record in self.watch.continuing():
            entry = self._cached(record['path'], record['identity'])
            items.append({**{key: record[key] for key in ('path', 'position_s', 'duration_s', 'updated_at')},
                          'name': Path(record['path']).name, 'media_identity': record['identity'],
                          'metadata': entry['metadata'] if entry else None,
                          'artwork_available': bool(entry and entry['poster'])})
        return {'items': items}

    def clear(self, path, identity):
        existing = self.watch.records.get(identity)
        active = self.watch.active
        if existing and existing['path'] != path or active and active.identity == identity and active.path != path:
            raise ContentError('media_changed')
        if existing and existing['path'] == path or active and active.path == path and active.identity == identity:
            self.watch.clear(identity)
        return {'cleared': True}

    def artwork(self, path, identity):
        canonical, descriptor, actual = self.open_approved(path, identity)
        os.close(descriptor)
        entry = self._cached(canonical, actual)
        if not entry or not entry['poster']:
            raise ContentError('media_artwork_unavailable')
        return entry['poster']

    def before_delete(self, path):
        """Return observed identity; original guarded delete remains authority."""
        try:
            canonical, descriptor, identity = self.open_approved(path)
        except ContentError:
            return None  # Original delete preserves its precise error semantics.
        try:
            info = os.fstat(descriptor)
            if self.watch.in_use(info.st_dev, info.st_ino):
                raise ContentError('media_in_use')
            return canonical, identity
        finally:
            os.close(descriptor)

    def after_delete(self, path, observed):
        for identity, entry in list(self.cache.items()):
            if entry['path'] == path:
                self.cache.pop(identity, None)
        invalidated = {identity for identity, record in self.watch.records.items() if record['path'] == path}
        if self.watch.active and self.watch.active.path == path:
            invalidated.add(self.watch.active.identity)
        if observed and observed[0] == path:
            invalidated.add(observed[1])
        for identity in invalidated:
            # Unlink already succeeded; failed history cleanup must never invite
            # a retry against another entry at the same name.
            with contextlib.suppress(Exception):
                self.watch.after_unlink(path, identity)

    async def close(self):
        tasks = list(self.jobs.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        async with self.lock:
            self.watch.shutdown()
        self.cache.clear()
