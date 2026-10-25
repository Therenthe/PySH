import asyncio
from unittest.mock import AsyncMock

from services.backend.app import Hub


def test_location_change_cannot_receive_previous_warning_response(tmp_path):
    async def probe():
        hub = Hub(tmp_path)
        first = {"name": "București", "latitude": 44.4, "longitude": 26.1}
        second = {"name": "Cluj", "latitude": 46.7, "longitude": 23.6}
        hub.store.update({"location": first})
        gate = asyncio.Event()

        async def response(location):
            if location["name"] == first["name"]:
                await gate.wait()
            return {"state": "available", "alerts": [], "location": location["name"]}

        hub.alert_provider.snapshot = response
        old = asyncio.create_task(hub.refresh_alerts())
        await asyncio.sleep(0)
        hub.store.update({"location": second})
        await hub.refresh_alerts()
        gate.set()
        await old
        assert hub.alerts["location"] == second["name"]

    asyncio.run(probe())


def test_failed_warning_provider_never_becomes_no_warnings(tmp_path):
    hub = Hub(tmp_path)
    hub.alert_provider.snapshot = AsyncMock(side_effect=OSError("fixture"))
    value = asyncio.run(hub.refresh_alerts())
    assert value["state"] == "unavailable"
    assert value["alerts"] == []
    assert value["error"] == "weather_alerts_unavailable"


def test_warning_refresh_is_separate_from_current_weather(tmp_path):
    hub = Hub(tmp_path)
    hub.weather = {"current": {"temperature_c": 14}, "stale": False}
    hub.alert_provider.snapshot = AsyncMock(return_value={"state": "stale", "alerts": []})
    asyncio.run(hub.refresh_alerts())
    assert hub.weather == {"current": {"temperature_c": 14}, "stale": False}
    assert hub.alerts["state"] == "stale"
