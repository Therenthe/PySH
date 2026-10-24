from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from services.backend.presentation import presentation_context


def prefs(**values):
    return SimpleNamespace(**({"language": "ro", "theme": "ink", "nightEnabled": True,
                              "nightMode": "solar", "nightStart": "22:00", "nightEnd": "07:00",
                              "timezone": "Europe/Bucharest"} | values))


@pytest.mark.parametrize("hour,theme", [(3, "night"), (4, "ink"), (12, "ink"), (16, "night"), (20, "night"), (22, "ink")])
def test_solar_drawer_matches_hub_day_and_night(hour, theme):
    now = datetime(2026, 10, 23, hour, tzinfo=timezone.utc)
    weather = {"timezone": "Europe/Bucharest", "daily": [{"date": "2026-10-23",
               "sunrise_epoch": datetime(2026, 10, 23, 4, tzinfo=timezone.utc).timestamp(),
               "sunset_epoch": datetime(2026, 10, 23, 16, tzinfo=timezone.utc).timestamp()}]}
    assert presentation_context(prefs(), weather, now) == {"language": "ro", "theme": theme}


@pytest.mark.parametrize("day", [{}, {"date": "2026-10-22"}, {"date": "2026-10-23", "sunrise_epoch": True, "sunset_epoch": 2},
                                  {"date": "2026-10-23", "sunrise_epoch": float("nan"), "sunset_epoch": 2}])
def test_missing_invalid_or_old_solar_times_retain_manual_palette(day):
    now = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
    assert presentation_context(prefs(theme="night"), {"daily": [day]}, now)["theme"] == "night"


@pytest.mark.parametrize("hour,theme", [(3, "night"), (4, "ink"), (18, "ink"), (19, "night")])
def test_schedule_uses_selected_timezone_and_half_open_interval(hour, theme):
    now = datetime(2026, 10, 23, hour, tzinfo=timezone.utc)
    assert presentation_context(prefs(nightMode="schedule", theme="night"), None, now)["theme"] == theme


def test_disabled_automatic_theme_never_overrides_chosen_palette():
    assert presentation_context(prefs(theme="night", nightEnabled=False), None)["theme"] == "night"
