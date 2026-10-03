"""Private stdin/stdout protocol for flash-pysh-ssh.py; Linux root, inactive SD only."""
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time

CHUNK = 1024 * 1024
_LAST_PROGRESS = {}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def progress(phase, done=0, total=0, **fields):
    now = time.monotonic()
    if total and done != total and phase in _LAST_PROGRESS and now - _LAST_PROGRESS[phase] < .5:
        return
    _LAST_PROGRESS[phase] = now
    print(json.dumps({'phase': phase, 'bytes': done, 'total': total,
                      'percent': round(done * 100 / total, 2) if total else None, **fields}), file=sys.stderr, flush=True)


def machine():
    return hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()


def inactive_nodes(nodes, mounts, swaps, held):
    for node in nodes:
        require(node['type'] in {'disk', 'part'}, 'Target has a mapped/held descendant')
        require(not any(node.get('mountpoints') or []) and node['maj:min'] not in mounts, 'Target or descendant is mounted')
        require(node['path'] not in swaps, 'Target contains active swap')
        require(not held(node['path']), 'Target has holders')


def snapshot(device):
    require(re.fullmatch('/dev/mmcblk[0-9]+', device), 'Only whole physical SD devices are permitted')
    path = Path(device)
    require(not path.is_symlink() and stat.S_ISBLK(path.stat().st_mode), 'Target is not a direct block device')
    tree = json.loads(subprocess.check_output(['lsblk', '--json', '--tree', '--bytes', '--output',
                     'PATH,TYPE,SIZE,MAJ:MIN,MOUNTPOINTS', device], text=True))['blockdevices']
    require(len(tree) == 1 and tree[0]['path'] == device and tree[0]['type'] == 'disk', 'Unexpected target tree')
    nodes = []
    def visit(node):
        nodes.append(node)
        for child in node.get('children', []):
            visit(child)
    visit(tree[0])
    mounts = {line.split()[2] for line in Path('/proc/self/mountinfo').read_text().splitlines()}
    swaps = {os.path.realpath(line.split()[0]) for line in Path('/proc/swaps').read_text().splitlines()[1:]}
    inactive_nodes(nodes, mounts, swaps,
                   lambda name: list((Path('/sys/class/block') / Path(name).name / 'holders').iterdir()))
    cid = (Path('/sys/class/block') / path.name / 'device/cid').read_text().strip().lower()
    require(re.fullmatch('[0-9a-f]{32}', cid), 'Missing physical SD CID')
    return {'target': device, 'cid': cid, 'size': int(tree[0]['size']), 'device': machine(),
            'major_minor': tree[0]['maj:min']}


def validated(device, cid, size):
    value = snapshot(device)
    require(value['cid'] == cid and value['size'] == size and size >= 1024, 'Target physical identity changed')
    return value


def open_target(device, expected, writing=False):
    # O_EXCL block-device claim additionally refuses a device already in use by the kernel.
    fd = os.open(device, (os.O_RDWR if writing else os.O_RDONLY) | os.O_EXCL | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISBLK(info.st_mode) and f'{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}' == expected['major_minor'],
                'Opened a different device')
        size = struct.unpack('Q', fcntl.ioctl(fd, 0x80081272, bytes(8)))[0]  # BLKGETSIZE64
        require(size == expected['size'], 'Opened device size changed')
        require(snapshot(device) == expected, 'Target changed before first I/O')
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_exact(stream, count):
    chunks = []
    remaining = count
    while remaining:
        data = stream.read(remaining)
        require(data, 'Incomplete input stream')
        chunks.append(data)
        remaining -= len(data)
    return b''.join(chunks)


def layout(mbr, image_size):
    require(len(mbr) == 512 and mbr[510:] == b'\x55\xaa', 'Invalid image MBR')
    parts = []
    for index in range(4):
        row = mbr[446 + index * 16:462 + index * 16]
        start, sectors = struct.unpack('<II', row[8:])
        if sectors:
            parts.append({'type': row[4], 'offset': start * 512, 'size': sectors * 512})
        else:
            require(row[4] == 0, 'Unexpected unused MBR slot')
    require(len(parts) == 2 and parts[0]['type'] in {6, 14, 11, 12} and parts[1]['type'] == 131,
            'Expected FAT boot and Linux root partitions')
    boot, root = parts
    require(boot['offset'] == 8388608 and boot['size'] == 268435456, 'Unexpected PySH boot partition bounds')
    require(root['offset'] >= boot['offset'] + boot['size'] and root['size'] > 0
            and root['offset'] + root['size'] <= image_size, 'Invalid root partition bounds')
    return boot


def public_key(encoded):
    data = base64.b64decode(encoded, validate=True)
    require(0 < len(data) <= 4096 and b'\x00' not in data, 'Invalid public key length')
    lines = data.decode('ascii').splitlines()
    require(len(lines) == 1, 'Expected one public key line')
    fields = lines[0].split()
    require(len(fields) >= 2 and fields[0] == 'ssh-ed25519', 'Only plain public Ed25519 keys supported')
    blob = base64.b64decode(fields[1], validate=True)
    require(len(blob) == 51 and blob[:15] == struct.pack('>I', 11) + b'ssh-ed25519'
            and blob[15:19] == struct.pack('>I', 32), 'Invalid Ed25519 key encoding')
    return data


def write_all(writer, data):
    position = 0
    while position < len(data):
        count = writer(data[position:])
        require(isinstance(count, int) and 0 < count <= len(data) - position, 'Incomplete target write')
        position += count


def stream_write(stream, writer, image_size, expected_hash, emit=progress):
    first = read_exact(stream, 512)
    boot = layout(first, image_size)
    h = hashlib.sha256()
    done = 0
    data = first
    while data:
        write_all(writer, data)
        h.update(data)
        done += len(data)
        emit('write', done, image_size)
        data = read_exact(stream, min(CHUNK, image_size - done)) if done < image_size else b''
    require(not stream.read(1), 'Input larger than declared image')
    require(h.hexdigest() == expected_hash, 'Transferred image checksum mismatch; target is incomplete')
    return boot


def read_hash(reader, total, phase, emit=progress):
    h = hashlib.sha256()
    done = 0
    while done < total:
        data = reader(min(CHUNK, total - done))
        require(data and len(data) <= total - done, 'Incomplete target read')
        h.update(data)
        done += len(data)
        emit(phase, done, total)
    return h.hexdigest()


def provision(device, expected, boot, key):
    require(snapshot(device) == expected, 'Target changed before key provisioning')
    subprocess.run(['blockdev', '--rereadpt', device], check=True)
    subprocess.run(['udevadm', 'settle', '--timeout=20'], check=True)
    partition = device + 'p1'
    require(not Path(partition).is_symlink() and stat.S_ISBLK(Path(partition).stat().st_mode), 'Missing direct boot partition')
    sysblock = Path('/sys/class/block') / Path(partition).name
    require(int((sysblock / 'start').read_text()) * 512 == boot['offset'] and
            int((sysblock / 'size').read_text()) * 512 == boot['size'], 'Boot partition bounds mismatch')
    require(subprocess.check_output(['blkid', '-p', '-s', 'TYPE', '-o', 'value', partition], text=True).strip() == 'vfat',
            'Boot partition is not FAT')
    require(snapshot(device) == expected, 'Target became mounted or changed before provisioning')
    key_hash = hashlib.sha256(key).hexdigest()
    with tempfile.TemporaryDirectory(prefix='pysh-flash-', dir='/run') as directory:
        mount = Path(directory)
        mounted = False
        try:
            subprocess.run(['mount', '-t', 'vfat', '-o', 'rw,nosuid,nodev,noexec', partition, directory], check=True)
            mounted = True
            require(all((mount / n).is_file() and not (mount / n).is_symlink() for n in ['config.txt', 'cmdline.txt']),
                    'Missing PySH boot files')
            target = mount / 'pysh-recovery.pub'
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, 'wb') as output:
                output.write(key)
                output.flush()
                os.fsync(output.fileno())
            subprocess.run(['umount', directory], check=True)
            mounted = False
            os.sync()
            subprocess.run(['mount', '-t', 'vfat', '-o', 'ro,nosuid,nodev,noexec', partition, directory], check=True)
            mounted = True
            require(not target.is_symlink() and hashlib.sha256(target.read_bytes()).hexdigest() == key_hash,
                    'Public key readback mismatch')
        finally:
            if mounted:
                subprocess.run(['umount', directory], check=True)
    progress('public-key-verified', sha256=key_hash, raw_image_modified=True)
    return key_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect', 'backup', 'flash'])
    parser.add_argument('--target', required=True)
    parser.add_argument('--cid')
    parser.add_argument('--size', type=int)
    parser.add_argument('--image-size', type=int)
    parser.add_argument('--image-sha256')
    parser.add_argument('--public-key')
    parser.add_argument('--receipt')
    args = parser.parse_args()
    require(os.geteuid() == 0, 'Root helper required')
    require(re.fullmatch('/dev/mmcblk[0-9]+', args.target), 'Only SD whole disks supported')
    with Path('/run/lock/pysh-flash-' + Path(args.target).name + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == 'inspect':
            print(json.dumps(snapshot(args.target)), flush=True)
            return
        expected = validated(args.target, args.cid, args.size)
        if args.action == 'backup':
            fd = open_target(args.target, expected)
            try:
                def read(count):
                    data = os.read(fd, count)
                    write_all(sys.stdout.buffer.write, data)
                    return data
                sha = read_hash(read, args.size, 'backup')
                sys.stdout.buffer.flush()
                progress('backup-complete', args.size, args.size, sha256=sha, **expected)
            finally:
                os.close(fd)
            return
        require(args.image_size is not None and 512 <= args.image_size <= args.size and
                re.fullmatch('[0-9a-f]{64}', args.image_sha256 or ''), 'Invalid image identity')
        key = public_key(args.public_key)
        receipt = json.loads(base64.b64decode(args.receipt, validate=True))
        require(set(receipt) == {'target', 'cid', 'size', 'device', 'backup_sha256', 'verified_on'} and
                all(receipt[k] == expected[k] for k in ['target', 'cid', 'size', 'device']) and
                re.fullmatch('[0-9a-f]{64}', receipt['backup_sha256']) and
                re.fullmatch('[0-9a-f]{64}', receipt['verified_on']) and receipt['verified_on'] != expected['device'],
                'Separate-host verified full backup receipt required')
        # Validate the MBR before opening the writable device or consuming the remaining stream.
        first = read_exact(sys.stdin.buffer, 512)
        boot = layout(first, args.image_size)
        expected = validated(args.target, args.cid, args.size)
        fd = open_target(args.target, expected, writing=True)
        try:
            class Prefixed:
                prefix = first
                def read(self, count):
                    if self.prefix:
                        data, self.prefix = self.prefix[:count], self.prefix[count:]
                        return data
                    return sys.stdin.buffer.read(count)
            stream_write(Prefixed(), lambda data: os.write(fd, data), args.image_size, args.image_sha256)
            os.fsync(fd)
            fcntl.ioctl(fd, 0x1261)  # BLKFLSBUF: invalidate block cache before independent readback.
            os.lseek(fd, 0, os.SEEK_SET)
            sha = read_hash(lambda count: os.read(fd, count), args.image_size, 'readback')
            require(sha == args.image_sha256, 'Independent raw image readback mismatch')
            progress('raw-image-verified', args.image_size, args.image_size, sha256=sha)
        finally:
            os.close(fd)
        key_sha = provision(args.target, expected, boot, key)
        print(json.dumps({'result': 'image-and-key-verified', 'image_sha256_before_provision': sha,
                          'public_key_sha256': key_sha, 'raw_image_modified_by_provision': True,
                          'target': args.target, 'cid': args.cid, 'size': args.size, 'boot_acceptance': 'OPEN'}), flush=True)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    signal.signal(signal.SIGHUP, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        progress('FAILED', error=str(error))
        raise SystemExit(1)
