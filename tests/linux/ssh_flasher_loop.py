"""Owned-loop kernel/FAT proof. Never permits physical disks or changes production policy."""
import argparse
import base64
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import struct
import subprocess
import time

SIZE = (540672 + 2048) * 512


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def run(arguments):
    return subprocess.check_output(arguments, text=True).strip()


def no_symlinks(path):
    for component in [path, *path.parents]:
        require(not component.is_symlink(), 'Symlink in fixture path')


def owned_loop(device, backing):
    require(re.fullmatch('/dev/loop[0-9]+', device), 'Fixture refuses all physical devices')
    require(not Path(device).is_symlink() and stat.S_ISBLK(Path(device).stat().st_mode), 'Missing direct loop device')
    rows = json.loads(run(['losetup', '--json', '--list', '--output', 'NAME,BACK-FILE,OFFSET,SIZELIMIT', device]))['loopdevices']
    require(len(rows) == 1 and rows[0]['name'] == device and
            Path(rows[0]['back-file']).resolve() == backing and int(rows[0]['offset']) == 0 and
            int(rows[0]['sizelimit']) == 0, 'Loop is not attached to the exact owned fixture file')
    require(backing.is_file() and not backing.is_symlink() and backing.stat().st_size == SIZE, 'Owned image identity changed')
    return rows[0]


def nodes(device):
    tree = json.loads(run(['lsblk', '--json', '--tree', '--bytes', '--output', 'PATH,TYPE,SIZE,MAJ:MIN,MOUNTPOINTS', device]))['blockdevices']
    require(len(tree) == 1 and tree[0]['path'] == device and tree[0]['type'] == 'loop' and int(tree[0]['size']) == SIZE,
            'Unexpected loop topology')
    result = []
    def visit(node):
        require(node['path'] == device or re.fullmatch(re.escape(device) + 'p[0-9]+', node['path']), 'Foreign loop descendant')
        require(node['type'] in {'loop', 'part'}, 'Mapped loop descendant refused')
        result.append(node)
        for child in node.get('children', []):
            visit(child)
    visit(tree[0])
    return result


def mounts_for(device):
    identities = {node['maj:min'] for node in nodes(device)}
    mounted = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        fields = line.split()
        if fields[2] in identities:
            value = fields[4]
            for escaped, plain in [('\\040', ' '), ('\\011', '\t'), ('\\012', '\n'), ('\\134', '\\')]:
                value = value.replace(escaped, plain)
            mounted.append(value)
    return mounted


def inactive(device, backing):
    owned_loop(device, backing)
    require(not mounts_for(device), 'Owned loop is mounted')
    for node in nodes(device):
        require(not any(node.get('mountpoints') or []), 'Owned loop mount reported by lsblk')
        require(not list((Path('/sys/class/block') / Path(node['path']).name / 'holders').iterdir()), 'Owned loop has holders')
    swaps = {os.path.realpath(line.split()[0]) for line in Path('/proc/swaps').read_text().splitlines()[1:]}
    require(not any(n['path'] in swaps for n in nodes(device)), 'Owned loop contains swap')


def wait_partition(device):
    partition = Path(device + 'p1')
    deadline = time.monotonic() + 10
    while not partition.exists():
        require(time.monotonic() < deadline, 'Loop partition node did not appear')
        time.sleep(.1)
    require(not partition.is_symlink() and stat.S_ISBLK(partition.stat().st_mode), 'Unsafe loop partition node')
    return str(partition)


def synthetic_image(path):
    header = bytearray(512)
    header[510:] = b'\x55\xaa'
    header[450] = 12
    header[466] = 131
    header[454:462] = struct.pack('<II', 16384, 524288)
    header[470:478] = struct.pack('<II', 540672, 2048)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(header)
        stream.truncate(SIZE)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--helper', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0, 'Root Linux fixture required')
    require(args.workspace.is_absolute() and args.helper.is_absolute() and args.report.is_absolute(), 'Explicit absolute paths required')
    no_symlinks(args.workspace)
    no_symlinks(args.helper)
    no_symlinks(args.report)
    require(all(p == p.resolve() for p in [args.workspace, args.helper, args.report]), 'Canonical explicit paths required')
    require(re.fullmatch('pysh-flasher-loop-[A-Za-z0-9_-]+', args.workspace.name), 'Fresh named fixture workspace required')
    require(not args.workspace.exists() and args.workspace.parent.is_dir(), 'Workspace must be new')
    require(args.helper.is_file() and args.helper.stat().st_size < 65536, 'Approved helper file required')
    require(args.report.parent.is_dir() and not args.report.exists() and not args.report.is_relative_to(args.workspace),
            'New report outside fixture workspace required')
    require(stat.S_IMODE(args.report.parent.stat().st_mode) & 0o077 == 0, 'Private report directory required')
    args.workspace.mkdir(mode=0o700)
    report_fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    report = {'result': 'FAIL', 'scope': 'owned loop kernel/FAT fixture; physical SD/boot acceptance OPEN',
              'helper_sha256': hashlib.sha256(args.helper.read_bytes()).hexdigest(), 'bytes': SIZE,
              'workspace': str(args.workspace), 'cleanup_errors': []}
    mappings = []
    failure = None
    try:
        spec = importlib.util.spec_from_file_location('approved_flasher_helper', args.helper)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        source = args.workspace / 'source.img'
        target = args.workspace / 'target.img'
        synthetic_image(source)
        with target.open('xb') as stream:
            stream.truncate(SIZE)
        source_loop = run(['losetup', '--find', '--show', '--partscan', str(source)])
        mappings.append((source_loop, source))
        inactive(source_loop, source)
        source_boot = wait_partition(source_loop)
        subprocess.run(['mkfs.vfat', '-F', '16', '-s', '8', '-n', 'PYSHBOOT', source_boot], check=True)
        mount = args.workspace / 'source-boot'
        mount.mkdir(mode=0o700)
        owned_loop(source_loop, source)
        subprocess.run(['mount', '-t', 'vfat', '-o', 'rw,nosuid,nodev,noexec', source_boot, str(mount)], check=True)
        (mount / 'config.txt').write_text('# synthetic owned fixture\n', encoding='ascii')
        (mount / 'cmdline.txt').write_text('console=tty1 root=fixture-only\n', encoding='ascii')
        for filename in ['config.txt', 'cmdline.txt']:
            with (mount / filename).open('rb') as stream:
                os.fsync(stream.fileno())
        subprocess.run(['umount', str(mount)], check=True)
        os.sync()
        inactive(source_loop, source)
        with source.open('rb') as stream:
            expected_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
        target_loop = run(['losetup', '--find', '--show', '--partscan', str(target)])
        mappings.append((target_loop, target))
        inactive(target_loop, target)
        expected = {'target': target_loop, 'cid': hashlib.sha256(str(target).encode()).hexdigest()[:32], 'size': SIZE,
                    'device': helper.machine(), 'major_minor': nodes(target_loop)[0]['maj:min']}
        # Fixture-only override checks an owned exact backing file every time. Production rejects loops unchanged.
        original_snapshot = helper.snapshot
        def fixture_snapshot(device):
            require(device == target_loop, 'Fixture snapshot refuses any other device')
            inactive(device, target)
            return dict(expected)
        helper.snapshot = fixture_snapshot
        try:
            descriptor = helper.open_target(target_loop, expected, writing=True)
            try:
                with source.open('rb') as stream:
                    boot = helper.stream_write(stream, lambda data: os.write(descriptor, data), SIZE, expected_hash)
                os.fsync(descriptor)
                fcntl.ioctl(descriptor, 0x1261)
                os.lseek(descriptor, 0, os.SEEK_SET)
                actual_hash = helper.read_hash(lambda count: os.read(descriptor, count), SIZE, 'loop-readback')
                require(actual_hash == expected_hash, 'Real loop image readback mismatch')
            finally:
                os.close(descriptor)
            key = b'ssh-ed25519 ' + base64.b64encode(struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32)
                                                   + hashlib.sha256(b'fixture public bytes; no private key').digest()) + b' fixture-only\n'
            require(helper.public_key(base64.b64encode(key)) == key, 'Synthetic public key rejected')
            key_hash = helper.provision(target_loop, expected, boot, key)
            inactive(target_loop, target)
            # Provisioning must change the raw image; the earlier exact-image proof remains separate.
            with target.open('rb') as stream:
                final_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
            require(final_hash != expected_hash and key_hash == hashlib.sha256(key).hexdigest(), 'Separate key/raw proof missing')
            report.update(result='PASS', raw_image_sha256_before_provision=actual_hash, public_key_sha256=key_hash,
                          raw_image_sha256_after_provision=final_hash, raw_image_modified_by_key=True,
                          target_loop=target_loop, real_block_flush=True, real_FAT_mount_remount=True)
        finally:
            helper.snapshot = original_snapshot
    except BaseException as error:
        failure = error
        report['error'] = str(error)
    finally:
        for device, backing in reversed(mappings):
            try:
                owned_loop(device, backing)
                for mountpoint in reversed(mounts_for(device)):
                    owned_loop(device, backing)
                    subprocess.run(['umount', mountpoint], check=True)
                inactive(device, backing)
                subprocess.run(['losetup', '--detach', device], check=True)
            except BaseException as error:
                report['cleanup_errors'].append(str(error))
        if report['cleanup_errors']:
            report['result'] = 'FAIL'
        report['all_owned_loops_detached'] = not report['cleanup_errors']
        with os.fdopen(report_fd, 'w', encoding='utf-8') as output:
            json.dump(report, output, indent=2)
            output.flush()
            os.fsync(output.fileno())
        print(json.dumps(report), flush=True)
    require(failure is None and report['result'] == 'PASS', 'Fixture failed; inspect private report and cleanup_errors')


if __name__ == '__main__':
    def interrupted(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    main()
