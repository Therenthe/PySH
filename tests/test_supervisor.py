"""Real Linux process trees, including descendants whose API parent has died."""
import ctypes
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux session/process-group supervisor")


@pytest.fixture(scope="module")
def supervisor():
    source = Path(os.environ.get("PYSH_SUPERVISOR_UNDER_TEST", str(Path(__file__).resolve().parents[1] / "scripts/run-hub.py")))
    spec = importlib.util.spec_from_file_location("pysh_supervisor_under_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    libc = ctypes.CDLL(None, use_errno=True)
    previous = ctypes.c_int()
    assert libc.prctl(37, ctypes.byref(previous), 0, 0, 0) == 0  # PR_GET_CHILD_SUBREAPER
    module.enable_child_reaping()
    try:
        yield module
    finally:
        assert libc.prctl(36, previous.value, 0, 0, 0) == 0


def wait_for_file(path):
    deadline = time.monotonic() + 5
    while not path.exists():
        assert time.monotonic() < deadline, "child did not become ready"
        time.sleep(.02)
    return int(path.read_text())


def assert_gone(pid):
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def spawn_tree(supervisor, tmp_path, *, parent_exits, stubborn):
    ready = tmp_path / "descendant.pid"
    descendant = "import os,signal,time; from pathlib import Path; "
    if stubborn:
        descendant += "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    descendant += f"Path({str(ready)!r}).write_text(str(os.getpid())); time.sleep(60)"
    parent = f"import subprocess,sys,time,os; from pathlib import Path; subprocess.Popen([sys.executable,'-c',{descendant!r}]); "
    parent += f"ready=Path({str(ready)!r}); "
    parent += "exec('while not ready.exists(): time.sleep(.01)'); "
    parent += "os._exit(23)" if parent_exits else "time.sleep(60)"
    worker = supervisor.start_owned([sys.executable, "-c", parent])
    descendant_pid = wait_for_file(ready)
    return worker, descendant_pid


def test_dead_api_parent_orphan_is_killed_and_reaped(supervisor, tmp_path):
    worker, descendant = spawn_tree(supervisor, tmp_path, parent_exits=True, stubborn=True)
    try:
        assert worker.wait(timeout=5) == 23
        assert os.getpgid(descendant) == worker.pid
        started = time.monotonic()
        supervisor.terminate(worker, grace=.15, kill_grace=2)
        assert time.monotonic() - started < 3
        assert_gone(descendant)
        assert worker.returncode == 23
        supervisor.terminate(worker, grace=.15)  # already cleaned, no historical list required
    finally:
        supervisor.terminate(worker, grace=.15)


def test_live_api_and_descendant_are_stopped(supervisor, tmp_path):
    worker, descendant = spawn_tree(supervisor, tmp_path, parent_exits=False, stubborn=False)
    try:
        assert os.getpgid(worker.pid) == worker.pid
        assert os.getpgid(descendant) == worker.pid
        supervisor.terminate(worker, grace=1)
        assert worker.returncode is not None
        assert_gone(descendant)
        assert_gone(worker.pid)
    finally:
        supervisor.terminate(worker, grace=.15)


def test_cleanup_never_signals_an_unowned_or_unrelated_group(supervisor):
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
    owned = supervisor.start_owned([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        with pytest.raises(ValueError, match="did not create"):
            supervisor.terminate(unrelated, grace=.15)
        assert unrelated.poll() is None
        supervisor.terminate(owned, grace=1)
        assert unrelated.poll() is None
    finally:
        supervisor.terminate(owned, grace=.15)
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_already_cleaned_handle_cannot_signal_a_reused_group(supervisor, monkeypatch):
    worker = supervisor.start_owned([sys.executable, "-c", "import time; time.sleep(60)"])
    supervisor.terminate(worker, grace=1)
    def forbidden(*args):
        raise AssertionError("An already cleaned group must never be signalled again")
    monkeypatch.setattr(os, "killpg", forbidden)
    supervisor.terminate(worker)
