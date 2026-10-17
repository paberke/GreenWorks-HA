"""Tests fuer die Aenderungen in 0.2.2."""

import json
import time

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.api import (
    GreenworksClient,
    build_mower,
)
from custom_components.greenworks.const import BASE_URL, DOMAIN
from tests.test_greenworks import UID, mock_cloud


def _login_mock(aioclient_mock, status, body):
    aioclient_mock.post(f"{BASE_URL}user_auth", status=status, json=body)


async def test_wrong_password_shows_invalid_auth(hass, aioclient_mock):
    _login_mock(aioclient_mock, 400, {"error": {"msg": "password error", "code": 4001007}})
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    r = await hass.config_entries.flow.async_configure(
        r["flow_id"], {CONF_EMAIL: "a@b.de", CONF_PASSWORD: "x"})
    assert r["errors"] == {"base": "invalid_auth"}


async def test_other_rejection_shows_login_rejected(hass, aioclient_mock):
    _login_mock(aioclient_mock, 400, {"error": {"msg": "too many requests", "code": 4001099}})
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    r = await hass.config_entries.flow.async_configure(
        r["flow_id"], {CONF_EMAIL: "a@b.de", CONF_PASSWORD: "x"})
    assert r["errors"] == {"base": "login_rejected"}


async def test_running_entry_other_rejection_retries_not_reauth(hass, aioclient_mock):
    _login_mock(aioclient_mock, 400, {"error": {"msg": "too many requests", "code": 4001099}})
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "a@b.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
    flows = hass.config_entries.flow.async_progress()
    assert not any(f["context"].get("source") == "reauth" for f in flows)


async def test_running_entry_wrong_password_starts_reauth(hass, aioclient_mock):
    _login_mock(aioclient_mock, 400, {"error": {"msg": "password error", "code": 4001007}})
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "a@b.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"].get("source") == "reauth" for f in flows)


def test_token_minimum_lifetime():
    c = GreenworksClient(None, "a", "b")
    now = time.time()
    c._store_tokens({"access_token": "t", "expire_in": 120})
    assert c._expires_at >= now + 600 - 1          # nie kuerzer als 10 Minuten
    c._store_tokens({"access_token": "t", "expire_in": 7200})
    assert abs(c._expires_at - (now + 6900)) < 5    # normal: 5 Min Puffer
    c._store_tokens({"access_token": "t"})
    assert abs(c._expires_at - (now + 3300)) < 5    # fehlt: Standard 1 Stunde


def _pos(lat, lon):
    return {"34": json.dumps({"request": {}, "response": {"latitude": lat, "longitude": lon, "hdop": "0.5"}})}


def test_gps_range():
    dev = {"id": 1, "product_id": "p", "name": "M"}
    ok = build_mower(dev, {}, _pos(52.2, 7.4))
    assert (ok.latitude, ok.longitude, ok.gps_accuracy) == (52.2, 7.4, 2.5)
    for lat, lon in ((95.0, 7.4), (52.2, 190.0), (-91, 0.5), (0, 0), ("abc", 7)):
        bad = build_mower(dev, {}, _pos(lat, lon))
        assert bad.latitude is None and bad.longitude is None, (lat, lon)


async def test_error_hint_has_umlaut(hass, aioclient_mock):
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "a@b.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    st = hass.states.get("sensor.testmaeher_last_error_code")
    assert "note" not in st.attributes and st.attributes["meaning"] == "e13"
    assert hass.states.get("sensor.testmaeher_last_error_message").state == "e13"


async def test_v023_statistics_time_and_names(hass, aioclient_mock):
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "a@b.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    st = hass.states.get("sensor.testmaeher_statistics_as_of")
    assert st is not None and st.state == "2026-08-14T16:49:52+00:00", st
    assert hass.states.get("binary_sensor.testmaeher_rain_protection").state == "on"
    assert hass.states.get("binary_sensor.testmaeher_frost_protection").state == "on"
