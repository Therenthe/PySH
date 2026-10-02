from pathlib import Path
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
