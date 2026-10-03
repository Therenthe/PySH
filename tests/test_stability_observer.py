"""Observer evidence, privacy and failure cases against owned fake proc/runtime files."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('stability_observer', Path(__file__).parents[1] / 'scripts/observe-stability.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)

UID = getattr(os, 'getuid', lambda:0)()
GROUP = '/user.slice/user-1000.slice/user@1000.service/app.slice/pysh.service'

def process(proc, pid, group=GROUP, state='S', pss=128, start=10):
    folder = proc / str(pid)
    folder.mkdir(parents=True)
    (folder / 'cgroup').write_text('0::' + group + '\n')
    fields = [state,'1'] + ['0']*17 + [str(start)]
    (folder / 'stat').write_text(f'{pid} (chromium child with spaces) ' + ' '.join(fields) + '\n')
    if state != 'Z':
        (folder / 'smaps_rollup').write_text(f'Rss: 2048 kB\nPss: {pss} kB\nPrivate_Dirty: 2 kB\n')
    return folder

def test_complete_app_cgroup_includes_detached_and_nested_but_not_prefix_or_sibling(tmp_path):
    proc = tmp_path / 'proc'
    process(proc, 100, pss=100)
    process(proc, 101, pss=200)  # PPid deliberately 1: detached Chromium still counted.
    process(proc, 102, GROUP + '/renderer', pss=300)
    process(proc, 103, GROUP + '-other', pss=9000)
    process(proc, 104, GROUP.rsplit('/',1)[0] + '/foreign.service', pss=9000)
    sample = observer.collect_processes(proc, GROUP, 100, UID)
    assert {row['pid'] for row in sample['processes']} == {100,101,102}
    assert sample['memory_observation_complete'] and sample['pss_kib_total'] == 600
    assert sample['unreadable_pids'] == []

def test_member_missing_pss_and_unknown_membership_are_explicit_not_complete(tmp_path):
    proc = tmp_path / 'proc'
    process(proc, 100)
    missing = process(proc, 101)
    (missing / 'smaps_rollup').unlink()
    unknown = process(proc, 102)
    (unknown / 'cgroup').unlink()
    sample = observer.collect_processes(proc, GROUP, 100, UID)
    assert not sample['memory_observation_complete'] and sample['pss_kib_total'] is None
    assert sample['pss_kib_observed'] == 128 and sample['unreadable_pids'] == [101]
    assert sample['membership_unreadable_pids'] == [102]

def test_zombie_is_recorded_without_fabricated_memory_and_missing_main_invalidates(tmp_path):
    proc = tmp_path / 'proc'
    process(proc, 100)
    process(proc, 101, state='Z')
    sample = observer.collect_processes(proc, GROUP, 100, UID)
    assert sample['zombies'] == 1 and sample['memory_observation_complete']
    assert next(row for row in sample['processes'] if row['pid']==101)['pss_kib'] == 0
    assert not observer.collect_processes(proc, GROUP, 999, UID)['memory_observation_complete']
    with pytest.raises(observer.Refused):
        observer.collect_processes(proc, '/', 100, UID)

def sensitive_state():
    return {'appliance':True,'serviceMode':False,
            'network':{'available':True,'connection':'PRIVATE-SSID','devices':[{'ip':'192.0.2.99'}]},
            'bluetooth':{'available':True,'devices':[{'name':'PRIVATE-SPEAKER','address':'PRIVATE-MAC'}]},
            'audio':{'available':True,'volume':53,'outputs':[{'name':'PRIVATE-OUTPUT'}]},
            'preferences':{'language':'ro','location':{'name':'PRIVATE-CITY'},'secret':'PRIVATE-PASSWORD'},
            'player':{'url':'https://private.example/song?token=PRIVATE-TOKEN','title':'PRIVATE-TITLE'},
            'username':'PRIVATE-USER','token':'PRIVATE-SESSION'}

def test_api_projection_cannot_emit_preferences_network_identifiers_or_media_secrets():
    value = observer.project_api(sensitive_state())
    assert value == {'api_ok':True,'service_mode':False,'availability':{'network':True,'bluetooth':True,'audio':True}}
    assert 'PRIVATE' not in json.dumps(value)
    bad = sensitive_state();bad['audio']['available'] = 'yes'
    with pytest.raises(observer.Refused):observer.project_api(bad)

@pytest.fixture
def candidate(tmp_path):
    root = tmp_path / 'opt/pysh'
    release = root / 'current'
    content = {'requirements.lock':b'locked','scripts/run-hub.py':b'python supervisor','dist/index.html':b'home'}
    files = {}
    for name, value in content.items():
        path = release / name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
        files[name] = hashlib.sha256(value).hexdigest()
    marker = tmp_path / 'etc/pysh-build.json';marker.parent.mkdir()
    marker.write_text(json.dumps({'runtime_build':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()[:12],'source':'a'*40}))
    return root, marker, release, files

def test_initial_manifest_hashes_and_runtime_change_invalidate(candidate):
    root, marker, release, _ = candidate
    value = observer.Candidate(root,marker);value.check()
    assert set(value.public()) == {'build','source_commit'}
    (release / 'dist/index.html').write_bytes(b'changed content')
    with pytest.raises(observer.Invalidated):value.check()
    with pytest.raises(observer.Refused):observer.Candidate(root,marker)

def test_managed_source_metadata_and_current_pointer_are_pinned(candidate):
    root, marker, release, files = candidate
    build = hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()[:12]
    managed = root / 'releases' / build;managed.parent.mkdir();release.rename(managed)
    try:
        release.symlink_to(managed, target_is_directory=True)
    except OSError:
        pytest.skip('Creating a real managed release symlink requires Windows symlink privilege; Linux CI exercises this guard')
    metadata = root / 'runtime-source.json'
    metadata.write_text(json.dumps({'build':build,'source_commit':'b'*40,'files':files}))
    value = observer.Candidate(root,marker);value.check()
    metadata.write_text(json.dumps({'build':build,'source_commit':'c'*40,'files':files}))
    with pytest.raises(observer.Invalidated):value.check()

class Clock:
    def __init__(self):self.now = 0
    def __call__(self):return self.now
    def sleep(self,seconds):self.now += seconds

class Identity:
    def __init__(self):self.changed = False
    def check(self):
        if self.changed:raise observer.Invalidated('candidate_changed')
    def public(self):return {'build':'0'*12,'source_commit':'1'*40}

def observe(tmp_path, **kwargs):
    folder = observer.create_output(tmp_path / 'observation')
    clock, identity = Clock(), Identity()
    unit = lambda:{'main_pid':100,'active':True,'group':GROUP,'invocation':'2'*32}
    memory = lambda group,pid:{'processes':[],'memory_observation_complete':True,'pss_kib_total':128}
    run = observer.Observer(identity,folder,duration=20,interval=10,clock=clock,sleep=clock.sleep,
                            unit_getter=kwargs.get('unit_getter',unit),api_getter=kwargs.get('api_getter',lambda:observer.project_api(sensitive_state())),
                            collector=kwargs.get('collector',memory))
    return run, folder, clock, identity

def test_elapsed_schedule_reaches_target_and_never_awards_product_acceptance(tmp_path):
    run, folder, _, _ = observe(tmp_path)
    report = run.run()
    samples = [json.loads(row) for row in (folder/'samples.jsonl').read_text().splitlines()]
    assert [row['elapsed_s'] for row in samples] == [0,10,20]
    assert report['duration_reached'] and report['telemetry_complete'] and report['elapsed_s']==20
    assert report['max_gap_s']==10 and report['acceptance'].startswith('OPEN:')
    assert 'PRIVATE' not in (folder/'samples.jsonl').read_text()+(folder/'status.json').read_text()
    if os.name == 'posix':
        assert folder.stat().st_mode & 0o777 == 0o700
        assert (folder/'samples.jsonl').stat().st_mode & 0o777 == 0o600
        assert (folder/'status.json').stat().st_mode & 0o777 == 0o600

def test_candidate_swap_during_sample_aborts_without_mixed_candidate_rows(tmp_path):
    run, folder, _, identity = observe(tmp_path)
    def changed():identity.changed=True;return observer.project_api(sensitive_state())
    run.api_getter = changed
    report = run.run()
    assert report['candidate_changed'] and not report['telemetry_complete'] and report['samples']==0
    assert (folder/'samples.jsonl').read_text()==''

def test_long_observation_gap_and_api_failure_are_recorded(tmp_path):
    run, _, clock, _ = observe(tmp_path)
    def stalled(group,pid):
        clock.now += 19
        return {'memory_observation_complete':True,'pss_kib_total':128,'processes':[]}
    def failed():raise OSError('PRIVATE-SECRET in exception must never be serialized')
    run.collector, run.api_getter = stalled, failed
    report = run.run()
    assert report['duration_reached'] and not report['sampling_gaps_within_limit']
    assert not report['telemetry_complete'] and report['api_errors']==2
    assert 'PRIVATE' not in json.dumps(report)

def test_unit_pid_changes_and_incomplete_memory_remain_visible(tmp_path):
    run, _, _, _ = observe(tmp_path)
    count = [0]
    def restarted():
        count[0]+=1
        return {'main_pid':100+count[0],'active':True,'group':GROUP,'invocation':str(count[0])*32}
    run.unit_getter = restarted
    run.collector = lambda group,pid:{'memory_observation_complete':False,'pss_kib_total':None,'processes':[],'unreadable_pids':[pid]}
    report = run.run()
    assert report['unit_identity_changes']==2 and report['incomplete_memory_samples']==3
    assert not report['telemetry_complete'] and report['first_pss_kib'] is None

def test_output_requires_new_directory_and_timing_rejects_invalid_values(tmp_path):
    existing = tmp_path/'existing';existing.mkdir();(existing/'keep').write_text('preserved')
    with pytest.raises(observer.Refused):observer.create_output(existing)
    assert (existing/'keep').read_text()=='preserved'
    for duration,interval in [(0,1),(10,0),(10,11),(float('inf'),1),(10,float('nan'))]:
        with pytest.raises(observer.Refused):observer.Observer(Identity(),tmp_path,duration=duration,interval=interval)


def test_invalid_metadata_type_during_observation_invalidates(candidate):
    root, marker, _, _ = candidate
    value = observer.Candidate(root,marker)
    marker.write_text('[]')
    with pytest.raises(observer.Invalidated):value.check()


def test_inactive_unit_or_non_appliance_api_prevents_complete_telemetry(tmp_path):
    run, _, _, _ = observe(tmp_path)
    run.unit_getter = lambda:{'main_pid':100,'active':False,'group':GROUP,'invocation':'2'*32}
    state = sensitive_state();state['appliance'] = False
    run.api_getter = lambda:observer.project_api(state)
    report = run.run()
    assert report['inactive_unit_samples']==3 and report['api_not_ready_samples']==3
    assert not report['telemetry_complete']


def test_interruption_even_at_duration_does_not_mark_complete(tmp_path):
    run, _, clock, _ = observe(tmp_path)
    def interrupted():
        clock.now = 20
        raise KeyboardInterrupt()
    run.api_getter = interrupted
    with pytest.raises(KeyboardInterrupt):run.run()
    report = json.loads((run.folder/'status.json').read_text())
    assert report['duration_reached'] and report['interrupted']
    assert not report['telemetry_complete']


def test_changed_unit_runtime_invalidates_before_any_sample(tmp_path):
    run, folder, _, _ = observe(tmp_path)
    def foreign_unit():raise observer.Invalidated('unit_runtime_changed')
    run.unit_getter = foreign_unit
    report = run.run()
    assert report['candidate_changed'] and not report['telemetry_complete']
    assert report['samples']==0 and (folder/'samples.jsonl').read_text()==''

def test_supervisor_resolves_current_alias_and_rejects_matching_extra_argument(candidate):
    root, _, target, _ = candidate
    script = target / 'scripts/run-hub.py'
    assert observer.supervisor_matches([b'python', os.fsencode(script)], target)
    assert observer.supervisor_matches([b'python', b'scripts/run-hub.py'], target)
    assert not observer.supervisor_matches([b'python', b'foreign.py', os.fsencode(script)], target)
    alias = root / 'runtime-alias'
    try:
        alias.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip('Real alias resolution is exercised by Linux CI')
    assert observer.supervisor_matches([b'python', os.fsencode(alias / 'scripts/run-hub.py')], target)
