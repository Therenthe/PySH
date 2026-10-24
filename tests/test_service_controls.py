import importlib.util
import io
import json
from pathlib import Path
import struct
from unittest.mock import MagicMock,Mock
import pytest


@pytest.fixture
def host():
    spec=importlib.util.spec_from_file_location('service_controls',Path(__file__).resolve().parents[1]/'scripts/service-keyboard-host.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def framed(value):
    raw=json.dumps(value).encode();return io.BytesIO(struct.pack('<I',len(raw))+raw)


def snapshot(**extra):
    return {'language':'en','theme':'ink','busy':False,
        'audio':{'available':True,'ready':True,'volume':40,'mute':False,'outputs':[{'id':'speaker','label':'Speaker','active':True}]},
        'brightness':{'available':True,'value':80},**extra}


@pytest.mark.parametrize('message',[{'action':'controls-status'},
    {'action':'controls-volume','value':0},{'action':'controls-volume','value':100},
    {'action':'controls-mute','value':False},{'action':'controls-brightness','value':1},
    {'action':'controls-output','value':'speaker'}])
def test_only_typed_bounded_control_messages(host,message):
    assert host.read_message(framed(message))==message


@pytest.mark.parametrize('message',[{'action':'controls-status','value':0},
    {'action':'controls-volume','value':True},{'action':'controls-volume','value':40.5},
    {'action':'controls-volume','value':101},{'action':'controls-brightness','value':0},
    {'action':'controls-mute','value':1},{'action':'controls-output','value':''},
    {'action':'controls-output','value':'speaker\x00bad'},
    {'action':'controls-output','value':'x'*201},
    {'action':'controls-volume','value':50,'url':'https://outside.invalid'},
    {'action':'controls-shell','value':'/bin/sh'}])
def test_rejects_unsafe_or_ambiguous_messages(host,message):
    with pytest.raises(host.ProtocolError):host.read_message(framed(message))


def test_control_snapshot_rebuilds_fields_instead_of_forwarding_payload(host,monkeypatch):
    raw=snapshot(token='private-token',preferences={'secret':'private'},network={'ssid':'private'})
    raw['audio']['password']='private';raw['audio']['outputs'][0]['address']='private'
    monkeypatch.setattr(host,'owner_json',lambda path:raw)
    result=host.control('controls-status')
    assert result=={'ok':True,'controls':snapshot()}
    assert 'private' not in json.dumps(result)


def test_output_must_be_in_the_actual_current_snapshot(host,monkeypatch):
    calls=[]
    def owner(path,*args):calls.append((path,args));return snapshot()
    monkeypatch.setattr(host,'owner_json',owner)
    result=host.control('controls-output','/tmp/arbitrary-path')
    assert result['ok'] is False and result['definite'] is True
    assert calls==[('/api/external/controls',())]


def test_busy_owner_does_not_receive_another_write(host,monkeypatch):
    calls=[]
    monkeypatch.setattr(host,'owner_json',lambda path,*args:calls.append((path,args)) or snapshot(busy=True))
    assert host.control('controls-volume',60)['error']=='controls_busy'
    assert len(calls)==1


def test_accepted_write_lost_readback_is_verified_without_replaying(host,monkeypatch):
    calls=[];reads=0
    def owner(path,body=None,method='GET'):
        nonlocal reads
        calls.append((path,body,method))
        if path=='/api/audio':return {'available':True}
        reads+=1
        if reads==2:raise OSError('private readback error')
        value=snapshot();value['audio']['volume']=60 if reads>2 else 40;return value
    monkeypatch.setattr(host,'owner_json',owner)
    assert host.control('controls-volume',60)=={'ok':False,'error':'controls_unverified','uncertain':True}
    assert host.control('controls-status')['controls']['audio']['volume']==60
    assert [entry for entry in calls if entry[2]!='GET']==[('/api/audio',{'volume':60},'POST')]


def test_brightness_uses_only_fixed_preferences_field_and_requires_readback(host,monkeypatch):
    calls=[]
    def owner(path,body=None,method='GET'):
        calls.append((path,body,method));value=snapshot()
        if len(calls)>2:value['brightness']['value']=25
        return value
    monkeypatch.setattr(host,'owner_json',owner)
    assert host.control('controls-brightness',25)['ok']
    assert calls[1]==('/api/preferences',{'screenBrightness':25},'PATCH')


def test_owner_token_never_leaves_fixed_loopback_request(host,monkeypatch):
    session=MagicMock();session.__enter__.return_value.read.return_value=b'{"token":"private-fixture-token"}'
    reply=MagicMock();reply.__enter__.return_value.read.return_value=b'{"ok":true}'
    opener=Mock();opener.open.side_effect=[session,reply]
    monkeypatch.setattr(host.urllib.request,'build_opener',Mock(return_value=opener))
    assert host.owner_json('/api/audio',{'mute':True},'POST')=={'ok':True}
    requests=[call.args[0]for call in opener.open.call_args_list]
    assert [item.full_url for item in requests]==['http://127.0.0.1:8765/api/session','http://127.0.0.1:8765/api/audio']
    assert requests[1].get_header('X-hub-token')=='private-fixture-token'
    assert requests[1].get_header('Origin')=='http://127.0.0.1:8765'
    assert json.loads(requests[1].data)=={'mute':True}


@pytest.mark.parametrize('status',[408,409,429,500])
def test_integration_or_ambiguous_http_failure_requires_state_verification(host,monkeypatch,status):
    writes=[]
    def owner(path,body=None,method='GET'):
        if method!='GET':
            writes.append(body)
            raise host.urllib.error.HTTPError('http://127.0.0.1:8765'+path,status,'integration result',{},None)
        return snapshot()
    monkeypatch.setattr(host,'owner_json',owner)
    assert host.control('controls-brightness',25)=={'ok':False,'error':'controls_unverified','uncertain':True}
    assert writes==[{'screenBrightness':25}]


@pytest.mark.parametrize('status',[403,413,422])
def test_known_prewrite_http_rejection_can_be_retried_without_readback(host,monkeypatch,status):
    def owner(path,body=None,method='GET'):
        if method!='GET':raise host.urllib.error.HTTPError('http://127.0.0.1:8765'+path,status,'rejected',{},None)
        return snapshot()
    monkeypatch.setattr(host,'owner_json',owner)
    assert host.control('controls-brightness',25)['definite'] is True
