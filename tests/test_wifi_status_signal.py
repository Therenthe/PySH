"""Network state uses only genuine radio/active-AP metadata, never a neighbour."""
import asyncio
from types import SimpleNamespace

import pytest

from services.backend.device import Device, NM_PATH, NM_SETTINGS_PATH, NM_DEVICE, NM_AP


MISSING=object()


def fixture(monkeypatch, *, strength=MISSING, active='/ap/active', enabled=MISSING):
    device=Device()
    device._linux,device._bus=True,object()
    reads=[]
    async def get_state():return 70
    async def get_primary_connection():return '/'
    async def get_active_connections():return []
    async def get_devices():return ['/device/wired','/device/wifi']
    async def list_connections():return []
    async def get_active_access_point():return active
    async def get_wireless_enabled():
        if isinstance(enabled,Exception):raise enabled
        return enabled
    manager=SimpleNamespace(get_state=get_state,get_primary_connection=get_primary_connection,
        get_active_connections=get_active_connections,call_get_devices=get_devices)
    if enabled is not MISSING:
        manager.get_wireless_enabled=get_wireless_enabled
    async def proxy(service,path,interface):
        if path==NM_PATH:return manager
        if path==NM_SETTINGS_PATH:return SimpleNamespace(call_list_connections=list_connections)
        assert path=='/device/wifi'
        return SimpleNamespace(get_active_access_point=get_active_access_point)
    async def props(service,path,interface):
        reads.append((path,interface))
        if path=='/device/wired':return {'DeviceType':1,'Interface':'end0','State':100}
        if path=='/device/wifi':return {'DeviceType':2,'Interface':'wlan0','State':100 if active!='/' else 30}
        assert path=='/ap/active' and interface==NM_AP
        data={'Ssid':list(b'Current network')}
        if strength is not MISSING:data['Strength']=strength
        return data
    monkeypatch.setattr(device,'_proxy',proxy)
    monkeypatch.setattr(device,'_props',props)
    return device,reads


@pytest.mark.parametrize('strength',[0,1,50,100])
def test_active_ap_strength_and_ssid_come_from_one_existing_read(monkeypatch,strength):
    device,reads=fixture(monkeypatch,strength=strength)
    result=asyncio.run(device.network_status())
    assert result['available'] and result['error'] is None
    wifi=next(d for d in result['devices'] if d['type']=='wifi')
    assert wifi['ssid']=='Current network' and wifi['signal']==strength
    assert reads.count(('/ap/active',NM_AP))==1
    assert 'signal' not in next(d for d in result['devices'] if d['type']=='ethernet')


@pytest.mark.parametrize('strength',[MISSING,None,False,True,-1,101,float('nan'),float('inf'),'80',25.5],
                         ids=['absent','null','false','true','negative','too-large','nan','inf','string','fraction'])
def test_missing_or_invalid_strength_is_unknown_not_invented(monkeypatch,strength):
    device,_=fixture(monkeypatch,strength=strength)
    result=asyncio.run(device.network_status())
    assert result['available'] and result['error'] is None
    assert 'signal' not in next(d for d in result['devices'] if d['type']=='wifi')


def test_disconnected_wifi_never_uses_cached_neighbour_strength(monkeypatch):
    device,reads=fixture(monkeypatch,strength=99,active='/')
    result=asyncio.run(device.network_status())
    wifi=next(d for d in result['devices'] if d['type']=='wifi')
    assert wifi['ssid'] is None and 'signal' not in wifi
    assert not any(interface==NM_AP for _,interface in reads)


@pytest.mark.parametrize('enabled',[True,False])
def test_radio_enabled_flag_is_the_real_nm_boolean(monkeypatch,enabled):
    device,_=fixture(monkeypatch,enabled=enabled)
    result=asyncio.run(device.network_status())
    assert result['wireless_enabled'] is enabled


@pytest.mark.parametrize('enabled',[MISSING,None,0,1,'false',RuntimeError('private daemon detail')],
                         ids=['unsupported','null','zero','one','string','failure'])
def test_optional_radio_metadata_failure_does_not_hide_connected_ethernet(monkeypatch,enabled):
    device,_=fixture(monkeypatch,enabled=enabled)
    result=asyncio.run(device.network_status())
    assert result['available'] and result['state']=='connected' and result['error'] is None
    assert 'wireless_enabled' not in result
    assert 'private' not in str(result)


def test_stalled_optional_radio_read_is_cancelled_without_losing_route(monkeypatch):
    device,_=fixture(monkeypatch)
    original_proxy=device._proxy
    cancelled=[]
    async def blocked_radio():
        try:
            await asyncio.Future()
        finally:
            cancelled.append(True)
    async def proxy(service,path,interface):
        value=await original_proxy(service,path,interface)
        if path==NM_PATH:value.get_wireless_enabled=blocked_radio
        return value
    monkeypatch.setattr(device,'_proxy',proxy)
    result=asyncio.run(device.network_status())
    assert cancelled==[True]
    assert result['available'] and result['state']=='connected' and result['error'] is None
    assert 'wireless_enabled' not in result
