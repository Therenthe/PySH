import asyncio
import threading
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest
from services.backend.content import Content
from services.backend.app import play, Play

UUID = "9617a958-0601-11e8-ae97-52543be04c81"

@pytest.mark.parametrize("identifier", [None, "", "arbitrary", "../foo", "https://evil.example", "1"*64])
def test_invalid_identifiers_never_contact_catalog(tmp_path, monkeypatch, identifier):
    c=Content(tmp_path)
    monkeypatch.setattr(c,"_get_json",lambda *a,**k:pytest.fail("network"))
    assert asyncio.run(c.radio_click(identifier)) is False

def test_fixed_host_uuid_lowercase_timeout_and_response_url_ignored(tmp_path, monkeypatch):
    c=Content(tmp_path);c._radio_servers_discovered=("nl1.api.radio-browser.info",);calls=[]
    def response(url,**kw):
        calls.append((url,kw));return {"ok":"true","url":"file:///must-not-select"}
    monkeypatch.setattr(c,"_get_json",response)
    assert asyncio.run(c.radio_click(UUID.upper())) is True
    assert calls==[("https://nl1.api.radio-browser.info/json/url/"+UUID,{"headers":{"User-Agent":"PiSmartHub/1.0","Accept":"application/json"},"timeout":2.0})]

def test_unsafe_mirror_and_outage_do_not_raise(tmp_path, monkeypatch):
    c=Content(tmp_path);c._radio_servers_discovered=("api.radio-browser.info.evil.example",)
    monkeypatch.setattr(c,"_get_json",lambda *a,**k:pytest.fail("unsafe mirror"))
    assert asyncio.run(c.radio_click(UUID)) is False
    c._radio_servers_discovered=()
    monkeypatch.setattr(c,"_get_json",lambda *a,**k:(_ for _ in ()).throw(OSError("offline")))
    assert asyncio.run(c.radio_click(UUID)) is False

def test_async_deadline_does_not_wait_for_worker(tmp_path, monkeypatch):
    c=Content(tmp_path);released=threading.Event()
    def blocked(*a,**k):released.wait(5);return {"ok":"true"}
    monkeypatch.setattr(c,"_get_json",blocked)
    async def scenario():
        start=time.monotonic()
        try:
            assert await c.radio_click(UUID) is False
            assert time.monotonic()-start<2.8
        finally:released.set()
    asyncio.run(scenario())

@pytest.mark.parametrize("identifier,source,state,expected",[(UUID,"radio","playing",1),(None,"radio","playing",0),(UUID,"radio","error",0),(UUID,"local","playing",0)])
def test_signal_only_after_successful_explicit_catalog_start(tmp_path,identifier,source,state,expected):
    # Local playback records the actual file identity under the shared media
    # lock; keep this fixture consistent with Hub without starting hardware.
    (tmp_path / "fixture.wav").write_bytes(b"fixture media")
    queued=[]
    def background(coro):queued.append(coro);coro.close()
    stored=[]
    hub=SimpleNamespace(refresh_device=AsyncMock(),audio_selected=True,snapshots={"audio":{"output":"fixture"}},player=SimpleNamespace(select_output=AsyncMock(),play=AsyncMock(return_value={"state":state})),content=SimpleNamespace(resolve_media=Mock(return_value=tmp_path/"fixture.wav"),media_list=AsyncMock(return_value={"items":[]}),radio_click=AsyncMock()),store=SimpleNamespace(value=SimpleNamespace(lastStation=None),update=stored.append),cache_playback=lambda x:x,visualizer=SimpleNamespace(close=AsyncMock()),background=background)
    hub.media_lock = asyncio.Lock()
    hub.media_identity = None
    req=SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(hub=hub)))
    body=Play(source=source,url="https://radio.example.org/stream",path="fixture.wav",station_uuid=identifier)
    result=asyncio.run(play(req,body))
    assert result=={"state":state};assert len(queued)==expected
    hub.player.play.assert_awaited_once_with("https://radio.example.org/stream" if source=="radio" else str(tmp_path/"fixture.wav"),title="",kind=source)
    if expected:
        hub.content.radio_click.assert_called_once_with(UUID)
        assert stored[0]["lastStation"]["uuid"]==UUID
    else:hub.content.radio_click.assert_not_called()
