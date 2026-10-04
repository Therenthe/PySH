import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from services.backend.app import app,Hub
from services.backend import app as module
from services.backend.external import DOCUMENT_URLS
from tests.test_external_browser import launches,manager

@pytest.fixture
def client(tmp_path,monkeypatch):
 hub=Hub(tmp_path);hub.player=SimpleNamespace(status=AsyncMock(return_value={'state':'playing','kind':'radio'}),command=AsyncMock());hub.visualizer=SimpleNamespace(close=AsyncMock());hub.external=SimpleNamespace(start=AsyncMock(return_value={'opened':True,'preparing':False}));hub.cache_playback=AsyncMock();app.state.hub=hub
 monkeypatch.setattr(module.sys,'platform','linux');monkeypatch.setattr(module.shutil,'which',lambda _: '/fixture/chromium')
 return TestClient(app,base_url='http://127.0.0.1:8765')

@pytest.mark.parametrize('provider',['open-meteo','cc-by'])
def test_documentation_does_not_interrupt_audio_or_preferences(client,provider):
 hub=app.state.hub;before=hub.store.export();r=client.post('/api/documentation',headers={'X-Hub-Token':hub.token},json={'provider':provider})
 assert r.status_code==200
 hub.external.start.assert_awaited_once_with(provider,'/fixture/chromium',before['language'],before['theme'])
 hub.player.command.assert_not_awaited();hub.visualizer.close.assert_not_awaited();hub.cache_playback.assert_not_called();assert hub.store.export()==before

@pytest.mark.parametrize('body',[{'provider':'https://evil.example'},{'provider':'open-meteo','url':'https://evil.example'},{'provider':'cc-by','path':'/other'},{'provider':'netflix'},{}])
def test_documentation_rejects_arbitrary_destinations(client,body):
 hub=app.state.hub;assert client.post('/api/documentation',headers={'X-Hub-Token':hub.token},json=body).status_code==422;hub.external.start.assert_not_awaited()

@pytest.mark.parametrize('provider',['open-meteo','cc-by'])
def test_documentation_plain_owned_spawn_and_existing_window_lock(tmp_path,launches,provider):
 async def run():
  browser=manager(tmp_path);r=await browser.start(provider,'chromium');assert r['opened'] and not r['preparing'];args=launches[0][0][0];assert not any('service-prepare' in x for x in args);assert '--app='+DOCUMENT_URLS[provider] in args
  from services.backend.external import ExternalError
  with pytest.raises(ExternalError,match='service_already_open'):await browser.start('youtube','chromium')
  await browser.close()
 asyncio.run(run())
