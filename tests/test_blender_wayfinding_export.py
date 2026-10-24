"""Check shipped atlas provenance and reject unsafe/mismatched authoring input.
Runs without Blender or a GPU; device acceptance remains separate.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'wayfinding_export', ROOT / 'scripts/blender/export_city_wayfinding_data.py'
)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


@pytest.fixture
def contract():
    return json.loads((ROOT / 'assets/blender/city-wayfinding/contract.json').read_text())


def test_shipped_atlases_match_the_verified_contract(contract):
    data = exporter.validate(contract)
    checked = exporter.check_assets(contract, ROOT / 'app/ui/public/ambient')
    assert len(data['signs']) == 5
    assert checked['atlas_files'] == 14
    assert checked['verified_atlas_bytes'] > 0
    assert contract['gates']['full_mesh_audit'] == 'PASS'


def test_repository_sources_match_recorded_render_source_after_lf_normalization(contract):
    provenance = json.loads((ROOT / 'assets/blender/city-wayfinding/authoring-provenance.json').read_text())
    canonical_contract = (ROOT / 'assets/blender/city-wayfinding/contract.json').read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha256(canonical_contract).hexdigest() == provenance['repository_lf_contract_sha256']
    for name, entry in provenance['sources'].items():
        actual = (ROOT / name).read_bytes().replace(b'\r\n', b'\n')
        assert hashlib.sha256(actual).hexdigest() == entry['repository_lf_sha256']
        key = 'renderer_sha256' if name.endswith('build_city_wayfinding.py') else 'candidate_sha256'
        assert entry['rendered_bytes_sha256'] == contract[key]


@pytest.mark.parametrize('gate', [
    'unicode', 'unstretched_native_cap_14_16', 'target48_nonoverlap',
    'all_intro_bob_object_beacon_clearance', 'viewport58_480',
    'original_inputs_unchanged', 'four_locale_palette_matrix', 'loop_pure_translation',
])
def test_failed_authoring_gate_cannot_generate_ui_data(contract, gate):
    contract['gates'][gate] = False
    with pytest.raises(ValueError):
        exporter.validate(contract)


def test_preview_cannot_be_promoted_as_an_animation(contract):
    contract['preview'] = True
    with pytest.raises(ValueError):
        exporter.validate(contract)


def test_mismatched_atlas_checksum_is_rejected(contract):
    contract['assets'][next(iter(contract['assets']))]['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='SHA256'):
        exporter.check_assets(contract, ROOT / 'app/ui/public/ambient')


def test_missing_atlas_is_rejected_before_output(contract, tmp_path):
    with pytest.raises(FileNotFoundError):
        exporter.check_assets(contract, tmp_path)


def test_atlas_reference_cannot_escape_the_asset_directory(contract):
    sign = contract['signs']['media']
    sign['languages'] = copy.deepcopy(sign['languages'])
    sign['languages']['en']['day'] = '../outside.png'
    with pytest.raises(ValueError):
        exporter.validate(contract)
