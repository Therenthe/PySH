"""Recorder commands/scheduling use synthetic processes; no real network/device."""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import io
import os
from pathlib import Path
import sqlite3
import sys
import uuid
from types import SimpleNamespace

import pytest

from services.backend import iptv_catalog as catalogue
from services.backend import iptv_recorder as recorder

NOW = datetime(2026, 11, 5, 15, 0, tzinfo=timezone.utc).timestamp()


def iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


@pytest.fixture
def env(tmp_path, monkeypatch):
    # No DNS in unit tests; public URL hardening has separate catalogue tests.
    monkeypatch.setattr(catalogue, 'verify_public_url', catalogue.public_url)
    clock = [NOW]
    store = recorder.RecorderStore(tmp_path / 'data', tmp_path / 'Videos' / 'MediaTool', clock=lambda: clock[0])
    return SimpleNamespace(store=store, clock=clock, path=tmp_path)


def create(env, *, start=NOW, end=NOW + 3600, **kwargs):
    return env.store.create({'id': 'channel-one', 'name': 'Synthetic TV', 'url': 'https://media.example/live.m3u8'},
                            kwargs.pop('title', 'Synthetic programme'), iso(start), iso(end), **kwargs)


class FakeInput(io.BytesIO):
    def __init__(self, process):
        super().__init__()
        self.process = process

    def write(self, data):
        if data == b'q\n':
            self.process.code = 0
        return super().write(data)


class FakeProcess:
    def __init__(self, command, **kwargs):
        self.command, self.options = command, kwargs
        self.output_seekable = kwargs['stdout'].seekable()
        self.code = None
        self.stdin = FakeInput(self)
        self.terminated = self.killed = False
        kwargs['stdout'].write(b'UNIT TEST: synthetic MKV bytes, not a playable media assertion')
        kwargs['stdout'].flush()

    def poll(self):
        return self.code

    def terminate(self):
        self.terminated, self.code = True, -15

    def kill(self):
        self.killed, self.code = True, -9

    def wait(self, timeout=None):
        return self.code


class FakeProxy:
    def __init__(self, *, path_prefix):
        self.path_prefix, self.closed = path_prefix, False

    def start(self, channel_id, url):
        return {'session_id': 'S' * 32, 'stream_url': self.path_prefix + '/' + 'S' * 32 + '/' + 'R' * 24}

    def close(self, session_id):
        assert session_id == 'S' * 32
        self.closed = True


@pytest.fixture
def daemon(env):
    service = recorder.RecorderDaemon(env.store, popen=FakeProcess, disk_free=lambda: 1024 ** 3, proxy_factory=FakeProxy)
    service.recover()
    yield service
    service.close()


def test_store_persists_commands_and_has_no_raw_urls_in_public_results(env):
    job = create(env)
    assert job['state'] == 'scheduled'
    other = recorder.RecorderStore(env.path / 'data', clock=lambda: NOW)
    assert other.get(job['id']) == job
    assert other.output_dir == env.store.output_dir
    assert 'url' not in str(job)
    assert 'media.example' not in str(other.list())
    assert other.status()['service_active'] is False


def test_padding_and_timezone_are_utc_and_survive_edit(env):
    job = env.store.create({'id': 'id', 'name': 'TV', 'url': 'https://media.example/live.m3u8'}, 'Evening',
                           '2026-11-05T19:00:00+02:00', '2026-11-05T20:00:00+02:00', 15, 30)
    assert job['start_at'] == '2026-11-05T17:00:00+00:00'
    assert job['record_start_at'] == '2026-11-05T16:45:00+00:00'
    assert job['record_end_at'] == '2026-11-05T18:30:00+00:00'
    edited = env.store.edit(job['id'], before_minutes=0, after_minutes=60, title='Updated')
    assert edited['title'] == 'Updated'
    assert edited['record_end_at'] == '2026-11-05T19:00:00+00:00'
    assert edited['version'] == job['version'] + 1


@pytest.mark.parametrize('before,after', [(-1, 0), (0, 61), (True, 0), (0, 1.5), ('5', 0)])
def test_padding_is_bounded_strict_integer(env, before, after):
    with pytest.raises(recorder.RecorderError, match='invalid_padding'):
        create(env, before_minutes=before, after_minutes=after)


@pytest.mark.parametrize('start,end', [
    ('2026-11-05T17:00:00', '2026-11-05T18:00:00+00:00'),
    ('nonsense', '2026-11-05T18:00:00+00:00'),
    (iso(NOW + 3600), iso(NOW)),
    (iso(NOW - 7200), iso(NOW - 3600)),
    (iso(NOW), iso(NOW + 86401)),
    (iso(NOW + 32 * 86400), iso(NOW + 32 * 86400 + 3600)),
])
def test_invalid_intervals_rejected(env, start, end):
    with pytest.raises(recorder.RecorderError, match='invalid_time'):
        env.store.create({'id': 'id', 'name': 'TV', 'url': 'https://media.example/live.m3u8'}, 'Programme', start, end)


def test_cancel_and_unknown_or_unrelated_ids_cannot_modify_jobs(env):
    job = create(env)
    assert env.store.cancel(job['id'])['state'] == 'cancelled'
    for job_id in ('../jobs.sqlite3', '0' * 32, '', None):
        with pytest.raises(recorder.RecorderError, match='not_found'):
            env.store.get(job_id)
    with pytest.raises(recorder.RecorderError, match='not_editable'):
        env.store.edit(job['id'], title='Too late')
    with pytest.raises(recorder.RecorderError, match='invalid_request'):
        env.store.edit(job['id'], filename='/etc/passwd')


def test_capacity_uses_padded_intervals_and_allows_nonconcurrent_two(env):
    first = create(env, start=NOW + 60, end=NOW + 600)
    create(env, start=NOW + 600, end=NOW + 1200)
    create(env, start=NOW + 60, end=NOW + 1200)
    with pytest.raises(recorder.RecorderError, match='capacity'):
        create(env, start=NOW + 120, end=NOW + 180)
    env.store.cancel(first['id'])
    create(env, start=NOW + 120, end=NOW + 180)


def test_daemon_starts_early_and_finalizes_at_padded_end(env, daemon):
    job = create(env, start=NOW + 300, end=NOW + 600, before_minutes=5, after_minutes=2)
    daemon.tick()
    active = env.store.get(job['id'])
    assert active['state'] == 'recording'
    assert active['has_file'] and active['size'] > 0
    process = daemon.running[job['id']]['process']
    assert '-c' in process.command and process.command[process.command.index('-c') + 1] == 'copy'
    assert '-map' not in process.command  # HLS master renditions use automatic single-stream selection.
    assert '-sn' in process.command and '-dn' in process.command
    assert process.command[-2:] == ['matroska', 'fd:']
    assert process.output_seekable
    assert 'https://media.example/live.m3u8' not in process.command
    assert any(arg.startswith('http://127.0.0.1:') for arg in process.command)
    assert process.options['stderr'] == recorder.subprocess.DEVNULL
    assert env.store.status()['service_active']
    env.clock[0] = NOW + 719
    daemon.tick()
    assert env.store.get(job['id'])['state'] == 'recording'
    env.clock[0] = NOW + 720
    daemon.tick()
    assert env.store.get(job['id'])['state'] == 'stopping'
    daemon.tick()
    assert env.store.get(job['id'])['state'] == 'completed'
    assert not daemon.running


def test_recording_survives_store_ui_recreation_and_stop_saves(env, daemon):
    job = create(env)
    daemon.tick()
    recreated = recorder.RecorderStore(env.path / 'data', clock=lambda: NOW)
    assert recreated.get(job['id'])['state'] == 'recording'
    with pytest.raises(recorder.RecorderError, match='not_editable'):
        recreated.edit(job['id'], title='Cannot change active schedule')
    with pytest.raises(recorder.RecorderError, match='active'):
        recreated.delete(job['id'])
    with pytest.raises(recorder.RecorderError, match='active'):
        recreated.open_recording(job['id'])
    recreated.stop(job['id'])
    daemon.tick()
    daemon.tick()
    assert recreated.get(job['id'])['state'] == 'stopped'
    fd = recreated.open_recording(job['id'])
    try:
        assert os.read(fd, 100).startswith(b'UNIT TEST')
    finally:
        os.close(fd)


def test_two_recordings_have_separate_sources_and_stopping_one_leaves_other(env, daemon):
    first, second = create(env), create(env)
    daemon.tick()
    one, two = daemon.running[first['id']], daemon.running[second['id']]
    assert one['proxy'] is not two['proxy']
    assert one['proxy'].path_prefix != two['proxy'].path_prefix
    env.store.stop(first['id'])
    daemon.tick()
    daemon.tick()
    assert one['proxy'].closed
    assert env.store.get(second['id'])['state'] == 'recording'
    assert not two['proxy'].closed


def test_missed_jobs_do_not_start_and_failure_does_not_claim_success(env, daemon):
    expired = create(env, start=NOW + 10, end=NOW + 20)
    env.clock[0] = NOW + 21
    daemon.tick()
    assert env.store.get(expired['id'])['state'] == 'missed'
    assert not daemon.running
    fresh = create(env, start=NOW + 21)
    daemon.tick()
    daemon.running[fresh['id']]['process'].code = 1
    daemon.tick()
    result = env.store.get(fresh['id'])
    assert result['state'] == 'failed'
    assert result['error'] == 'recording_stream_failed'
    assert result['has_file']  # A partial file remains recoverable; no success claim.


def test_disk_threshold_before_start_and_while_active(env, daemon):
    job = create(env)
    daemon.disk_free = lambda: recorder.MIN_FREE - 1
    daemon.tick()
    assert env.store.get(job['id'])['error'] == 'recording_disk_full'
    second = create(env)
    daemon.disk_free = lambda: recorder.MIN_FREE
    daemon.tick()
    assert env.store.get(second['id'])['state'] == 'recording'
    daemon.disk_free = lambda: recorder.STOP_FREE - 1
    daemon.tick()
    daemon.tick()
    result = env.store.get(second['id'])
    assert result['state'] == 'stopped' and result['error'] == 'recording_disk_full'
    assert result['has_file']


def test_restart_marks_previous_owned_active_job_interrupted(env, daemon):
    job = create(env)
    daemon.tick()
    # In production systemd kills the old cgroup before restarting this daemon.
    daemon.running[job['id']]['process'].code = 1
    recovered = recorder.RecorderDaemon(env.store)
    recovered.recover()
    result = env.store.get(job['id'])
    assert result['state'] == 'interrupted'
    assert result['error'] == 'recording_service_interrupted'
    assert result['has_file']


def test_output_name_is_exclusive_and_replacements_are_not_streamed_or_deleted(env, daemon):
    job = create(env)
    path = env.store.output_dir / (job['id'] + '.mkv')
    path.write_bytes(b'Unrelated preexisting file')
    daemon.tick()
    assert env.store.get(job['id'])['state'] == 'failed'
    assert path.read_bytes() == b'Unrelated preexisting file'
    with pytest.raises(recorder.RecorderError, match='changed'):
        env.store.open_recording(job['id'])
    with pytest.raises(recorder.RecorderError, match='changed'):
        env.store.delete(job['id'])


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason='Windows open handles deny rename; Linux procfs/descriptor ownership is verified natively.')
def test_returned_descriptor_pins_owned_file_and_replaced_path_is_rejected(env, daemon):
    job = create(env)
    daemon.tick()
    env.store.stop(job['id'])
    daemon.tick()
    daemon.tick()
    fd = env.store.open_recording(job['id'])
    path = env.store.recording_path(job['id'])
    original = path.with_suffix('.original')
    try:
        path.rename(original)
        path.write_bytes(b'Replacement is unrelated')
        assert os.read(fd, 100).startswith(b'UNIT TEST')
        with pytest.raises(recorder.RecorderError, match='changed'):
            env.store.open_recording(job['id'])
        with pytest.raises(recorder.RecorderError, match='changed'):
            env.store.delete(job['id'])
        assert path.read_bytes() == b'Replacement is unrelated'
    finally:
        os.close(fd)


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason='Atomic quarantine deletion is Linux-only, consistent with Hub media deletion.')
def test_delete_owned_terminal_file_and_cancelled_schedule(env, daemon):
    job = create(env)
    daemon.tick()
    env.store.stop(job['id'])
    daemon.tick()
    daemon.tick()
    path = env.store.recording_path(job['id'])
    assert env.store.delete(job['id']) == {'deleted': True}
    assert not path.exists()
    assert not env.store.list()
    cancelled = create(env)
    env.store.cancel(cancelled['id'])
    assert env.store.delete(cancelled['id']) == {'deleted': True}


def test_output_directory_configuration_cannot_be_redirected(env):
    with pytest.raises(recorder.RecorderError, match='output_changed'):
        recorder.RecorderStore(env.path / 'data', env.path / 'somewhere-else')


def test_closed_daemon_clears_heartbeat_and_preserves_partial_file(env, daemon):
    job = create(env)
    daemon.tick()
    daemon.close()
    result = env.store.get(job['id'])
    assert result['state'] == 'interrupted'
    assert result['has_file']
    assert not env.store.status()['service_active']
    daemon.close()


def test_create_retry_is_idempotent_and_conflicting_payload_rejected_even_after_end(env, monkeypatch):
    request_id = str(uuid.uuid4())
    first = create(env, request_id=request_id)
    env.clock[0] = NOW + 7200
    monkeypatch.setattr(catalogue, 'verify_public_url', lambda *_: (_ for _ in ()).throw(AssertionError('Retry must not need internet')))
    assert create(env, request_id=request_id)['id'] == first['id']
    assert len(env.store.list()) == 1
    with pytest.raises(recorder.RecorderError, match='request_conflict'):
        create(env, request_id=request_id, title='Different requested programme')


def test_deleted_request_is_not_recreated_by_late_post_retry(env):
    request_id = str(uuid.uuid4())
    first = create(env, request_id=request_id)
    env.store.cancel(first['id'])
    env.store.delete(first['id'])
    repeated = create(env, request_id=request_id)
    assert repeated['id'] == first['id'] and repeated['state'] == 'deleted'
    assert not env.store.list()


def test_same_create_retry_returns_current_edited_job_without_reverting_it(env):
    request_id = str(uuid.uuid4())
    first = create(env, request_id=request_id)
    edited = env.store.edit(first['id'], title='Edited title', after_minutes=10)
    retried = create(env, request_id=request_id)
    assert retried == edited


def test_shared_media_in_use_guard_covers_startup_recording_and_stopping(env, daemon):
    job = create(env)
    path = env.store.output_dir / (job['id'] + '.mkv')
    assert not env.store.in_use(path)
    daemon._set(job['id'], state='starting')
    assert env.store.in_use(path)  # Protect the short interval before file creation.
    daemon._set(job['id'], state='scheduled')
    daemon.tick()
    assert env.store.in_use(path)
    assert not env.store.in_use(path.with_name('unrelated.mkv'))
    env.store.stop(job['id'])
    daemon.tick()
    assert env.store.in_use(path)
    daemon.tick()
    assert not env.store.in_use(path)


def test_shared_media_guard_checks_inode_aliases(env, daemon):
    job = create(env)
    daemon.tick()
    path = env.store.recording_path(job['id'])
    alias = path.with_name('alias.mkv')
    try:
        os.link(path, alias)
    except OSError:
        pytest.skip('Hard-link capability unavailable in this test workspace')
    assert env.store.in_use(alias)


def test_concurrent_retries_create_only_one_job(env):
    request_id = str(uuid.uuid4())
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(lambda _: create(env, request_id=request_id), range(4)))
    assert len({job['id'] for job in results}) == 1
    assert len(env.store.list()) == 1
