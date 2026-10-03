"""Network status must identify the real route even with active loopback."""
import asyncio
from types import SimpleNamespace

import pytest

from services.backend.device import Device, NM_PATH, NM_SETTINGS_PATH


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("primary", ["/active/wired", "/active/wifi", "/"])
def test_route_selection_ignores_loopback_and_tracks_profile_uuid(monkeypatch, reverse, primary):
    device = Device()
    device._linux, device._bus = True, object()
    active = {
        "/active/wired": {"Id": "same-name", "Uuid": "wired", "Type": "802-3-ethernet", "State": 2, "Default": True},
        "/active/wifi": {"Id": "wifi-route", "Uuid": "wifi", "Type": "802-11-wireless", "State": 2},
        "/active/loop": {"Id": "lo", "Uuid": "loop", "Type": "loopback", "State": 2},
    }
    profiles = {
        "/saved/wired": {"id": "same-name", "uuid": "wired", "type": "802-3-ethernet"},
        "/saved/unused": {"id": "same-name", "uuid": "unused", "type": "802-11-wireless"},
        "/saved/loop": {"id": "lo", "uuid": "loop", "type": "loopback"},
    }

    async def get_state(): return 70
    async def get_primary_connection(): return primary
    async def get_active_connections(): return list(active)[::(-1 if reverse else 1)]
    async def call_list_connections(): return list(profiles)
    async def call_get_devices(): return ["/device/loop", "/device/wired"]

    async def proxy(service, path, interface):
        if path == NM_PATH:
            return SimpleNamespace(get_state=get_state, get_primary_connection=get_primary_connection,
                                   get_active_connections=get_active_connections, call_get_devices=call_get_devices)
        if path == NM_SETTINGS_PATH:
            return SimpleNamespace(call_list_connections=call_list_connections)
        async def call_get_settings(): return {"connection": profiles[path]}
        return SimpleNamespace(call_get_settings=call_get_settings)

    async def props(service, path, interface):
        if path == "/device/loop": return {"DeviceType": 32, "Interface": "lo", "State": 100}
        if path == "/device/wired": return {"DeviceType": 1, "Interface": "eth0", "State": 100}
        return active[path]

    monkeypatch.setattr(device, "_proxy", proxy)
    monkeypatch.setattr(device, "_props", props)
    result = asyncio.run(device.network_status())
    assert result["error"] is None
    assert result["connection"] == ("wifi-route" if primary == "/active/wifi" else "same-name")
    assert [d["interface"] for d in result["devices"]] == ["eth0"]
    assert {p["id"]: p["active"] for p in result["saved"]} == {"wired": True, "unused": False}


def test_loopback_alone_is_not_a_network_connection(monkeypatch):
    device = Device()
    device._linux, device._bus = True, object()
    async def get_state(): return 20
    async def get_primary_connection(): return "/"
    async def get_active_connections(): return ["/active/loop"]
    async def call_list_connections(): return []
    async def call_get_devices(): return []
    async def proxy(service, path, interface):
        return SimpleNamespace(get_state=get_state, get_primary_connection=get_primary_connection,
                               get_active_connections=get_active_connections,
                               call_get_devices=call_get_devices, call_list_connections=call_list_connections)
    async def props(service, path, interface):
        return {"Type": "loopback", "State": 2, "Id": "lo"}
    monkeypatch.setattr(device, "_proxy", proxy)
    monkeypatch.setattr(device, "_props", props)
    result = asyncio.run(device.network_status())
    assert result["state"] == "disconnected"
    assert result["connection"] is None
    assert result["saved"] == []
