"""Saved-profile transactions, using D-Bus fakes rather than active networking."""
import asyncio
from copy import deepcopy

import pytest
from dbus_next import Variant

from services.backend.device import Device, DeviceError, NM_PATH, NM_SETTINGS_PATH


PROFILE = "12345678-1234-1234-1234-123456789abc"


def fixture(monkeypatch, failure=None, *, ssid=b"Hub", kind="802-11-wireless", duplicate=False, key_mgmt="wpa-psk", psk_flags=0):
    device = Device()
    device._linux = True
    device._bus = object()
    events = []
    original = {
        "connection": {"uuid": Variant("s", PROFILE), "id": Variant("s", "Friendly name"),
                       "type": Variant("s", kind), "autoconnect": Variant("b", False)},
        "802-11-wireless": {"ssid": Variant("ay", ssid)},
        "802-11-wireless-security": {"key-mgmt": Variant("s", key_mgmt), "psk-flags": Variant("u", psk_flags)},
        "ipv4": {"method": Variant("s", "manual"), "address-data": Variant("aa{sv}", [])},
        "ipv6": {"method": Variant("s", "disabled")},
    }

    class Connection:
        def __init__(self):
            self.memory = deepcopy(original)
            self.disk = deepcopy(original)
            self.disk["802-11-wireless-security"]["psk"] = Variant("s", "old-private-credential")
            self.updates = []

        async def call_get_settings(self):
            events.append("settings")
            return deepcopy(original)

        async def call_get_secrets(self, name):
            events.append("secrets")
            if failure == "snapshot":
                raise RuntimeError("private credential daemon detail")
            if failure == "missing-secret":
                return {}
            return {name: {"psk": Variant("s", "old-private-credential")}}

        async def call_update2(self, settings, flags, args):
            assert flags == 2 and args == {}
            assert settings["connection"]["autoconnect"].value is False
            assert settings["ipv4"] == original["ipv4"]
            assert settings["ipv6"] == original["ipv6"]
            value = settings["802-11-wireless-security"]["psk"].value
            events.append("restore" if value == "old-private-credential" else "update")
            self.updates.append(deepcopy(settings))
            self.memory = deepcopy(settings)
            if failure == "update" and value != "old-private-credential":
                raise RuntimeError("new-private-credential")
            if failure == "restore" and value == "old-private-credential":
                raise RuntimeError("old-private-credential")

        async def call_save(self):
            events.append("save")
            self.disk = deepcopy(self.memory)
            if failure == "restore-save" or (failure == "persist" and self.memory["802-11-wireless-security"]["psk"].value != "old-private-credential"):
                raise RuntimeError("new-private-credential")

        async def call_delete(self):
            raise AssertionError("Original saved profile must never be deleted")

    connection = Connection()

    class Settings:
        async def call_list_connections(self):
            return ["/saved/1", "/saved/2"] if duplicate else ["/saved/1"]

    class NetworkManager:
        async def call_checkpoint_create(self, paths, timeout, flags):
            assert paths == ["/wifi"] and timeout == 120 and flags == 0
            events.append("checkpoint")
            if failure == "checkpoint":
                raise RuntimeError("private daemon detail")
            return "/checkpoint"

        async def call_activate_connection(self, path, device_path, ap):
            assert (path, device_path, ap) == ("/saved/1", "/wifi", "/ap")
            assert connection.disk["802-11-wireless-security"]["psk"].value == "old-private-credential"
            events.append("activate")
            if failure in ("activate", "restore"):
                raise RuntimeError("new-private-credential")
            return "/active"

        async def call_checkpoint_destroy(self, path):
            events.append("destroy")
            if failure in ("destroy", "restore-save") and events.count("destroy") == 1:
                raise RuntimeError("private daemon detail")

        async def call_checkpoint_rollback(self, path):
            events.append("rollback")
            if failure in ("rollback", "cancel-rollback"):
                raise RuntimeError("private daemon detail")
            if failure != "restore":
                assert connection.memory["802-11-wireless-security"]["psk"].value == "old-private-credential"
            if failure == "rollback-code":
                return {"/wifi": 1}
            if failure == "rollback-empty":
                return {}
            if failure == "rollback-missing":
                return {"/other": 0}
            return {"/wifi": 0}

    class Wifi:
        async def call_request_scan(self, args):
            pass

        async def get_access_points(self):
            return ["/ap"]

    async def proxy(service, path, interface):
        if path == NM_PATH:
            return NetworkManager()
        if path == NM_SETTINGS_PATH:
            return Settings()
        if path.startswith("/saved/"):
            return connection
        if path == "/wifi":
            return Wifi()
        raise AssertionError(path)

    async def paths():
        return ["/ethernet", "/wifi"]

    async def props(service, path, interface):
        if path == "/ethernet":
            return {"DeviceType": 1}
        if path == "/wifi":
            return {"DeviceType": 2}
        return {"Ssid": list(b"Hub"), "RsnFlags": 1, "Strength": 70}

    async def wait(path, timeout):
        events.append("activated")
        if failure in ("wait", "rollback", "rollback-code", "rollback-empty", "rollback-missing"):
            raise DeviceError("authentication_failed")
        if failure in ("cancel", "cancel-rollback"):
            raise asyncio.CancelledError()

    async def sleep(seconds):
        pass

    monkeypatch.setattr(device, "_proxy", proxy)
    monkeypatch.setattr(device, "_props", props)
    monkeypatch.setattr(device, "_nm_device_paths", paths)
    monkeypatch.setattr(device, "_wait_for_activation", wait)
    monkeypatch.setattr("services.backend.device.asyncio.sleep", sleep)
    return device, connection, events


def test_selected_profile_updates_in_memory_then_saves_after_activation(monkeypatch):
    device, conn, events = fixture(monkeypatch)
    result = asyncio.run(device.network_connect("Hub", "new-private-credential", PROFILE))
    assert result == {"available": True, "connected": True, "ssid": "Hub", "profile_id": PROFILE, "error": None}
    assert events == ["settings", "secrets", "checkpoint", "update", "activate", "activated", "save", "destroy"]
    assert conn.disk["802-11-wireless-security"]["psk"].value == "new-private-credential"
    assert conn.disk["connection"]["id"].value == "Friendly name"


@pytest.mark.parametrize("failure", ["update", "activate", "wait", "persist", "destroy", "rollback", "restore", "restore-save", "rollback-code", "rollback-empty", "rollback-missing", "cancel", "cancel-rollback"])
def test_failure_restores_before_rollback_and_never_deletes_original(monkeypatch, caplog, failure):
    device, conn, events = fixture(monkeypatch, failure)
    error = asyncio.CancelledError if failure.startswith("cancel") else DeviceError
    with pytest.raises(error) as raised:
        asyncio.run(device.network_connect("Hub", "new-private-credential", PROFILE))
    assert events.index("restore") < events.index("rollback")
    assert "private-credential" not in str(raised.value)
    assert "private-credential" not in caplog.text
    assert conn.disk["802-11-wireless-security"]["psk"].value == "old-private-credential"
    if failure in ("restore", "restore-save", "rollback", "rollback-code", "rollback-empty", "rollback-missing"):
        assert raised.value.code == "network_recovery_failed"
    elif failure == "wait":
        assert raised.value.code == "authentication_failed"


@pytest.mark.parametrize("failure", ["snapshot", "missing-secret", "checkpoint"])
def test_snapshot_or_checkpoint_failure_never_mutates(monkeypatch, failure):
    device, conn, events = fixture(monkeypatch, failure)
    with pytest.raises(DeviceError):
        asyncio.run(device.network_connect("Hub", "new-private-credential", PROFILE))
    assert conn.updates == []
    assert "activate" not in events and "save" not in events


@pytest.mark.parametrize("kwargs", [{"ssid": b"Other"}, {"kind": "802-3-ethernet"}, {"duplicate": True}])
def test_profile_selection_rejects_mismatch_or_ambiguous_uuid(monkeypatch, kwargs):
    device, conn, events = fixture(monkeypatch, **kwargs)
    with pytest.raises(DeviceError, match="invalid_argument"):
        asyncio.run(device.network_connect("Hub", "new-private-credential", PROFILE))
    assert conn.updates == []
    assert "checkpoint" not in events


@pytest.mark.parametrize("identifier", ["/saved/1", "", 1])
def test_invalid_profile_id_rejected_before_system_access(identifier):
    with pytest.raises(DeviceError, match="invalid_argument"):
        asyncio.run(Device().network_connect("Hub", "credential", identifier))


def test_missing_explicit_profile_never_falls_back_to_new_connection(monkeypatch):
    device, conn, events = fixture(monkeypatch)
    with pytest.raises(DeviceError, match="not_found"):
        asyncio.run(device.network_connect("Hub", "credential", "87654321-1234-1234-1234-123456789abc"))
    assert conn.updates == [] and "checkpoint" not in events


def test_sae_key_management_and_secret_flags_are_preserved(monkeypatch):
    device, conn, events = fixture(monkeypatch, key_mgmt="sae")
    asyncio.run(device.network_connect("Hub", "new-private-credential", PROFILE))
    security = conn.disk["802-11-wireless-security"]
    assert security["key-mgmt"].value == "sae"
    assert security["psk-flags"].value == 0


def test_enterprise_credentials_not_silently_replaced_with_psk(monkeypatch):
    device, conn, events = fixture(monkeypatch, key_mgmt="wpa-eap")
    with pytest.raises(DeviceError, match="credential_update_unsupported"):
        asyncio.run(device.network_connect("Hub", "credential", PROFILE))
    assert "checkpoint" not in events and conn.updates == []


@pytest.mark.parametrize("flags", [1, 2, 3, 4, 7])
def test_nonpersistent_or_agent_owned_psk_rejected_before_reading_or_sending_secret(monkeypatch, flags):
    device, conn, events = fixture(monkeypatch, psk_flags=flags)
    with pytest.raises(DeviceError, match="credential_update_unsupported"):
        asyncio.run(device.network_connect("Hub", "new-private-credential", PROFILE))
    assert events == ["settings"]
    assert conn.updates == []


def test_concurrent_network_mutations_return_busy_and_release_lock(monkeypatch):
    device, conn, events = fixture(monkeypatch)
    async def run():
        async with device._network_lock:
            with pytest.raises(DeviceError, match="busy"):
                await device.network_connect("Hub", "credential", PROFILE)
            with pytest.raises(DeviceError, match="busy"):
                await device.network_forget(PROFILE)
        await device.network_connect("Hub", "credential", PROFILE)
        assert not device._network_lock.locked()
    asyncio.run(run())


def test_failed_operation_releases_network_lock(monkeypatch):
    device, conn, events = fixture(monkeypatch, "snapshot")
    with pytest.raises(DeviceError):
        asyncio.run(device.network_connect("Hub", "credential", PROFILE))
    assert not device._network_lock.locked()
