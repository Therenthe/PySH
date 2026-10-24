"""Install the optional LAN bridge beside PySH; never replace the running hub.

Run as root on the identified appliance with a locally verified source archive.
The archive contains only the four allowlisted gateway source files.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import subprocess
import tarfile

FILES = {"services/remote/__init__.py", "services/remote/__main__.py", "services/remote/gateway.py", "services/remote/pysh-remote.service"}


def run(*command):
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--host", required=True)
    args = parser.parse_args()
    assert os.geteuid() == 0, "Run as root"
    assert Path("/etc/pysh-build.json").is_file(), "PySH appliance marker required"
    assert Path("/opt/pysh/venv/bin/python").is_file(), "Existing PySH interpreter required"
    import ipaddress
    address = ipaddress.ip_address(args.host)
    assert address.version == 4 and any(address in ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")), "Explicit private IPv4 required"
    digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    assert digest == args.sha256, "Archive checksum mismatch"
    account = pwd.getpwnam("pysh")
    home = Path(account.pw_dir)
    runtime = Path("/opt/pysh-remote")
    unit = home / ".config/systemd/user/pysh-remote.service"
    assert not runtime.exists() and not runtime.is_symlink(), "Existing sidecar retained; update requires a separate transaction"
    assert not unit.exists() and not unit.is_symlink(), "Existing unit retained"
    data = home / ".local/share/pi-smart-hub/remote"
    assert not data.exists(), "Existing pairing and certificate data retained"
    with tarfile.open(args.archive, "r:gz") as archive:
        entries = archive.getmembers()
        assert len(entries) == len(FILES) and {e.name for e in entries} == FILES, "Unexpected archive member"
        assert all(e.isfile() and e.size < 128 * 1024 for e in entries), "Unexpected source file"
        release = runtime / "releases" / digest[:12]
        release.mkdir(parents=True, mode=0o755)
        for member in entries:
            target = release / member.name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            with archive.extractfile(member) as stream:
                target.write_bytes(stream.read())
            target.chmod(0o644)
    hashes = {name: hashlib.sha256((release / name).read_bytes()).hexdigest() for name in sorted(FILES)}
    (release / "manifest.json").write_text(json.dumps({"build": digest[:12], "archive_sha256": digest, "files": hashes}, indent=2))
    runtime.joinpath("current").symlink_to(release, target_is_directory=True)
    run("sudo", "-H", "-u", "pysh", "/opt/pysh/venv/bin/python", "-c", "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('services.remote',run_name='__main__')", str(release), "init", "--host", args.host)
    unit.parent.mkdir(parents=True, exist_ok=True)
    os.chown(unit.parent, account.pw_uid, account.pw_gid)
    unit.write_text((release / "services/remote/pysh-remote.service").read_text().replace("WorkingDirectory=/opt/pysh/current", "WorkingDirectory=/opt/pysh-remote/current"))
    unit.chmod(0o644)
    os.chown(unit, account.pw_uid, account.pw_gid)
    user = ("sudo", "-H", "-u", "pysh", "env", f"XDG_RUNTIME_DIR=/run/user/{account.pw_uid}", f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{account.pw_uid}/bus", "systemctl", "--user")
    run(*user, "daemon-reload")
    run(*user, "enable", "--now", "pysh-remote.service")
    run(*user, "is-active", "pysh-remote.service")
    print(json.dumps({"build": digest[:12], "files": len(hashes), "host": args.host, "port": 8766, "hub_runtime": str(Path('/opt/pysh/current').resolve())}))


if __name__ == "__main__":
    main()
