#!/usr/bin/python3
"""Linux root-only integration test. Creates/detaches ONLY its own sparse loop disk.
Dependencies: cloud-guest-utils util-linux e2fsprogs dosfstools udev python3.
Exercises real offline and mounted-online resize of owned loops only.
Physical SD/USB/NVMe first boot still needs hardware evidence.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

spec = importlib.util.spec_from_file_location('growfs', Path(__file__).resolve().parents[1] / 'assets/pysh-growfs.py')
grow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grow)

def shell(*args, stdin=None):
    return subprocess.run(args, input=stdin, text=True, capture_output=True, check=True, env=grow.ENV).stdout.strip()

def expect_failure(call, fragment):
    try:
        call()
    except RuntimeError as error:
        assert fragment in str(error), str(error)
    else:
        raise AssertionError('Expected guard failure')

assert os.geteuid() == 0, 'Run only on a throwaway Linux CI runner as root'
with tempfile.TemporaryDirectory(prefix='pysh-growfs-loop-') as folder:
    folder = Path(folder)
    image = folder / 'throwaway.img'
    with image.open('wb') as stream:
        stream.truncate(6 * 1024**3)
    loop = shell('losetup', '--find', '--show', '--partscan', str(image))
    assert loop.startswith('/dev/loop')
    own_mounts = []
    try:
        shell('sfdisk', loop, stdin='label: dos\nunit: sectors\n\nstart=16384,size=524288,type=c\nstart=540672,size=8388608,type=83\n')
        shell('partx', '--update', loop)
        shell('udevadm', 'settle', '--timeout=15')
        root, boot = loop + 'p2', loop + 'p1'
        shell('mkfs.vfat', '-F', '32', boot)
        shell('mkfs.ext4', '-F', '-q', root)
        root_id, boot_id = grow.uuid_for(root), grow.uuid_for(boot)
        fstab, stamp = folder / 'fstab', folder / 'stamp.json'
        valid = f'UUID={root_id} / ext4 rw 0 1\nUUID={boot_id} /boot/firmware vfat rw 0 2\n'
        fstab.write_text(valid)
        initial = grow.plan(root, boot, fstab, allow_loop_test=True)
        # Rejected layouts modify only the table of this owned, unmounted loop.
        # Never wipe the ext4/VFAT signatures; restore the exact original dump.
        original_dump = shell('sfdisk', '--dump', loop)
        def signatures():
            values = []
            for node in (root, boot):
                with open(node, 'rb') as stream:
                    values.append(hashlib.sha256(stream.read(65536)).hexdigest())
            return values
        original_signatures = signatures()
        malformed = [
            ('extra_partition', 'label: dos\nunit: sectors\n\nstart=16384,size=524288,type=c\nstart=540672,size=8388608,type=83\nstart=8929280,size=65536,type=83\n'),
            ('gpt_layout', 'label: gpt\nunit: sectors\n\nstart=16384,size=524288,type=U\nstart=540672,size=8388608,type=L\n'),
        ]
        for name, table in malformed:
            try:
                assert Path(shell('losetup', '--noheadings', '--output', 'BACK-FILE', loop)).resolve() == image.resolve()
                shell('sfdisk', '--wipe', 'always', '--wipe-partitions', 'never', loop, stdin=table)
                shell('partx', '--update', loop)
                shell('udevadm', 'settle', '--timeout=15')
                expect_failure(lambda: grow.expand(root, boot, fstab, stamp, allow_loop_test=True), 'two-partition layout')
                assert not stamp.exists(), name
                assert signatures() == original_signatures, name
            finally:
                shell('sfdisk', '--wipe', 'always', '--wipe-partitions', 'never', loop, stdin=original_dump + '\n')
                shell('partx', '--update', loop)
                shell('udevadm', 'settle', '--timeout=15')
            assert shell('sfdisk', '--dump', loop) == original_dump, name
            assert grow.plan(root, boot, fstab, allow_loop_test=True)['table'] == initial['table'], name
            assert signatures() == original_signatures, name
        foreign_image = folder / 'unrelated-test-only.img'
        with foreign_image.open('wb') as stream:
            stream.truncate(16 * 1024**2)
        foreign_loop = shell('losetup', '--find', '--show', '--partscan', str(foreign_image))
        assert foreign_loop.startswith('/dev/loop') and foreign_loop != loop
        try:
            shell('sfdisk', foreign_loop, stdin='label: dos\nunit: sectors\n\nstart=2048,size=16384,type=c\n')
            shell('partx', '--update', foreign_loop)
            shell('udevadm', 'settle', '--timeout=15')
            foreign_before = shell('sfdisk', '--json', foreign_loop)
            expect_failure(lambda: grow.expand(root, foreign_loop + 'p1', fstab, stamp, allow_loop_test=True), 'same disk')
            assert shell('sfdisk', '--json', foreign_loop) == foreign_before
            assert not stamp.exists()
        finally:
            shell('losetup', '--detach', foreign_loop)
        # Production will never accept loop targets; test exemption is internal only.
        expect_failure(lambda: grow.plan(root, boot, fstab), 'parent disk type')
        fstab.write_text(valid.replace(root_id, 'wrong-uuid'))
        expect_failure(lambda: grow.expand(root, boot, fstab, stamp, allow_loop_test=True), 'UUID/type')
        assert not stamp.exists()
        fstab.write_text(valid)
        expect_failure(lambda: grow.plan(boot, root, fstab, allow_loop_test=True), 'partition 1')
        def failed_grow(*args, **kwargs):
            if args[0] == 'growpart':
                return subprocess.CompletedProcess(args, 2, '', 'FAILED: injected partition failure')
            return grow.run(*args, **kwargs)
        expect_failure(lambda: grow.expand(root, boot, fstab, stamp, allow_loop_test=True, runner=failed_grow), 'growpart failed')
        assert grow.plan(root, boot, fstab, allow_loop_test=True)['table'] == initial['table']
        assert not stamp.exists()
        def ambiguous_nochange(*args, **kwargs):
            if args[0] == 'growpart':
                return subprocess.CompletedProcess(args, 1, '', 'unknown failure')
            return grow.run(*args, **kwargs)
        expect_failure(lambda: grow.expand(root, boot, fstab, stamp, allow_loop_test=True, runner=ambiguous_nochange), 'growpart failed')
        assert not stamp.exists()
        def failed_resize(*args, **kwargs):
            if args[0] == 'resize2fs':
                raise subprocess.CalledProcessError(1, args)
            return grow.run(*args, **kwargs)
        try:
            grow.expand(root, boot, fstab, stamp, allow_loop_test=True, runner=failed_resize)
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError('Expected resize failure')
        assert not stamp.exists()
        grown = grow.plan(root, boot, fstab, allow_loop_test=True)
        assert grown['table']['partitions'][1]['size'] > initial['table']['partitions'][1]['size']
        # Recovery retry: partition already expanded -> genuine growpart NOCHANGE,
        # then filesystem resize still executes and must verify its final block size.
        grow.expand(root, boot, fstab, stamp, allow_loop_test=True)
        first = json.loads(stamp.read_text())
        assert first['bytes'] > 5 * 1024**3
        grow.expand(root, boot, fstab, stamp, allow_loop_test=True)
        assert json.loads(stamp.read_text()) == first
        final = grow.plan(root, boot, fstab, allow_loop_test=True)
        assert final['table']['partitions'][0] == initial['table']['partitions'][0]
        assert final['root_uuid'] == root_id and final['boot_uuid'] == boot_id
        # Use private exact mountpoints; never mount over the runner's / or /boot.
        root_mount, boot_mount = folder / 'mounted-root', folder / 'mounted-boot'
        root_mount.mkdir()
        boot_mount.mkdir()
        shell('mount', '-t', 'ext4', root, str(root_mount))
        own_mounts.append(root_mount)
        shell('mount', '-t', 'vfat', boot, str(boot_mount))
        own_mounts.append(boot_mount)
        assert grow.mounted(str(root_mount)) == root
        assert grow.mounted(str(boot_mount)) == boot
        marker = root_mount / 'preserved.txt'
        marker.write_text('PySH owned-loop online growth marker\n')
        shell('sync', '-f', str(marker))
        assert Path(shell('losetup', '--noheadings', '--output', 'BACK-FILE', loop)).resolve() == image.resolve()
        with image.open('r+b') as stream:
            stream.truncate(7 * 1024**3)
            stream.flush()
            os.fsync(stream.fileno())
        shell('losetup', '--set-capacity', loop)
        assert int(shell('blockdev', '--getsize64', loop)) == 7 * 1024**3
        online_stamp = root_mount / 'online-growth.json'
        grow.expand(grow.mounted(str(root_mount)), grow.mounted(str(boot_mount)), fstab, online_stamp, allow_loop_test=True)
        online = json.loads(online_stamp.read_text())
        assert online['bytes'] > first['bytes'] + 512 * 1024**2
        assert marker.read_text() == 'PySH owned-loop online growth marker\n'
        assert grow.mounted(str(root_mount)) == root and grow.mounted(str(boot_mount)) == boot
        online_table = grow.plan(root, boot, fstab, allow_loop_test=True)
        assert online_table['table']['partitions'][0] == initial['table']['partitions'][0]
        assert online_table['root_uuid'] == root_id and online_table['boot_uuid'] == boot_id
        # Repeat while still mounted: actual NOCHANGE + online resize is idempotent.
        grow.expand(root, boot, fstab, online_stamp, allow_loop_test=True)
        assert json.loads(online_stamp.read_text()) == online
        print(json.dumps({'result':'PASS', 'offline_bytes':first['bytes'], 'online_bytes':online['bytes'], 'loop':loop, 'checks':['wrong_uuid','foreign_boot_disk_untouched','wrong_partition','production_loop_rejection','extra_partition','gpt_layout','grow_failure','ambiguous_nochange','resize_failure_no_stamp','retry_actual_nochange','idempotent','boot_unchanged','mounted_findmnt_root_boot','online_grow_resize','online_file_preserved','online_idempotent']}))
    finally:
        # No broad/lazy/forced unmount. Detach only after our exact mounts unmount.
        for mount in reversed(own_mounts):
            shell('umount', str(mount))
        # Never broad detach (-D); detach precisely the one loop allocated above.
        shell('losetup', '--detach', loop)
