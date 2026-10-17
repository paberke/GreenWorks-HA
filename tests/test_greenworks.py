"""Test der Greenworks-Integration mit nachgestellten Cloud-Antworten."""

import json

import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.const import BASE_URL, DOMAIN

UID, PID, DID = 4711, "160fa8b69e2503e9160fa8b69e250601", 123456789


def dp(request, response=None):
    return json.dumps({"request": request, "response": response or {"return_code": 0}})


DATAPOINTS = {
    "31": dp({"request_time": "2026-10-09T18:06:50.727Z"}, {"mower_main_state": 9, "mower_sub_state": 0,
             "next_start": 4294967295, "battery_status": 95, "signal_quality": 58}),
    "32": dp({"mower_main_state": 2, "next_start": 1791874800, "battery_status": 99, "source_for_next_start": 2,
              "request_time": "2026-10-12T20:01:35.126Z"}),
    "33": dp({"current_mower_main_state": 9, "event_id": 13, "timestamp_for_error": 1791568428,
              "request_time": "2026-10-10T07:29:20.263Z"}),
    "34": dp({"request_time": "2026-10-12T20:01:35.126Z"}, {"latitude": 52.0, "longitude": 8.0, "hdop": "0.6"}),
    "48": dp({"request_time": "2026-08-14T16:49:52.362Z"}, {"cutting_time": 3844451, "running_time": 4488731,
             "charging_time": 3103343, "no_of_fatal_error": 63}),
    "117": dp({"mower_main_application_major_sw_version": 6, "mower_main_application_minor_sw_version": 65}),
    "230": "1",
    "online": True,
    "last_update": "2026-10-12T20:01:35.126Z",
    "neues_feld_das_es_frueher_nicht_gab": {"x": 1},
}
PROPERTIES = {
    "is_frost_sensor_on": True, "geofence_latitude": 52.0, "is_rain_sensor_on": True,
    "device_blade_usage_time": {"BladeUsageTime": [114160, 960193]},
    "device_type_no": {"SubDeviceNo": 1}, "device_model_name": "Optimow 10", "geofence_longitude": 8.0,
}


def mock_cloud(aioclient_mock, login_status=200):
    if login_status == 200:
        aioclient_mock.post(f"{BASE_URL}user_auth", json={
            "access_token": "tok", "refresh_token": "ref", "user_id": UID, "expire_in": 7200, "authorize": "x"})
    else:
        aioclient_mock.post(f"{BASE_URL}user_auth", status=400,
                            json={"error": {"msg": "password error", "code": 4001007}})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", json={"list": [
        {"id": DID, "product_id": PID, "name": "Testmaeher", "sn": "SN0000001", "is_online": True}]})
    aioclient_mock.get(f"{BASE_URL}product/{PID}/device/{DID}/property", json=PROPERTIES)
    aioclient_mock.get(f"{BASE_URL}product/{PID}/v_device/{DID}", json=DATAPOINTS)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def test_config_flow_ok(hass, aioclient_mock):
    mock_cloud(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "test@example.de", CONF_PASSWORD: "geheim"})
    assert result["type"] == "create_entry", result
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is ConfigEntryState.LOADED


async def test_config_flow_wrong_password(hass, aioclient_mock):
    mock_cloud(aioclient_mock, login_status=400)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "test@example.de", CONF_PASSWORD: "falsch"})
    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_entities(hass, aioclient_mock):
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "test@example.de", CONF_PASSWORD: "geheim"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    states = {s.entity_id: s for s in hass.states.async_all()}
    for eid, s in sorted(states.items()):
        print(f"{eid:45} {s.state:28} {dict(s.attributes).get('friendly_name')}")

    assert states["lawn_mower.testmaeher"].state == "docked"
    assert states["sensor.testmaeher_battery"].state == "99"
    assert states["sensor.testmaeher_status"].state == "parked_by_schedule"
    assert states["sensor.testmaeher_next_start"].state == "2026-10-13T07:00:00+00:00"
    assert states["sensor.testmaeher_last_error_code"].state == "13"
    assert states["sensor.testmaeher_total_cutting_time"].state == "1067.9"
    assert states["binary_sensor.testmaeher_rain_protection"].state == "on"
    assert states["binary_sensor.testmaeher_online"].state == "on"

    reg = er.async_get(hass)
    tracker = reg.async_get("device_tracker.testmaeher_position")
    assert tracker is not None and tracker.disabled_by is not None

    # Unload sauber?
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_cloud_down_does_not_crash(hass, aioclient_mock):
    aioclient_mock.post(f"{BASE_URL}user_auth", status=500, text="kaputt")
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "test@example.de", CONF_PASSWORD: "geheim"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY  # HA versucht es spaeter erneut


async def test_error_meaning(hass, aioclient_mock):
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "test@example.de", CONF_PASSWORD: "geheim"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    st = hass.states.get("sensor.testmaeher_last_error_code")
    print("ATTR:", dict(st.attributes))
    assert st.state == "13"
    assert st.attributes["meaning"] == "e13"
