"""Exercise FastAPI/uvicorn over loopback; this is a toolchain fixture, not the app."""
import json
import multiprocessing
import socket
import time
import urllib.request


def serve(port):
    from fastapi import FastAPI
    import uvicorn
    fixture = FastAPI()

    @fixture.get('/ready')
    def ready():
        return {'fixture': 'environment-only', 'ok': True}

    uvicorn.run(fixture, host='127.0.0.1', port=port, log_level='error')


def main():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    process = multiprocessing.Process(target=serve, args=(port,), daemon=True)
    process.start()
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/ready', timeout=1) as response:
                    value = json.load(response)
                assert value == {'fixture': 'environment-only', 'ok': True}, value
                print('BACKEND_HTTP_SMOKE_PASS; fixture only, no product functionality')
                return
            except (OSError, urllib.error.URLError):
                time.sleep(.2)
        raise RuntimeError('Backend HTTP fixture did not respond')
    finally:
        process.terminate()
        process.join(5)


if __name__ == '__main__':
    main()
