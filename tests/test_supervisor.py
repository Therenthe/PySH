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


def test_dead_api_external_group_in_owned_session_is_stopped(supervisor, tmp_path):
    ready = tmp_path / "external-group.pid"
    external_code = (
        "import os,signal,time; from pathlib import Path; "
        "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        f"Path({str(ready)!r}).write_text(str(os.getpid())); time.sleep(60)"
    )
    api_code = (
        "import subprocess,sys,time,os; from pathlib import Path; "
        f"subprocess.Popen([sys.executable,'-c',{external_code!r}], process_group=0); "
        f"ready=Path({str(ready)!r}); "
        "exec('while not ready.exists(): time.sleep(.01)'); os._exit(23)"
    )
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
    worker = supervisor.start_owned([sys.executable, "-c", api_code])
    descendant = wait_for_file(ready)
    try:
        assert worker.wait(timeout=5) == 23
        assert os.getpgid(descendant) == descendant
        assert os.getsid(descendant) == worker.pid
        supervisor.terminate(worker, grace=.15, kill_grace=2)
        assert_gone(descendant)
        assert unrelated.poll() is None
    finally:
        supervisor.terminate(worker, grace=.15)
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_reused_session_id_never_signalled(supervisor, monkeypatch):
    worker = supervisor.start_owned([sys.executable, "-c", "import time; time.sleep(60)"])
    supervisor.terminate(worker, grace=1)
    worker._pysh_owned_cleaned = False  # Test the generation guard, not the cleaned shortcut.
    original = worker._pysh_owned_generation
    monkeypatch.setattr(supervisor, "session_snapshot", lambda sid: {sid: {"generation": (original[0] + 1, original[1]), "ppid": os.getpid(), "pgid": sid}})
    def forbidden(*args):
        raise AssertionError("Reused session ID must never be signalled")
    monkeypatch.setattr(os, "killpg", forbidden)
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


def wait_for_zombie(pid, *, parent=None):
    deadline = time.monotonic() + 5
    while True:
        state = Path(f"/proc/{pid}/stat").read_text().rpartition(")")[2].split()
        if state[0] == "Z" and (parent is None or int(state[1]) == parent):
            return
        assert time.monotonic() < deadline, "process did not become an adopted zombie"
        time.sleep(.02)


def test_detached_adopted_zombie_reaped_without_stealing_leader_exit(supervisor, tmp_path):
    ready = tmp_path / "detached.pid"
    release = tmp_path / "release-detached"
    detached_code = (
        "import os,time; from pathlib import Path; "
        f"Path({str(ready)!r}).write_text(str(os.getpid())); "
        f"release=Path({str(release)!r}); "
        "exec('while not release.exists(): time.sleep(.01)'); os._exit(17)"
    )
    parent_code = (
        "import subprocess,sys,time,os; from pathlib import Path; "
        f"subprocess.Popen([sys.executable,'-c',{detached_code!r}], start_new_session=True); "
        f"ready=Path({str(ready)!r}); "
        "exec('while not ready.exists(): time.sleep(.01)'); os._exit(23)"
    )
    parent = supervisor.start_owned([sys.executable, "-c", parent_code])
    leader = supervisor.start_owned([sys.executable, "-c", "import os; os._exit(31)"])
    detached = None
    try:
        detached = wait_for_file(ready)
        assert parent.wait(timeout=5) == 23
        assert os.getpgid(detached) == detached  # Outside its original worker's group.
        release.touch()
        wait_for_zombie(detached, parent=os.getpid())
        wait_for_zombie(leader.pid, parent=os.getpid())
        assert leader.returncode is None  # Popen has not collected the exit status yet.
        assert supervisor.reap_adopted_children(parent, leader) >= 1
        assert_gone(detached)
        assert leader.returncode is None
        assert leader.wait(timeout=1) == 31
        assert parent.returncode == 23
    finally:
        release.touch()
        supervisor.terminate(parent, grace=.15)
        supervisor.terminate(leader, grace=.15)
        if detached is not None:
            try:
                os.kill(detached, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(detached, 0)
            except ChildProcessError:
                pass
