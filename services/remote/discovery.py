"""Publish one explicit LAN listener using the existing Avahi system service."""
import asyncio
import json
import subprocess
import threading
import time

from .gateway import LanServer, atomic_json, lan_address


def private_interface(preferred):
    try:
        addresses = json.loads(subprocess.run(['ip', '-j', '-4', 'addr', 'show', 'scope', 'global'], capture_output=True, check=True, timeout=3).stdout)
        routes = json.loads(subprocess.run(['ip', '-j', '-4', 'route', 'show', 'default'], capture_output=True, check=True, timeout=3).stdout)
        default = routes[0].get('dev') if routes else None
        options = [(a['local'], interface['ifindex'], interface['ifname']) for interface in addresses if 'UP' in interface.get('flags', []) for a in interface.get('addr_info', []) if a.get('family') == 'inet' and lan_address(a.get('local', ''))]
        selected = next((o for o in options if o[2] == default), None) or next((o for o in options if o[0] == preferred), None) or next(iter(options), None)
        return selected[:2] if selected else None
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return None


class Advertisement:
    def __init__(self):
        self.bus = self.group = None

    async def close(self):
        if self.group:
            try:
                await self.group.call_free()
            except Exception:
                pass
        self.group = None
        if self.bus:
            self.bus.disconnect()
        self.bus = None

    async def publish(self, interface, port, hub_id):
        await self.close()
        from dbus_next import BusType
        from dbus_next.aio import MessageBus
        self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        xml = await self.bus.introspect('org.freedesktop.Avahi', '/')
        server = self.bus.get_proxy_object('org.freedesktop.Avahi', '/', xml).get_interface('org.freedesktop.Avahi.Server')
        path = await server.call_entry_group_new()
        xml = await self.bus.introspect('org.freedesktop.Avahi', path)
        self.group = self.bus.get_proxy_object('org.freedesktop.Avahi', path, xml).get_interface('org.freedesktop.Avahi.EntryGroup')
        txt = [value.encode() for value in ('hubId=' + hub_id, 'protocol=2', 'name=PySH')]
        await self.group.call_add_service(interface, 0, 0, 'PySH ' + hub_id[:8], '_pysh-control._tcp', '', '', port, txt)
        await self.group.call_commit()


async def serve_dynamic(config, directory, context, devices, pin):
    server = thread = None
    current = None
    advertised = False
    advertisement = Advertisement()
    hub_id = devices.hub_id()
    try:
        while True:
            address = await asyncio.to_thread(private_interface, config['host'])
            enabled = await asyncio.to_thread(devices.enabled)
            desired = address if enabled else None
            if advertised:
                try:
                    state = await asyncio.wait_for(advertisement.group.call_get_state(), timeout=2)
                    if state not in (1, 2):
                        raise RuntimeError('Advertisement unavailable')
                except Exception:
                    await advertisement.close()
                    advertised = False
            if desired != current or thread and not thread.is_alive():
                await advertisement.close()
                advertised = False
                if server:
                    await asyncio.to_thread(server.shutdown)
                    await asyncio.to_thread(thread.join, 3)
                    server.server_close()
                server = thread = None
                current = None
                if desired:
                    try:
                        server = LanServer(desired[0], config['port'], context, devices, pin=pin)
                        thread = threading.Thread(target=server.serve_forever, daemon=True)
                        thread.start()
                        current = desired
                    except OSError:
                        if server:
                            server.server_close()
                        server = None
            if current and not advertised:
                try:
                    await asyncio.wait_for(advertisement.publish(current[1], config['port'], hub_id), timeout=4)
                    advertised = True
                except Exception:
                    await advertisement.close()
            # While disabled, the local screen can distinguish a healthy supervisor
            # from a crashed service even though no LAN port is open.
            atomic_json(directory / 'runtime.json', {'updated': time.time(), 'protocol': 2, 'ready': bool(current) or not enabled, 'discovery': advertised or not enabled, 'host': current[0] if current else '', 'port': config['port']})
            await asyncio.sleep(2)
    finally:
        await advertisement.close()
        if server:
            await asyncio.to_thread(server.shutdown)
            await asyncio.to_thread(thread.join, 3)
            server.server_close()
        atomic_json(directory / 'runtime.json', {'updated': time.time(), 'ready': False, 'discovery': False})
