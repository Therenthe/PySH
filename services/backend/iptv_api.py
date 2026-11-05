"""Hub-bound IPTV routes. Public source fetching stays out of the media lock."""
import asyncio
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from .content import ContentError
from .local_media import media_await, media_thread

router = APIRouter(prefix='/api/iptv')


class Body(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Refresh(Body):
    kind: Literal['playlists', 'guide']


class Sources(Body):
    kind: Literal['playlists', 'xmltv']
    urls: list[str] = Field(max_length=8)


class Channel(Body):
    channel_id: str = Field(min_length=1, max_length=256, strict=True)


class Favorite(Channel):
    favorite: bool = Field(strict=True)


class RecordingEdit(Body):
    title: str = Field(min_length=1, max_length=200, strict=True)
    start_at: str = Field(min_length=10, max_length=40, strict=True)
    end_at: str = Field(min_length=10, max_length=40, strict=True)
    before_minutes: int = Field(default=0, ge=0, le=60, strict=True)
    after_minutes: int = Field(default=0, ge=0, le=60, strict=True)


class RecordingCreate(RecordingEdit):
    channel_id: str = Field(min_length=1, max_length=256, strict=True)
    programme_id: str | None = Field(default=None, max_length=256, strict=True)
    request_id: str = Field(pattern=r'^[0-9a-f-]{36}$', strict=True)


async def refresh(hub, kind):
    # One worker owns both kinds. A source change during a fetch queues another
    # pass instead of losing the new generation until the next six-hour cycle.
    pending = getattr(hub, 'iptv_refresh_pending', None)
    if pending is None:
        hub.iptv_refresh_pending = pending = set()
    pending.add(kind)
    hub.iptv_refreshing.add(kind)
    if getattr(hub, 'iptv_refresh_worker', None) is not None:
        return
    worker = asyncio.current_task()
    hub.iptv_refresh_worker = worker
    try:
        while pending:
            selected = 'playlists' if 'playlists' in pending else 'guide'
            pending.remove(selected)
            operation = hub.iptv.refresh_playlists if selected == 'playlists' else hub.iptv.refresh_guide
            try:
                await media_thread(operation)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                if getattr(error, 'code', '') in {'iptv_sources_changed', 'iptv_refresh_busy'}:
                    pending.add(selected)
                    await asyncio.sleep(.25)
                # Per-source safe status is available in the catalogue; no raw
                # source URL or upstream exception text is logged here.
            finally:
                if selected not in pending:
                    hub.iptv_refreshing.discard(selected)
    finally:
        if hub.iptv_refresh_worker is worker:
            hub.iptv_refresh_worker = None
            pending.clear()
            hub.iptv_refreshing.clear()


async def refresh_loop(hub):
    # Small cache reads are immediate. Refreshes never delay Hub initialization.
    last_lists = 0
    last_guide = 0
    loop = asyncio.get_running_loop()
    while True:
        now = loop.time()
        if now - last_lists >= 86400 or not last_lists:
            await refresh(hub, 'playlists')
            last_lists = loop.time()
        if now - last_guide >= 21600 or not last_guide:
            await refresh(hub, 'guide')
            last_guide = loop.time()
        await asyncio.sleep(60)


@router.get('')
async def catalogue(request: Request):
    hub = request.app.state.hub
    value = await media_thread(hub.iptv.catalogue)
    value['channels'] = [{key: channel.get(key) for key in ('id', 'name', 'logo', 'group', 'favorite')}
                         for channel in value['channels']]
    value['refreshing'] = bool(hub.iptv_refreshing)
    return value


@router.post('/refresh')
async def update(request: Request, body: Refresh):
    hub = request.app.state.hub
    hub.background(refresh(hub, body.kind))
    return {'accepted': True}


@router.put('/sources')
async def sources(request: Request, body: Sources):
    hub = request.app.state.hub
    await media_thread(hub.iptv.set_sources, body.kind, body.urls)
    hub.background(refresh(hub, 'playlists' if body.kind == 'playlists' else 'guide'))
    return {'saved': True}


@router.post('/favorites')
async def favorite(request: Request, body: Favorite):
    return await media_thread(request.app.state.hub.iptv.set_favorite, body.channel_id, body.favorite)


@router.get('/guide/{channel_id}')
async def guide(request: Request, channel_id: str):
    return await media_thread(request.app.state.hub.iptv.guide, channel_id)


@router.post('/view')
async def view(request: Request, body: Channel):
    hub = request.app.state.hub
    # DNS checks can take time and never run with audio/device mutations locked.
    channel = await media_thread(hub.iptv.resolve, body.channel_id)
    async with hub.media_lock:
        async def transition():
            if hub.power.standby or hub.service_mode:
                raise ContentError('standby_active' if hub.power.standby else 'service_mode')
            await media_thread(hub.local_media.watch.expire)
            if hub.local_media.watch.active or hub.iptv_stream.active():
                raise ContentError('media_in_use')
            # One viewer owns sound. Explicit TV start replaces the retained mpv item.
            await hub.player.command('stop')
            hub.cache_playback({})
            await hub.visualizer.close()
            return hub.iptv_stream.start(channel['id'], channel['url'])
        return await media_await(transition(), on_cancel=lambda reply: hub.iptv_stream.close(reply['session_id']))


@router.delete('/view/{session_id}')
async def close_view(request: Request, session_id: str):
    return {'closed': request.app.state.hub.iptv_stream.close(session_id)}


@router.patch('/view/{session_id}')
async def touch_view(request: Request, session_id: str, body: Body | None = None):
    request.app.state.hub.iptv_stream.touch(session_id)
    return {'active': True}


@router.get('/stream/{session_id}/{resource_id}')
async def stream(request: Request, session_id: str, resource_id: str):
    value = await request.app.state.hub.iptv_stream.afetch(session_id, resource_id, request.headers.get('range'))
    return Response(value.data, status_code=value.status_code, media_type=value.media_type, headers=value.headers)


@router.get('/recordings')
async def recordings(request: Request):
    store = await media_thread(getattr, request.app.state.hub, 'recorder')
    items, status = await asyncio.gather(media_thread(store.list), media_thread(store.status))
    return {'items': items, 'service': {**status, 'active': status['service_active']}}


@router.post('/recordings')
async def record(request: Request, body: RecordingCreate):
    hub = request.app.state.hub
    channel = await media_thread(hub.iptv.resolve, body.channel_id)
    if body.programme_id:
        guide = await media_thread(hub.iptv.guide, body.channel_id)
        if not any(p['id'] == body.programme_id for p in guide['programmes']):
            raise ContentError('iptv_programme_changed')
    store = await media_thread(getattr, hub, 'recorder')
    return await media_thread(store.create, channel, body.title, body.start_at, body.end_at,
                              body.before_minutes, body.after_minutes, request_id=body.request_id)


@router.patch('/recordings/{job_id}')
async def edit_record(request: Request, job_id: str, body: RecordingEdit):
    store = await media_thread(getattr, request.app.state.hub, 'recorder')
    return await media_thread(store.edit, job_id, **body.model_dump())


@router.post('/recordings/{job_id}/cancel')
async def cancel_record(request: Request, job_id: str):
    store = await media_thread(getattr, request.app.state.hub, 'recorder')
    return await media_thread(store.cancel, job_id)


@router.post('/recordings/{job_id}/stop')
async def stop_record(request: Request, job_id: str):
    store = await media_thread(getattr, request.app.state.hub, 'recorder')
    return await media_thread(store.stop, job_id)


@router.delete('/recordings/{job_id}')
async def delete_record(request: Request, job_id: str):
    hub = request.app.state.hub
    store = await media_thread(getattr, hub, 'recorder')
    async with hub.media_lock:
        async def complete():
            row = await media_thread(store.get, job_id)
            if row.get('has_file'):
                path = await media_thread(store.recording_path, job_id)
                observed = await media_thread(hub.local_media.before_delete, str(path))
                playback = await hub.player.status()
                if playback.get('url') == str(path) and playback.get('state') not in {'idle', 'ended', 'error'}:
                    raise ContentError('media_in_use')
                result = await media_thread(store.delete, job_id)
                await media_thread(hub.local_media.after_delete, str(path), observed)
                return result
            return await media_thread(store.delete, job_id)
        return await media_await(complete())


@router.get('/recordings/{job_id}/media')
async def recorded_media(request: Request, job_id: str):
    hub = request.app.state.hub
    store = await media_thread(getattr, hub, 'recorder')
    async with hub.media_lock:
        # Pin the recorder's terminal file, then require the listing to describe
        # that inode/version. Playback revalidates this identity again on open.
        descriptor = await media_thread(store.open_recording, job_id, on_cancel=os.close)
        try:
            path = await media_thread(store.recording_path, job_id)
            expected = hub.content.media_identity(Path(path), os.fstat(descriptor))
            listing = await hub.content.media_list(str(Path(path).parent))
            value = hub.local_media.enrich(listing)
            for item in value['items']:
                if item['path'] == str(path) and item.get('media_identity') == expected:
                    return item
        finally:
            os.close(descriptor)
    raise ContentError('media_not_found')
