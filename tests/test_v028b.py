"""0.2.8: Maehplan, Fehlerverlauf, Softwarestaende - mit Patricks echten Daten."""

import json
from pathlib import Path

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.api import _parse_schedule, build_mower
from custom_components.greenworks.const import BASE_URL, DOMAIN

from .test_greenworks import DID, PID, UID

SAMPLE = json.loads((Path(__file__).parent / "fixtures" / "sample_mower.json").read_text())
MOWER = {"raw_properties": SAMPLE["properties"], "raw_datapoints": SAMPLE["datapoints"]}


def real_cloud(aioclient_mock):
    aioclient_mock.post(f"{BASE_URL}user_auth", json={
        "access_token": "tok", "refresh_token": "ref", "user_id": UID, "expire_in": 7200, "authorize": "x"})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", json={"list": [
        {"id": DID, "product_id": PID, "name": "Testmaeher", "sn": "1", "is_online": True}]})
    aioclient_mock.get(f"{BASE_URL}product/{PID}/device/{DID}/property", json=MOWER["raw_properties"])
    aioclient_mock.get(f"{BASE_URL}product/{PID}/v_device/{DID}", json=MOWER["raw_datapoints"])


def test_build_from_real_data():
    m = build_mower({"id": DID, "product_id": PID, "name": "R"}, MOWER["raw_properties"], MOWER["raw_datapoints"])
    assert m.schedule[0] == [(540, 210)] and m.schedule[4] == [(540, 210)]
    assert m.schedule[5] == [] and m.schedule[6] == []
    assert m.schedule_time.isoformat().startswith("2026-10-13")   # 125 ist neuer als 124
    assert len(m.error_history) == 11
    assert m.error_history[0][1] == 47                              # neuester zuerst
    assert m.error_history[-1][0].year == 2023
    assert m.sw_cutting == "1.0" and m.sw_charging_station == "1.0" and m.firmware == "6.65"
    assert round(m.blade_time / 3600, 1) == 90.9
    assert m.state_code == 2 and m.park_reason == 2


def test_schedule_edge_cases():
    assert _parse_schedule({}) is None
    p = _parse_schedule({"monday_timer_1_timer_mode": 1, "monday_timer_1_start_time_hour": 22,
                         "monday_timer_1_start_time_minute": 0, "monday_timer_1_length_minutes": 180,
                         "monday_timer_2_timer_mode": 1, "monday_timer_2_start_time_hour": 99,
                         "monday_timer_2_start_time_minute": 0, "monday_timer_2_length_minutes": 10})
    assert p[0] == [(1320, 180)] and p[1] == []                     # ungueltige Zeit verworfen


async def test_real_sensors_de(hass, aioclient_mock):
    hass.config.language = "de"
    await hass.config.async_set_time_zone("Europe/Berlin")
    real_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    plan = hass.states.get("sensor.testmaeher_mahplan")
    print("PLAN:", plan.state, dict(plan.attributes))
    assert plan.state == "Mo–Fr 09:00–12:30"
    assert plan.attributes["monday"] == "09:00–12:30"
    assert plan.attributes["sunday"] == "–"

    err = hass.states.get("sensor.testmaeher_letzte_fehlermeldung")
    print("HIST:", err.attributes["history"])
    assert err.attributes["history"][0] == "11.08.2026 20:15 – Akku leer (47)"
    assert "Steckengeblieben (53)" in err.attributes["history"][4]

    sw = hass.states.get("sensor.testmaeher_software")
    assert sw.state == "6.65" and sw.attributes["cutting_unit"] == "1.0"

    blade = hass.states.get("sensor.testmaeher_messer_laufzeit")
    assert blade.state == "90.9"


async def test_real_sensors_en(hass, aioclient_mock):
    hass.config.language = "en"
    real_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_mowing_schedule").state == "Mon–Fri 09:00–12:30"


def test_settings_from_real_data():
    m = build_mower({"id": DID, "product_id": PID, "name": "R"}, MOWER["raw_properties"], MOWER["raw_datapoints"])
    assert m.drive_past_wire == 320                     # 89 (gesetzt) ist neuer als 90 (gelesen)
    assert m.wire_corridor == {"boundary": (4, 8), "guide_1": (0, 4), "guide_2": (0, 8)}
    assert m.start_points == [(1, 0, 250, 33)]


async def test_settings_sensors_de(hass, aioclient_mock):
    hass.config.language = "de"
    real_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_uberfahrweite").state == "32.0"
    wd = hass.states.get("sensor.testmaeher_abstand_beim_drahtfolgen")
    assert wd.state == "4–8" and wd.attributes["guide_wire_1"] == "0–4"
    sp = hass.states.get("sensor.testmaeher_startpunkte")
    print("SP:", dict(sp.attributes))
    assert sp.state == "1"
    assert sp.attributes["point_1"] == "Leitdraht 1, 250 m, 33 %"
    assert sp.attributes["charging_station"] == "67 %"
