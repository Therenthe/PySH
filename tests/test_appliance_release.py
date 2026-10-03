"""Filesystem transactions with failing service restart and untrusted packages."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile

import pytest

spec = importlib.util.spec_from_file_location('appliance_release', Path(__file__).parents[1] / 'scripts/appliance-release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding='utf-8')


def runtime(path, version):
    for name, content in {'requirements.lock': 'same-dependencies', 'scripts/run-hub.py': version,
                          'dist/index.html': '<html>' + version}.items():
        p = path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    return release.inventory(path)


@pytest.fixture
def device(tmp_path):
    root = tmp_path / 'opt/pysh'
    files = runtime(root / 'current', 'old')
    write_json(tmp_path / 'etc/pysh-build.json', {'runtime_build': release.identity(files), 'source': '1' * 40})
    prefs = tmp_path / 'home/pysh/.local/share/pi-smart-hub/preferences.json'
    write_json(prefs, {'language': 'ro', 'volume': 37})
    events = []
    appliance = release.Appliance(tmp_path, lambda *args: events.append(args))
    return appliance, events, prefs


def package(tmp_path, version='new', extra=None):
    folder = tmp_path / ('package-' + version)
    files = runtime(folder, version)
    archive = tmp_path / (version + '.tar.gz')
    with tarfile.open(archive, 'w:gz') as bundle:
        for name in files:
            bundle.add(folder / name, arcname=name)
        if extra:
            info = tarfile.TarInfo(extra)
            info.size = 1
            bundle.addfile(info, io.BytesIO(b'x'))
    m = {'build': release.identity(files), 'files': files, 'sha256': release.digest(archive)}
    p = tmp_path / (version + '.json')
    write_json(p, m)
    return archive, p, m


def receipt(tmp_path, result):
    p = tmp_path / ('receipt-' + result['build'] + '.json')
    write_json(p, {k: result[k] for k in ('build', 'backup_sha256', 'device')} | {'verified_on': 'f' * 64})
    return p


@pytest.mark.skipif(os.name != 'posix', reason='Real Linux symlink transaction')
def test_initial_image_update_and_explicit_rollback_preserve_data(device, tmp_path):
    a, events, prefs = device
    old = a.active()[1]
    before = prefs.read_bytes()
    archive, m, expected = package(tmp_path)
    staged = a.prepare(archive, m, '2' * 40)
    assert a.active()[1] == old and events == []
    backup = release.check_backup(Path(staged['backup']), staged['backup_sha256'])
    assert backup['old'] == old
    a.activate(receipt(tmp_path, staged))
    assert a.active()[1]['build'] == expected['build']
    assert (a.root / ('image-current-' + old['build'])).is_dir()
    reverse = a.prepare_rollback()
    a.activate(receipt(tmp_path, reverse))
    assert a.active()[1] == old
    assert prefs.read_bytes() == before
    assert len(events) == 6
    again = a.prepare_rollback()
    # Each operation gets a separate backup; an old receipt cannot authorize it.
    assert again['backup_sha256'] != staged['backup_sha256']
    a.activate(receipt(tmp_path, again))
    assert a.active()[1]['build'] == expected['build']
    assert len(list(a.state.glob('*.activated.json'))) == 3


@pytest.mark.skipif(os.name != 'posix', reason='Real Linux symlink transaction')
def test_failed_readiness_restores_old_source_and_retains_new(device, tmp_path):
    a, events, prefs = device
    old = a.active()[1]
    archive, m, new = package(tmp_path)
    staged = a.prepare(archive, m, '2' * 40)
    failed = False
    def runner(action, target=None):
        nonlocal failed
        events.append((action, target))
        if action == 'ready' and target.name == new['build'] and not failed:
            failed = True
            raise RuntimeError('service cannot start')
    a.runner = runner
    with pytest.raises(RuntimeError, match='cannot start'):
        a.activate(receipt(tmp_path, staged))
    assert a.active()[1] == old
    assert (a.root / 'releases' / new['build']).is_dir()
    assert not (a.state / 'transaction.json').exists()


@pytest.mark.parametrize('bad', ['../../outside', '/etc/ssh/config', 'services/backend/../escape', 'unknown.py'])
def test_unsafe_or_unknown_archive_never_changes_active(device, tmp_path, bad):
    a, events, prefs = device
    old = a.active()[1]
    archive, m, _ = package(tmp_path, extra=bad)
    with pytest.raises(release.Refused):
        a.prepare(archive, m, '2' * 40)
    assert a.active()[1] == old and not events


def test_local_or_wrong_backup_receipt_refused_before_stop(device, tmp_path):
    a, events, prefs = device
    archive, m, _ = package(tmp_path)
    staged = a.prepare(archive, m, '2' * 40)
    p = receipt(tmp_path, staged)
    value = json.loads(p.read_text())
    value['verified_on'] = staged['device']
    write_json(p, value)
    with pytest.raises(release.Refused, match='Separate-host'):
        a.activate(p)
    assert not events


def test_user_preference_change_requires_new_review(device, tmp_path):
    a, events, prefs = device
    archive, m, _ = package(tmp_path)
    staged = a.prepare(archive, m, '2' * 40)
    prefs.write_text('{"volume":42}', encoding='utf-8')
    with pytest.raises(release.Refused, match='Protected state changed'):
        a.activate(receipt(tmp_path, staged))
    assert not events


@pytest.mark.skipif(os.name != 'posix', reason='Real Linux symlink transaction')
def test_recover_interrupted_pointer_switch(device, tmp_path):
    a, events, prefs = device
    old = a.active()[1]
    archive, m, _ = package(tmp_path)
    a.prepare(archive, m, '2' * 40)
    (a.root / 'current').rename(a.root / ('image-current-' + old['build']))
    a.recover()
    assert a.active()[1] == old
    previous_events = list(events)
    assert a.recover()['pending'] is False
    assert events == previous_events


@pytest.mark.skipif(os.name != 'posix', reason='Real Linux symlink transaction')
def test_metadata_write_failure_rolls_back_and_removes_new_previous(device, tmp_path, monkeypatch):
    a, events, prefs = device
    old = a.active()[1]
    archive, m, _ = package(tmp_path)
    staged = a.prepare(archive, m, '2' * 40)
    original = release.atomic_json
    failed = False
    def write(path, value):
        nonlocal failed
        if path.name == 'runtime-source.json' and not failed:
            failed = True
            raise OSError('disk write failure')
        original(path, value)
    monkeypatch.setattr(release, 'atomic_json', write)
    with pytest.raises(OSError, match='disk write failure'):
        a.activate(receipt(tmp_path, staged))
    assert a.active()[1] == old
    assert not (a.root / 'previous').exists()


def test_backup_inner_hash_is_checked_not_only_outer_checksum(device, tmp_path):
    a, events, prefs = device
    archive, m, _ = package(tmp_path)
    staged = a.prepare(archive, m, '2' * 40)
    backup = Path(staged['backup'])
    with tarfile.open(backup, 'r:gz') as bundle:
        members = {x.name: bundle.extractfile(x).read() for x in bundle}
    members['runtime/dist/index.html'] = b'corrupted runtime'
    backup.chmod(0o600)
    with tarfile.open(backup, 'w:gz') as bundle:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
    with pytest.raises(release.Refused, match='member hash'):
        release.check_backup(backup, release.digest(backup))


def test_changed_dependency_lock_is_rejected_without_runtime_stop(device, tmp_path):
    a, events, prefs = device
    archive, m, new = package(tmp_path)
    with tarfile.open(archive, 'r:gz') as bundle:
        content = {x.name: bundle.extractfile(x).read() for x in bundle}
    content['requirements.lock'] = b'new-dependency'
    with tarfile.open(archive, 'w:gz') as bundle:
        for name, data in content.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
    import hashlib
    new['files'] = {n: hashlib.sha256(v).hexdigest() for n, v in content.items()}
    new['build'] = release.identity(new['files'])
    new['sha256'] = release.digest(archive)
    write_json(m, new)
    with pytest.raises(release.Refused, match='Dependency changes'):
        a.prepare(archive, m, '2' * 40)
    assert not events


@pytest.mark.skipif(os.name != 'posix', reason='POSIX permission enforcement')
def test_backup_is_private_before_tar_writer_receives_any_payload(device, tmp_path, monkeypatch):
    a, events, prefs = device
    archive, m, _ = package(tmp_path)
    original = tarfile.open
    observed = []
    def opened(*args, **kwargs):
        stream = kwargs.get('fileobj')
        if stream is not None:
            import stat
            info = os.fstat(stream.fileno())
            assert stat.S_IMODE(info.st_mode) == 0o600
            assert info.st_uid == os.geteuid()
            assert info.st_size == 0
            observed.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(tarfile, 'open', opened)
    staged = a.prepare(archive, m, '2' * 40)
    assert observed == [True]
    assert release.check_backup(Path(staged['backup']), staged['backup_sha256'])['old'] == a.active()[1]


@pytest.mark.skipif(os.name != 'posix', reason='POSIX permission enforcement')
def test_existing_readable_state_is_refused_before_private_backup(device, tmp_path):
    a, events, prefs = device
    a.state.mkdir(mode=0o755)
    archive, m, _ = package(tmp_path)
    with pytest.raises(release.Refused, match='Insecure appliance state permissions'):
        a.prepare(archive, m, '2' * 40)
    assert not list(a.state.iterdir()) and not events
