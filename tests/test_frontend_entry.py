"""A release must serve its current entry page without clearing browser profiles."""
import hashlib
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

import services.backend.app as backend


@pytest.fixture
def frontend(tmp_path, monkeypatch):
    # No lifespan, hardware initialization, network access or production build.
    dist = tmp_path / 'dist'
    dist.mkdir()
    index = dist / 'index.html'
    index.write_text('<!doctype html><script src="/assets/release-one.js"></script>', encoding='utf8')
    monkeypatch.setattr(backend, 'ROOT', tmp_path)
    monkeypatch.setattr(backend.app.state, 'hub', SimpleNamespace(token='owned-frontend-test'), raising=False)
    client = TestClient(backend.app, base_url='http://127.0.0.1:8765')
    return client, index


@pytest.mark.parametrize('url', ['/', '/index.html', '/?ui=owned-one', '/index.html?ui=owned-one'])
@pytest.mark.parametrize('method', ['GET', 'HEAD'])
def test_entry_is_current_no_store_even_with_cached_validators(frontend, url, method):
    client, index = frontend
    first = client.get(url)
    assert first.status_code == 200
    assert first.headers['cache-control'] == 'no-store'
    assert first.headers['content-type'].startswith('text/html')
    assert 'release-one.js' in first.text

    # Preserve file size and mtime: a validator must not resurrect the old HTML.
    previous_stat = index.stat()
    index.write_text('<!doctype html><script src="/assets/release-two.js"></script>', encoding='utf8')
    os.utime(index, ns=(previous_stat.st_atime_ns, previous_stat.st_mtime_ns))
    for headers in [
        {'If-None-Match': first.headers['etag']},
        {'If-Modified-Since': 'Thu, 01 Jan 2099 00:00:00 GMT'},
        {'If-None-Match': first.headers['etag'], 'If-Modified-Since': first.headers['last-modified']},
    ]:
        response = client.request(method, url, headers=headers)
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['content-type'].startswith('text/html')
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['referrer-policy'] == 'no-referrer'
        assert response.headers['x-frame-options'] == 'DENY'
        assert "frame-ancestors 'none'" in response.headers['content-security-policy']
        if method == 'HEAD':
            assert response.content == b''
        else:
            assert response.content == index.read_bytes()
            assert 'release-two.js' in response.text
            assert 'release-one.js' not in response.text


@pytest.mark.parametrize('url', ['/', '/index.html?ui=missing'])
def test_missing_frontend_is_explicit_and_not_cached(frontend, url):
    client, index = frontend
    index.unlink()
    response = client.get(url)
    assert response.status_code == 503
    assert response.headers['cache-control'] == 'no-store'
    assert response.json() == {'error': 'frontend_unavailable'}
    head = client.head(url)
    assert head.status_code == 503
    assert head.headers['cache-control'] == 'no-store'
    assert head.content == b''


def test_kiosk_entry_version_tracks_index_content_only(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'scripts/run-hub.py'
    spec = importlib.util.spec_from_file_location('frontend_entry_supervisor', source)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    dist = tmp_path / 'dist'
    dist.mkdir()
    index = dist / 'index.html'
    first = b'<script src="/assets/one.js"></script>'
    second = b'<script src="/assets/two.js"></script>'
    index.write_bytes(first)
    expected = 'http://127.0.0.1:8765/?ui=' + hashlib.sha256(first).hexdigest()[:16]
    assert supervisor.kiosk_url(tmp_path) == expected
    assert supervisor.kiosk_url(tmp_path) == expected
    # Timestamp and unrelated assets cannot change the content identity.
    os.utime(index, (1, 1))
    (dist / 'unrelated.css').write_text('body{}')
    assert supervisor.kiosk_url(tmp_path) == expected
    index.write_bytes(second)
    assert supervisor.kiosk_url(tmp_path) == 'http://127.0.0.1:8765/?ui=' + hashlib.sha256(second).hexdigest()[:16]
    assert supervisor.kiosk_url(tmp_path) != expected
