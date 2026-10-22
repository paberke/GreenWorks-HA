"""0.3.0: weitere Tests fuer Einrichtung, Neu-Anmeldung, Token und Update-Pruefung."""

import aiohttp
import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.api import GreenworksClient, GreenworksError
from custom_components.greenworks.const import BASE_URL, CONF_GROUPS, DOMAIN

from .test_greenworks import DID, PID, UID, mock_cloud
from .test_v030 import _setup, eid


async def _start_flow(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"status": 403, "json": {"error": {"msg": "unknown user", "code": 4001001}}}, "login_rejected"),
        ({"exc": aiohttp.ClientError()}, "cannot_connect"),
        ({"exc": RuntimeError("kaputt")}, "unknown"),
    ],
)
async def test_config_flow_errors(hass, aioclient_mock, kwargs, error):
    aioclient_mock.post(f"{BASE_URL}user_auth", **kwargs)
    result = await _start_flow(hass)
    assert result["type"] == "form" and result["errors"] == {"base": error}


async def test_config_flow_no_devices(hass, aioclient_mock):
    aioclient_mock.post(f"{BASE_URL}user_auth", json={
        "access_token": "tok", "refresh_token": "ref", "user_id": UID, "expire_in": 7200})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", json={"list": []})
    result = await _start_flow(hass)
    assert result["errors"] == {"base": "no_devices"}


async def test_reauth_flow(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_PASSWORD: "neu"})
    assert result["type"] == "abort" and result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "neu"


async def test_position_group(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, options={CONF_GROUPS: ["position"]}, minor_version=2)
    st = hass.states.get(eid(hass, "device_tracker", "position"))
    assert st is not None
    assert st.attributes["latitude"] == 52.0 and st.attributes["longitude"] == 8.0
    assert st.attributes["gps_accuracy"] == 3.0


# --- Client direkt -----------------------------------------------------------------

def _client(hass):
    client = GreenworksClient(async_get_clientsession(hass), "t@e.de", "x")
    client._access_token, client._refresh_token, client._expires_at = "alt", "ref", 0
    client.user_id = UID
    return client


async def test_token_refresh_ok(hass, aioclient_mock):
    aioclient_mock.post(f"{BASE_URL}user/token/refresh", json={
        "access_token": "neu", "refresh_token": "ref2", "expire_in": 7200})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", json={"list": []})
    client = _client(hass)
    assert await client.async_get_devices() == []
    assert client._access_token == "neu"


async def test_token_refresh_fails_logs_in_again(hass, aioclient_mock):
    aioclient_mock.post(f"{BASE_URL}user/token/refresh", exc=aiohttp.ClientError())
    aioclient_mock.post(f"{BASE_URL}user_auth", json={
        "access_token": "login", "refresh_token": "ref", "user_id": UID, "expire_in": 7200})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", json={"list": []})
    client = _client(hass)
    await client.async_get_devices()
    assert client._access_token == "login"


async def test_rejected_twice_is_no_password_problem(hass, aioclient_mock):
    aioclient_mock.post(f"{BASE_URL}user_auth", json={
        "access_token": "login", "refresh_token": "ref", "user_id": UID, "expire_in": 7200})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", status=401)
    client = _client(hass)
    client._expires_at = 9e12
    with pytest.raises(GreenworksError, match="Zugriff verweigert"):
        await client.async_get_devices()


async def test_get_network_error(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", exc=aiohttp.ClientError())
    client = _client(hass)
    client._expires_at = 9e12
    with pytest.raises(GreenworksError, match="fehlgeschlagen"):
        await client.async_get_devices()



async def test_properties_missing_is_ok(hass, aioclient_mock):
    """Eigenschaften nicht abrufbar: Maeher trotzdem da (ohne Modell/Regenschutz)."""
    mock_cloud(aioclient_mock)
    aioclient_mock.clear_requests()
    aioclient_mock.post(f"{BASE_URL}user_auth", json={
        "access_token": "tok", "refresh_token": "ref", "user_id": UID, "expire_in": 7200})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", json={"list": [
        {"id": DID, "product_id": PID, "name": "Testmaeher", "is_online": True},
        {"id": None, "product_id": PID}]})
    aioclient_mock.get(f"{BASE_URL}product/{PID}/device/{DID}/property", status=500)
    aioclient_mock.get(f"{BASE_URL}product/{PID}/v_device/{DID}", json={"online": True})
    client = GreenworksClient(async_get_clientsession(hass), "t@e.de", "x")
    mowers = await client.async_get_mowers()
    assert list(mowers) == [DID] and mowers[DID].rain_sensor is None
