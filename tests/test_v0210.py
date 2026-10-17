"""0.2.10: Maeher offline -> Status 'Offline', Maeher-Entitaet nicht verfuegbar."""

import copy
from unittest.mock import patch

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.translation import async_get_translations
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.const import DOMAIN

from .test_greenworks import DATAPOINTS, UID, mock_cloud
from .test_v029 import today


async def _setup(hass, aioclient_mock, datapoints):
    hass.config.language = "de"
    with patch.dict(DATAPOINTS, datapoints, clear=True):
        mock_cloud(aioclient_mock)
        entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                                data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


async def test_offline_after_error(hass, aioclient_mock):
    d = today()                      # Fehler 2 nach der letzten Statusmeldung
    d["online"] = False              # danach offline (wie am 14.10. ab 12:46)
    await _setup(hass, aioclient_mock, d)
    st = hass.states.get("sensor.testmaeher_status")
    assert st.state == "offline"
    assert st.attributes["last_status"] == "error"
    assert hass.states.get("lawn_mower.testmaeher").state == "unavailable"
    assert hass.states.get("binary_sensor.testmaeher_online").state == "off"
    assert hass.states.get("sensor.testmaeher_batterie").state == "79"   # andere Werte bleiben


async def test_online_normal(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, copy.deepcopy(DATAPOINTS))
    st = hass.states.get("sensor.testmaeher_status")
    assert st.state == "parked_by_schedule" and "last_status" not in st.attributes
    assert hass.states.get("lawn_mower.testmaeher").state == "docked"


async def test_offline_translations(hass):
    await async_setup_component(hass, "sensor", {})
    for lang, off, attr in (("de", "Offline", "Letzter Zustand"), ("en", "Offline", "Last state")):
        t = await async_get_translations(hass, lang, "entity", ["greenworks"])
        base = "component.greenworks.entity.sensor.status"
        assert t[f"{base}.state.offline"] == off
        assert t[f"{base}.state_attributes.last_status.name"] == attr
        assert t[f"{base}.state_attributes.last_status.state.error"]
