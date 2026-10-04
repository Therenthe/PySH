"""Ephemeral output-monitor samples; never records a microphone or writes audio."""
import asyncio
import math
import re
import shutil
import struct
import time
from datetime import datetime, timezone


def pcm_levels(raw: bytes) -> dict:
    """64 signed waveform samples and 16 time-domain RMS bins (not FFT)."""
    count = len(raw) // 2
    if not count:
        raise ValueError("empty_pcm")
    values = [value / 32768 for value in struct.unpack('<' + 'h' * count, raw[:count * 2])]
    waveform = [round(values[min(count - 1, i * count // 64)], 4) for i in range(64)]
    bars = []
    for index in range(16):
        segment = values[index * count // 16:max(index * count // 16 + 1, (index + 1) * count // 16)]
        bars.append(round(math.sqrt(sum(value * value for value in segment) / len(segment)), 4))
    peak = max(abs(value) for value in values)
    rms = math.sqrt(sum(value * value for value in values) / count)
    return dict(waveform=waveform, bars=bars, peak=round(peak, 4), rms=round(rms, 4), silent=peak < .001)


def selected_monitor(audio: dict, player: dict) -> tuple[str | None, str]:
    if player.get('state') != 'playing' or player.get('kind') not in ('radio', 'audio'):
        return None, 'inactive'
    if not audio.get('ready') or audio.get('mute') or not isinstance(audio.get('volume'), (int, float)) or isinstance(audio.get('volume'), bool) or not math.isfinite(audio['volume']) or audio['volume'] <= 0:
        return None, 'inactive'
    sink = audio.get('output')
    if not isinstance(sink, str) or len(sink) > 200 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', sink) or sink.endswith('.monitor'):
        return None, 'invalid_output'
    if not any(node.get('id') == sink and node.get('active') is True for node in audio.get('outputs', []) if isinstance(node, dict)):
        return None, 'invalid_output'
    return sink + '.monitor', 'ready'


class OutputVisualizer:
    def __init__(self, context_provider, *, clock=time.monotonic, launcher=asyncio.create_subprocess_exec, executable=None):
        self.context_provider = context_provider
        self.clock = clock
        self.launcher = launcher
        self.executable = executable
        self.deadline = 0
        self.task = None
        self.monitor = None
        self.sample = None
        self.sample_time = 0
        self.status = 'inactive'
        self.retry_at = 0
        self.lock = asyncio.Lock()

    def _context(self):
        return selected_monitor(*self.context_provider())

    async def close(self):
        self.deadline = 0
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
            self.task = None
        self.sample = None
        self.monitor = None

    async def snapshot(self, enabled=True):
        async with self.lock:
            monitor, reason = self._context() if enabled else (None, 'off')
            if not monitor:
                await self.close()
                self.status = reason
                return self._result()
            if monitor != self.monitor:
                await self.close()
                self.retry_at = 0
            self.deadline = self.clock() + 2
            if (not self.task or self.task.done()) and self.clock() >= self.retry_at:
                self.sample = None
                self.monitor = monitor
                self.status = 'starting'
                self.task = asyncio.create_task(self._capture(monitor))
            return self._result()

    def _result(self):
        if self.sample and self.clock() - self.sample_time <= .5:
            return {'available': True, 'status': 'ready', **self.sample}
        return {'available': False, 'status': 'stale' if self.sample else self.status, 'waveform': [], 'bars': [], 'peak': None, 'rms': None, 'sampled_at': None, 'silent': None}

    async def _capture(self, monitor):
        process = None
        try:
            executable = self.executable or shutil.which('parec')
            if not executable:
                self.status = 'unsupported'
                return
            process = await self.launcher(executable, '--device=' + monitor, '--raw', '--format=s16le', '--rate=8000', '--channels=1', '--latency-msec=100', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, limit=3200)
            while self.clock() < self.deadline:
                cycle_started = self.clock()
                current, reason = self._context()
                if current != monitor:
                    self.status = reason if not current else 'routing_changed'
                    return
                raw = await asyncio.wait_for(process.stdout.readexactly(1600), .6)
                # Recheck after a blocked read; routing/pause must clear old samples.
                if self._context()[0] != monitor or self.clock() >= self.deadline:
                    self.status = 'inactive'
                    return
                self.sample = {**pcm_levels(raw), 'sampled_at': datetime.now(timezone.utc).isoformat()}
                self.sample_time = self.clock()
                self.status = 'ready'
                await asyncio.sleep(max(0, .1 - (self.clock() - cycle_started)))
            self.status = 'inactive'
        except asyncio.CancelledError:
            raise
        except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError, ValueError):
            self.status = 'unavailable'
        finally:
            self.sample = None
            self.retry_at = self.clock() + 2
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), .5)
                except ProcessLookupError:
                    pass
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
