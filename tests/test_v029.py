"""0.2.9: Status aus neuerer Fehlermeldung, kurze Aussetzer ueberbruecken."""

import copy
from datetime import timedelta
import json
from unittest.mock import patch

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.greenworks.api import GreenworksError, build_mower
from custom_components.greenworks.const import DOMAIN

from .test_greenworks import DATAPOINTS, DID, PID, UID, mock_cloud

DEV = {"id": DID, "product_id": PID, "name": "R"}


def dp(request, response=None):
    return json.dumps({"request": request, "response": response or {"return_code": 0}})


def today(error_state=8, error_time="2026-10-14T10:31:28.000Z"):
    d = copy.deepcopy(DATAPOINTS)
    d["32"] = dp({"mower_main_state": 6, "next_start": 1791961200, "battery_status": 79,
                  "source_for_next_start": 0, "request_time": "2026-10-14T10:30:57.000Z"})
    d["33"] = dp({"current_mower_main_state": error_state, "event_id": 2,
                  "timestamp_for_error": 1792060288, "mower_sub_state": 0,
                  "request_time": error_time})
    return d


def test_error_newer_than_status():
    m = build_mower(DEV, {}, today())
    assert m.state_code == 8 and m.last_error_code == 2
    assert m.battery == 79                       # Akku bleibt aus der Statusmeldung


def test_status_newer_than_error():
    m = build_mower(DEV, {}, today(error_time="2026-10-14T10:00:00.000Z"))
    assert m.state_code == 6                     # alte Fehlermeldung aendert nichts


def test_old_error_data_unchanged():
    m = build_mower(DEV, {}, DATAPOINTS)         # Fehler 10.10., Status 12.10.
    assert m.state_code == 2 and m.park_reason == 2


async def test_entities_show_error(hass, aioclient_mock):
    hass.config.language = "de"
    with patch.dict(DATAPOINTS, today(), clear=True):
        mock_cloud(aioclient_mock)
        entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                                data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_status").state == "error"
    assert hass.states.get("lawn_mower.testmaeher").state == "error"


async def test_short_outage_keeps_values(hass, aioclient_mock):
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_battery").state == "99"

    coordinator = entry.runtime_data
    start = dt_util.utcnow()
    with patch.object(coordinator.client, "async_get_mowers", side_effect=GreenworksError("DNS")):
        for minutes in (1, 2, 4):              # unter 5 Minuten: Werte bleiben
            with patch("custom_components.greenworks.coordinator.dt_util.utcnow",
                       return_value=start + timedelta(minutes=minutes)):
                await coordinator.async_refresh()
            assert hass.states.get("sensor.testmaeher_battery").state == "99", minutes
        with patch("custom_components.greenworks.coordinator.dt_util.utcnow",
                   return_value=start + timedelta(minutes=6)):
            await coordinator.async_refresh()  # laenger als 5 Minuten: nicht verfuegbar
        await hass.async_block_till_done()
        assert hass.states.get("sensor.testmaeher_battery").state == "unavailable"

    await coordinator.async_refresh()          # Cloud wieder da
    await hass.async_block_till_done()
    assert hass.states.get("sensor.testmaeher_battery").state == "99"
    assert coordinator._failing_since is None
