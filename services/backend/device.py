"""Real hardware adapters for NetworkManager, BlueZ and PipeWire/WirePlumber.

This module intentionally exposes a small, structured API.  It never accepts
commands or arbitrary D-Bus paths from callers.  A non-Linux development host
reports the hardware services as unavailable.
"""
import asyncio
import json
import logging
import platform
import re
import shutil
import uuid
from typing import Any

from dbus_next import BusType, Variant
from dbus_next.aio import MessageBus
from dbus_next.errors import DBusError
from dbus_next.service import ServiceInterface, method

LOG = logging.getLogger(__name__)

NM = "org.freedesktop.NetworkManager"
NM_PATH = "/org/freedesktop/NetworkManager"
NM_SETTINGS_PATH = "/org/freedesktop/NetworkManager/Settings"
NM_IFACE = "org.freedesktop.NetworkManager"
NM_SETTINGS = "org.freedesktop.NetworkManager.Settings"
NM_DEVICE = "org.freedesktop.NetworkManager.Device"
NM_WIFI = "org.freedesktop.NetworkManager.Device.Wireless"
NM_AP = "org.freedesktop.NetworkManager.AccessPoint"
NM_ACTIVE = "org.freedesktop.NetworkManager.Connection.Active"
NM_CONN = "org.freedesktop.NetworkManager.Settings.Connection"
DBUS_PROPERTIES = "org.freedesktop.DBus.Properties"
DBUS_OBJECT_MANAGER = "org.freedesktop.DBus.ObjectManager"
BLUEZ = "org.bluez"
BLUEZ_ADAPTER = "org.bluez.Adapter1"
BLUEZ_DEVICE = "org.bluez.Device1"
BLUEZ_AGENT_MANAGER = "org.bluez.AgentManager1"
BLUEZ_AGENT_PATH = "/com/pi_smart_hub/agent"

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
BT_ADDRESS_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
BT_ACTIONS = {"pair", "connect", "disconnect", "forget"}
MAX_SCAN_SECONDS = 20


class DeviceError(Exception):
    """An operation failed with an API-safe, stable error code."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _unvariant(value: Any) -> Any:
    if isinstance(value, Variant):
        return _unvariant(value.value)
    if isinstance(value, dict):
        return {str(k): _unvariant(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_unvariant(v) for v in value]
    if isinstance(value, bytes):
        return list(value)
    return value


def _variant(value: Any, signature: str) -> Variant:
    return Variant(signature, value)


def _dbus_code(exc: BaseException) -> str:
    """Map D-Bus errors without returning daemon messages or possible secrets."""
    name = getattr(exc, "type", "") or getattr(exc, "_dbus_error_name", "")
    name = str(name).lower()
    if "serviceunknown" in name or "noreply" in name:
        return "unavailable"
    if "notfound" in name or "unknownobject" in name:
        return "not_found"
    if "invalidargs" in name or "invalidargument" in name:
        return "invalid_argument"
    if "timeout" in name:
        return "timeout"
    if "notauthorized" in name or "accessdenied" in name or "permissiondenied" in name:
        return "permission_denied"
    if "alreadyexists" in name or "alreadyconnected" in name:
        return "already_exists"
    if "authentication" in name or "secretswere required" in str(exc).lower():
        return "authentication_failed"
    return "operation_failed"


class _PairingAgent(ServiceInterface):
    """BlueZ agent that waits for explicit UI decisions for every request."""

    def __init__(self, device: "Device") -> None:
        super().__init__("org.bluez.Agent1")
        self.device = device

    async def _request(self, address: str, kind: str, value: str | None = None) -> str | None:
        prompt_id = uuid.uuid4().hex
        future = asyncio.get_running_loop().create_future()
        prompt = {"id": prompt_id, "address": address, "name": self.device._bt_name(address), "kind": kind}
        if value is not None:
            prompt["value"] = value
        self.device._bt_pending[prompt_id] = (future, prompt)
        try:
            return await asyncio.wait_for(future, timeout=120)
        except asyncio.TimeoutError as exc:
            raise DBusError("org.bluez.Error.Rejected", "Pairing request timed out") from exc
        finally:
            self.device._bt_pending.pop(prompt_id, None)

    @method()
    async def Release(self) -> '':
        self.device._agent_registered = False

    @method()
    async def Cancel(self) -> '':
        for future, _ in tuple(self.device._bt_pending.values()):
            if not future.done():
                future.set_exception(DBusError("org.bluez.Error.Canceled", "Pairing canceled"))

    @method()
    async def RequestPinCode(self, device: "o") -> "s":
        result = await self._request(self.device._address_from_path(device), "pin_code")
        if result is None:
            raise DBusError("org.bluez.Error.Rejected", "Pairing rejected")
        if not (1 <= len(result) <= 16) or not result.isascii() or not result.isprintable():
            raise DBusError("org.bluez.Error.Rejected", "Invalid PIN")
        return result

    @method()
    async def RequestPasskey(self, device: "o") -> "u":
        result = await self._request(self.device._address_from_path(device), "passkey")
        if result is None or not result.isdigit() or len(result) > 6:
            raise DBusError("org.bluez.Error.Rejected", "Invalid passkey")
        return int(result)

    @method()
    async def DisplayPinCode(self, device: "o", pincode: "s") -> '':
        await self._request(self.device._address_from_path(device), "display_pin", pincode)

    @method()
    async def DisplayPasskey(self, device: "o", passkey: "u", entered: "q") -> '':
        await self._request(self.device._address_from_path(device), "display_passkey", f"{passkey:06d}")

    @method()
    async def RequestConfirmation(self, device: "o", passkey: "u") -> '':
        result = await self._request(self.device._address_from_path(device), "confirmation", f"{passkey:06d}")
        if result is None:
            raise DBusError("org.bluez.Error.Rejected", "Pairing rejected")

    @method()
    async def RequestAuthorization(self, device: "o") -> '':
        result = await self._request(self.device._address_from_path(device), "authorization")
        if result is None:
            raise DBusError("org.bluez.Error.Rejected", "Pairing rejected")

    @method()
    async def AuthorizeService(self, device: "o", uuid_value: "s") -> '':
        result = await self._request(self.device._address_from_path(device), "service_authorization", uuid_value)
        if result is None:
            raise DBusError("org.bluez.Error.Rejected", "Service rejected")


class Device:
    """Asynchronous Linux hardware adapter used by the local API service."""

    def __init__(self) -> None:
        self._linux = platform.system() == "Linux"
        self._bus: MessageBus | None = None
        self._nm_obj_cache: dict[tuple[str, str], Any] = {}
        self._bt_pending: dict[str, tuple[asyncio.Future[str | None], dict[str, Any]]] = {}
        self._bt_names: dict[str, str] = {}
        self._agent = _PairingAgent(self)
        self._agent_registered = False
        self._bluetooth_error: str | None = None

    async def initialize(self) -> None:
        """Connect to the system bus; failure leaves methods honestly unavailable."""
        if not self._linux:
            return
        try:
            self._bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            await self._ensure_agent()
        except Exception as exc:
            LOG.info("System D-Bus unavailable (%s)", type(exc).__name__)
            self._bus = None
            self._bluetooth_error = "unavailable"

    async def close(self) -> None:
        if self._bus is not None:
            try:
                if self._agent_registered:
                    obj = await self._proxy(BLUEZ, "/org/bluez", BLUEZ_AGENT_MANAGER)
                    await obj.call_unregister_agent(BLUEZ_AGENT_PATH)
            except Exception:
                pass
            self._bus.disconnect()
            self._bus = None
        for future, _ in tuple(self._bt_pending.values()):
            if not future.done():
                future.cancel()

    async def _proxy(self, service: str, path: str, interface: str) -> Any:
        if self._bus is None:
            raise DeviceError("unavailable")
        key = (service, path)
        obj = self._nm_obj_cache.get(key)
        if obj is None:
            introspection = await self._bus.introspect(service, path)
            obj = self._bus.get_proxy_object(service, path, introspection)
            self._nm_obj_cache[key] = obj
        return obj.get_interface(interface)

    async def _props(self, service: str, path: str, interface: str) -> dict[str, Any]:
        props = await self._proxy(service, path, DBUS_PROPERTIES)
        return _unvariant(await props.call_get_all(interface))

    async def _get(self, service: str, path: str, interface: str, name: str) -> Any:
        props = await self._proxy(service, path, DBUS_PROPERTIES)
        return _unvariant(await props.call_get(interface, name))

    async def _set(self, service: str, path: str, interface: str, name: str, value: Any, signature: str) -> None:
        props = await self._proxy(service, path, DBUS_PROPERTIES)
        await props.call_set(interface, name, _variant(value, signature))

    async def _objects(self, service: str, path: str) -> dict[str, dict[str, dict[str, Any]]]:
        manager = await self._proxy(service, path, DBUS_OBJECT_MANAGER)
        objects = await manager.call_get_managed_objects()
        return _unvariant(objects)

    async def _ensure_agent(self) -> None:
        if self._bus is None or self._agent_registered:
            return
        try:
            self._bus.export(BLUEZ_AGENT_PATH, self._agent)
            manager = await self._proxy(BLUEZ, "/org/bluez", BLUEZ_AGENT_MANAGER)
            await manager.call_register_agent(BLUEZ_AGENT_PATH, "KeyboardDisplay")
            await manager.call_request_default_agent(BLUEZ_AGENT_PATH)
            self._agent_registered = True
        except Exception as exc:
            # BlueZ may be absent or blocked. Bluetooth methods report it.
            self._bluetooth_error = _dbus_code(exc)
            try:
                self._bus.unexport(BLUEZ_AGENT_PATH, self._agent)
            except Exception:
                pass

    @staticmethod
    def _variants(values: dict[str, Any]) -> dict[str, Variant]:
        result = {}
        for key, value in values.items():
            if isinstance(value, Variant):
                result[key] = value
            elif isinstance(value, bool):
                result[key] = Variant("b", value)
            elif isinstance(value, int):
                result[key] = Variant("u", value)
            else:
                result[key] = Variant("s", value)
        return result

    @staticmethod
    def _ssid(raw: Any) -> str:
        if isinstance(raw, str):
            return raw
        if isinstance(raw, (bytes, bytearray)):
            raw = bytes(raw)
        elif isinstance(raw, list):
            raw = bytes(raw)
        else:
            return ""
        return raw.decode("utf-8", errors="replace").rstrip("\x00")

    @staticmethod
    def _security(props: dict[str, Any]) -> str:
        if int(props.get("WpaFlags", 0) or 0) or int(props.get("RsnFlags", 0) or 0):
            return "secured"
        if int(props.get("Flags", 0) or 0) & 1:
            return "secured"
        return "open"

    @staticmethod
    def _state_name(state: int) -> str:
        return {
            0: "unknown", 10: "unmanaged", 20: "unavailable", 30: "disconnected",
            40: "prepare", 50: "config", 60: "ip_config", 70: "ip_check",
            80: "secondaries", 100: "connected", 110: "deactivating", 120: "failed",
        }.get(int(state), "unknown")

    async def _nm_device_paths(self) -> list[str]:
        nm = await self._proxy(NM, NM_PATH, NM_IFACE)
        return list(await nm.call_get_devices())

    async def network_status(self) -> dict[str, Any]:
        result: dict[str, Any] = {"available": False, "state": "unavailable", "connection": None, "devices": [], "saved": [], "error": None}
        if not self._linux or self._bus is None:
            result["error"] = "unavailable"
            return result
        try:
            nm = await self._proxy(NM, NM_PATH, NM_IFACE)
            # NetworkManager exposes both a historical state() method and the
            # State property; use the documented property for status reads.
            nm_state = int(await nm.get_state())
            result["available"] = True
            result["state"] = "connected" if nm_state in (50, 60, 70) else ("disconnected" if nm_state in (20, 30, 40) else "connecting")
            for path in await self._nm_device_paths():
                p = await self._props(NM, path, NM_DEVICE)
                device_type = int(p.get("DeviceType", 0))
                if device_type not in (1, 2):
                    continue
                entry: dict[str, Any] = {"interface": p.get("Interface", ""), "type": {1: "ethernet", 2: "wifi"}.get(device_type, "other"), "state": self._state_name(int(p.get("State", 0)))}
                if device_type == 2:
                    wifi = await self._proxy(NM, path, NM_WIFI)
                    ap_path = await wifi.get_active_access_point()
                    if ap_path and ap_path != "/":
                        ap = await self._props(NM, ap_path, NM_AP)
                        entry["ssid"] = self._ssid(ap.get("Ssid", []))
                    else:
                        entry["ssid"] = None
                ip_path = p.get("Ip4Config", "/")
                if ip_path and ip_path != "/":
                    ip_props = await self._props(NM, ip_path, "org.freedesktop.NetworkManager.IP4Config")
                    addresses = ip_props.get("AddressData", [])
                    if addresses:
                        entry["ip"] = addresses[0].get("address")
                result["devices"].append(entry)
            settings = await self._proxy(NM, NM_SETTINGS_PATH, "org.freedesktop.NetworkManager.Settings")
            active_paths = await nm.get_active_connections()
            primary_path = await nm.get_primary_connection()
            active_profiles: set[str] = set()
            candidates: list[tuple[tuple, str]] = []
            connection_types = {"802-3-ethernet", "802-11-wireless"}
            for active_path in active_paths:
                try:
                    active = await self._props(NM, active_path, NM_ACTIVE)
                    if active.get("Type") not in connection_types or active.get("State") != 2:
                        continue
                    active_profiles.add(str(active.get("Uuid", "")))
                    name = str(active.get("Id", ""))
                    # Loopback is also active on recent NetworkManager versions.
                    # Use its primary route, rather than whichever object is last.
                    priority = (active_path != primary_path,
                                not (active.get("Default") or active.get("Default6")),
                                active.get("Type") != "802-3-ethernet", name, active_path)
                    candidates.append((priority, name))
                except Exception:
                    continue
            if candidates:
                result["connection"] = min(candidates)[1]
            for conn_path in await settings.call_list_connections():
                try:
                    conn = await self._proxy(NM, conn_path, NM_CONN)
                    config = _unvariant(await conn.call_get_settings())
                    cs = config.get("connection", {})
                    if cs.get("type") not in connection_types:
                        continue
                    name = str(cs.get("id", ""))
                    profile_id = str(cs.get("uuid", ""))
                    result["saved"].append({"id": profile_id, "name": name, "active": profile_id in active_profiles, "type": str(cs.get("type", "other"))})
                except Exception:
                    continue
            return result
        except Exception as exc:
            result["error"] = _dbus_code(exc)
            return result

    async def network_scan(self) -> dict[str, Any]:
        result: dict[str, Any] = {"available": False, "networks": [], "error": None}
        if not self._linux or self._bus is None:
            result["error"] = "unavailable"
            return result
        try:
            paths = await self._nm_device_paths()
            for path in paths:
                props = await self._props(NM, path, NM_DEVICE)
                if int(props.get("DeviceType", 0)) != 2:
                    continue
                wifi = await self._proxy(NM, path, NM_WIFI)
                await wifi.call_request_scan({})
                await asyncio.sleep(2)
                access_points = await wifi.get_access_points()
                active = await wifi.get_active_access_point()
                by_ssid: dict[str, dict[str, Any]] = {}
                for ap_path in access_points:
                    ap = await self._props(NM, ap_path, NM_AP)
                    ssid = self._ssid(ap.get("Ssid", []))
                    if not ssid:
                        continue
                    strength = int(ap.get("Strength", 0))
                    item = {"ssid": ssid, "signal": strength, "security": self._security(ap), "in_use": ap_path == active}
                    if ssid not in by_ssid or strength > by_ssid[ssid]["signal"]:
                        by_ssid[ssid] = item
                result["networks"].extend(by_ssid.values())
            result["networks"].sort(key=lambda n: (-n["signal"], n["ssid"].casefold()))
            result["available"] = True
        except Exception as exc:
            result["error"] = _dbus_code(exc)
        return result

    async def network_connect(self, ssid: str, password: str) -> dict[str, Any]:
        if not isinstance(ssid, str) or not ssid or len(ssid.encode("utf-8")) > 32 or "\x00" in ssid:
            raise DeviceError("invalid_argument")
        if not isinstance(password, str) or len(password) > 128 or "\x00" in password:
            raise DeviceError("invalid_argument")
        if not self._linux or self._bus is None:
            raise DeviceError("unavailable")
        nm = await self._proxy(NM, NM_PATH, NM_IFACE)
        settings = await self._proxy(NM, NM_SETTINGS_PATH, "org.freedesktop.NetworkManager.Settings")
        checkpoint: str | None = None
        profile: str | None = None
        profile_uuid: str | None = None
        try:
            device_paths = await self._nm_device_paths()
            wifi_devices = []
            matching: list[tuple[str, str, dict[str, Any]]] = []
            for path in device_paths:
                p = await self._props(NM, path, NM_DEVICE)
                if int(p.get("DeviceType", 0)) != 2:
                    continue
                wifi_devices.append(path)
                wifi = await self._proxy(NM, path, NM_WIFI)
                await wifi.call_request_scan({})
                await asyncio.sleep(1)
                for ap_path in await wifi.get_access_points():
                    ap = await self._props(NM, ap_path, NM_AP)
                    if self._ssid(ap.get("Ssid", [])) == ssid:
                        matching.append((path, ap_path, ap))
            if not wifi_devices:
                raise DeviceError("unavailable")
            if not matching:
                raise DeviceError("not_found")
            matching.sort(key=lambda item: int(item[2].get("Strength", 0)), reverse=True)
            device_path, ap_path, ap_props = matching[0]
            secured = self._security(ap_props) == "secured"
            if secured and not password:
                raise DeviceError("authentication_failed")
            if not secured and password:
                # Avoid silently storing or sending a credential for an open AP.
                raise DeviceError("invalid_argument")
            checkpoint = await nm.call_checkpoint_create(wifi_devices, 120, 0)
            profile_uuid = str(uuid.uuid4())
            setting: dict[str, dict[str, Variant]] = {
                "connection": self._variants({"id": ssid, "uuid": profile_uuid, "type": "802-11-wireless", "autoconnect": False}),
                "802-11-wireless": {"ssid": Variant("ay", ssid.encode("utf-8")), "mode": Variant("s", "infrastructure")},
                "ipv4": {"method": Variant("s", "auto")},
                "ipv6": {"method": Variant("s", "auto")},
            }
            if secured:
                setting["802-11-wireless-security"] = {
                    "key-mgmt": Variant("s", "wpa-psk"),
                    "psk": Variant("s", password),
                }
            options = {"persist": Variant("s", "disk")}
            profile, active_path, _ = await nm.call_add_and_activate_connection2(setting, device_path, ap_path, options)
            await self._wait_for_activation(active_path, 45)
            await self._enable_autoconnect(profile, secured)
            await nm.call_checkpoint_destroy(checkpoint)
            checkpoint = None
            return {"available": True, "connected": True, "ssid": ssid, "error": None}
        except DeviceError:
            if checkpoint:
                await self._rollback_network(nm, checkpoint, settings, profile, profile_uuid)
            raise
        except Exception as exc:
            if checkpoint:
                await self._rollback_network(nm, checkpoint, settings, profile, profile_uuid)
            raise DeviceError(_dbus_code(exc)) from None

    async def _wait_for_activation(self, active_path: str, timeout: int) -> None:
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            props = await self._props(NM, active_path, NM_ACTIVE)
            state = int(props.get("State", 0))
            if state == 2:
                return
            if state in (3, 4):
                reason = int(props.get("StateReason", [0, 0])[1]) if isinstance(props.get("StateReason"), list) else 0
                raise DeviceError("authentication_failed" if reason in (7, 8, 9, 10) else "operation_failed")
            await asyncio.sleep(0.5)
        raise DeviceError("timeout")

    async def _enable_autoconnect(self, profile_path: str, secured: bool) -> None:
        """Persist auto-connect only after activation has succeeded.

        NetworkManager's Update replaces settings, and GetSettings omits
        secrets. Preserve the PSK by requesting it separately for this update;
        it remains in memory only and is never included in logs or responses.
        """
        connection = await self._proxy(NM, profile_path, NM_CONN)
        settings = await connection.call_get_settings()
        settings = {name: dict(values) for name, values in settings.items()}
        settings.setdefault("connection", {})["autoconnect"] = Variant("b", True)
        if secured:
            secrets = await connection.call_get_secrets("802-11-wireless-security")
            for setting_name, values in secrets.items():
                settings.setdefault(setting_name, {}).update(values)
        await connection.call_update(settings)

    async def _rollback_network(self, nm: Any, checkpoint: str, settings: Any, profile: str | None, profile_uuid: str | None = None) -> None:
        try:
            await nm.call_checkpoint_rollback(checkpoint)
        except Exception:
            LOG.warning("NetworkManager checkpoint rollback failed")
        finally:
            try:
                await nm.call_checkpoint_destroy(checkpoint)
            except Exception:
                pass
        if profile is None and profile_uuid:
            try:
                for candidate in await settings.call_list_connections():
                    conn = await self._proxy(NM, candidate, NM_CONN)
                    data = _unvariant(await conn.call_get_settings())
                    if str(data.get("connection", {}).get("uuid", "")).lower() == profile_uuid.lower():
                        profile = candidate
                        break
            except Exception:
                LOG.warning("Failed to locate Wi-Fi profile after rollback")
        if profile:
            try:
                conn = await self._proxy(NM, profile, NM_CONN)
                await conn.call_delete()
            except Exception:
                LOG.warning("Failed Wi-Fi profile cleanup after rollback")

    async def network_forget(self, profile_id: str) -> dict[str, Any]:
        if not isinstance(profile_id, str) or not UUID_RE.fullmatch(profile_id):
            raise DeviceError("invalid_argument")
        if not self._linux or self._bus is None:
            raise DeviceError("unavailable")
        settings = await self._proxy(NM, NM_SETTINGS_PATH, "org.freedesktop.NetworkManager.Settings")
        nm = await self._proxy(NM, NM_PATH, NM_IFACE)
        try:
            for path in await settings.call_list_connections():
                conn = await self._proxy(NM, path, NM_CONN)
                data = _unvariant(await conn.call_get_settings())
                cs = data.get("connection", {})
                if str(cs.get("uuid", "")).lower() != profile_id.lower():
                    continue
                for active_path in await nm.get_active_connections():
                    active = await self._props(NM, active_path, NM_ACTIVE)
                    if str(active.get("Uuid", "")).lower() == profile_id.lower():
                        await nm.call_deactivate_connection(active_path)
                await conn.call_delete()
                return {"available": True, "forgotten": True, "id": profile_id, "error": None}
            raise DeviceError("not_found")
        except DeviceError:
            raise
        except Exception as exc:
            raise DeviceError(_dbus_code(exc)) from None

    async def _bluez_paths(self) -> list[str]:
        if not self._linux or self._bus is None:
            raise DeviceError("unavailable")
        objects = await self._objects(BLUEZ, "/")
        return [path for path, interfaces in objects.items() if BLUEZ_ADAPTER in interfaces]

    async def _adapter_path(self) -> str:
        paths = await self._bluez_paths()
        if not paths:
            raise DeviceError("unavailable")
        return sorted(paths)[0]

    @staticmethod
    def _address_from_path(path: str) -> str:
        match = re.search(r"dev_([0-9A-Fa-f_]{17})$", path)
        return match.group(1).replace("_", ":") if match else ""

    def _bt_name(self, address: str) -> str | None:
        if address in self._bt_names:
            return self._bt_names[address]
        for prompt in self._bt_pending.values():
            if prompt[1].get("address", "").lower() == address.lower():
                return prompt[1].get("name")
        return None

    async def _bt_device(self, address: str) -> tuple[str, Any]:
        if not isinstance(address, str) or not BT_ADDRESS_RE.fullmatch(address):
            raise DeviceError("invalid_argument")
        objects = await self._objects(BLUEZ, "/")
        for path, interfaces in objects.items():
            props = interfaces.get(BLUEZ_DEVICE)
            if props and str(props.get("Address", "")).lower() == address.lower():
                return path, await self._proxy(BLUEZ, path, BLUEZ_DEVICE)
        raise DeviceError("not_found")

    async def _bluetooth_devices(self) -> list[dict[str, Any]]:
        objects = await self._objects(BLUEZ, "/")
        devices = []
        for path, interfaces in objects.items():
            p = interfaces.get(BLUEZ_DEVICE)
            if not p:
                continue
            address = str(p.get("Address", ""))
            if not BT_ADDRESS_RE.fullmatch(address):
                continue
            self._bt_names[address] = str(p.get("Alias") or p.get("Name") or address)
            devices.append({
                "address": address,
                "name": p.get("Alias") or p.get("Name") or address,
                "paired": bool(p.get("Paired", False)),
                "connected": bool(p.get("Connected", False)),
                "trust": bool(p.get("Trusted", False)),
                "uuids": list(p.get("UUIDs", [])),
            })
        devices.sort(key=lambda item: (not item["paired"], str(item["name"]).casefold(), item["address"]))
        return devices

    async def bluetooth_status(self) -> dict[str, Any]:
        result = {"available": False, "powered": False, "discovering": False, "devices": [], "prompts": [], "error": None}
        if not self._linux or self._bus is None:
            result["error"] = "unavailable"
            return result
        try:
            adapter_path = await self._adapter_path()
            props = await self._props(BLUEZ, adapter_path, BLUEZ_ADAPTER)
            result.update({"available": True, "powered": bool(props.get("Powered", False)), "discovering": bool(props.get("Discovering", False)), "devices": await self._bluetooth_devices(), "prompts": [p for _, p in self._bt_pending.values()]})
            if not result["powered"]:
                result["devices"] = [d for d in result["devices"] if d["paired"]]
        except Exception as exc:
            result["error"] = exc.code if isinstance(exc, DeviceError) else _dbus_code(exc)
            if self._bluetooth_error:
                result["error"] = self._bluetooth_error
        return result

    async def bluetooth_power(self, enabled: bool) -> dict[str, Any]:
        if not isinstance(enabled, bool):
            raise DeviceError("invalid_argument")
        try:
            path = await self._adapter_path()
            await self._set(BLUEZ, path, BLUEZ_ADAPTER, "Powered", enabled, "b")
            return {"available": True, "powered": enabled, "error": None}
        except Exception as exc:
            raise DeviceError(exc.code if isinstance(exc, DeviceError) else _dbus_code(exc)) from None

    async def bluetooth_scan(self) -> dict[str, Any]:
        try:
            path = await self._adapter_path()
            adapter = await self._proxy(BLUEZ, path, BLUEZ_ADAPTER)
            powered = bool(await self._get(BLUEZ, path, BLUEZ_ADAPTER, "Powered"))
            if not powered:
                raise DeviceError("unavailable")
            try:
                await adapter.call_start_discovery()
                await asyncio.sleep(MAX_SCAN_SECONDS)
            finally:
                try:
                    await adapter.call_stop_discovery()
                except Exception:
                    pass
            return {"available": True, "devices": await self._bluetooth_devices(), "error": None}
        except Exception as exc:
            raise DeviceError(exc.code if isinstance(exc, DeviceError) else _dbus_code(exc)) from None

    async def bluetooth_action(self, address: str, action: str) -> dict[str, Any]:
        if action not in BT_ACTIONS:
            raise DeviceError("invalid_argument")
        path, device = await self._bt_device(address)
        try:
            if action == "pair":
                await self._ensure_agent()
                if not self._agent_registered:
                    raise DeviceError("unavailable")
                await asyncio.wait_for(device.call_pair(), timeout=125)
                await self._set(BLUEZ, path, BLUEZ_DEVICE, "Trusted", True, "b")
                state = "paired"
            elif action == "connect":
                await asyncio.wait_for(device.call_connect(), timeout=40)
                state = "connected"
            elif action == "disconnect":
                await device.call_disconnect()
                state = "disconnected"
            else:
                try:
                    await device.call_disconnect()
                except Exception:
                    pass
                await device.call_remove_device() if hasattr(device, "call_remove_device") else await (await self._proxy(BLUEZ, path.rsplit("/dev_", 1)[0], BLUEZ_ADAPTER)).call_remove_device(path)
                state = "forgotten"
            return {"available": True, "action": action, "address": address, "state": state, "error": None}
        except Exception as exc:
            raise DeviceError(exc.code if isinstance(exc, DeviceError) else _dbus_code(exc)) from None

    async def bluetooth_reply(self, prompt_id: str, accept: bool, value: str | None = None) -> dict[str, Any]:
        if not isinstance(prompt_id, str) or not re.fullmatch(r"[0-9a-f]{32}", prompt_id) or not isinstance(accept, bool):
            raise DeviceError("invalid_argument")
        entry = self._bt_pending.get(prompt_id)
        if entry is None:
            raise DeviceError("not_found")
        future, prompt = entry
        if future.done():
            raise DeviceError("not_found")
        if not accept:
            future.set_result(None)
        elif prompt["kind"] in ("pin_code", "passkey"):
            if not isinstance(value, str) or not value or not value.isascii() or not value.isdigit():
                raise DeviceError("invalid_argument")
            if prompt["kind"] == "passkey" and (len(value) > 6 or int(value) > 999999):
                raise DeviceError("invalid_argument")
            if prompt["kind"] == "pin_code" and len(value) > 16:
                raise DeviceError("invalid_argument")
            future.set_result(value)
        elif value is not None:
            raise DeviceError("invalid_argument")
        else:
            future.set_result("accept")
        return {"available": True, "replied": True, "id": prompt_id, "error": None}

    @staticmethod
    def _pw_nodes(data: Any) -> tuple[list[dict[str, Any]], str | None]:
        if not isinstance(data, list):
            raise DeviceError("operation_failed")
        nodes: list[dict[str, Any]] = []
        default_id: str | None = None
        for item in data:
            if not isinstance(item, dict):
                continue
            info = item.get("info") or {}
            props = info.get("props") or {}
            if item.get("type", "").endswith(":Interface:Metadata"):
                for record in item.get("metadata", info.get("metadata", [])):
                    if record.get("key") == "default.audio.sink":
                        try:
                            raw_value = record.get("value", {})
                            value = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
                            if not isinstance(value, dict):
                                continue
                            default_id = str(value.get("name") or "") or None
                        except (ValueError, TypeError, AttributeError):
                            pass
            if props.get("media.class") != "Audio/Sink":
                continue
            name = str(props.get("node.name", ""))
            description = str(props.get("node.description") or props.get("device.description") or name)
            bluetooth = "bluez" in (name + " " + str(props.get("device.api", ""))).lower() or "bluetooth" in description.lower()
            nodes.append({"id": name, "wp_id": str(item.get("id", "")), "name": name, "description": description, "active": False, "bluetooth": bluetooth})
        return nodes, default_id

    async def _run_audio(self, *args: str, timeout: float = 4) -> str:
        executable = shutil.which(args[0])
        if not executable:
            raise DeviceError("unavailable")
        try:
            proc = await asyncio.create_subprocess_exec(executable, *args[1:], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise DeviceError("timeout") from exc
        if proc.returncode != 0:
            raise DeviceError("operation_failed")
        return stdout.decode("utf-8", errors="replace")

    async def audio_status(self) -> dict[str, Any]:
        result = {"available": False, "volume": None, "mute": None, "output": None, "outputs": [], "error": None}
        if not self._linux:
            result["error"] = "unavailable"
            return result
        try:
            raw = await self._run_audio("pw-dump")
            nodes, default_name = self._pw_nodes(json.loads(raw))
            if not nodes:
                result["error"] = "no_output"
                return result
            default = next((node for node in nodes if node["name"] == default_name), None)
            if default is None:
                # WirePlumber's default can be resolved by wpctl even if metadata
                # is not exposed in this pw-dump version.
                status = await self._run_audio("wpctl", "status")
                match = re.search(r"\*\s+(\d+)\.\s+(.+?)\s+\[vol:", status)
                if match:
                    default = next((node for node in nodes if node["wp_id"] == match.group(1)), None)
            if default is None:
                default = next((node for node in nodes if node.get("active")), nodes[0])
            volume_text = await self._run_audio("wpctl", "get-volume", default["wp_id"])
            match = re.search(r"Volume:\s*([0-9.]+)(?:\s+\[(MUTED)\])?", volume_text)
            if not match:
                raise DeviceError("operation_failed")
            default["active"] = True
            result.update({"available": True, "volume": max(0, min(100, round(float(match.group(1)) * 100))), "mute": bool(match.group(2)), "output": default["id"], "outputs": nodes})
        except Exception as exc:
            result["error"] = exc.code if isinstance(exc, DeviceError) else "unavailable" if isinstance(exc, (FileNotFoundError, OSError)) else "operation_failed"
        return result

    async def audio_set(self, volume: int | None = None, mute: bool | None = None, output: str | None = None) -> dict[str, Any]:
        if volume is not None and (not isinstance(volume, int) or isinstance(volume, bool) or not 0 <= volume <= 100):
            raise DeviceError("invalid_argument")
        if mute is not None and not isinstance(mute, bool):
            raise DeviceError("invalid_argument")
        if output is not None and (not isinstance(output, str) or not output or len(output) > 256 or "\x00" in output):
            raise DeviceError("invalid_argument")
        state = await self.audio_status()
        if not state["available"]:
            raise DeviceError(state["error"] or "unavailable")
        selected = output if output is not None else state["output"]
        selected_node = next((node for node in state["outputs"] if node["id"] == selected), None)
        if selected_node is None:
            raise DeviceError("not_found")
        pipewire_id = selected_node["wp_id"]
        try:
            if output is not None:
                await self._run_audio("wpctl", "set-default", pipewire_id)
            if volume is not None:
                await self._run_audio("wpctl", "set-volume", pipewire_id, f"{volume / 100:.2f}")
            if mute is not None:
                await self._run_audio("wpctl", "set-mute", pipewire_id, "1" if mute else "0")
        except DeviceError:
            raise
        except Exception as exc:
            raise DeviceError("operation_failed") from exc
        return await self.audio_status()
