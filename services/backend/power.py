"""Recoverable software standby, genuine backlight, and monotonic sleep timers."""
import asyncio
from datetime import datetime, timezone
import math
import os
import platform
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from .device import DeviceError


class Backlight:
    def __init__(self, device, root=Path('/sys/class/backlight')):
        self.device, self.root = device, Path(root)

    def target(self):
        if platform.system() != 'Linux':
            raise DeviceError('brightness_unavailable')
        candidates = [path for path in self.root.iterdir() if path.name in {'rpi_backlight', '10-0045', '11-0045', '12-0045'} or 'dsi' in path.name.lower()]
        if len(candidates) != 1:
            raise DeviceError('brightness_unavailable')
        path = candidates[0]
        maximum = int((path / 'max_brightness').read_text().strip())
        if not 1 <= maximum <= 65535:
            raise DeviceError('brightness_unavailable')
        return path, maximum

    async def status(self):
        try:
            path, maximum = await asyncio.to_thread(self.target)
            actual = int(await asyncio.to_thread((path / 'actual_brightness').read_text))
            return {'available': True, 'value': max(0, min(100, round(actual * 100 / maximum)))}
        except (OSError, ValueError, DeviceError):
            return {'available': False, 'value': None, 'error': 'brightness_unavailable'}

    async def set(self, percent):
        try:
            path, maximum = await asyncio.to_thread(self.target)
            raw = 0 if percent == 0 else max(1, round(maximum * percent / 100))
            try:
                await asyncio.to_thread((path / 'brightness').write_text, str(raw))
            except PermissionError:
                # logind authorizes the active session; no broad chmod or root helper.
                manager = await self.device._proxy('org.freedesktop.login1', '/org/freedesktop/login1', 'org.freedesktop.login1.Manager')
                sessions = await manager.call_list_sessions()
                active = []
                for item in sessions:
                    if item[1] == os.getuid() and item[3] and await self.device._get('org.freedesktop.login1', item[4], 'org.freedesktop.login1.Session', 'Active'):
                        active.append(item)
                if len(active) != 1:
                    raise DeviceError('brightness_permission_denied')
                session_path = active[0][4]
                session = await self.device._proxy('org.freedesktop.login1', session_path, 'org.freedesktop.login1.Session')
                await session.call_set_brightness('backlight', path.name, raw)
            result = await self.status()
            if not result['available'] or abs(result['value'] - percent) > max(1, math.ceil(100 / maximum)):
                raise DeviceError('brightness_write_failed')
            return result
        except DeviceError:
            raise
        except PermissionError as error:
            raise DeviceError('brightness_permission_denied') from error
        except Exception as error:
            raise DeviceError('brightness_write_failed') from error


class PowerController:
    def __init__(self, hub, backlight=None, monotonic=time.monotonic, utc_now=None):
        self.hub = hub
        self.backlight = backlight or Backlight(hub.device)
        self.monotonic = monotonic
        self.utc_now = utc_now or (lambda: datetime.now(timezone.utc))
        self.standby = False
        self.deadline = None
        self.deadline_wall = None
        self.error = None
        self.lock = asyncio.Lock()
        self.daily_key = None
        self.previous_local = None
        self.daily_dates = set()
        self.generation = 0

    async def snapshot(self):
        preferences = self.hub.store.value
        brightness = await self.backlight.status()
        brightness['desired'] = preferences.screenBrightness
        result = {'standby': self.standby, 'brightness': brightness,
                  'timer': {'deadline': self.deadline_wall, 'remainingSeconds': max(0, math.ceil(self.deadline - self.monotonic())) if self.deadline is not None else 0},
                  'daily': {'enabled': preferences.dailyStandbyEnabled, 'time': preferences.dailyStandbyTime}}
        if self.error:
            result['error'] = self.error
        return result

    async def change(self, standby, expected_generation=None, daily_date=None):
        async with self.hub.media_lock, self.lock:
            if expected_generation is not None and expected_generation != self.generation:
                return await self.snapshot()
            if standby:
                playback = await self.hub.player.status()
                if playback.get('state') not in {'idle', 'ended', 'error', 'paused'}:
                    self.hub.cache_playback(await self.hub.player.command('pause'))
                await self.hub.external.close()
                await self.hub.visualizer.close()
                # Failure to control backlight leaves a visible, touch-wakeable
                # software standby rather than inventing a hardware capability.
                try:
                    await self.backlight.set(0)
                    self.error = None
                except DeviceError as error:
                    self.error = error.code
                self.standby = True
            else:
                try:
                    await self.backlight.set(self.hub.store.value.screenBrightness)
                    self.error = None
                except DeviceError as error:
                    self.error = error.code
                self.standby = False
            self.deadline = self.deadline_wall = None
            self.generation += 1
            if daily_date:
                self.daily_dates.add(daily_date)
            if not standby:
                preferences = self.hub.store.value
                local = self.utc_now().astimezone(ZoneInfo(preferences.timezone))
                if preferences.dailyStandbyEnabled and local.strftime('%H:%M') >= preferences.dailyStandbyTime:
                    self.daily_dates.add(local.date().isoformat())
        return await self.snapshot()

    async def timer(self, minutes):
        async with self.lock:
            self.deadline = self.monotonic() + minutes * 60 if minutes else None
            self.deadline_wall = datetime.fromtimestamp(self.utc_now().timestamp() + minutes * 60, timezone.utc).isoformat() if minutes else None
            self.generation += 1

    async def brightness(self, percent, persist=True):
        if persist:
            return await self.update_preferences({'screenBrightness': percent})
        async with self.lock:
            # Write hardware first: failed writes must not persist a misleading slider.
            if not self.standby:
                await self.backlight.set(percent)

    async def update_preferences(self, patch):
        async with self.lock:
            type(self.hub.store.value).model_validate({**self.hub.store.export(), **patch})
            previous = self.hub.store.value.screenBrightness
            changed = 'screenBrightness' in patch and not self.standby
            if changed:
                await self.backlight.set(patch['screenBrightness'])
            try:
                result = self.hub.store.update(patch)
            except OSError as error:
                if changed:
                    try:
                        await self.backlight.set(previous)
                    except DeviceError:
                        self.error = 'brightness_restore_failed'
                raise DeviceError('preferences_write_failed') from error
            if {'dailyStandbyEnabled', 'dailyStandbyTime', 'timezone'} & patch.keys():
                self.generation += 1
            if 'screenBrightness' in patch:
                self.error = None
            return result

    async def tick(self):
        async with self.lock:
            now = self.utc_now()
            preferences = self.hub.store.value
            local = now.astimezone(ZoneInfo(preferences.timezone))
            key = (preferences.dailyStandbyEnabled, preferences.dailyStandbyTime, preferences.timezone)
            date = local.date().isoformat()
            clock = local.strftime('%H:%M')
            if key != self.daily_key:
                self.daily_key, self.previous_local = key, local
                # Restart/toggle after today's time does not unexpectedly undo wake.
                if preferences.dailyStandbyEnabled and clock >= preferences.dailyStandbyTime:
                    self.daily_dates.add(date)
            daily_due = (preferences.dailyStandbyEnabled and date not in self.daily_dates
                         and clock >= preferences.dailyStandbyTime and self.previous_local is not None)
            self.previous_local = local
            timer_due = self.deadline is not None and self.monotonic() >= self.deadline
            generation = self.generation
        if daily_due or timer_due:
            try:
                await self.change(True, expected_generation=generation, daily_date=date if daily_due else None)
            except Exception:
                async with self.lock:
                    if self.generation == generation:
                        self.error = 'standby_failed'
                        self.deadline = self.deadline_wall = None
                        self.generation += 1

    async def run(self):
        # Hardware backlight may remain zero after a killed process; always
        # restore desired level while runtime standby starts awake.
        try:
            await self.brightness(self.hub.store.value.screenBrightness, persist=False)
        except DeviceError as error:
            self.error = error.code
        while True:
            if not self.standby and self.error:
                # Early startup may precede system-bus initialization. Retry the
                # intended awake brightness until that component becomes ready.
                try:
                    await self.brightness(self.hub.store.value.screenBrightness, persist=False)
                    self.error = None
                except DeviceError as error:
                    self.error = error.code
            await self.tick()
            await asyncio.sleep(1)


class RemotePresence:
    def __init__(self, monotonic=time.monotonic):
        self.monotonic, self.devices = monotonic, {}

    def update(self, device_id, active):
        self.snapshot()
        if active and (device_id in self.devices or len(self.devices) < 16):
            self.devices[device_id] = self.monotonic() + 15
        else:
            self.devices.pop(device_id, None)

    def snapshot(self):
        now = self.monotonic()
        self.devices = {key: expiry for key, expiry in self.devices.items() if expiry > now}
        return {'connected': bool(self.devices), 'count': len(self.devices)}
