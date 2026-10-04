import json
import pytest
from pydantic import ValidationError
from services.backend.preferences import PreferenceStore


def test_legacy_preferences_get_safe_ambient_defaults(tmp_path):
    (tmp_path / 'preferences.json').write_text(json.dumps({'language': 'en', 'volume': 23}))
    store = PreferenceStore(tmp_path)
    assert not store.recovered
    assert store.value.decorativeAircraft is True
    assert store.value.decorativeLunarDust is False
    assert store.value.volume == 23


def test_ambient_choices_persist_and_recover_without_losing_other_preferences(tmp_path):
    store = PreferenceStore(tmp_path)
    store.update({'decorativeAircraft': False, 'decorativeLunarDust': True, 'language': 'en'})
    store.update({'volume': 31})
    restored = PreferenceStore(tmp_path)
    assert restored.value.decorativeAircraft is False
    assert restored.value.decorativeLunarDust is True
    assert restored.value.volume == 31
    restored.path.write_text('corrupt', encoding='utf-8')
    recovered = PreferenceStore(tmp_path)
    assert recovered.recovered
    assert recovered.value.decorativeAircraft is False
    assert recovered.value.decorativeLunarDust is True
    assert recovered.value.language == 'en'


@pytest.mark.parametrize('field', ['decorativeAircraft', 'decorativeLunarDust'])
@pytest.mark.parametrize('value', ['false', 'on', 1, 0, None, [], {}])
def test_ambient_settings_reject_non_boolean_values_without_writing(tmp_path, field, value):
    store = PreferenceStore(tmp_path)
    store.update({'volume': 19})
    before = store.path.read_bytes()
    memory = store.export()
    with pytest.raises(ValidationError):
        store.update({field: value})
    assert store.path.read_bytes() == before
    assert store.export() == memory
