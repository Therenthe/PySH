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
