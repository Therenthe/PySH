#!/usr/bin/env python3
"""Own only our API and kiosk processes; recover crashes, respect explicit exit."""
import contextlib
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("PI_HUB_DATA", str(Path.home() / ".local/share/pi-smart-hub")))
DATA.mkdir(parents=True, exist_ok=True)
os.chmod(DATA, 0o700)
lock = (DATA / "session.lock").open("w")
try:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit("Hub is already running")

exit_request = DATA / "exit-request"
exit_request.unlink(missing_ok=True)
environment = dict(os.environ, PI_HUB_SUPERVISED="1", PI_HUB_DATA=str(DATA))
children = []
stopping = False


def stop(signum=None, frame=None):
    global stopping
    stopping = True


def terminate(child):
    if child and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
api = None
browser = None
try:
    while not stopping and not exit_request.exists():
        if api is None or api.poll() is not None:
            terminate(browser)
            browser = None
            api = subprocess.Popen([sys.executable, "-m", "uvicorn", "services.backend.app:app", "--host", "127.0.0.1", "--port", "8765", "--no-access-log"], cwd=ROOT, env=environment)
            children.append(api)
            for _ in range(80):
                if stopping or api.poll() is not None:
                    break
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8765/api/session", timeout=.5):
                        break
                except Exception:
                    time.sleep(.25)
        if api.poll() is None and (browser is None or browser.poll() is not None):
            browser = subprocess.Popen(["chromium", "--ozone-platform=wayland", "--no-first-run", "--noerrdialogs", "--disable-session-crashed-bubble", "--password-store=basic", "--kiosk", "--user-data-dir=" + str(DATA / "hub-browser"), "--app=http://127.0.0.1:8765"], env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            children.append(browser)
        time.sleep(1)
finally:
    for child in reversed(children):
        with contextlib.suppress(ProcessLookupError):
            terminate(child)
    exit_request.unlink(missing_ok=True)
