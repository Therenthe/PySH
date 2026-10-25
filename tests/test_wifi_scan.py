"""Native NetworkManager scan errors must not strand a just-selected AP."""
import asyncio
from types import SimpleNamespace

import pytest
from dbus_next.errors import DBusError

from services.backend.device import Device


def scan_fixture(monkeypatch, *, error, cached=True, state=30):
    device = Device()
    device._linux, device._bus = True, object()

    async def paths():
        return ["/ethernet", "/wifi"]

    async def request_scan(options):
        if error:
            raise DBusError(error, "private daemon detail")

    async def access_points():
        return ["/ap"] if cached else []

    async def active_access_point():
        return "/"

    async def proxy(service, path, interface):
        assert path == "/wifi"
        return SimpleNamespace(call_request_scan=request_scan, get_access_points=access_points,
                               get_active_access_point=active_access_point)

    async def props(service, path, interface):
        if path == "/ethernet":
            return {"DeviceType": 1}
        if path == "/wifi":
            return {"DeviceType": 2, "State": state}
        assert path == "/ap"
        return {"Ssid": list(b"Hub"), "RsnFlags": 1, "Strength": 70}

    async def sleep(seconds):
        pass

    monkeypatch.setattr(device, "_proxy", proxy)
    monkeypatch.setattr(device, "_props", props)
    monkeypatch.setattr(device, "_nm_device_paths", paths)
    monkeypatch.setattr("services.backend.device.asyncio.sleep", sleep)
    return device


def test_scan_rate_limit_uses_visible_access_points_without_changing_ethernet(monkeypatch):
    device = scan_fixture(monkeypatch, error="org.freedesktop.NetworkManager.Device.NotAllowed")
    result = asyncio.run(device.network_scan())
    assert result == {"available": True, "networks": [
        {"ssid": "Hub", "signal": 70, "security": "secured", "in_use": False}
    ], "error": None}


@pytest.mark.parametrize("error,cached,state", [
    ("org.freedesktop.NetworkManager.NotAuthorized", True, 30),
    ("org.freedesktop.NetworkManager.Device.NotAllowed", False, 30),
    ("org.freedesktop.NetworkManager.Device.NotAllowed", True, 20),
    ("org.freedesktop.DBus.Error.NoReply", True, 30),
])
def test_scan_does_not_hide_permission_hardware_or_empty_scan_errors(monkeypatch, error, cached, state):
    device = scan_fixture(monkeypatch, error=error, cached=cached, state=state)
    result = asyncio.run(device.network_scan())
    assert result["available"] is False
    assert result["error"] is not None
    assert result["networks"] == []
    assert "private" not in str(result)
