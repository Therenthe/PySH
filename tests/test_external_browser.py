"""Real preparation state transitions, subprocess ownership and CDM path boundary."""
import asyncio
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

from services.backend import external


class Process:
    def __init__(self, pid):
        self.pid = pid
        self.returncode = None
        self.waits = 0
        self.group_live = True

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9
        self.group_live = False

    async def wait(self):
        self.waits += 1
        return self.returncode


@pytest.fixture
def launches(monkeypatch):
    items, signals = [], []
    async def spawn(*args, **kwargs):
        assert not any(process.returncode is None for _, _, process in items), "Previous owned browser remains live"
        process = Process(9000000 + len(items))
        items.append((args, kwargs, process))
        return process
    def killpg(pid, number):
        signals.append((pid, number))
        process = next(process for _, _, process in items if process.pid == pid)
        process.returncode = -number
        if number == 9:
            process.group_live = False
    def snapshot(pgid):
        return {process.pid: (process.pid, 1000) for _, _, process in items if process.pid == pgid and process.group_live}
    monkeypatch.setattr(external.asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(external.os, "killpg", killpg, raising=False)
    monkeypatch.setattr(external, "_group_snapshot", snapshot)
    return items, signals


def manager(tmp_path, **kwargs):
    return external.ExternalBrowser(tmp_path, tmp_path / "extension", poll_interval=.01, **kwargs)


def component(browser, version="4.10.3057.0"):
    root = browser.profile / "WidevineCdm"
    target = root / version
    library = target / "_platform_specific/linux_arm64/libwidevinecdm.so"
    library.parent.mkdir(parents=True)
    library.write_bytes(b"owned-CDM-fixture")
    (target / "manifest.json").write_text(json.dumps({"version": version}))
    (root / "latest-component-updated-widevine-cdm").write_text(json.dumps({"Path": str(target.resolve())}))
    return target


async def wait_state(browser, job, wanted):
    for _ in range(100):
        status = await browser.status(job)
        if status["state"] == wanted:
            return status
        await asyncio.sleep(.01)
    raise AssertionError(f"Did not reach {wanted}: {status}")


def test_direct_youtube_and_browser_ownership(tmp_path, launches):
    async def scenario():
        browser = manager(tmp_path)
        result = await browser.start("youtube", "/usr/bin/chromium")
        assert result["opened"] and not result["preparing"] and browser.running
        assert (await browser.status(result["jobId"]))["state"] == "opened"
        args, kwargs, process = launches[0][0]
        assert args[-1] == "--app=https://www.youtube.com"
        assert kwargs.get("process_group") == 0 if sys.platform == "linux" else kwargs["start_new_session"] is True
        assert kwargs["stdin"] == kwargs["stdout"] == kwargs["stderr"] == asyncio.subprocess.DEVNULL
        await browser.close()
        assert not browser.running and process.waits == 1
    asyncio.run(scenario())


def test_ready_requires_actual_probe_not_component(tmp_path, launches):
    async def scenario():
        browser = manager(tmp_path)
        component(browser)
        result = await browser.start("netflix", "chromium", "ro", "night")
        assert result["preparing"] and not result["opened"]
        status = await browser.status(result["jobId"])
        assert status["state"] == "checking" and "url" not in status
        assert status["language"] == "ro" and status["theme"] == "night"
        assert "service-prepare?job=" in launches[0][0][0][-1]
        status = await browser.report(result["jobId"], status["attempt"], True)
        assert status["state"] == "ready" and status["url"] == "https://www.netflix.com"
        assert len(launches[0]) == 1
        await browser.close()
    asyncio.run(scenario())


def test_component_arrival_restarts_once_then_requires_new_probe(tmp_path, launches):
    async def scenario():
        browser = manager(tmp_path)
        result = await browser.start("spotify", "chromium")
        first = await browser.status(result["jobId"])
        await browser.report(result["jobId"], first["attempt"], False)
        component(browser)
        second = await wait_state(browser, result["jobId"], "checking")
        assert second["attempt"] != first["attempt"] and "url" not in second
        assert len(launches[0]) == 2 and launches[0][0][2].waits == 1
        with pytest.raises(external.ExternalError, match="stale_preparation"):
            await browser.report(result["jobId"], first["attempt"], True)
        failed = await browser.report(result["jobId"], second["attempt"], False)
        assert failed["error"] == "protected_playback_unavailable"
        await asyncio.sleep(.03)
        assert len(launches[0]) == 2
        retry = await browser.retry(result["jobId"])
        assert retry["state"] == "checking"
        ready = await browser.report(result["jobId"], retry["attempt"], True)
        assert ready["url"] == "https://open.spotify.com"
        await browser.close()
    asyncio.run(scenario())


def test_timeout_retry_keeps_browser_alive_and_cancel_invalidates(tmp_path, launches):
    async def scenario():
        browser = manager(tmp_path, timeout=.02)
        result = await browser.start("netflix", "chromium")
        first = await browser.status(result["jobId"])
        await browser.report(result["jobId"], first["attempt"], False)
        timed_out = await wait_state(browser, result["jobId"], "error")
        assert timed_out["error"] == "protected_playback_timeout" and browser.running
        assert not launches[0][0][2].waits
        retried = await browser.retry(result["jobId"])
        assert retried["attempt"] == first["attempt"] and retried["state"] == "checking"
        assert (await browser.cancel(result["jobId"]))["state"] == "cancelled"
        assert not browser.running
        with pytest.raises(external.ExternalError, match="stale_preparation"):
            await browser.report(result["jobId"], first["attempt"], True)
        await browser.close()
    asyncio.run(scenario())


def test_duplicate_start_serialized_while_spawn_is_blocked(tmp_path, launches, monkeypatch):
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        original = external.asyncio.create_subprocess_exec
        async def blocked(*args, **kwargs):
            entered.set()
            await release.wait()
            return await original(*args, **kwargs)
        monkeypatch.setattr(external.asyncio, "create_subprocess_exec", blocked)
        browser = manager(tmp_path)
        first = asyncio.create_task(browser.start("netflix", "chromium"))
        await entered.wait()
        duplicate = asyncio.create_task(browser.start("spotify", "chromium"))
        await asyncio.sleep(0)
        assert not duplicate.done()
        release.set()
        await first
        with pytest.raises(external.ExternalError, match="service_already_open"):
            await duplicate
        assert len(launches[0]) == 1
        await browser.close()
    asyncio.run(scenario())


def test_cancel_during_restart_closes_new_owned_browser(tmp_path, launches, monkeypatch):
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        original = external.asyncio.create_subprocess_exec
        async def blocked_restart(*args, **kwargs):
            if len(launches[0]) == 1:
                entered.set()
                await release.wait()
            return await original(*args, **kwargs)
        monkeypatch.setattr(external.asyncio, "create_subprocess_exec", blocked_restart)
        browser = manager(tmp_path)
        result = await browser.start("netflix", "chromium")
        initial = await browser.status(result["jobId"])
        component(browser)
        await browser.report(result["jobId"], initial["attempt"], False)
        await asyncio.wait_for(entered.wait(), 1)
        cancel = asyncio.create_task(browser.cancel(result["jobId"]))
        await asyncio.sleep(0)
        assert not cancel.done()
        release.set()
        assert (await cancel)["state"] == "cancelled"
        assert len(launches[0]) == 2 and all(item[2].waits for item in launches[0])
        assert not browser.running
        await browser.close()
    asyncio.run(scenario())


def test_browser_close_and_bad_inputs_are_sanitized(tmp_path, launches, monkeypatch):
    async def scenario():
        browser = manager(tmp_path)
        with pytest.raises(external.ExternalError, match="invalid_request"):
            await browser.start("arbitrary", "chromium")
        result = await browser.start("netflix", "chromium")
        status = await browser.status(result["jobId"])
        with pytest.raises(external.ExternalError, match="invalid_request"):
            await browser.report(result["jobId"], status["attempt"], "true")
        launches[0][0][2].returncode = 1
        assert (await browser.status(result["jobId"]))["error"] == "browser_closed"
        await browser.close()
        async def failed(*args, **kwargs):
            raise OSError("do_not_expose_private_detail")
        monkeypatch.setattr(external.asyncio, "create_subprocess_exec", failed)
        with pytest.raises(external.ExternalError, match="^browser_unavailable$"):
            await browser.start("netflix", "chromium")
        await browser.close()
    asyncio.run(scenario())


def test_stop_escalates_and_reaps_owned_browser(tmp_path, launches):
    async def scenario():
        browser = manager(tmp_path)
        await browser.start("youtube", "chromium")
        process = launches[0][0][2]
        async def stuck_wait():
            process.waits += 1
            if process.waits == 1:
                raise asyncio.TimeoutError
            return process.returncode
        process.wait = stuck_wait
        await browser.close()
        assert process.waits == 2 and process.returncode == -9
        assert not browser.running
    asyncio.run(scenario())


def test_reused_dead_leader_group_never_signalled(tmp_path, launches, monkeypatch):
    async def scenario():
        monkeypatch.setattr(external.sys, "platform", "linux")
        browser = manager(tmp_path)
        await browser.start("youtube", "chromium")
        process = launches[0][0][2]
        process.returncode = 0
        monkeypatch.setattr(external, "_group_snapshot", lambda pgid: {pgid: (pgid + 1, 1000)})
        await browser.close()
        assert launches[1] == []
        assert process.waits == 1 and process.returncode == 0
    asyncio.run(scenario())


def test_group_generation_uses_task_uid_not_proc_inode_owner(tmp_path, monkeypatch):
    directory = tmp_path / "12345"
    directory.mkdir()
    fields = ["0"] * 20
    fields[0], fields[1], fields[2], fields[3], fields[19] = "Z", "88", "333", "333", "777"
    path = directory / "stat"
    path.write_text("12345 (owned zombie) " + " ".join(fields))
    (directory / "status").write_text("Name:\towned\nUid:\t1001\t1001\t1001\t1001\n")
    class StatFile:
        parent = directory
        def read_text(self):
            return path.read_text()
        def stat(self):
            raise AssertionError("A root-owned proc inode is not task identity")
    root = Mock()
    root.glob.return_value = [StatFile()]
    monkeypatch.setattr(external, "Path", lambda argument: root)
    assert external._group_snapshot(333) == {12345: (777, 1001)}


@pytest.mark.parametrize("corruption", ["bad_hint", "oversized", "relative", "outside", "wrong_version", "empty_library"])
def test_component_hint_boundary(tmp_path, corruption):
    browser = manager(tmp_path)
    target = component(browser)
    root = target.parent
    hint = root / "latest-component-updated-widevine-cdm"
    if corruption == "bad_hint":
        hint.write_text("[]")
    elif corruption == "oversized":
        hint.write_text(" " * 16385)
    elif corruption == "relative":
        hint.write_text(json.dumps({"Path": "WidevineCdm/4.10.3057.0"}))
    elif corruption == "outside":
        hint.write_text(json.dumps({"Path": str((tmp_path / "elsewhere/4.10.3057.0").resolve())}))
    elif corruption == "wrong_version":
        (target / "manifest.json").write_text('{"version":"1.0.0.0"}')
    else:
        (target / "_platform_specific/linux_arm64/libwidevinecdm.so").write_bytes(b"")
    assert browser._component() is None


@pytest.mark.parametrize("part", ["root", "manifest", "library", "profile"])
def test_rejects_symlink_escape(tmp_path, part):
    browser = manager(tmp_path)
    target = component(browser)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        if part in {"root", "profile"}:
            path = target.parent if part == "root" else browser.profile
            renamed = path.with_name(path.name + "-original")
            path.rename(renamed)
            path.symlink_to(outside, target_is_directory=True)
        else:
            path = target / ("manifest.json" if part == "manifest" else "_platform_specific/linux_arm64/libwidevinecdm.so")
            destination = outside / path.name
            destination.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(destination)
    except OSError:
        pytest.skip("Symlink creation unavailable on this host")
    assert browser._component() is None


@pytest.mark.skipif(sys.platform != "linux", reason="Real owned Linux process group")
def test_real_owned_group_stops_stubborn_descendant(tmp_path):
    async def scenario():
        child_ready = tmp_path / "child-ready"
        child_code = "import os,signal,time\nfrom pathlib import Path\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\nPath(" + repr(str(child_ready)) + ").write_text(str(os.getpid()))\ntime.sleep(60)\n"
        child_script = tmp_path / "child.py"
        child_script.write_text(child_code)
        executable = tmp_path / "owned-browser"
        executable.write_text("#!" + sys.executable + "\nimport subprocess,sys,time\nsubprocess.Popen([sys.executable," + repr(str(child_script)) + "])\ntime.sleep(60)\n")
        executable.chmod(0o700)
        browser = manager(tmp_path)
        try:
            await browser.start("youtube", str(executable))
            for _ in range(200):
                if child_ready.exists():
                    break
                await asyncio.sleep(.01)
            assert child_ready.exists()
            child_pid = int(child_ready.read_text())
            await browser.close()
            for _ in range(100):
                path = Path(f"/proc/{child_pid}/stat")
                if not path.exists() or path.read_text().split(") ", 1)[1].split()[0] == "Z":
                    break
                await asyncio.sleep(.01)
            else:
                raise AssertionError("Owned descendant survived browser close")
            assert not browser.running
        finally:
            await browser.close()
    asyncio.run(scenario())
