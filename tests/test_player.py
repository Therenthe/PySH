import asyncio
import json

import pytest

from services.backend.player import Player, PlayerError


class FakeProcess:
    returncode = None


class FakeWriter:
    def __init__(self, reader, values=None, error_for=None):
        self.reader = reader
        self.values = values or {}
        self.error_for = error_for

    def write(self, payload):
        request = json.loads(payload.decode("utf-8"))
        command = request["command"]
        error = "success"
        data = None
        if command[0] == "get_property":
            prop = command[1]
            if prop == self.error_for:
                error = "property unavailable"
            else:
                data = self.values.get(prop)
        self.reader.feed_data((json.dumps({"request_id": request["request_id"], "error": error, "data": data}) + "\n").encode())

    async def drain(self):
        return None

    def close(self):
        return None

    async def wait_closed(self):
        return None


def test_status_reads_actual_mpv_properties_and_maps_pause():
    async def scenario():
        player = Player()
        player._process = FakeProcess()
        player._reader = asyncio.StreamReader()
        player._writer = FakeWriter(player._reader, {
            "pause": True,
            "time-pos": 17.25,
            "duration": 180.0,
            "volume": 63.0,
            "mute": False,
            "media-title": "Actual stream title",
            "paused-for-cache": False,
            "idle-active": False,
        })
        player._url = "https://radio.example/live"
        player._title = "Saved station title"
        player._connecting = False
        state = await player.status()
        assert state["state"] == "paused"
        assert state["position"] == 17.25
        assert state["duration"] == 180
        assert state["volume"] == 63
        assert state["title"] == "Actual stream title"
        assert state["url"] == "https://radio.example/live"

    asyncio.run(scenario())


def test_unavailable_optional_ipc_property_does_not_break_status():
    async def scenario():
        player = Player()
        player._process = FakeProcess()
        player._reader = asyncio.StreamReader()
        player._url = "https://radio.example/live"
        player._writer = FakeWriter(player._reader, {"pause": False, "idle-active": False}, error_for="media-title")
        player._connecting = False
        state = await player.status()
        assert state["state"] == "playing"
        assert state["title"] == ""

    asyncio.run(scenario())


@pytest.mark.parametrize("metadata, expected", [
    ("128", "Radio Swiss Jazz"),
    ("https://radio.example/mp3/128", "Radio Swiss Jazz"),
    (None, "Radio Swiss Jazz"),
    ("Artist — Track", "Artist — Track"),
])
def test_radio_url_fallback_does_not_hide_station_but_keeps_broadcast_metadata(metadata, expected):
    async def scenario():
        player = Player()
        player._process = FakeProcess()
        player._reader = asyncio.StreamReader()
        player._writer = FakeWriter(player._reader, {"media-title": metadata, "idle-active": False})
        player._url = "https://radio.example/mp3/128"
        player._title = "Radio Swiss Jazz"
        assert (await player.status())["title"] == expected

    asyncio.run(scenario())


def test_unsupported_commands_and_invalid_ranges_have_stable_codes():
    async def scenario():
        player = Player()
        with pytest.raises(PlayerError) as unknown:
            await player.command("shell", "rm -rf")
        assert unknown.value.code == "invalid_command"
        with pytest.raises(PlayerError) as seek:
            await player.command("seek", -2)
        assert seek.value.code == "invalid_command"
        with pytest.raises(PlayerError) as volume:
            await player.command("volume", 101)
        assert volume.value.code == "invalid_command"

    asyncio.run(scenario())


def test_non_linux_player_reports_unavailable_instead_of_simulating(monkeypatch):
    async def scenario():
        monkeypatch.setattr("services.backend.player.sys.platform", "win32")
        player = Player()
        with pytest.raises(PlayerError) as error:
            await player.start()
        assert error.value.code == "player_unavailable"
        assert (await player.status())["state"] == "error"
        assert (await player.status())["error"] == "player_unavailable"

    asyncio.run(scenario())


def test_ipc_command_failure_is_reported():
    async def scenario():
        player = Player()
        player._reader = asyncio.StreamReader()
        player._writer = FakeWriter(player._reader)

        class FailingWriter(FakeWriter):
            def write(self, payload):
                request = json.loads(payload.decode())
                self.reader.feed_data((json.dumps({"request_id": request["request_id"], "error": "unsupported command"}) + "\n").encode())

        player._writer = FailingWriter(player._reader)
        with pytest.raises(PlayerError) as error:
            await player._command(["stop"])
        assert error.value.code == "playback_command_failed"

    asyncio.run(scenario())


def test_end_file_error_event_uses_mpv_nested_data_shape():
    player = Player()
    player._url = "https://radio.example/live"
    player._connecting = True
    player._handle_event({"event": "end-file", "data": {"reason": "error", "file_error": "network timeout"}})
    assert player._error == "stream_failed"
    assert player._connecting is False


def test_flat_ipc_error_survives_idle_properties_until_a_new_file_loads():
    async def scenario():
        player = Player()
        player._process = FakeProcess()
        player._reader = asyncio.StreamReader()
        player._writer = FakeWriter(player._reader, {"idle-active": True})
        player._url = "file:///tmp/invalid.mp3"
        player._reader.feed_data(b'{"event":"end-file","reason":"error","file_error":"unrecognized file format","playlist_entry_id":1}\n')
        state = await player.status()
        assert state["state"] == "error"
        assert state["error"] == "stream_failed"
        assert (await player.status())["state"] == "error"
        player._handle_event({"event": "file-loaded"})
        player._writer.values["idle-active"] = False
        assert (await player.status())["state"] == "playing"
        assert player._error is None

    asyncio.run(scenario())


def test_natural_end_is_visible_and_explicit_stop_clears_it():
    async def scenario():
        player = Player()
        player._process = FakeProcess()
        player._reader = asyncio.StreamReader()
        player._writer = FakeWriter(player._reader, {"idle-active": True})
        player._url = "file:///tmp/test.wav"
        player._handle_event({"event": "end-file", "reason": "eof"})
        assert (await player.status())["state"] == "ended"
        assert (await player.command("stop"))["state"] == "idle"
        assert player._url == ""

    asyncio.run(scenario())


def test_replacement_stop_event_does_not_clear_newly_selected_source():
    player = Player()
    player._url = "file:///tmp/new.wav"
    player._connecting = True
    player._handle_event({"event": "end-file", "reason": "stop", "playlist_entry_id":1})
    assert player._url == "file:///tmp/new.wav"
    assert player._connecting is True
