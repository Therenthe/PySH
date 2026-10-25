"""Descriptor-pinned file responses for Starlette 1.7.0 on Linux procfs.

The caller confines and validates a readable regular fd, then constructs this
response while still holding media_lock. This class authorizes no paths.
"""
from __future__ import annotations

import asyncio
import os
import stat
import sys
import weakref

from anyio import CancelScope
from starlette.responses import FileResponse
from starlette.types import Receive, Scope, Send


class DescriptorResponseUnavailable(RuntimeError):
    pass


class _ResponseStopped(Exception):
    """Normal unwinding permits delegated async file cleanup to finish."""


async def _finish(task):
    # Both explicit task cancellation and the ASGI server's AnyIO cancellation
    # must let the FileResponse async file context close before our dup closes.
    with CancelScope(shield=True):
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
        return task.result()


class DescriptorFileResponse(FileResponse):
    def __init__(self, approved_fd: int, *, media_type: str):
        if not sys.platform.startswith('linux') or not os.path.isdir('/proc/self/fd'):
            raise DescriptorResponseUnavailable('descriptor_response_unavailable')
        if type(approved_fd) is not int or approved_fd < 0:
            raise ValueError('invalid_media_descriptor')
        owned = os.dup(approved_fd)
        try:
            info = os.fstat(owned)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('media_descriptor_not_regular')
            super().__init__(f'/proc/self/fd/{owned}', media_type=media_type, stat_result=info)
            self._release = weakref.finalize(self, os.close, owned)
            self._called = False
        except BaseException:
            os.close(owned)
            raise

    def close_owned(self) -> None:
        """Dispose an unused response deterministically after cancelled creation."""
        self._release()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self._called:
            raise RuntimeError('media_response_already_used')
        self._called = True
        try:
            if scope['type'] != 'http':
                raise ValueError('media_response_http_only')
            # The server must consume bytes now, not defer opening this fd path.
            bounded_scope = {**scope, 'extensions': {
                key: value for key, value in scope.get('extensions', {}).items()
                if key != 'http.response.pathsend'
            }}
            stopped = asyncio.Event()

            async def disconnected():
                try:
                    while not stopped.is_set():
                        if (await receive())['type'] == 'http.disconnect':
                            stopped.set()
                            return
                except asyncio.CancelledError:
                    raise
                except Exception:
                    stopped.set()

            async def bounded_send(message):
                if stopped.is_set():
                    raise _ResponseStopped()
                sending = asyncio.create_task(send(message))
                stopping = asyncio.create_task(stopped.wait())
                try:
                    await asyncio.wait((sending, stopping), return_when=asyncio.FIRST_COMPLETED)
                    if stopped.is_set():
                        raise _ResponseStopped()
                    return sending.result()
                finally:
                    for task in (sending, stopping):
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(sending, stopping, return_exceptions=True)

            respond = super().__call__

            async def complete_response():
                # Do not cancel the delegated read/file context on disconnect.
                # A normal exception from bounded_send unwinds and awaits close.
                with CancelScope(shield=True):
                    try:
                        await respond(bounded_scope, receive, bounded_send)
                    except _ResponseStopped:
                        pass

            monitor = asyncio.create_task(disconnected())
            response = asyncio.create_task(complete_response())
            try:
                await asyncio.shield(response)
            except asyncio.CancelledError:
                stopped.set()
                await _finish(response)
                raise
            finally:
                stopped.set()
                monitor.cancel()
                with CancelScope(shield=True):
                    await asyncio.gather(monitor, return_exceptions=True)
        finally:
            self._release()
