from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from services.backend.app import app, Hub


@pytest.fixture
def client(tmp_path):
    # Do not start hardware or external network services in HTTP boundary tests.
    hub = Hub(tmp_path)
    hub.device = SimpleNamespace(audio_set=AsyncMock(return_value={"available": False, "error":"unavailable"}))
    hub.player = SimpleNamespace(status=AsyncMock(return_value={"state":"idle"}), play=AsyncMock())
    app.state.hub = hub
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_session_and_preference_roundtrip(client):
    token = client.get('/api/session').json()['token']
    response = client.patch('/api/preferences', headers={'X-Hub-Token':token}, json={'language':'en'})
    assert response.status_code == 200
    assert client.get('/api/state').json()['preferences']['language'] == 'en'


@pytest.mark.parametrize('headers', [{'Origin':'https://evil.example'}, {'Host':'evil.example:8765'}, {'Sec-Fetch-Site':'cross-site'}])
def test_host_and_cross_site_boundary(client, headers):
    assert client.get('/api/session', headers=headers).status_code == 403


def test_mutation_requires_token(client):
    assert client.patch('/api/preferences', json={'language':'en'}).status_code == 403
    assert app.state.hub.store.value.language == 'ro'


def test_validation_never_reflects_submitted_credentials(client):
    token = client.get('/api/session').json()['token']
    secret = 'private-network-password-do-not-return'
    response = client.post('/api/network/connect', headers={'X-Hub-Token':token}, json={'ssid':'','password':secret})
    assert response.status_code == 422
    assert secret not in response.text
    assert response.json() == {'error':'invalid_request'}


def test_unknown_preferences_rejected_without_persistence(client):
    token = client.get('/api/session').json()['token']
    response = client.patch('/api/preferences', headers={'X-Hub-Token':token}, json={'command':'shell'})
    assert response.status_code == 422
    assert not app.state.hub.store.path.exists()


def test_diagnostics_do_not_expose_network_identifiers_or_token(client):
    hub = app.state.hub
    hub.snapshots['network'] = {'available':True, 'connection':'private-ssid', 'devices':[{'ip':'192.168.1.5'}]}
    response = client.get('/api/diagnostics')
    assert response.status_code == 200
    assert all(value not in response.text for value in ['private-ssid','192.168.1.5',hub.token])
