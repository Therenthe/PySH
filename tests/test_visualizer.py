import asyncio
import math
import struct

import pytest

from services.backend.visualizer import OutputVisualizer, pcm_levels, selected_monitor


def run_async(scenario):
    def test():
        asyncio.run(scenario())
    return test


def context(sink='bluez_output.AA_BB.1', state='playing', kind='radio'):
    return ({'ready': True, 'volume': 25, 'mute': False, 'output': sink, 'outputs': [{'id': sink, 'active': True}]}, {'state': state, 'kind': kind})


def test_pcm_real_amplitudes_and_silence():
    silence = pcm_levels(bytes(1600))
    assert silence['silent'] and silence['bars'] == [0] * 16 and silence['waveform'] == [0] * 64
    raw = struct.pack('<800h', *[round(16384 * math.sin(index * math.pi / 20)) for index in range(800)])
    signal = pcm_levels(raw)
    assert signal['peak'] == .5 and abs(signal['rms'] - .3536) < .001
    assert len(signal['waveform']) == 64 and len(signal['bars']) == 16
    assert not signal['silent'] and min(signal['waveform']) < 0
    with pytest.raises(ValueError):
        pcm_levels(b'')


@pytest.mark.parametrize('sink', ['@DEFAULT_SOURCE@', 'input.monitor', '-device', 'sink;record', 'sink\nname', '', 'a' * 201])
def test_monitor_never_defaults_or_accepts_injection(sink):
    assert selected_monitor(*context(sink))[0] is None


@pytest.mark.parametrize('state,kind', [('paused', 'radio'), ('buffering', 'radio'), ('playing', 'video'), ('playing', 'local')])
def test_only_active_radio_or_audio(state, kind):
    assert selected_monitor(*context(state=state, kind=kind))[0] is None
    assert selected_monitor(*context(kind='audio'))[0].endswith('.monitor')


def test_output_must_be_selected_active_ready_and_audible():
    audio, player = context()
    for key, value in [('mute', True), ('ready', False), ('volume', 0), ('volume', float('nan')), ('volume', True), ('outputs', [])]:
        assert selected_monitor({**audio, key: value}, player)[0] is None


class Process:
    def __init__(self):
        self.stdout = asyncio.StreamReader()
        self.returncode = None
        self.terminated = False
    def terminate(self):
        self.terminated = True
        self.returncode = 0
    def kill(self):
        self.terminate()
    async def wait(self):
        return self.returncode


@run_async
async def test_capture_lifecycle_routing_and_no_disk_recording():
    current = list(context())
    processes, commands = [], []
    async def launch(*args, **kwargs):
        commands.append((args, kwargs))
        proc = Process()
        processes.append(proc)
        proc.stdout.feed_data(bytes(1600))
        return proc
    visualizer = OutputVisualizer(lambda: current, launcher=launch, executable='/usr/bin/parec')
    assert not (await visualizer.snapshot())['available']
    await asyncio.sleep(.01)
    first = await visualizer.snapshot()
    assert first['available'] and first['silent']
    assert commands[0][0][1] == '--device=bluez_output.AA_BB.1.monitor'
    assert '--raw' in commands[0][0] and 'shell' not in commands[0][1]
    current[:] = context('alsa_output.new')
    changed = await visualizer.snapshot()
    assert not changed['available'] and processes[0].terminated
    await asyncio.sleep(.01)
    assert commands[1][0][1] == '--device=alsa_output.new.monitor'
    current[1]['state'] = 'paused'
    assert (await visualizer.snapshot())['status'] == 'inactive'
    assert processes[1].terminated
    await visualizer.close()


@run_async
async def test_heartbeat_and_staleness_clear_capture():
    now = [10.0]
    proc = Process()
    proc.stdout.feed_data(bytes(1600))
    async def launch(*args, **kwargs): return proc
    visualizer = OutputVisualizer(lambda: context(), clock=lambda: now[0], launcher=launch, executable='parec')
    await visualizer.snapshot()
    await asyncio.sleep(.01)
    assert visualizer._result()['available']
    now[0] += .6
    assert visualizer._result()['status'] == 'stale'
    now[0] += 3
    proc.stdout.feed_data(bytes(1600))
    await asyncio.sleep(.15)
    assert proc.terminated and not visualizer._result()['available']
    await visualizer.close()


@run_async
async def test_failure_has_no_fallback_and_off_stops():
    calls = []
    async def fail(*args, **kwargs):
        calls.append(args)
        raise OSError('missing monitor')
    visualizer = OutputVisualizer(lambda: context(), launcher=fail, executable='parec')
    await visualizer.snapshot()
    await asyncio.sleep(.01)
    assert (await visualizer.snapshot())['status'] == 'unavailable'
    assert len(calls) == 1
    assert (await visualizer.snapshot(enabled=False))['status'] == 'off'
    assert visualizer.task is None and visualizer.sample is None


@run_async
async def test_unresponsive_monitor_is_terminated_and_signal_cleared():
    proc = Process()
    async def launch(*args, **kwargs): return proc
    visualizer = OutputVisualizer(lambda: context(), launcher=launch, executable='parec')
    await visualizer.snapshot()
    await asyncio.sleep(.65)
    assert proc.terminated
    assert visualizer._result()['status'] == 'unavailable'
    assert not visualizer._result()['available']
    await visualizer.close()
