#!/usr/bin/env python3
"""Read-only PySH stability telemetry. Completion alone never accepts REL-01."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import time
import urllib.request

ACCEPTANCE = 'OPEN: telemetry requires separate periodic physical touch/media evidence'

class Invalidated(RuntimeError):
    """Candidate changed; observations cannot be combined across candidates."""

class Refused(RuntimeError):
    """A read-only observation guard failed."""

def require(condition, message):
    if not condition:
        raise Refused(message)

def allowed(name):
    path = PurePosixPath(name)
    return (str(path) == name and not path.is_absolute() and '..' not in path.parts
            and '\\' not in name and '__pycache__' not in path.parts and not name.endswith('.pyc')
            and (name.startswith(('services/backend/', 'app/browser-extension/', 'dist/'))
                 or name in {'requirements.lock', 'scripts/run-hub.py', 'scripts/install-session.sh',
                             'scripts/activate-release.sh', 'scripts/rollback.sh',
                             'scripts/probe-application.py', 'scripts/service-keyboard-host.py'}))

def read_json(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 4_000_000, 'invalid_metadata')
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

class Candidate:
    def __init__(self, root=Path('/opt/pysh'), marker=Path('/etc/pysh-build.json')):
        self.root, self.marker = Path(root), Path(marker)
        self.baseline = self.read(verify=True)

    def read(self, verify=False):
        require(self.root.is_dir() and not self.root.is_symlink(), 'invalid_runtime_root')
        for parent in self.root.parents:
            require(not parent.is_symlink(), 'runtime_ancestor_symlink')
        image = read_json(self.marker)
        require(isinstance(image, dict), 'invalid_image_marker')
        require(re.fullmatch('[0-9a-f]{12}', image.get('runtime_build', '')) and re.fullmatch('[0-9a-f]{40}', image.get('source', '')), 'invalid_image_marker')
        current = self.root / 'current'
        target = current.resolve(strict=True)
        managed = current.is_symlink()
        if managed:
            require(target.parent == self.root / 'releases' and target.name != '' and not (self.root / 'releases').is_symlink(), 'foreign_runtime_target')
            metadata = read_json(self.root / 'runtime-source.json')
            require(isinstance(metadata, dict), 'invalid_runtime_metadata')
            metadata_digest = sha(self.root / 'runtime-source.json')
        else:
            require(target == current and current.is_dir(), 'invalid_initial_runtime')
            metadata, metadata_digest = {}, None
        fingerprints, hashes = {}, {}
        for path in target.rglob('*'):
            require(not path.is_symlink(), 'runtime_file_symlink')
            if path.is_dir():
                continue
            if '__pycache__' in path.parts and path.suffix == '.pyc':
                continue
            name = path.relative_to(target).as_posix()
            require(path.is_file() and allowed(name), 'unknown_runtime_file')
            info = path.stat()
            fingerprints[name] = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_mode)
            if verify:
                hashes[name] = sha(path)
        if verify:
            build = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:12]
            require({'requirements.lock', 'scripts/run-hub.py', 'dist/index.html'} <= hashes.keys(), 'incomplete_runtime')
            if managed:
                require(metadata.get('files') == hashes and metadata.get('build') == target.name == build, 'runtime_manifest_mismatch')
            else:
                require(build == image['runtime_build'], 'image_runtime_mismatch')
        else:
            build = metadata.get('build') if managed else image['runtime_build']
        source = metadata.get('source_commit') if managed else image['source']
        require(re.fullmatch('[0-9a-f]{12}', build or '') and re.fullmatch('[0-9a-f]{40}', source or ''), 'invalid_candidate_identity')
        return {'build':build, 'source_commit':source, 'target':target, 'marker_digest':sha(self.marker),
                'metadata_digest':metadata_digest, 'fingerprints':fingerprints}

    def check(self):
        try:
            current = self.read()
        except (OSError, ValueError, TypeError, AttributeError, Refused) as error:
            raise Invalidated('candidate_unverifiable') from error
        if current != self.baseline:
            raise Invalidated('candidate_changed')

    def public(self):
        return {key:self.baseline[key] for key in ('build', 'source_commit')}

def in_group(group, expected):
    return group == expected or group.startswith(expected + '/')

def group_of(directory):
    groups = [row.split(':',2)[2] for row in (directory / 'cgroup').read_text().splitlines() if row.startswith('0::')]
    require(len(groups) == 1 and groups[0].startswith('/'), 'unreadable_unified_cgroup')
    return groups[0]

def process_status(directory):
    fields = (directory / 'stat').read_text().rpartition(')')[2].split()
    require(len(fields) >= 20 and fields[0] in {'R','S','D','Z','T','t','X','I','P'}, 'invalid_process_status')
    return fields[0], int(fields[19])

def discover(proc, expected, uid):
    members, unknown = set(), []
    for directory in proc.glob('[0-9]*'):
        pid = int(directory.name)
        try:
            if directory.stat().st_uid != uid:
                continue
            if in_group(group_of(directory), expected):
                members.add(pid)
        except (OSError, ValueError, Refused):
            # Membership unreadable for a same-user process cannot be silently
            # assumed foreign. A vanished unrelated process is also explicit.
            unknown.append(pid)
    return members, sorted(unknown)

def collect_processes(proc, group, main_pid, uid):
    require(group.startswith('/') and group != '/' and '..' not in group.split('/'), 'invalid_unit_cgroup')
    members, unknown = discover(Path(proc), group, uid)
    rows, unreadable = [], []
    for pid in sorted(members):
        directory = Path(proc) / str(pid)
        try:
            state, began = process_status(directory)
            pss = 0
            if state != 'Z':
                values = [line.split() for line in (directory / 'smaps_rollup').read_text().splitlines() if line.startswith('Pss:')]
                require(len(values) == 1 and len(values[0]) == 3 and values[0][2] == 'kB', 'invalid_pss')
                pss = int(values[0][1])
                require(pss >= 0, 'invalid_pss')
            after_state, after_began = process_status(directory)
            # Scheduling transitions such as sleeping→running do not change PID
            # identity. PID reuse, zombie transitions and ownership changes do.
            require(after_began == began and (after_state == 'Z') == (state == 'Z')
                    and in_group(group_of(directory), group), 'process_changed_during_sample')
            rows.append({'pid':pid, 'state':state, 'pss_kib':pss, 'start_ticks':began})
        except (OSError, ValueError, Refused):
            unreadable.append(pid)
    after, after_unknown = discover(Path(proc), group, uid)
    membership_changed = after != members
    complete = not (unknown or after_unknown or unreadable or membership_changed) and main_pid in members and main_pid in {row['pid'] for row in rows}
    total = sum(row['pss_kib'] for row in rows)
    return {'processes':rows, 'unreadable_pids':unreadable, 'membership_unreadable_pids':sorted(set(unknown+after_unknown)),
            'membership_changed':membership_changed, 'memory_observation_complete':complete,
            'pss_kib_observed':total, 'pss_kib_total':total if complete else None,
            'zombies':sum(row['state']=='Z' for row in rows)}

def project_api(state):
    require(isinstance(state, dict) and type(state.get('appliance')) is bool and type(state.get('serviceMode')) is bool, 'invalid_api_state')
    services = {}
    for name in ('network','bluetooth','audio'):
        value = state.get(name)
        require(isinstance(value, dict) and type(value.get('available')) is bool, 'invalid_api_availability')
        services[name] = value['available']
    return {'api_ok':state['appliance'], 'service_mode':state['serviceMode'], 'availability':services}

def read_api():
    with urllib.request.urlopen('http://127.0.0.1:8765/api/state', timeout=5) as response:
        data = response.read(4_000_001)
    require(len(data) <= 4_000_000, 'api_response_too_large')
    return project_api(json.loads(data))

def read_unit(unit):
    result = subprocess.run(['systemctl','--user','show',unit,'-p','MainPID','-p','ActiveState','-p','ControlGroup','-p','InvocationID'], capture_output=True, text=True, check=True, timeout=5)
    value = dict(row.split('=',1) for row in result.stdout.splitlines() if '=' in row)
    pid = int(value['MainPID'])
    group = value['ControlGroup']
    require(group.startswith('/') and group.endswith('/' + unit) and '..' not in group.split('/'), 'unit_cgroup_mismatch')
    require(re.fullmatch('[0-9a-f]{32}', value.get('InvocationID','')), 'invalid_unit_invocation')
    return {'main_pid':pid, 'active':value['ActiveState']=='active', 'group':group, 'invocation':value['InvocationID']}

def supervisor_matches(arguments, target):
    if len(arguments) < 2 or not arguments[1]:
        return False
    script = Path(os.fsdecode(arguments[1]))
    if not script.is_absolute():
        script = target / script
    try:
        return script.resolve(strict=True) == (target / 'scripts/run-hub.py').resolve(strict=True)
    except (OSError, ValueError):
        return False

def create_output(path):
    path = Path(path).absolute()
    require(path.parent.is_dir(), 'output_parent_missing')
    require(not path.exists() and not path.is_symlink(), 'output_must_be_new')
    for parent in path.parents:
        require(not parent.is_symlink(), 'output_ancestor_symlink')
    path.mkdir(mode=0o700 if os.name == 'posix' else 0o777)
    if os.name == 'posix':
        path.chmod(0o700)
    return path

def write_json(folder, value):
    temporary = folder / 'status.next.json'
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600 if os.name == 'posix' else 0o666)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, folder / 'status.json')

class Observer:
    def __init__(self, candidate, folder, *, duration=8*3600, interval=30, unit_getter=None,
                 api_getter=read_api, collector=None, clock=time.monotonic, sleep=time.sleep):
        require(math.isfinite(duration) and duration > 0 and math.isfinite(interval) and interval > 0 and interval <= duration, 'invalid_observation_timing')
        self.candidate, self.folder = candidate, Path(folder)
        self.duration, self.interval = duration, interval
        self.unit_getter = unit_getter or (lambda:read_unit('pysh.service'))
        self.api_getter, self.collector = api_getter, collector or (lambda group,pid:collect_processes(Path('/proc'),group,pid,os.getuid()))
        self.clock, self.sleep = clock, sleep

    def run(self):
        start = self.clock()
        due = start
        report = {**self.candidate.public(), 'running':True, 'target_s':self.duration, 'interval_s':self.interval,
                  'samples':0, 'observation_errors':0, 'api_errors':0, 'incomplete_memory_samples':0,
                  'unit_identity_changes':0, 'inactive_unit_samples':0, 'api_not_ready_samples':0, 'max_gap_s':0, 'candidate_changed':False,
                  'telemetry_complete':False, 'interrupted':False, 'acceptance':ACCEPTANCE}
        previous_time, previous_unit = None, None
        first, last, peak = None, None, None
        fd = os.open(self.folder / 'samples.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600 if os.name == 'posix' else 0o666)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as log:
                while True:
                    now = self.clock()
                    if now < due:
                        self.sleep(due-now)
                    began = self.clock()
                    try:
                        self.candidate.check()
                    except Invalidated:
                        report['candidate_changed'] = True
                        break
                    sample = {'elapsed_s':round(began-start,3), 'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
                    if previous_time is not None:
                        report['max_gap_s'] = max(report['max_gap_s'], began-previous_time)
                    previous_time = began
                    try:
                        info = self.unit_getter()
                        sample.update(unit_active=info['active'], main_pid=info['main_pid'], invocation=info['invocation'])
                        if not info['active']:
                            report['inactive_unit_samples'] += 1
                        identity = (info['main_pid'], info['invocation'])
                        if previous_unit is not None and identity != previous_unit:
                            report['unit_identity_changes'] += 1
                        previous_unit = identity
                        sample.update(self.collector(info['group'], info['main_pid']))
                        if not sample['memory_observation_complete']:
                            report['incomplete_memory_samples'] += 1
                        if sample['pss_kib_total'] is not None:
                            last = sample['pss_kib_total']
                            first = last if first is None else first
                            peak = last if peak is None else max(peak,last)
                    except Invalidated:
                        report['candidate_changed'] = True
                        break
                    except (OSError, ValueError, KeyError, Refused, subprocess.SubprocessError) as error:
                        report['observation_errors'] += 1
                        sample.update(observation_error=type(error).__name__, memory_observation_complete=False)
                        report['incomplete_memory_samples'] += 1
                    try:
                        sample.update(self.api_getter())
                        if not sample['api_ok']:
                            report['api_not_ready_samples'] += 1
                    except (OSError, ValueError, Refused) as error:
                        report['api_errors'] += 1
                        sample.update(api_ok=False, api_error=type(error).__name__)
                    # A candidate swap during slow /proc or API reads invalidates even
                    # this sample; no telemetry may join two release identities.
                    try:
                        self.candidate.check()
                    except Invalidated:
                        report['candidate_changed'] = True
                        break
                    log.write(json.dumps(sample)+'\n')
                    log.flush()
                    os.fsync(log.fileno())
                    report['samples'] += 1
                    report['elapsed_s'] = round(self.clock()-start,3)
                    write_json(self.folder, report)
                    if began-start >= self.duration:
                        break
                    due = min(start + (math.floor((self.clock()-start)/self.interval)+1)*self.interval, start+self.duration)
        except BaseException:
            report['interrupted'] = True
            raise
        finally:
            elapsed = self.clock()-start
            report.update(running=False, elapsed_s=round(elapsed,3), first_pss_kib=first, last_pss_kib=last, peak_pss_kib=peak,
                          duration_reached=elapsed >= self.duration,
                          sampling_gaps_within_limit=report['max_gap_s'] <= self.interval*1.5+1)
            report['telemetry_complete'] = (report['duration_reached'] and not report['candidate_changed']
                and report['sampling_gaps_within_limit'] and not report['interrupted'] and not report['observation_errors']
                and not report['api_errors'] and not report['api_not_ready_samples']
                and not report['inactive_unit_samples'] and not report['incomplete_memory_samples'])
            write_json(self.folder, report)
        return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New private directory; its parent must already exist')
    parser.add_argument('--duration', type=float, default=8*3600, help='Monotonic observation seconds (default 8 hours)')
    parser.add_argument('--interval', type=float, default=30, help='Sample interval seconds (default 30)')
    args = parser.parse_args()
    import pwd
    require(os.geteuid() != 0 and pwd.getpwuid(os.geteuid()).pw_name == 'pysh', 'run_as_nonroot_pysh')
    candidate = Candidate()
    unit = read_unit('pysh.service')
    require(unit['active'] and unit['main_pid'] > 1, 'app_unit_not_active')
    require((Path('/proc') / str(unit['main_pid']) / 'cwd').resolve() == candidate.baseline['target'], 'unit_runtime_mismatch')
    values = (Path('/proc') / str(unit['main_pid']) / 'cmdline').read_bytes().split(b'\0')
    require(supervisor_matches(values, candidate.baseline['target']), 'unit_supervisor_mismatch')
    def checked_unit():
        current = read_unit('pysh.service')
        if current['active'] and current['main_pid'] > 1:
            process = Path('/proc') / str(current['main_pid'])
            if process.joinpath('cwd').resolve() != candidate.baseline['target']:
                raise Invalidated('unit_runtime_changed')
            arguments = process.joinpath('cmdline').read_bytes().split(b'\0')
            if not supervisor_matches(arguments, candidate.baseline['target']):
                raise Invalidated('unit_supervisor_changed')
        return current
    folder = create_output(args.output)
    report = Observer(candidate, folder, duration=args.duration, interval=args.interval, unit_getter=checked_unit).run()
    print(json.dumps(report))
    return 0 if report['telemetry_complete'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
