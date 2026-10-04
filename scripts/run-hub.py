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
    child._pysh_owned_members = session_snapshot(child.pid)
    child._pysh_owned_generation = child._pysh_owned_members.get(child.pid, {}).get("generation")
    return child


def session_snapshot(sid):
    """Capture kernel PID generations and groups within one Linux session."""
    members = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rpartition(")")[2].split()
            if int(fields[3]) == sid:
                # proc inode ownership can become root for nondumpable/zombie
                # tasks. The task's real UID remains in status; inode UID is not
                # part of a PID generation and must not prevent zombie reaping.
                status = (path.parent / "status").read_text()
                uid = int(next(line for line in status.splitlines() if line.startswith("Uid:")).split()[1])
                members[int(path.parent.name)] = {"generation": (int(fields[19]), uid),
                                                   "ppid": int(fields[1]), "pgid": int(fields[2])}
        except (OSError, ValueError, IndexError, StopIteration):
            pass
    return members


def owned_session_members(child):
    current = session_snapshot(child.pid)
    recorded = getattr(child, "_pysh_owned_members", {})
    generation = getattr(child, "_pysh_owned_generation", None)
    if not generation:
        return {}
    if child.pid in current and current[child.pid]["generation"] != generation:
        return {}  # The numeric session leader PID has been reused.
    proven = any(value["generation"] == current.get(pid, {}).get("generation") for pid, value in recorded.items())
    if not proven and child.pid not in current:
        # A dead worker's live children are adopted by this subreaper. Independent
        # sessions cannot acquire this parent relationship merely by PID reuse.
        proven = any(value["ppid"] == os.getpid() and value["generation"][1] == generation[1]
                     and value["generation"][0] >= generation[0] for value in current.values())
    if not proven:
        return {}
    recorded.update(current)
    child._pysh_owned_members = recorded
    return current


def terminate(child, grace=5, kill_grace=2):
    """Clean all groups in our session, including a crashed API's service browser."""
    if child is None or getattr(child, "_pysh_owned_cleaned", False):
        return
    pgid = getattr(child, "_pysh_owned_pgid", None)
    if pgid != child.pid:
        raise ValueError("Refusing to signal a process group we did not create")

    def reap():
        # Popen owns its direct child's return code; only reap descendants after it.
        if child.poll() is not None:
            groups = {value["pgid"] for value in owned_session_members(child).values()}
            for group in groups:
                while True:
                    try:
                        pid, _ = os.waitpid(-group, os.WNOHANG)
                        if pid == 0:
                            break
                    except ChildProcessError:
                        break

    def exists():
        reap()
        return bool(owned_session_members(child))

    def signal_group(sig):
        groups = {value["pgid"] for value in owned_session_members(child).values()}
        for group in groups:
            try:
                os.killpg(group, sig)
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
                browser = start_owned(["chromium", "--ozone-platform=wayland", "--no-first-run", "--disable-features=Translate", "--noerrdialogs", "--disable-session-crashed-bubble", "--password-store=basic", "--kiosk", "--user-data-dir=" + str(DATA / "hub-browser"), "--app=http://127.0.0.1:8765"], env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
