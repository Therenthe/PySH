#!/usr/bin/python3
"""Linux root-only integration test. Creates/detaches ONLY its own sparse loop disk.
Dependencies: cloud-guest-utils util-linux e2fsprogs dosfstools udev python3.
This intentionally exercises offline resize; mounted first boot needs hardware evidence.
"""
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
        print(json.dumps({'result':'PASS', 'bytes':first['bytes'], 'loop':loop, 'checks':['wrong_uuid','foreign_boot_disk_untouched','wrong_partition','production_loop_rejection','grow_failure','ambiguous_nochange','resize_failure_no_stamp','retry_actual_nochange','idempotent','boot_unchanged']}))
    finally:
        # Never broad detach (-D); detach precisely the one loop allocated above.
        shell('losetup', '--detach', loop)
