"""Read-only hardware/runtime audit; no speaker/DRM acceptance claims."""
import asyncio
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess


def command(*args):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=15)
    return {'exit': proc.returncode, 'output': proc.stdout.strip(), 'error': proc.stderr.strip()}


async def dbus_probe():
    from dbus_next.aio import MessageBus
    from dbus_next.constants import BusType
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    try:
        bluez = await bus.introspect('org.bluez', '/')
        network = await bus.introspect('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        return {'bluez': bool(bluez.interfaces), 'network_manager': bool(network.interfaces)}
    finally:
        bus.disconnect()


report = {
    'model': Path('/proc/device-tree/model').read_text().rstrip('\x00'),
    'os': Path('/etc/os-release').read_text(),
    'disk': shutil.disk_usage('/')._asdict(),
    'display': {str(p): p.read_text().strip() for p in Path('/sys/class/drm').glob('card*-DSI-*/modes')},
    'touch_present': 'ft5' in Path('/proc/bus/input/devices').read_text().lower(),
    'system_services': {s: command('systemctl', 'is-active', s) for s in ['ssh', 'NetworkManager', 'bluetooth', 'lightdm']},
    'user_services': {s: command('systemctl', '--user', 'is-active', s) for s in ['pipewire', 'wireplumber']},
    'tools': {s: shutil.which(s) for s in ['chromium', 'mpv', 'nmcli', 'bluetoothctl', 'wpctl', 'git', 'grim']},
    'versions': {s: importlib.metadata.version(s) for s in ['fastapi', 'uvicorn', 'dbus-next']},
    'package_integrity': command('dpkg', '--audit'),
    'bluetooth_power': command('busctl', '--system', 'get-property', 'org.bluez', '/org/bluez/hci0', 'org.bluez.Adapter1', 'Powered'),
    'dbus': asyncio.run(dbus_probe()),
    'not_tested': ['physical Bluetooth speaker playback', 'touch gestures by hand', 'Netflix DRM', 'application flows'],
}
print(json.dumps(report, indent=2))
required = [r['exit'] == 0 and r['output'] == 'active' for r in [*report['system_services'].values(), *report['user_services'].values()]]
passed = all(required) and all(report['tools'].values()) and all(report['dbus'].values()) and report['touch_present'] and report['display'] and not report['package_integrity']['output'] and report['package_integrity']['exit'] == 0
raise SystemExit(0 if passed else 1)
