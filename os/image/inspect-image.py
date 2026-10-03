"""Inspect the generated disk/partition files without mounting or flashing."""
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

image = Path(sys.argv[1]).resolve(strict=True)
root = image.parent / 'root.ext4'
boot = image.parent / 'boot.vfat'
with image.open('rb') as stream:
    mbr = stream.read(512)
assert mbr[510:] == b'\x55\xaa', 'Missing MBR signature'
partitions = []
for i in range(4):
    entry = mbr[446+i*16:462+i*16]
    start, sectors = struct.unpack('<II', entry[8:])
    if sectors:
        assert start > 0 and (start+sectors)*512 <= image.stat().st_size
        partitions.append({'type': entry[4], 'start': start, 'sectors': sectors})
assert len(partitions) == 2 and partitions[0]['type'] in {11,12} and partitions[1]['type'] == 131
assert partitions[0]['start']+partitions[0]['sectors'] <= partitions[1]['start']

def read_root(path):
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder) / 'file'
        subprocess.run(['debugfs', '-R', f'dump {path} {output}', str(root)], check=True, capture_output=True)
        assert output.is_file(), f'Missing image file: {path}'
        return output.read_bytes()

# Probe the generated filesystems themselves; naming the disk sda/mmcblk0 is unnecessary.
def filesystem_uuid(path):
    value = subprocess.check_output(['blkid', '-p', '-s', 'UUID', '-o', 'value', str(path)], text=True).strip()
    assert value, f'Missing filesystem UUID: {path}'
    return value

root_uuid, boot_uuid = filesystem_uuid(root), filesystem_uuid(boot)
fstab = [line.split() for line in read_root('/etc/fstab').decode().splitlines()
         if line.strip() and not line.lstrip().startswith('#')]
assert [row for row in fstab if row[1] == '/'] == [
    [f'UUID={root_uuid}', '/', 'ext4', 'rw,relatime,errors=remount-ro,commit=30', '0', '1']]
assert [row for row in fstab if row[1] == '/boot/firmware'] == [
    [f'UUID={boot_uuid}', '/boot/firmware', 'vfat', 'defaults,rw,noatime,errors=remount-ro', '0', '2']]
cmdline = subprocess.check_output(['mtype', '-i', str(boot), '::cmdline.txt'], text=True).split()
assert [token for token in cmdline if token.startswith('root=')] == [f'root=UUID={root_uuid}']
layout = json.loads(Path('.runtime/os-build/image-layout.json').read_text())
assert layout['upstream_commit'] == '262d4df5a9f9d4133370465399a7958a7c22cdc7'
assert layout['setup_sha256'] == hashlib.sha256(Path('os/image/assets/image-setup.sh').read_bytes()).hexdigest()
assert layout['files']['setup.sh'] == layout['setup_sha256']

manifest = json.loads(Path('os/image/payload/manifest.json').read_text())
for name, expected in manifest['files'].items():
    assert hashlib.sha256(read_root('/opt/pysh/current/'+name)).hexdigest() == expected, name
for name in ['pysh.service']:
    assert read_root('/etc/systemd/user/'+name) == Path('os/image/assets', name).read_bytes()
for name, installed in {
    'pysh-session':'/usr/local/bin/pysh-session',
    'labwc-autostart':'/etc/xdg/labwc/autostart',
    'labwc-rc.xml':'/etc/xdg/labwc/rc.xml',
    'greetd.toml':'/etc/greetd/config.toml',
    'greetd-tty.conf':'/etc/systemd/system/greetd.service.d/pysh-tty.conf',
    'pysh-provision-recovery':'/usr/local/sbin/pysh-provision-recovery',
    'pysh-recovery.service':'/etc/systemd/system/pysh-recovery.service',
    'pysh-growfs.py':'/usr/local/sbin/pysh-growfs',
    'pysh-growfs.service':'/etc/systemd/system/pysh-growfs.service',
    'org.pysh.keyboard.json':'/etc/chromium/native-messaging-hosts/org.pysh.keyboard.json',
}.items():
    assert read_root(installed) == Path('os/image/assets',name).read_bytes(), installed
groups = {line.split(':')[0]:line.split(':')[-1].split(',') for line in read_root('/etc/group').decode().splitlines()}
assert 'pysh' not in groups.get('sudo', [])
assert b'AllowUsers pysh-admin' in read_root('/etc/ssh/sshd_config.d/pysh-recovery.conf')
assert b'PasswordAuthentication no' in read_root('/etc/ssh/sshd_config.d/pysh-recovery.conf')
packages = read_root('/var/lib/dpkg/status')
package_records = [dict(line.split(': ', 1) for line in record.splitlines()
                        if ': ' in line and not line.startswith(' '))
                   for record in packages.decode().split('\n\n')]
assert any(p.get('Package') == 'libspa-0.2-bluetooth' and
           p.get('Status') == 'install ok installed' for p in package_records), 'Bluetooth audio plugin missing'
for required in ('wvkbd',):
    assert any(p.get('Package') == required and p.get('Status') == 'install ok installed'
               for p in package_records), f'Service-browser dependency missing: {required}'
keyboard_manifest = json.loads(read_root('/etc/chromium/native-messaging-hosts/org.pysh.keyboard.json'))
extension = json.loads(read_root('/opt/pysh/current/app/browser-extension/manifest.json'))
import base64
extension_id = ''.join(chr(97+int(c,16)) for c in hashlib.sha256(base64.b64decode(extension['key'])).hexdigest()[:32])
assert keyboard_manifest['allowed_origins'] == [f'chrome-extension://{extension_id}/']
Path('.runtime/os-build/packages.txt').write_bytes(packages)
source = json.loads(read_root('/etc/pysh-build.json'))
assert source == json.loads(Path('os/image/payload/source.json').read_text())
listing = subprocess.check_output(['mdir','-i',str(boot),'::'],text=True)
assert 'config' in listing and 'cmdline' in listing and 'kernel' in listing
report = {'source':source,'partitions':partitions,'image_bytes':image.stat().st_size,'verified_runtime_files':len(manifest['files']),'boot_firmware_present':True,'hub_has_sudo':False,'ssh':'key-only pysh-admin, requires offline provisioning','physical_boot':'OPEN','root_uuid':root_uuid,'boot_uuid':boot_uuid,'mounts':'verified filesystem UUIDs','image_layout':layout}
Path('.runtime/os-build/image-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
