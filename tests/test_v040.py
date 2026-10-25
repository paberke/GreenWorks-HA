"""0.4.0: Statustext wie in der App, PIN-Schutz/Geofence, Geraetedaten."""

import copy
from datetime import datetime, timedelta, timezone
import json

from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from custom_components.greenworks.api import GreenworksMower
from custom_components.greenworks.const import DOMAIN
from custom_components.greenworks.status_text import status_text

from .test_greenworks import DATAPOINTS, DID
from .test_v030 import _setup, eid

NOW = datetime(2026, 10, 23, 6, 0, tzinfo=timezone.utc)  # Freitag, 08:00 Uhr in Berlin


def _m(**kw):
    m = GreenworksMower(device_id=1, product_id="p", name="M", online=True)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


async def test_status_text_variants(hass):
    await hass.config.async_set_time_zone("Europe/Berlin")
    today_9 = NOW + timedelta(hours=1)          # heute 09:00
    monday_9 = datetime(2026, 10, 26, 8, 0, tzinfo=timezone.utc)  # Montag 09:00 (Winterzeit)
    cases = [
        (_m(state_code=2, park_reason=2, next_start=today_9), "Nach Zeitplan geparkt bis 09:00"),
        (_m(state_code=2, park_reason=2, next_start=monday_9), "Nach Zeitplan geparkt bis Mo. 09:00"),
        (_m(state_code=2, park_reason=4), "Vom Benutzer geparkt bis auf Weiteres"),
        (_m(state_code=2, park_reason=5, next_start=today_9), "Vom Regenschutz geparkt bis 09:00"),
        (_m(state_code=4, next_start=today_9), "Mäht bis 09:00"),
        (_m(state_code=9, last_error_code=13), "Schwerer Fehler: Zu starke Neigung (Fehler 13)"),
        (_m(online=False), "Offline"),
        (_m(online=False, winter_pause=True), "Winterpause"),
        (_m(state_code=6), "Sucht Station"),
    ]
    for mower, expected in cases:
        assert status_text(mower, "de", NOW) == expected
    assert status_text(_m(state_code=2, park_reason=2, next_start=monday_9), "en", NOW) == \
        "Parked by schedule until Mon 09:00"
    assert status_text(_m(), "de", NOW) is None


async def test_status_text_entity(hass, aioclient_mock):
    hass.config.language = "de"
    await _setup(hass, aioclient_mock)
    st = hass.states.get(eid(hass, "sensor", "status_text"))
    assert st is not None and st.state.startswith("Nach Zeitplan geparkt")


async def test_pin_and_geofence(hass, aioclient_mock):
    dps = copy.deepcopy(DATAPOINTS)
    dps["7"] = json.dumps({"request": {"security_level": 0, "request_time": "2022-11-17T17:22:59Z"},
                           "response": {"return_code": 0, "response_time": "2022-11-17T17:23:00Z"}})
    dps["8"] = json.dumps({"request": {"request_time": "2026-10-21T14:14:07Z"},
                           "response": {"return_code": 0, "security_level": 9,
                                        "response_time": "2026-10-21T14:14:08Z"}})
    await _setup(hass, aioclient_mock, datapoints=dps)
    assert hass.states.get(eid(hass, "binary_sensor", "pin_protection")).state == "on"
    assert hass.states.get(eid(hass, "binary_sensor", "geofence")).state == "on"


async def test_pin_and_geofence_unknown(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    assert hass.states.get(eid(hass, "binary_sensor", "pin_protection")).state == "unknown"


async def test_device_data(hass, aioclient_mock):
    dps = copy.deepcopy(DATAPOINTS)
    dps["21"] = json.dumps({"request": {"request_time": "2026-07-18T09:36:23Z"}, "response": {
        "mower_pn": 310012355, "mower_revision": 1, "mower_production_time": 1551324710}})
    await _setup(hass, aioclient_mock, datapoints=dps)
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, str(DID))})
    assert device.model_id == "310012355"
    assert device.hw_version == "Rev. 1 (2019-02)"
