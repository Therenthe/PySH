"""Stream and destructive-boundary checks without opening a real block device."""
import argparse
import base64
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import struct

import pytest

ROOT = Path(__file__).parents[1]
namespace = {'__name__': 'target_under_test'}
exec(compile((ROOT / 'scripts/flash-pysh-target.py').read_text(encoding='utf-8').replace('import fcntl\n', ''),
             'flash-pysh-target.py', 'exec'), namespace)
spec = importlib.util.spec_from_file_location('pc_flasher', ROOT / 'scripts/flash-pysh-ssh.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


def image_header():
    header = bytearray(512)
    header[510:] = b'\x55\xaa'
    header[450] = 12
    header[466] = 131
    header[454:462] = struct.pack('<II', 16384, 524288)
    header[470:478] = struct.pack('<II', 540672, 8192)
    return bytes(header)


SIZE = (540672 + 8192) * 512


def test_mbr_is_validated_before_any_writer_call():
    writes = []
    with pytest.raises(RuntimeError, match='Invalid image MBR'):
        namespace['stream_write'](io.BytesIO(b'bad' * 200), writes.append, SIZE, '0' * 64)
    assert not writes


@pytest.mark.parametrize('header', [b'bad', bytes(512)])
def test_unknown_partition_layout_refused(header):
    with pytest.raises(RuntimeError):
        namespace['layout'](header, SIZE)


def test_short_target_writes_are_completed_and_zero_write_fails():
    written = bytearray()
    def short(data):
        written.extend(data[:3])
        return min(3, len(data))
    namespace['write_all'](short, b'abcdefghijk')
    assert written == b'abcdefghijk'
    with pytest.raises(RuntimeError, match='Incomplete target write'):
        namespace['write_all'](lambda _: 0, b'test')


def test_incomplete_input_cannot_emit_complete_progress():
    events = []
    with pytest.raises(RuntimeError, match='Incomplete input stream'):
        namespace['stream_write'](io.BytesIO(image_header() + b'partial'), lambda data: len(data), SIZE, '0' * 64,
                                  lambda phase, done, total: events.append((phase, done, total)))
    assert events == [('write', 512, SIZE)]


def test_independent_readback_hash_and_progress_detect_short_read():
    data = b'raw actual disk bytes' * 17
    reader = io.BytesIO(data)
    events = []
    actual = namespace['read_hash'](lambda count: reader.read(min(count, 13)), len(data), 'readback',
                                     lambda *args: events.append(args))
    assert actual == hashlib.sha256(data).hexdigest()
    assert events[-1] == ('readback', len(data), len(data))
    with pytest.raises(RuntimeError, match='Incomplete target read'):
        namespace['read_hash'](io.BytesIO(data).read, len(data) + 1, 'readback', lambda *args: None)


def test_strict_public_key_rejects_options_private_material_and_wrong_binary_type():
    key = b'ssh-ed25519 ' + base64.b64encode(struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32) + bytes(32)) + b' owner\n'
    assert namespace['public_key'](base64.b64encode(key)) == key
    for bad in [b'-----BEGIN OPENSSH PRIVATE KEY-----', b'command="bad" ' + key, key + key, b'ssh-ed25519 ' + base64.b64encode(bytes(51))]:
        with pytest.raises((RuntimeError, ValueError)):
            namespace['public_key'](base64.b64encode(bad))


def test_ssh_host_cannot_inject_options_and_remote_args_remain_single_values(tmp_path):
    key, known = tmp_path / 'key', tmp_path / 'known'
    key.write_text('not read by this command builder')
    known.write_text('known host fixture')
    args = argparse.Namespace(host='192.168.100.127', user='pysh-admin', key=key, known_hosts=known, ssh='ssh')
    command = pc.ssh_command(args, 'inspect', {'target': '/dev/mmcblk0; touch /tmp/no'})
    assert shlex.split(command[-1])[-1] == '/dev/mmcblk0; touch /tmp/no'
    assert 'StrictHostKeyChecking=yes' in command and 'BatchMode=yes' in command and '-T' in command
    args.host = '-oProxyCommand=evil'
    with pytest.raises(RuntimeError, match='Invalid explicit host'):
        pc.ssh_command(args, 'inspect', {'target': '/dev/mmcblk0'})


def test_backup_receipt_rechecks_full_size_hash_and_separate_host(tmp_path, monkeypatch):
    backup = tmp_path / 'sd.raw'
    backup.write_bytes(b'complete card contents')
    record = {'target': '/dev/mmcblk0', 'cid': 'a' * 32, 'size': backup.stat().st_size,
              'device': 'b' * 64, 'backup_sha256': pc.sha(backup)}
    monkeypatch.setattr(pc, 'local_id', lambda: 'c' * 64)
    receipt = tmp_path / 'receipt.json'
    assert pc.verify_backup(backup, record, receipt)['verified_on'] == 'c' * 64
    backup.write_bytes(b'changed card contents!')
    with pytest.raises(RuntimeError):
        pc.verify_backup(backup, record, tmp_path / 'bad.json')
    assert not (tmp_path / 'bad.json').exists()


def test_target_identity_recheck_refuses_swapped_physical_card(monkeypatch):
    monkeypatch.setitem(namespace, 'snapshot', lambda target: {'target': target, 'cid': 'a' * 32, 'size': 4096})
    with pytest.raises(RuntimeError, match='physical identity changed'):
        namespace['validated']('/dev/mmcblk0', 'b' * 32, 4096)


def test_root_usb_or_partition_rejected_before_any_block_open(monkeypatch):
    opened = []
    monkeypatch.setattr(os, 'open', lambda *args: opened.append(args))
    for target in ['/dev/sda', '/dev/sda2', '/dev/mmcblk0p1', '/dev/disk/by-id/sd']:
        with pytest.raises(RuntimeError, match='Only whole physical SD'):
            namespace['snapshot'](target)
    assert not opened


@pytest.mark.parametrize('condition', ['root-mount', 'boot-mount', 'swap', 'holder', 'mapped'])
def test_all_target_descendants_must_be_inactive(condition):
    nodes = [{'path': '/dev/mmcblk0', 'type': 'disk', 'maj:min': '179:0', 'mountpoints': []},
             {'path': '/dev/mmcblk0p1', 'type': 'part', 'maj:min': '179:1', 'mountpoints': []},
             {'path': '/dev/mmcblk0p2', 'type': 'part', 'maj:min': '179:2', 'mountpoints': []}]
    mounts, swaps = set(), set()
    if condition == 'root-mount':
        mounts.add('179:2')
    elif condition == 'boot-mount':
        nodes[1]['mountpoints'] = ['/boot/firmware']
    elif condition == 'swap':
        swaps.add('/dev/mmcblk0p2')
    elif condition == 'mapped':
        nodes.append({'path': '/dev/dm-0', 'type': 'crypt', 'maj:min': '253:0', 'mountpoints': []})
    with pytest.raises(RuntimeError):
        namespace['inactive_nodes'](nodes, mounts, swaps, lambda path: condition == 'holder' and path.endswith('p2'))


def test_complete_stream_wrong_hash_never_succeeds(monkeypatch):
    monkeypatch.setitem(namespace, 'layout', lambda *args: {'offset': 8388608})
    data = image_header() + b'payload' * 100
    events = []
    with pytest.raises(RuntimeError, match='Transferred image checksum mismatch'):
        namespace['stream_write'](io.BytesIO(data), lambda part: len(part), len(data), '0' * 64,
                                  lambda *args: events.append(args))
    # 100% written is explicitly distinct from hash-verified completion.
    assert events[-1] == ('write', len(data), len(data))


def test_extra_stream_bytes_are_refused_even_when_prefix_hash_matches(monkeypatch):
    monkeypatch.setitem(namespace, 'layout', lambda *args: {'offset': 8388608})
    data = image_header() + b'payload'
    with pytest.raises(RuntimeError, match='Input larger'):
        namespace['stream_write'](io.BytesIO(data + b'extra'), lambda part: len(part), len(data), hashlib.sha256(data).hexdigest(),
                                  lambda *args: None)
