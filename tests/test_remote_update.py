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
