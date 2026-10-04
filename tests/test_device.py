"""Hardware adapter tests use parsed data and fakes; they never touch a Pi."""
from __future__ import annotations

import asyncio

import pytest

from services.backend.device import Device, DeviceError, NM_SETTINGS_PATH, NM_PATH, _dbus_code


def test_ssid_and_security_parsing_handles_byte_arrays_and_hidden_networks():
    assert Device._ssid([72, 111, 109, 101]) == "Home"
    assert Device._ssid(b"caf\xc3\xa9\x00") == "café"
    assert Device._ssid([]) == ""
    assert Device._security({"Flags": 1, "WpaFlags": 0, "RsnFlags": 0}) == "secured"
    assert Device._security({"Flags": 0, "WpaFlags": 0, "RsnFlags": 0}) == "open"
    assert Device._security({"RsnFlags": 2}) == "secured"


def test_pipewire_parser_identifies_default_and_bluetooth_sink():
    nodes, default = Device._pw_nodes([
        {
            "id": 1,
            "type": "PipeWire:Interface:Metadata",
            "metadata": [{"key": "default.audio.sink", "value": '{"name":"bluez_output.11_22"}'}],
        },
        {"id": 41, "type": "PipeWire:Interface:Node", "info": {"props": {
            "media.class": "Audio/Sink", "node.name": "bluez_output.11_22",
            "node.description": "Living room speaker", "device.api": "bluez5",
        }}},
        {"id": 42, "type": "PipeWire:Interface:Node", "info": {"props": {
            "media.class": "Audio/Sink", "node.name": "alsa_output.analog", "node.description": "Built-in audio",
        }}},
        {"id": 55, "type": "PipeWire:Interface:Node", "info": {"props": {"media.class": "Audio/Source"}}},
    ])
    assert default == "bluez_output.11_22"
    assert [node["id"] for node in nodes] == ["bluez_output.11_22", "alsa_output.analog"]
    assert [node["wp_id"] for node in nodes] == ["41", "42"]
    assert nodes[0]["bluetooth"] is True
    assert nodes[1]["bluetooth"] is False


@pytest.mark.parametrize("value", ['{"name":"alsa_output.default"}', {"name": "alsa_output.default"}])
def test_pipewire_parser_accepts_string_or_decoded_metadata(value):
    nodes, default = Device._pw_nodes([
        {"id": 1, "type": "PipeWire:Interface:Metadata", "metadata": [
            {"key": "default.audio.sink", "value": value},
        ]},
        {"id": 57, "type": "PipeWire:Interface:Node", "info": {"props": {
            "media.class": "Audio/Sink", "node.name": "alsa_output.default",
            "node.description": "Built-in audio",
        }}},
    ])
    assert default == "alsa_output.default"
    assert nodes[0]["active"] is False


def test_dbus_errors_are_reduced_to_stable_codes_without_daemon_text():
    error = type("FakeDBusError", (Exception,), {"type": "org.freedesktop.NetworkManager.NotAuthorized"})
    exc = error("secret-bearing daemon detail")
    assert _dbus_code(exc) == "permission_denied"
    assert "secret-bearing" not in _dbus_code(exc)
    assert _dbus_code(TimeoutError()) == "operation_failed"


def test_windows_host_reports_hardware_unavailable_without_fake_success(monkeypatch):
    device = Device()
    monkeypatch.setattr(device, "_linux", False)

    async def run():
        await device.initialize()
        assert (await device.network_status()) == {
            "available": False, "state": "unavailable", "connection": None,
            "devices": [], "saved": [], "error": "unavailable",
        }
        assert (await device.bluetooth_status())["available"] is False
        assert (await device.bluetooth_status())["error"] == "unavailable"
        assert (await device.audio_status())["available"] is False
        assert (await device.network_scan()) == {"available": False, "networks": [], "error": "unavailable"}
        with pytest.raises(DeviceError, match="unavailable"):
            await device.bluetooth_power(True)

    asyncio.run(run())


def test_network_inputs_and_identifiers_are_validated_before_system_access():
    device = Device()

    async def run():
        with pytest.raises(DeviceError, match="invalid_argument"):
            await device.network_connect("", "secret")
        with pytest.raises(DeviceError, match="invalid_argument"):
            await device.network_connect("x" * 33, "secret")
        with pytest.raises(DeviceError, match="invalid_argument"):
            await device.network_forget("/org/freedesktop/NetworkManager/Settings/1")
        with pytest.raises(DeviceError, match="invalid_argument"):
            await device.bluetooth_action("../../hci0", "pair")
        with pytest.raises(DeviceError, match="invalid_argument"):
            await device.bluetooth_action("11:22:33:44:55:66", "shell")

    asyncio.run(run())


def test_pairing_reply_requires_an_existing_prompt_and_valid_numeric_input():
    device = Device()
    loop = asyncio.new_event_loop()
    future = loop.create_future()
    prompt_id = "a" * 32
    device._bt_pending[prompt_id] = (future, {"id": prompt_id, "kind": "passkey"})

    async def run():
        with pytest.raises(DeviceError, match="invalid_argument"):
            await device.bluetooth_reply(prompt_id, True, "1234567")
        result = await device.bluetooth_reply(prompt_id, True, "012345")
        assert result["replied"] is True
        assert future.result() == "012345"
        with pytest.raises(DeviceError, match="not_found"):
            await device.bluetooth_reply("b" * 32, True)

    try:
        loop.run_until_complete(run())
    finally:
        loop.close()


def test_network_status_uses_settings_object_path_and_state_property(monkeypatch):
    device = Device()
    device._linux = True
    device._bus = object()
    requested: list[tuple[str, str, str]] = []

    class NetworkManager:
        async def get_state(self):
            return 70

        async def get_active_connections(self):
            return []

        async def get_primary_connection(self):
            return "/"

    class Settings:
        async def call_list_connections(self):
            return []

    async def proxy(service, path, interface):
        requested.append((service, path, interface))
        if path == NM_PATH:
            return NetworkManager()
        if path == NM_SETTINGS_PATH:
            return Settings()
        raise AssertionError(f"Unexpected D-Bus path: {path}")

    async def device_paths():
        return []

    monkeypatch.setattr(device, "_proxy", proxy)
    monkeypatch.setattr(device, "_nm_device_paths", device_paths)

    async def run():
        state = await device.network_status()
        assert state["available"] is True
        assert state["state"] == "connected"
        assert state["saved"] == []

    asyncio.run(run())
    assert ("org.freedesktop.NetworkManager", NM_SETTINGS_PATH, "org.freedesktop.NetworkManager.Settings") in requested


def test_wifi_profile_autoconnect_is_enabled_after_activation_and_keeps_secret(monkeypatch):
    device = Device()
    device._linux = True
    device._bus = object()
    events: list[str] = []

    class NetworkManager:
        async def call_checkpoint_create(self, paths, timeout, flags):
            events.append("checkpoint")
            return "/checkpoint/1"

        async def call_add_and_activate_connection2(self, settings, path, ap, options):
            assert settings["connection"]["autoconnect"].value is False
            events.append("activate")
            return "/settings/1", "/active/1", {}

        async def call_checkpoint_destroy(self, path):
            events.append("destroy")

    class Settings:
        async def call_list_connections(self):
            return []

    class Wifi:
        async def call_request_scan(self, options):
            return None

        async def get_access_points(self):
            return ["/ap/1"]

    class Connection:
        async def call_get_settings(self):
            return {"connection": {"autoconnect": __import__("dbus_next").Variant("b", False)}}

        async def call_get_secrets(self, setting_name):
            assert setting_name == "802-11-wireless-security"
            return {"802-11-wireless-security": {"psk": __import__("dbus_next").Variant("s", "private-passphrase")}}

        async def call_update(self, settings):
            assert settings["connection"]["autoconnect"].value is True
            assert settings["802-11-wireless-security"]["psk"].value == "private-passphrase"
            events.append("save-autoconnect")

    nm, settings, wifi, connection = NetworkManager(), Settings(), Wifi(), Connection()
    requested: list[str] = []

    async def proxy(service, path, interface):
        if path == NM_PATH:
            return nm
        if path == NM_SETTINGS_PATH:
            requested.append(path)
            return settings
        if path == "/org/freedesktop/NetworkManager/Devices/wlan0":
            return wifi
        if path == "/settings/1":
            return connection
        raise AssertionError(f"Unexpected D-Bus path: {path}")

    async def device_paths():
        return ["/org/freedesktop/NetworkManager/Devices/wlan0"]

    async def props(service, path, interface):
        if path.endswith("wlan0"):
            return {"DeviceType": 2}
        if path == "/ap/1":
            return {"Ssid": list(b"Hub"), "Flags": 0, "WpaFlags": 1, "RsnFlags": 0, "Strength": 80}
        raise AssertionError(f"Unexpected properties path: {path}")

    async def wait_for_activation(active_path, timeout):
        assert active_path == "/active/1"
        assert timeout == 45
        events.append("activated")

    async def rollback(*args):
        raise AssertionError("Successful activation should not roll back")

    monkeypatch.setattr(device, "_proxy", proxy)
    monkeypatch.setattr(device, "_nm_device_paths", device_paths)
    monkeypatch.setattr(device, "_props", props)
    monkeypatch.setattr(device, "_wait_for_activation", wait_for_activation)
    monkeypatch.setattr(device, "_rollback_network", rollback)

    async def run():
        result = await device.network_connect("Hub", "private-passphrase")
        assert result["connected"] is True

    asyncio.run(run())
    assert requested == [NM_SETTINGS_PATH]
    assert events == ["checkpoint", "activate", "activated", "save-autoconnect", "destroy"]


def test_audio_set_only_changes_an_enumerated_output(monkeypatch):
    device = Device()
    calls: list[tuple[str, ...]] = []

    async def status():
        return {"available": True, "volume": 20, "mute": False, "output": "41", "outputs": [
            {"id": "bluez_output", "wp_id": "41", "name": "bluez_output", "bluetooth": True},
        ], "error": None}

    async def run_audio(*args: str, timeout: float = 4):
        calls.append(args)
        return ""

    monkeypatch.setattr(device, "audio_status", status)
    monkeypatch.setattr(device, "_run_audio", run_audio)

    async def run():
        with pytest.raises(DeviceError, match="not_found"):
            await device.audio_set(output="missing_output")
        assert calls == []
        with pytest.raises(DeviceError, match="invalid_argument"):
            await device.audio_set(volume=101)
        await device.audio_set(volume=65, mute=True, output="bluez_output")
        assert calls == [
            ("wpctl", "set-default", "41"),
            ("wpctl", "set-volume", "41", "0.65"),
            ("wpctl", "set-mute", "41", "1"),
        ]

    asyncio.run(run())
