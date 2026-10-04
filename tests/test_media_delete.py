"""Deletion touches only temporary fixture media; Linux guards use real dirfds."""
import asyncio
import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from services.backend.app import app, Hub
from services.backend.content import ContentError

LINUX = pytest.mark.skipif(sys.platform != 'linux', reason='Production unlink requires Linux nofollow dirfds')


@pytest.fixture
def media(tmp_path, monkeypatch):
    root = tmp_path / 'Music'
    root.mkdir()
    hub = Hub(tmp_path / 'data')
    monkeypatch.setattr(hub.content, '_media_roots', lambda: [root])
    hub.player = SimpleNamespace(status=AsyncMock(return_value={'state': 'idle'}))
    app.state.hub = hub
    return root, hub, TestClient(app, base_url='http://127.0.0.1:8765')


def token(hub, path):
    return hub.content._delete_token(path, path.stat())


def request(client, hub, path, identity, **kwargs):
    return client.request('DELETE', '/api/media', headers={'X-Hub-Token': hub.token},
                          json={'path': str(path), 'token': identity}, **kwargs)


def test_delete_csrf_and_strict_body(media):
    root, hub, client = media
    file = root / 'keep.mp3'
    file.write_bytes(b'keep')
    body = {'path': str(file), 'token': 'a' * 64}
    assert client.request('DELETE', '/api/media', json=body).status_code == 403
    assert client.request('DELETE', '/api/media', headers={'X-Hub-Token': hub.token, 'Origin': 'https://evil.example'}, json=body).status_code == 403
    for invalid in [{'path': str(file)}, dict(body, extra='private'), dict(body, token=4), dict(body, path='\x00')]:
        response = client.request('DELETE', '/api/media', headers={'X-Hub-Token': hub.token}, json=invalid)
        assert response.status_code == 422
        assert response.json() == {'error': 'invalid_request'}
    assert file.read_bytes() == b'keep'


@LINUX
@pytest.mark.parametrize('suffix', ['.mp3', '.mp4'])
def test_regular_delete_updates_listing_and_queue(media, suffix):
    root, hub, client = media
    files = [root / ('a' + suffix), root / ('b' + suffix), root / ('c' + suffix)]
    for file in files:
        file.write_bytes(b'fixture')
    listing = client.get('/api/media', params={'path': str(root)}).json()['items']
    item = next(item for item in listing if item['path'] == str(files[0]))
    assert item['deletable'] and len(item['delete_token']) == 64
    hub.queue = [{'path': str(file), 'name': file.name} for file in files]
    hub.queue_index = 1
    response = request(client, hub, files[0], item['delete_token'])
    assert response.status_code == 200 and response.json() == {'deleted': True}
    assert not files[0].exists() and files[1].exists() and files[2].exists()
    assert hub.queue_index == 0 and hub.queue[0]['path'] == str(files[1])
    assert all(item['path'] != str(files[0]) for item in client.get('/api/media', params={'path': str(root)}).json()['items'])
    assert not list(root.glob('.pysh-delete-*'))


@LINUX
def test_refuses_paths_and_stale_identity(media):
    root, hub, client = media
    file = root / 'track.mp3'
    file.write_bytes(b'old')
    old = token(hub, file)
    file.write_bytes(b'changed')
    assert request(client, hub, file, old).json() == {'error': 'media_changed'}
    outside = root.parent / 'private.mp3'
    outside.write_bytes(b'private')
    folder = root / 'folder.mp3'
    folder.mkdir()
    unsupported = root / 'notes.txt'
    unsupported.write_text('notes')
    for path, expected in [(outside, 'media_path_not_allowed'), (root / 'missing.mp3', 'media_not_found'),
                           (folder, 'media_delete_not_supported'), (unsupported, 'media_delete_not_supported'),
                           (str(root) + '/../Music/track.mp3', 'media_path_not_allowed')]:
        response = request(client, hub, path, 'a' * 64)
        assert response.status_code == 409 and response.json() == {'error': expected}
    assert file.read_bytes() == b'changed' and outside.read_bytes() == b'private'
    assert folder.is_dir() and unsupported.read_text() == 'notes'


@LINUX
def test_symlink_alias_and_ancestor_never_delete_target(media):
    root, hub, client = media
    folder = root / 'album'
    folder.mkdir()
    file = folder / 'track.mp3'
    file.write_bytes(b'keep')
    alias = root / 'alias.mp3'
    alias.symlink_to(file)
    ancestor = root / 'linked'
    ancestor.symlink_to(folder, target_is_directory=True)
    items = client.get('/api/media', params={'path': str(root)}).json()['items']
    listed = next(item for item in items if item['name'] == alias.name)
    assert listed['deletable'] is False and listed['delete_token'] is None
    for path in [alias, ancestor / file.name]:
        assert request(client, hub, path, token(hub, file)).json() == {'error': 'media_path_not_allowed'}
    assert file.read_bytes() == b'keep'


@LINUX
def test_hardlinks_and_unreadable_file_refused(media, monkeypatch):
    root, hub, client = media
    file = root / 'track.mp3'
    file.write_bytes(b'keep')
    link = root / 'linked.mp3'
    os.link(file, link)
    assert request(client, hub, file, token(hub, file)).json() == {'error': 'media_delete_not_supported'}
    link.unlink()
    original = os.open
    def denied(path, *args, **kwargs):
        if path == file.name:
            raise PermissionError('fixture only')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', denied)
    assert request(client, hub, file, token(hub, file)).json() == {'error': 'media_delete_denied'}
    assert file.read_bytes() == b'keep'


@LINUX
@pytest.mark.parametrize('conflict', [False, True])
def test_capture_race_restores_or_preserves_without_overwrite(media, monkeypatch, conflict):
    root, hub, _ = media
    file = root / 'track.mp3'
    file.write_bytes(b'expected')
    identity = token(hub, file)
    held = root / 'held.mp3'
    original = os.rename
    def raced(src, dst, **kwargs):
        original(file, held)
        file.write_bytes(b'unexpected')
        original(src, dst, **kwargs)
        if conflict:
            file.write_bytes(b'new original')
    monkeypatch.setattr(os, 'rename', raced)
    with pytest.raises(ContentError) as failure:
        hub.content._delete_media(str(file), identity)
    assert failure.value.code == ('media_delete_recovery_required' if conflict else 'media_changed')
    assert held.read_bytes() == b'expected'
    if conflict:
        assert file.read_bytes() == b'new original'
        preserved = list(root.glob('.pysh-delete-*/*'))
        assert len(preserved) == 1 and preserved[0].read_bytes() == b'unexpected'
        assert preserved[0].parent.stat().st_mode & 0o777 == 0o700
    else:
        assert file.read_bytes() == b'unexpected'
        assert not list(root.glob('.pysh-delete-*'))


@LINUX
@pytest.mark.parametrize('state', ['playing', 'paused'])
def test_active_local_and_renamed_inode_blocked(media, state):
    root, hub, client = media
    file = root / 'track.mp3'
    file.write_bytes(b'playing')
    hub.player.status.return_value = {'state': state, 'kind': 'audio', 'url': file.as_uri()}
    assert request(client, hub, file, token(hub, file)).json() == {'error': 'media_in_use'}
    info = file.stat()
    hub.media_identity = (info.st_dev, info.st_ino)
    renamed = root / 'renamed.mp3'
    file.rename(renamed)
    assert request(client, hub, renamed, token(hub, renamed)).json() == {'error': 'media_in_use'}
    assert renamed.read_bytes() == b'playing'


@LINUX
def test_unlink_failure_restores_expected_file(media, monkeypatch):
    root, hub, _ = media
    file = root / 'track.mp3'
    file.write_bytes(b'keep')
    identity = token(hub, file)
    original = os.unlink
    def denied(path, *args, **kwargs):
        if kwargs.get('dir_fd') is not None:
            raise PermissionError('fixture only')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(os, 'unlink', denied)
    with pytest.raises(ContentError) as failure:
        hub.content._delete_media(str(file), identity)
    assert failure.value.code == 'media_delete_denied'
    assert file.read_bytes() == b'keep'
    assert not list(root.glob('.pysh-delete-*'))


def test_delete_and_transport_share_lock(media):
    _, hub, client = media
    async def check():
        from services.backend.app import delete_media, MediaDelete
        entered = asyncio.Event()
        async def status():
            entered.set()
            return {'state': 'idle'}
        hub.player.status = status
        hub.content.delete_media = AsyncMock(return_value='/fixture/track.mp3')
        request_object = SimpleNamespace(app=app)
        async with hub.media_lock:
            task = asyncio.create_task(delete_media(request_object, MediaDelete(path='/fixture/track.mp3', token='a' * 64)))
            await asyncio.sleep(0)
            assert not entered.is_set()
        assert await task == {'deleted': True}
    asyncio.run(check())
