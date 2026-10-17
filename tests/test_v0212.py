"""0.2.12: Maehzeit mitzaehlen, Einstellungen (Konfigurieren)."""

import copy
from datetime import timedelta
import json
from unittest.mock import patch

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.const import CONF_OUTAGE_GRACE, DOMAIN

from .test_greenworks import DATAPOINTS, UID, mock_cloud

NOW = "custom_components.greenworks.coordinator.dt_util.utcnow"


def dp(request, response=None):
    return json.dumps({"request": request, "response": response or {"return_code": 0}})


def mowing():
    d = copy.deepcopy(DATAPOINTS)
    d["32"] = dp({"mower_main_state": 4, "next_start": 1791874800, "battery_status": 80,
                  "source_for_next_start": 0, "request_time": "2026-10-12T20:01:35.126Z"})
    return d


async def _setup(hass, aioclient_mock, options=None):
    hass.config.language = "de"
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID), options=options or {},
                            data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_counts_while_mowing(hass, aioclient_mock):
    start = dt_util.utcnow()
    with patch.dict(DATAPOINTS, mowing(), clear=True), patch(NOW, return_value=start):
        entry = await _setup(hass, aioclient_mock)
    coordinator = entry.runtime_data
    base = float(hass.states.get("sensor.testmaeher_mahzeit_gesamt").state)   # 1067.9
    with patch.dict(DATAPOINTS, mowing(), clear=True):
        for minute in range(1, 31):            # 30 Minuten maehen
            with patch(NOW, return_value=start + timedelta(minutes=minute)):
                await coordinator.async_refresh()
    await hass.async_block_till_done()
    st = hass.states.get("sensor.testmaeher_mahzeit_gesamt")
    assert float(st.state) == round(base + 0.5, 1)
    assert st.attributes["counted"] == 0.5
    assert st.attributes["last_statistics"].startswith("2026-08-14")
    blade = hass.states.get("sensor.testmaeher_messer_laufzeit")
    assert blade.attributes["counted"] == 0.5

    # neue echte Statistik -> Zaehlung beginnt von vorn
    d = mowing()
    d["48"] = dp({"request_time": "2026-10-17T10:00:00.000Z"},
                 {"cutting_time": 3846251, "running_time": 1, "charging_time": 1, "no_of_fatal_error": 63,
                  "response_time": "2026-10-17T10:00:01.000Z"})
    aioclient_mock.clear_requests()
    with patch.dict(DATAPOINTS, d, clear=True), patch(NOW, return_value=start + timedelta(minutes=31)):
        mock_cloud(aioclient_mock)               # Cloud liefert jetzt die neue Statistik
        await coordinator.async_refresh()
    await hass.async_block_till_done()
    st = hass.states.get("sensor.testmaeher_mahzeit_gesamt")
    assert st.attributes["counted"] == 0.0
    assert float(st.state) == round(3846251 / 3600, 1)


async def test_stops_counting_when_docked(hass, aioclient_mock):
    start = dt_util.utcnow()
    with patch.dict(DATAPOINTS, mowing(), clear=True), patch(NOW, return_value=start):
        entry = await _setup(hass, aioclient_mock)
    coordinator = entry.runtime_data
    for minute in range(1, 7):                  # 6 Minuten maehen
        with patch(NOW, return_value=start + timedelta(minutes=minute)):
            await coordinator.async_refresh()
    aioclient_mock.clear_requests()
    with patch.dict(DATAPOINTS, copy.deepcopy(DATAPOINTS), clear=True):
        mock_cloud(aioclient_mock)               # jetzt wieder geparkt (Zustand 2)
    for minute in range(7, 20):
        with patch(NOW, return_value=start + timedelta(minutes=minute)):
            await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_mahzeit_gesamt").attributes["counted"] == 0.1  # 6 min


async def test_no_count_when_docked(hass, aioclient_mock):
    start = dt_util.utcnow()
    with patch(NOW, return_value=start):
        entry = await _setup(hass, aioclient_mock)          # Zustand 2 = geparkt
    coordinator = entry.runtime_data
    for minute in range(1, 11):
        with patch(NOW, return_value=start + timedelta(minutes=minute)):
            await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_mahzeit_gesamt").attributes["counted"] == 0.0


async def test_long_gap_is_capped(hass, aioclient_mock):
    start = dt_util.utcnow()
    with patch.dict(DATAPOINTS, mowing(), clear=True), patch(NOW, return_value=start):
        entry = await _setup(hass, aioclient_mock)
    coordinator = entry.runtime_data
    with patch.dict(DATAPOINTS, mowing(), clear=True), patch(NOW, return_value=start + timedelta(hours=2)):
        await coordinator.async_refresh()       # 2 h Luecke zaehlt hoechstens 3 Intervalle
    await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_mahzeit_gesamt").attributes["counted"] == 0.1  # 3 min


async def test_counter_survives_restart(hass, aioclient_mock, hass_storage):
    start = dt_util.utcnow()
    with patch.dict(DATAPOINTS, mowing(), clear=True), patch(NOW, return_value=start):
        entry = await _setup(hass, aioclient_mock)
    coordinator = entry.runtime_data
    with patch.dict(DATAPOINTS, mowing(), clear=True):
        for minute in range(1, 13):
            with patch(NOW, return_value=start + timedelta(minutes=minute)):
                await coordinator.async_refresh()
    await coordinator._store.async_save(coordinator._counters)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_mahzeit_gesamt").attributes["counted"] == 0.2


async def test_options_flow(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    assert entry.runtime_data.update_interval == timedelta(seconds=60)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form" and result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 120, CONF_OUTAGE_GRACE: 10})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    assert entry.options == {CONF_SCAN_INTERVAL: 120, CONF_OUTAGE_GRACE: 10}
    assert entry.runtime_data.update_interval == timedelta(seconds=120)      # neu geladen
    assert entry.runtime_data._outage_grace == timedelta(minutes=10)


async def test_options_range(hass, aioclient_mock):
    import pytest
    import voluptuous as vol
    entry = await _setup(hass, aioclient_mock)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    with pytest.raises(vol.Invalid):
        await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_SCAN_INTERVAL: 5, CONF_OUTAGE_GRACE: 5})
