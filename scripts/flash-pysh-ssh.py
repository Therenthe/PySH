"""Inspect by default; stream an inactive Raspberry SD backup/image over strict OpenSSH."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import threading
import time

HELPER = Path(__file__).with_name('flash-pysh-target.py')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path, phase=None):
    with path.open('rb') as stream:
        if not phase:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
        total, done, previous = path.stat().st_size, 0, 0.0
        h = hashlib.sha256()
        print(phase + ': started', flush=True)
        while data := stream.read(1024 * 1024):
            h.update(data)
            done += len(data)
            now = time.monotonic()
            if now - previous >= .5 or done == total:
                print(f'{phase}: {done:,}/{total:,} bytes ({round(done * 100 / total, 2)}%)', flush=True)
                previous = now
        require(done == total, 'Local file changed or was truncated during hashing')
        return h.hexdigest()


def local_id():
    p = Path('/etc/machine-id')
    return hashlib.sha256(p.read_bytes() if p.exists() else socket.gethostname().encode()).hexdigest()


def json_file(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def ssh_command(args, action, values):
    require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]*', args.host or ''), 'Invalid explicit host')
    require(re.fullmatch('[A-Za-z_][A-Za-z0-9_-]*', args.user or ''), 'Invalid explicit SSH user')
    require(args.key.is_file() and args.known_hosts.is_file(), 'Explicit SSH key and known-hosts files required')
    code = base64.b64encode(HELPER.read_bytes()).decode('ascii')
    invocation = "import base64;exec(compile(base64.b64decode('" + code + "'),'<pysh-flash-target>','exec'))"
    remote = ['sudo', '-n', 'python3', '-c', invocation, action]
    for key, value in values.items():
        remote.extend(['--' + key.replace('_', '-'), str(value)])
    return [args.ssh, '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
            '-o', 'IdentitiesOnly=yes', '-o', 'PasswordAuthentication=no',
            '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=3',
            '-o', 'UserKnownHostsFile=' + str(args.known_hosts.resolve()), '-i', str(args.key.resolve()),
            args.user + '@' + args.host, shlex.join(remote)]


def stderr_reader(stream, events):
    for raw in iter(stream.readline, b''):
        line = raw.decode('utf-8', errors='replace').strip()
        try:
            value = json.loads(line)
            events.append(value)
            phase = value.get('phase', '')
            if value.get('total'):
                print(f"{phase}: {value['bytes']:,}/{value['total']:,} bytes ({value['percent']}%)", flush=True)
            else:
                print(phase + (': ' + value['error'] if value.get('error') else ''), flush=True)
        except (ValueError, TypeError, KeyError):
            # OpenSSH diagnostics only; no passwords, browser data or helper command logging.
            print('SSH: ' + line, file=sys.stderr, flush=True)


def run_remote(args, action, values, input_path=None, backup_path=None):
    command = ssh_command(args, action, values)
    events = []
    process = subprocess.Popen(command, stdin=subprocess.PIPE if input_path else subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    observer = threading.Thread(target=stderr_reader, args=(process.stderr, events), daemon=True)
    observer.start()
    partial = None
    try:
        if backup_path:
            require(not backup_path.exists(), 'Backup destination already exists')
            partial = backup_path.with_name(backup_path.name + '.partial')
            descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            h = hashlib.sha256()
            count = 0
            with os.fdopen(descriptor, 'wb') as output:
                while data := process.stdout.read(1024 * 1024):
                    output.write(data)
                    h.update(data)
                    count += len(data)
                output.flush()
                os.fsync(output.fileno())
            result = None
        else:
            if input_path:
                with input_path.open('rb') as source:
                    while data := source.read(1024 * 1024):
                        process.stdin.write(data)
                process.stdin.close()
            result = process.stdout.read()
        require(process.wait() == 0, 'Remote operation failed; no success or reboot inferred')
        observer.join()
        require(not any(e.get('phase') == 'FAILED' for e in events), 'Remote helper reported failure')
        if backup_path:
            completed = [e for e in events if e.get('phase') == 'backup-complete']
            require(len(completed) == 1 and count == values['size'] == completed[0]['bytes'] and
                    h.hexdigest() == completed[0]['sha256'], 'Backup stream size/hash mismatch')
            require(all(completed[0][k] == values[k] for k in ['target', 'cid', 'size']), 'Backup identity mismatch')
            # Exclusive publication: never overwrite a file created while the stream was running.
            os.link(partial, backup_path)
            partial.unlink()
            return {k: completed[0][k] for k in ['target', 'cid', 'size', 'device']} | {'backup_sha256': h.hexdigest()}
        return json.loads(result)
    except BaseException:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        observer.join(timeout=5)
        # An incomplete local backup is retained as .partial, never certified or reused.
        raise
    finally:
        for stream in [process.stdin, process.stdout, process.stderr]:
            if stream is not None and not stream.closed:
                stream.close()


def verify_backup(path, record, receipt):
    require(set(record) == {'target', 'cid', 'size', 'device', 'backup_sha256'}, 'Invalid backup record')
    require(re.fullmatch('/dev/mmcblk[0-9]+', record['target']) and re.fullmatch('[0-9a-f]{32}', record['cid']), 'Invalid SD identity')
    require(isinstance(record['size'], int) and path.stat().st_size == record['size'], 'Full SD backup size mismatch')
    require(sha(path, 'backup-local-verify') == record['backup_sha256'], 'Independent PC backup checksum mismatch')
    require(local_id() != record['device'], 'Backup verification requires a separate computer')
    value = record | {'verified_on': local_id()}
    json_file(receipt, value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect', 'backup', 'hash', 'verify-backup', 'flash'], nargs='?', default='inspect')
    parser.add_argument('--ssh', default='ssh')
    parser.add_argument('--host')
    parser.add_argument('--user')
    parser.add_argument('--key', type=Path)
    parser.add_argument('--known-hosts', type=Path)
    parser.add_argument('--target')
    parser.add_argument('--cid')
    parser.add_argument('--size', type=int)
    parser.add_argument('--backup', type=Path)
    parser.add_argument('--backup-record', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--image', type=Path)
    parser.add_argument('--image-sha256')
    parser.add_argument('--public-key', type=Path)
    parser.add_argument('--write', action='store_true', help='Explicit destructive authorization; otherwise flash is a dry-run')
    args = parser.parse_args()
    if args.action == 'verify-backup':
        require(args.backup and args.backup_record and args.receipt, 'Backup, record and new receipt paths required')
        result = verify_backup(args.backup, json.loads(args.backup_record.read_text(encoding='utf-8')), args.receipt)
        print(json.dumps({'backup_verified': result['backup_sha256'], 'receipt': str(args.receipt)}))
        return
    require(args.key and args.known_hosts and args.target, 'Explicit SSH identity, known hosts and target required')
    require(re.fullmatch('/dev/mmcblk[0-9]+', args.target), 'Only whole SD devices supported')
    if args.action == 'inspect':
        print(json.dumps(run_remote(args, 'inspect', {'target': args.target}), indent=2))
        return
    require(re.fullmatch('[0-9a-f]{32}', args.cid or '') and args.size and args.size > 0,
            'Expected physical CID and exact size required')
    values = {'target': args.target, 'cid': args.cid, 'size': args.size}
    if args.action == 'hash':
        print(json.dumps(run_remote(args, 'hash', values), indent=2), flush=True)
        return
    if args.action == 'backup':
        require(args.backup and args.backup_record and not args.backup_record.exists(), 'New backup and record destinations required')
        record = run_remote(args, 'backup', values, backup_path=args.backup)
        json_file(args.backup_record, record)
        print(json.dumps({'backup_saved': str(args.backup), **record}))
        return
    require(args.image and args.image.is_file() and re.fullmatch('[0-9a-f]{64}', args.image_sha256 or ''),
            'Uncompressed image and expected SHA-256 required')
    require(args.image.stat().st_size <= args.size and sha(args.image, 'local-image-verify') == args.image_sha256, 'Local image checksum/size mismatch')
    # Import only pure format validators; Linux fcntl module is absent on Windows.
    source = HELPER.read_text(encoding='utf-8').replace('import fcntl\n', '')
    namespace = {'__name__': 'format_validator'}
    exec(compile(source, str(HELPER), 'exec'), namespace)
    with args.image.open('rb') as stream:
        namespace['layout'](stream.read(512), args.image.stat().st_size)
    require(args.public_key and args.receipt and args.backup and args.backup_record, 'Public key and verified full backup paths required')
    key = base64.b64encode(args.public_key.read_bytes()).decode('ascii')
    namespace['public_key'](key)
    record = json.loads(args.backup_record.read_text(encoding='utf-8'))
    receipt = json.loads(args.receipt.read_text(encoding='utf-8'))
    require(receipt == record | {'verified_on': local_id()} and sha(args.backup, 'backup-recheck') == record['backup_sha256'] and
            args.backup.stat().st_size == args.size and all(record[k] == values[k] for k in values),
            'Verified full backup receipt does not match selected SD')
    inspected = run_remote(args, 'inspect', {'target': args.target})
    require(all(inspected[k] == record[k] for k in ['target', 'cid', 'size', 'device']), 'Target changed since backup')
    print(json.dumps({'phase': 'plan', **values, 'image_bytes': args.image.stat().st_size,
                      'image_sha256': args.image_sha256, 'action': 'WRITE' if args.write else 'DRY-RUN'}), flush=True)
    if not args.write:
        return
    values.update(image_size=args.image.stat().st_size, image_sha256=args.image_sha256, public_key=key,
                  receipt=base64.b64encode(json.dumps(receipt).encode()).decode('ascii'))
    result = run_remote(args, 'flash', values, input_path=args.image)
    require(result.get('result') == 'image-and-key-verified' and result.get('image_sha256_before_provision') == args.image_sha256,
            'Missing verified completion; do not boot target')
    require(result.get('public_key_sha256') == hashlib.sha256(args.public_key.read_bytes()).hexdigest() and
            result.get('raw_image_modified_by_provision') is True and all(result.get(k) == values[k] for k in ['target', 'cid', 'size']),
            'Final public-key or physical target proof mismatch')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print('FAILED: ' + str(error), file=sys.stderr, flush=True)
        raise SystemExit(1)
