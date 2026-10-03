from pathlib import Path
import json
import pytest
from pydantic import ValidationError
from services.backend.preferences import PreferenceStore


def test_persistence_and_recovery(tmp_path: Path):
    store = PreferenceStore(tmp_path)
    store.update({"language": "en", "theme": "night"})
    store.update({"volume": 65})
    assert PreferenceStore(tmp_path).value.volume == 65
    store.path.write_text("truncated", encoding="utf-8")
    recovered = PreferenceStore(tmp_path)
    assert recovered.recovered
    assert recovered.value.language == "en"
    assert recovered.value.theme == "night"


@pytest.mark.parametrize("patch", [{"volume":101},{"language":"fr"},{"timezone":"../../etc/passwd"},{"nightStart":"25:00"},{"password":"secret"}])
def test_invalid_patch_never_changes_disk(tmp_path, patch):
    store = PreferenceStore(tmp_path)
    store.update({"language":"en"})
    before = store.path.read_bytes()
    with pytest.raises(ValidationError):
        store.update(patch)
    assert store.path.read_bytes() == before


def test_legacy_night_schedule_preserved_and_new_saver_choices_persist(tmp_path):
    (tmp_path / 'preferences.json').write_text(json.dumps({'nightEnabled': True, 'nightStart':'21:00'}))
    store = PreferenceStore(tmp_path)
    assert store.value.nightMode == 'schedule'
    store.update({'nightMode':'solar','screensaverLayout':'visualizer','visualizerStyle':'orbit'})
    restored = PreferenceStore(tmp_path).value
    assert (restored.nightMode, restored.screensaverLayout, restored.visualizerStyle) == ('solar','visualizer','orbit')

def test_home_customization_survives_restart(tmp_path):
    store = PreferenceStore(tmp_path)
    assert store.value.homeCards == ['weather', 'forecast', 'playback']
    assert store.value.visualizerSize == 'compact'
    store.update({'homeCards': ['weather'], 'visualizerSize': 'large', 'visualizerStyle': 'rings',
                  'homePositions': {'weather': {'x': .2, 'y': .4, 'z': 4}, 'visualizer': {'x': 0, 'y': 1}}})
    restored = PreferenceStore(tmp_path).value
    assert restored.homeCards == ['weather']
    assert restored.visualizerSize == 'large'
    assert restored.homePositions['weather'].x == .2
    assert restored.homePositions['weather'].z == 4
    assert restored.homePositions['visualizer'].y == 1


@pytest.mark.parametrize('patch', [
    {'homePositions': {'weather': {'x': -1, 'y': 0}}},
    {'homePositions': {'forecast': {'x': .5, 'y': 1.01}}},
    {'homePositions': {'visualizer': {'x': float('nan'), 'y': 0}}},
    {'homePositions': {'unknown': {'x': 0, 'y': 0}}},
    {'homePositions': {'weather': {'x': 0, 'y': 0, 'z': 0}}},
    {'homePositions': {'weather': {'x': 0, 'y': 0, 'z': 5}}},
    {'homeCards': ['unknown']}, {'visualizerSize': 'huge'}, {'visualizerStyle': 'invalid'}])
def test_invalid_home_customization_preserves_saved_preferences(tmp_path, patch):
    store = PreferenceStore(tmp_path)
    store.update({'homeCards': []})
    before = store.path.read_bytes()
    with pytest.raises(ValidationError):
        store.update(patch)
    assert store.path.read_bytes() == before
