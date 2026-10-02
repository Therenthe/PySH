#!/usr/bin/python3
"""Expand only the running PySH UUID-backed two-partition root."""
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

ENV = {**os.environ, 'LC_ALL': 'C', 'PATH': '/usr/sbin:/usr/bin:/sbin:/bin'}

def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, env=ENV, check=check, timeout=180)

def scalar(*args):
    value = run(*args).stdout.strip()
    if not value or '\n' in value:
        raise RuntimeError('Expected a single nonempty value: ' + args[0])
    return value

def block(path):
    path = Path(path).resolve(strict=True)
    if not stat.S_ISBLK(path.stat().st_mode):
        raise RuntimeError('Expected block device')
    return str(path)

def uuid_for(path):
    return scalar('blkid', '-s', 'UUID', '-o', 'value', path)

def fstab_uuids(path):
    found = {}
    for line in Path(path).read_text().splitlines():
        row = line.split()
        if not row or row[0].startswith('#') or len(row) < 4:
            continue
        if row[1] in ('/', '/boot/firmware'):
            if row[1] in found or not row[0].startswith('UUID='):
                raise RuntimeError('Expected unique UUID fstab entries')
            found[row[1]] = (row[0][5:], row[2])
    if set(found) != {'/', '/boot/firmware'}:
        raise RuntimeError('Missing expected fstab entries')
    return found

def mounted(target):
    mount = json.loads(run('findmnt', '--json', '--mountpoint', target, '--output', 'SOURCE,FSTYPE,MAJ:MIN,OPTIONS').stdout)['filesystems']
    if len(mount) != 1:
        raise RuntimeError('Expected exactly one mount')
    value = mount[0]
    if 'rw' not in value['options'].split(','):
        raise RuntimeError('Filesystem is not writable')
    # /dev/root aliases and mmc/nvme/sd names resolve through the kernel device ID.
    tree = json.loads(run('lsblk', '--json', '--list', '--paths', '--output', 'NAME,MAJ:MIN').stdout)['blockdevices']
    nodes = [node['name'] for node in tree if node['maj:min'] == value['maj:min']]
    if len(nodes) != 1:
        raise RuntimeError('Ambiguous mount block identity')
    return block(nodes[0])

def plan(root, boot, fstab, *, allow_loop_test=False):
    root, boot = block(root), block(boot)
    if scalar('lsblk', '--nodeps', '--noheadings', '--output', 'TYPE', root) != 'part':
        raise RuntimeError('Root is not a plain partition')
    if scalar('lsblk', '--nodeps', '--noheadings', '--output', 'TYPE', boot) != 'part':
        raise RuntimeError('Boot is not a plain partition')
    def parent(node):
        return block('/dev/' + Path(scalar('lsblk', '--nodeps', '--noheadings', '--output', 'PKNAME', node)).name)
    disk = parent(root)
    if parent(boot) != disk:
        raise RuntimeError('Boot and root are not on the same disk')
    kind = scalar('lsblk', '--nodeps', '--noheadings', '--output', 'TYPE', disk)
    if kind != 'disk' and not (allow_loop_test and kind == 'loop'):
        raise RuntimeError('Unsupported parent disk type')
    def number(node):
        return int((Path('/sys/class/block') / Path(node).name / 'partition').read_text())
    if number(root) != 2 or number(boot) != 1:
        raise RuntimeError('Expected boot partition 1 and final root partition 2')
    expected = fstab_uuids(fstab)
    if expected['/'] != (uuid_for(root), 'ext4') or expected['/boot/firmware'] != (uuid_for(boot), 'vfat'):
        raise RuntimeError('Filesystem UUID/type differs from fstab')
    if scalar('blkid', '-s', 'TYPE', '-o', 'value', root) != 'ext4' or scalar('blkid', '-s', 'TYPE', '-o', 'value', boot) != 'vfat':
        raise RuntimeError('Unexpected actual filesystem')
    table = json.loads(run('sfdisk', '--json', disk).stdout)['partitiontable']
    parts = table['partitions']
    if table['label'] != 'dos' or table.get('sectorsize') != 512 or len(parts) != 2:
        raise RuntimeError('Expected the exact PySH DOS two-partition layout')
    first, last = parts
    if block(first['node']) != boot or block(last['node']) != root:
        raise RuntimeError('Partition nodes differ from mounted devices')
    if (first['start'], first['size'], first['type'].lower()) != (16384, 524288, 'c'):
        raise RuntimeError('Boot geometry differs from PySH image')
    if last['start'] != 540672 or last['size'] < 8388608 or last['type'].lower() != '83':
        raise RuntimeError('Root geometry differs from PySH image')
    if first['start'] + first['size'] != last['start']:
        raise RuntimeError('Unexpected partition ordering')
    return {'disk': disk, 'root': root, 'boot': boot, 'root_uuid': uuid_for(root), 'boot_uuid': uuid_for(boot), 'table': table}

def expand(root, boot, fstab, stamp, *, allow_loop_test=False, runner=run):
    before = plan(root, boot, fstab, allow_loop_test=allow_loop_test)
    Path(stamp).unlink(missing_ok=True)
    # Every run revalidates identity. Stamp is evidence, never a bypass of guards.
    result = runner('growpart', before['disk'], '2', check=False)
    output = result.stdout + result.stderr
    if result.returncode != 0 and not (result.returncode == 1 and output.startswith('NOCHANGE:')):
        raise RuntimeError('growpart failed; no success stamp: ' + output.strip())
    runner('udevadm', 'settle', '--timeout=15')
    after = plan(root, boot, fstab, allow_loop_test=allow_loop_test)
    if before['table'].get('id') != after['table'].get('id') or before['disk'] != after['disk'] or before['root_uuid'] != after['root_uuid'] or before['boot_uuid'] != after['boot_uuid']:
        raise RuntimeError('Block identity changed')
    if before['table']['partitions'][0] != after['table']['partitions'][0] or after['table']['partitions'][1]['size'] < before['table']['partitions'][1]['size']:
        raise RuntimeError('Unexpected partition mutation')
    expected_size = after['table']['partitions'][1]['size'] * 512
    deadline = time.monotonic() + 10
    while int(scalar('blockdev', '--getsize64', root)) != expected_size:
        if time.monotonic() > deadline:
            raise RuntimeError('Kernel partition size not refreshed; retry next boot')
        time.sleep(.2)
    runner('resize2fs', root)
    header = runner('dumpe2fs', '-h', root).stdout
    count = int(re.search(r'^Block count:\s+(\d+)$', header, re.M)[1])
    size = int(re.search(r'^Block size:\s+(\d+)$', header, re.M)[1])
    if count * size < expected_size - size:
        raise RuntimeError('Filesystem did not fill the expanded root partition')
    stamp = Path(stamp)
    stamp.parent.mkdir(parents=True, exist_ok=True)
    temporary = stamp.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump({'root_uuid': before['root_uuid'], 'bytes': count * size}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, stamp)
    directory = os.open(stamp.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    print('PySH root expansion verified', json.dumps({'root_uuid': before['root_uuid'], 'bytes': count * size}))

if __name__ == '__main__':
    if os.geteuid() != 0:
        raise SystemExit('Root required')
    with open('/run/pysh-growfs.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        expand(mounted('/'), mounted('/boot/firmware'), '/etc/fstab', '/var/lib/pysh/growfs.json')
