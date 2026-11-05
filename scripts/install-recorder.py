"""Install the explicit independent recording unit on a verified PySH appliance.

Run as root after activating a runtime containing this module and the unit.
This does not stop the Hub, change networking, or restart an active recording.
"""
import hashlib
import json
import os
from pathlib import Path
import pwd
import sqlite3
import subprocess
import sys


def main():
    if sys.platform != 'linux' or os.geteuid() != 0:
        raise SystemExit('Run as root on the PySH Linux appliance.')
    current = Path('/opt/pysh/current').resolve(strict=True)
    if current.parent != Path('/opt/pysh/releases'):
        raise SystemExit('Expected an activated versioned runtime.')
    marker = json.loads(Path('/opt/pysh/runtime-source.json').read_text(encoding='utf8'))
    source = current / 'os/systemd/pysh-recorder.service'
    if marker['build'] != current.name or marker['files'].get('os/systemd/pysh-recorder.service') != hashlib.sha256(source.read_bytes()).hexdigest():
        raise SystemExit('Recording unit is not part of the verified active release.')
    owner = pwd.getpwnam('pysh')
    database = Path(owner.pw_dir) / '.local/share/pi-smart-hub/iptv-recordings/jobs.sqlite3'
    if database.is_symlink():
        raise SystemExit('Unsafe recording database.')
    if database.exists():
        with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True, timeout=5) as connection:
            if connection.execute("SELECT count(*) FROM jobs WHERE state IN ('starting','recording','stopping')").fetchone()[0]:
                raise SystemExit('An active recording prevents updating its service. Try after it finishes.')
    target = Path('/etc/systemd/user/pysh-recorder.service')
    if target.is_symlink():
        raise SystemExit('Unsafe recording unit path.')
    if target.exists() and target.read_bytes() != source.read_bytes():
        raise SystemExit('An existing different recording unit needs an explicit migration.')
    if not target.exists():
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(descriptor, 'wb') as output:
            output.write(source.read_bytes()); output.flush(); os.fsync(output.fileno())
    prefix = ['runuser', '-u', 'pysh', '--', 'env', f'XDG_RUNTIME_DIR=/run/user/{owner.pw_uid}',
              f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{owner.pw_uid}/bus', 'systemctl', '--user']
    for args in (['daemon-reload'], ['enable', '--now', 'pysh-recorder.service'], ['is-active', 'pysh-recorder.service']):
        subprocess.run(prefix+args, check=True, timeout=30)
    print(json.dumps({'unit_installed': True, 'runtime': current.name, 'independent_of_hub': True}))


if __name__ == '__main__':
    main()
