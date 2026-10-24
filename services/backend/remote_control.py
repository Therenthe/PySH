"""Physical-hub approval boundary for Android App Control.

The gateway and local API share atomic, owner-only state. Approval mutations are
intentionally absent from the LAN proxy allowlist.
"""
import json
import time
from pathlib import Path
from services.remote.gateway import DeviceStore, RemoteError


class AndroidControl:
    def __init__(self, directory):
        self.directory = Path(directory) / 'remote'
        self.devices = DeviceStore(self.directory)

    def snapshot(self):
        if not (self.directory / 'config.json').is_file():
            return {'available': False, 'enabled': False, 'hubId': '', 'pending': [], 'devices': [], 'error': 'control_unavailable'}
        try:
            state = self.devices.read()
            now = time.time()
            runtime = json.loads((self.directory / 'runtime.json').read_text()) if (self.directory / 'runtime.json').exists() else {}
            available = runtime.get('updated', 0) > now - 10 and runtime.get('ready') is True
            result = {'available': available, 'enabled': state.get('enabled', True) is True, 'hubId': state.get('hubId', ''), 'pending': [{'requestId': r['requestId'], 'name': r['name'], 'expiresIn': max(0, int(r['expires'] - now))} for r in state.get('requests', []) if r['expires'] > now and r['status'] == 'pending'], 'devices': [{'deviceId': d['deviceId'], 'name': d['name']} for d in state['devices']]}
            if not available:
                result['error'] = 'control_unavailable'
            elif runtime.get('discovery') is not True:
                result['error'] = 'discovery_unavailable'
            return result
        except (OSError, ValueError, KeyError, TypeError):
            return {'available': False, 'enabled': False, 'hubId': '', 'pending': [], 'devices': [], 'error': 'control_unavailable'}

    def enable(self, enabled):
        if not (self.directory / 'config.json').is_file():
            raise RemoteError('control_unavailable', 409)
        self.devices.set_enabled(enabled)
        return self.snapshot()

    def approve(self, request_id, accept):
        if not (self.directory / 'config.json').is_file():
            raise RemoteError('control_unavailable', 409)
        self.devices.approve(request_id, accept)
        return self.snapshot()

    def revoke(self, device_id):
        if not (self.directory / 'config.json').is_file():
            raise RemoteError('control_unavailable', 409)
        if not self.devices.revoke(device_id):
            raise RemoteError('device_not_found', 404)
        return self.snapshot()
