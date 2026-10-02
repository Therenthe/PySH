#!/usr/bin/env python3
"""Own only our API and kiosk processes; recover crashes, respect explicit exit."""
import ctypes
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

def enable_child_reaping():
    """Adopt crashed workers' descendants so owned orphan processes are reaped."""
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER (Linux)
        raise OSError(ctypes.get_errno(), "Cannot enable child subreaping")


def reap_adopted_children(*leaders):
    """Reap exited adoptees, even when they detached from their worker's group.

    Direct Popen leaders keep ownership of their exit status. Reading our Linux
    child list avoids waitpid(-1), which could steal one of those return codes.
    This helper never signals a process and never waits for a running child.
    """
    protected = {child.pid for child in leaders if child is not None}
    child_list = Path(f"/proc/self/task/{os.getpid()}/children")
    reaped = 0
    for value in child_list.read_text(encoding="ascii").split():
        pid = int(value)
        if pid in protected:
            continue
        try:
            waited, _ = os.waitpid(pid, os.WNOHANG)
            reaped += bool(waited)
        except ChildProcessError:
            pass  # Already reaped or no longer our child.
    return reaped


def start_owned(*args, **kwargs):
    child = subprocess.Popen(*args, **kwargs, start_new_session=True)
    child._pysh_owned_pgid = child.pid
    return child


def terminate(child, grace=5, kill_grace=2):
    """Clean a session we created, including descendants of a dead leader."""
    if child is None or getattr(child, "_pysh_owned_cleaned", False):
        return
    pgid = getattr(child, "_pysh_owned_pgid", None)
    if pgid != child.pid:
        raise ValueError("Refusing to signal a process group we did not create")

    def reap():
        # Popen owns its direct child's return code; only reap descendants after it.
        if child.poll() is not None:
            while True:
                try:
                    pid, _ = os.waitpid(-pgid, os.WNOHANG)
                    if pid == 0:
                        break
                except ChildProcessError:
                    break

    def exists():
        reap()
        try:
            os.killpg(pgid, 0)
            return True
        except ProcessLookupError:
            return False

    def signal_group(sig):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            pass

    def wait_group(timeout):
        deadline = time.monotonic() + timeout
        while exists():
            if time.monotonic() >= deadline:
                return False
            time.sleep(.05)
        return True

    signal_group(signal.SIGTERM)
    if not wait_group(grace):
        signal_group(signal.SIGKILL)
        if not wait_group(kill_grace):
            raise RuntimeError("Owned process group did not stop within the deadline")
    child.wait(timeout=kill_grace)
    child._pysh_owned_cleaned = True


def main():
    import fcntl

    enable_child_reaping()

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

    stopping = False

    def stop(signum=None, frame=None):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    api = None
    browser = None
    try:
        while not stopping and not exit_request.exists():
            reap_adopted_children(api, browser)
            if api is None or api.poll() is not None:
                if api is not None:
                    print(f"API exited code={api.returncode}; restarting API and kiosk", file=sys.stderr, flush=True)
                terminate(browser)
                browser = None
                terminate(api)
                api = start_owned([sys.executable, "-m", "uvicorn", "services.backend.app:app", "--host", "127.0.0.1", "--port", "8765", "--no-access-log"], cwd=ROOT, env=environment)
                for _ in range(80):
                    if stopping or exit_request.exists() or api.poll() is not None:
                        break
                    try:
                        with urllib.request.urlopen("http://127.0.0.1:8765/api/session", timeout=.5):
                            break
                    except Exception:
                        time.sleep(.25)
            if not stopping and not exit_request.exists() and api.poll() is None and (browser is None or browser.poll() is not None):
                if browser is not None:
                    print(f"Kiosk exited code={browser.returncode}; restarting kiosk", file=sys.stderr, flush=True)
                terminate(browser)
                browser = start_owned(["chromium", "--ozone-platform=wayland", "--no-first-run", "--noerrdialogs", "--disable-session-crashed-bubble", "--password-store=basic", "--kiosk", "--user-data-dir=" + str(DATA / "hub-browser"), "--app=http://127.0.0.1:8765"], env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
    finally:
        failures = []
        for child in (browser, api):
            try:
                terminate(child)
            except Exception as error:
                failures.append(error)
                print(f"Owned process cleanup failed: {error}", file=sys.stderr, flush=True)
        reap_adopted_children(api, browser)
        exit_request.unlink(missing_ok=True)
        if failures:
            raise failures[0]


if __name__ == "__main__":
    main()
