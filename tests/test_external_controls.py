from types import SimpleNamespace
from unittest.mock import AsyncMock
import asyncio
import pytest
from fastapi.testclient import TestClient
from services.backend.app import app, Hub
from services.backend.external_controls import controls_snapshot


def test_projection_is_bounded_and_excludes_private_owner_state():
    audio={'available':True,'ready':True,'volume':42,'mute':False,'output':'speaker',
        'password':'do-not-return','outputs':[{'id':'speaker','description':'Speaker','address':'private-address'}]*60}
    value=controls_snapshot(audio,{'brightness':{'available':True,'value':70},'daily':{'time':'private-time'}},{'language':'ro','theme':'night'})
    assert value=={'language':'ro','theme':'night','busy':False,
        'audio':{'available':True,'ready':True,'volume':42,'mute':False,'outputs':[{'id':'speaker','label':'Speaker','active':True}]},
        'brightness':{'available':True,'value':70}}
    assert 'private' not in str(value) and 'password' not in str(value)
    audio['outputs']=[{'id':str(index),'description':'X'*500}for index in range(60)]
    bounded=controls_snapshot(audio,{}, {'language':'en','theme':'ink'})
    assert len(bounded['audio']['outputs'])==32
    assert all(len(item['label'])==300 for item in bounded['audio']['outputs'])


def test_projection_does_not_invent_numeric_or_device_state():
    value=controls_snapshot({'available':1,'volume':True,'mute':'false','outputs':{}},
        {'brightness':{'available':True,'value':False}},{'language':'en','theme':'ink'},busy=True)
    assert value['busy'] and not value['audio']['available']
    assert value['audio']['volume'] is None and value['audio']['mute'] is None
    assert value['audio']['outputs']==[] and value['brightness']['value'] is None


def test_controls_route_keeps_loopback_origin_boundary_and_reports_pending(tmp_path):
    hub=Hub(tmp_path);app.state.hub=hub
    hub.snapshots['audio']={'available':True,'ready':True,'volume':40,'mute':False,'outputs':[]}
    hub.power.snapshot=AsyncMock(return_value={'brightness':{'available':True,'value':80}})
    hub._visualizer_suspended=1
    client=TestClient(app,base_url='http://127.0.0.1:8765')
    response=client.get('/api/external/controls')
    assert response.status_code==200 and response.json()['busy'] is True
    assert set(response.json())=={'language','theme','busy','audio','brightness'}
    assert 'preferences' not in response.json() and 'network' not in response.json()
    assert client.get('/api/external/controls',headers={'Origin':'https://www.youtube.com'}).status_code==403
    assert client.get('/api/external/controls',headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
