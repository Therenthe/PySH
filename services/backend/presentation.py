"""The external drawer follows the hub's chosen or solar/scheduled palette."""
from datetime import datetime, timezone
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def presentation_context(preferences, weather, now=None):
    now = now or datetime.now(timezone.utc)
    theme = preferences.theme
    if preferences.nightEnabled:
        if preferences.nightMode == "solar":
            try:
                zone = ZoneInfo((weather or {}).get("timezone") or preferences.timezone)
            except (ZoneInfoNotFoundError, ValueError, TypeError):
                zone = ZoneInfo(preferences.timezone)
            date = now.astimezone(zone).date().isoformat()
            day = next((day for day in (weather or {}).get("daily", []) if day.get("date") == date), {})
            sunrise, sunset = day.get("sunrise_epoch"), day.get("sunset_epoch")
            if all(type(value) in (int, float) and math.isfinite(value) for value in (sunrise, sunset)) and sunrise < sunset:
                theme = "night" if now.timestamp() < sunrise or now.timestamp() >= sunset else "ink"
        else:
            local = now.astimezone(ZoneInfo(preferences.timezone)).strftime("%H:%M")
            start, end = preferences.nightStart, preferences.nightEnd
            active = start <= local < end if start <= end else local >= start or local < end
            theme = "night" if active else "ink"
    return {"language": preferences.language, "theme": theme}
