import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import pytest

spec=importlib.util.spec_from_file_location('remote_update',Path(__file__).parents[1]/'scripts/update-remote-sidecar.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def pack(tmp_path,names):
    archive=tmp_path/'gateway.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name in names:
            entry=tarfile.TarInfo(name);data=b'# source';entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
    return archive,hashlib.sha256(archive.read_bytes()).hexdigest()

def test_exact_source_archive_and_checksum(tmp_path):
    archive,sha=pack(tmp_path,module.FILES)
    assert set(module.archive_files(archive,sha))==module.FILES
    with pytest.raises(RuntimeError,match='checksum'):module.archive_files(archive,'0'*64)

@pytest.mark.parametrize('foreign',['../gateway.py','remote/config.json','services/remote/private-key.pem'])
def test_foreign_source_and_pairing_material_refused(tmp_path,foreign):
    archive,sha=pack(tmp_path,module.FILES|{foreign})
    with pytest.raises(RuntimeError,match='member'):module.archive_files(archive,sha)


@pytest.fixture
def units(tmp_path):
    candidate=(Path(__file__).parents[1]/'services/remote/pysh-remote.service').read_text()
    previous=candidate.replace(' AF_NETLINK','')
    installed=tmp_path/'pysh-remote.service'
    installed.write_text(previous.replace('WorkingDirectory=/opt/pysh/current','WorkingDirectory=/opt/pysh-remote/current'))
    return installed,previous,candidate


def test_only_exact_netlink_migration_and_verified_existing_unit_are_accepted(units):
    installed,previous,candidate=units
    planned=module.unit_plan(installed,previous,candidate)
    assert planned.decode().split('RestrictAddressFamilies=')[1].splitlines()[0]=='AF_INET AF_INET6 AF_UNIX AF_NETLINK'
    assert module.unit_plan(installed,previous,previous) is None
    for foreign in (candidate.replace('AF_NETLINK','AF_NETLINK AF_PACKET'),
                    candidate.replace('NoNewPrivileges=yes','NoNewPrivileges=no'),
                    candidate.replace('-m services.remote serve','-m services.remote serve --host 0.0.0.0')):
        with pytest.raises(RuntimeError,match='separate review'):
            module.unit_plan(installed,previous,foreign)
    installed.write_text(installed.read_text()+'Environment=UNREVIEWED=1\n')
    with pytest.raises(RuntimeError,match='differs'):
        module.unit_plan(installed,previous,candidate)


def test_successful_unit_migration_reloads_before_start_and_preserves_credentials(tmp_path,units):
    installed,previous,candidate=units
    credentials=tmp_path/'devices.json';credentials.write_text('{"fixture":"preserved"}')
    preserved=credentials.read_bytes()
    events=[]
    pointer={'current':'old'}
    def link(target,name):pointer[name]=target;events.append(('link',target))
    def restart():events.append(('restart',pointer['current'],installed.read_text()))
    module.activate('new','old',installed,module.unit_plan(installed,previous,candidate),link,restart,
                    lambda:events.append(('reload',installed.read_text())),lambda started:events.append(('healthy',)))
    assert pointer['current']=='new'
    assert events[0][0]=='reload' and 'AF_NETLINK' in events[0][1]
    assert events[1]==('link','new') and events[2][0]=='restart' and events[-1]==('healthy',)
    assert credentials.read_bytes()==preserved
    assert not list(tmp_path.glob('*.update-*'))


@pytest.mark.parametrize('stage',['reload','restart','health'])
def test_migration_failure_restores_exact_unit_and_previous_code_before_restart(tmp_path,units,stage):
    installed,previous,candidate=units
    saved=installed.read_bytes()
    credentials=tmp_path/'devices.json';credentials.write_text('{"fixture":"preserved"}')
    events=[];pointer={'current':'old'};failed=False
    def action(name):
        nonlocal failed
        events.append((name,pointer['current'],installed.read_bytes()))
        if name==stage and not failed:
            failed=True
            raise RuntimeError('fixture failure')
    def link(target,name):pointer[name]=target
    with pytest.raises(RuntimeError,match='fixture failure'):
        module.activate('new','old',installed,module.unit_plan(installed,previous,candidate),link,
                        lambda:action('restart'),lambda:action('reload'),lambda started:action('health'))
    assert pointer['current']=='old' and installed.read_bytes()==saved
    assert events[-1]==('restart','old',saved)
    assert credentials.read_text()=='{"fixture":"preserved"}'
    assert not list(tmp_path.glob('*.update-*'))


def test_unchanged_unit_update_does_not_rewrite_or_reload(units):
    installed,previous,candidate=units
    saved=installed.read_bytes()
    events=[]
    module.activate('new','old',installed,None,lambda *args:events.append('link'),
                    lambda:events.append('restart'),lambda:events.append('reload'),lambda started:None)
    assert events==['link','restart'] and installed.read_bytes()==saved
