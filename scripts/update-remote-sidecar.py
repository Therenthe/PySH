"""Verified code-only LAN gateway update; retain pairing keys and rollback code.

Usage on the appliance: sudo python3 update-remote-sidecar.py ARCHIVE --sha256 SHA
No certificate, token, port, networking, unit or main hub changes are made.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
import urllib.request

LEGACY_FILES={'services/remote/__init__.py','services/remote/__main__.py','services/remote/gateway.py','services/remote/pysh-remote.service'}
FILES=LEGACY_FILES|{'services/remote/discovery.py'}

def require(ok,message):
    if not ok:raise RuntimeError(message)

def archive_files(archive,sha):
    require(re.fullmatch('[0-9a-f]{64}',sha) is not None,'Invalid checksum')
    require(hashlib.sha256(archive.read_bytes()).hexdigest()==sha,'Archive checksum mismatch')
    with tarfile.open(archive,'r:gz') as bundle:
        members=bundle.getmembers()
        require(len(members)==len(FILES) and {m.name for m in members}==FILES,'Unexpected archive member')
        require(all(m.isfile() and 0<=m.size<128*1024 for m in members),'Unexpected source file')
        return {m.name:bundle.extractfile(m).read() for m in members}

def verify_release(release):
    require(release.parent==Path('/opt/pysh-remote/releases') and re.fullmatch('[0-9a-f]{12}',release.name) is not None,'Foreign release')
    require(release.is_dir() and not release.is_symlink(),'Invalid release directory')
    manifest=json.loads((release/'manifest.json').read_text())
    names=set(manifest['files'])
    require(manifest['build']==release.name and names in (FILES,LEGACY_FILES),'Unexpected manifest')
    require({str(p.relative_to(release)) for p in release.rglob('*') if p.is_file()}==names|{'manifest.json'},'Unexpected runtime file')
    for name in names:
        path=release/name
        require(not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==manifest['files'][name],'Modified installed source')
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive',type=Path);parser.add_argument('--sha256',required=True);args=parser.parse_args()
    require(os.name=='posix' and os.geteuid()==0,'Run on Linux as root')
    require(Path('/etc/pysh-build.json').is_file(),'PySH appliance marker required')
    import fcntl,pwd
    with Path('/run/lock/pysh-remote-update.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        runtime=Path('/opt/pysh-remote');current=runtime/'current'
        require(runtime.is_dir() and not runtime.is_symlink() and current.is_symlink(),'Existing managed gateway required')
        require(runtime.stat().st_uid==0 and not runtime.stat().st_mode&0o022,'Insecure gateway root')
        require(not (runtime/'releases').is_symlink() and (runtime/'releases').stat().st_uid==0 and not (runtime/'releases').stat().st_mode&0o022,'Insecure release root')
        old=current.resolve();verify_release(old)
        contents=archive_files(args.archive,args.sha256)
        account=pwd.getpwnam('pysh');unit=Path(account.pw_dir)/'.config/systemd/user/pysh-remote.service'
        expected=contents['services/remote/pysh-remote.service'].decode().replace('WorkingDirectory=/opt/pysh/current','WorkingDirectory=/opt/pysh-remote/current')
        require(unit.is_file() and not unit.is_symlink() and unit.read_text()==expected,'Unit changes require separate review')
        release=runtime/'releases'/args.sha256[:12]
        require(not release.exists() and not release.is_symlink(),'Release already exists')
        release.mkdir(mode=0o755)
        for name,data in contents.items():
            target=release/name;target.parent.mkdir(parents=True,exist_ok=True,mode=0o755);target.write_bytes(data);target.chmod(0o644)
        manifest={'build':release.name,'archive_sha256':args.sha256,'files':{name:hashlib.sha256(data).hexdigest() for name,data in contents.items()}}
        (release/'manifest.json').write_text(json.dumps(manifest,indent=2));verify_release(release)
        environment=['runuser','-u','pysh','--','env',f'XDG_RUNTIME_DIR=/run/user/{account.pw_uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{account.pw_uid}/bus','systemctl','--user']
        def restart():subprocess.run(environment+['restart','pysh-remote.service'],check=True,timeout=30)
        def link(target,name):
            pointer=runtime/(name+'.next');require(not pointer.exists() and not pointer.is_symlink(),'Unexpected temporary pointer')
            pointer.symlink_to(target,target_is_directory=True);os.replace(pointer,runtime/name)
        # Use the saved, unchanged private LAN host; never return bearer tokens.
        config=json.loads((Path(account.pw_dir)/'.local/share/pi-smart-hub/remote/config.json').read_text())
        import ssl,ipaddress
        remote_data=Path(account.pw_dir)/'.local/share/pi-smart-hub/remote'
        marker=remote_data/'runtime.json'
        endpoint_host=config['host']
        if marker.exists():
            live=json.loads(marker.read_text())
            if live.get('ready') is True and live.get('updated',0)>time.time()-10 and live.get('host'):
                endpoint_host=live['host']
        address=ipaddress.ip_address(endpoint_host)
        require(address.version==4 and any(address in ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16')) and config['port']==8766,'Unexpected LAN endpoint')
        context=ssl.create_default_context(cafile=str(Path(account.pw_dir)/'.local/share/pi-smart-hub/remote/certificate.pem'))
        # DHCP may change the address while the exact trusted self-signed
        # certificate stays fixed. Trust the retained certificate, not its old SAN.
        context.check_hostname=False
        previous=runtime/'previous'
        require(not previous.exists() or previous.is_symlink() and previous.resolve().parent==runtime/'releases','Foreign previous pointer')
        try:
            link(release,'current');restarted_at=time.time();restart()
            deadline=time.monotonic()+15
            while True:
                try:
                    enabled=json.loads((remote_data/'devices.json').read_text()).get('enabled',True) is True
                    if not enabled:
                        live=json.loads(marker.read_text())
                        require(live.get('protocol')==2 and live.get('updated',0)>restarted_at and live.get('ready') is True and live.get('host')=='','Disabled supervisor not ready')
                        subprocess.run(environment+['is-active','--quiet','pysh-remote.service'],check=True,timeout=3)
                        break
                    result=json.load(urllib.request.urlopen(f"https://{endpoint_host}:8766/remote/health",context=context,timeout=2))
                    require(result.get('service')=='pysh-remote','Unexpected gateway health');break
                except Exception:
                    if time.monotonic()>=deadline:raise
                    time.sleep(.25)
        except BaseException:
            link(old,'current');restart();raise
        link(old,'previous')
        print(json.dumps({'activated':release.name,'previous':old.name,'pairing_preserved':True}))

if __name__=='__main__':main()
