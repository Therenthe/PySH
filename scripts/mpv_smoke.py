"""Real mpv IPC and decoding test with null audio. Never claims audible output."""
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time

with tempfile.TemporaryDirectory(prefix='pi-hub-mpv-') as directory:
    endpoint = str(Path(directory) / 'ipc.sock')
    process = subprocess.Popen(['mpv', '--no-config', '--idle=yes', '--ao=null', '--vo=null', '--no-terminal', '--input-ipc-server=' + endpoint], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 10
        while not os.path.exists(endpoint) and time.monotonic() < deadline:
            time.sleep(.1)
        client = socket.socket(socket.AF_UNIX)
        client.settimeout(5)
        client.connect(endpoint)
        stream = client.makefile('rwb', buffering=0)
        serial = 0

        def request(*command):
            global serial
            serial += 1
            stream.write((json.dumps({'command': command, 'request_id': serial}) + '\n').encode())
            while True:
                line = stream.readline()
                if not line:
                    raise RuntimeError('IPC disconnected')
                response = json.loads(line)
                if response.get('request_id') == serial:
                    assert response.get('error') == 'success', response
                    return response.get('data')

        version = request('get_property', 'mpv-version')
        request('loadfile', 'av://lavfi:anullsrc=r=48000:cl=stereo')
        time.sleep(1)
        position = request('get_property', 'time-pos')
        assert position > 0, position
        request('set_property', 'pause', True)
        assert request('get_property', 'pause') is True
        print(json.dumps({'result': 'MPV_IPC_PASS', 'version': version, 'decoded_seconds': position, 'audio_output': 'null; no physical speaker tested'}))
        stream.close()
        client.close()
    finally:
        process.terminate()
        process.wait(timeout=5)
