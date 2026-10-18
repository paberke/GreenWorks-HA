"""0.2.14: Messerwechsel-Erinnerung (Grenze in den Einstellungen)."""

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.const import CONF_BLADE_LIMIT, CONF_OUTAGE_GRACE, DOMAIN

from .test_greenworks import UID, mock_cloud

ENTITY = "binary_sensor.testmaeher_messerwechsel_fallig"   # Messer-Laufzeit im Test: 769,5 h


async def _setup(hass, aioclient_mock, options=None):
    hass.config.language = "de"
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID), options=options or {},
                            data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_default_150h(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    st = hass.states.get(ENTITY)
    assert st.state == "on"
    assert st.attributes["limit"] == 150 and st.attributes["remaining"] == 0.0


async def test_not_due_yet(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, {CONF_BLADE_LIMIT: 1000})
    st = hass.states.get(ENTITY)
    assert st.state == "off" and st.attributes["remaining"] == 230.5


async def test_switched_off(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, {CONF_BLADE_LIMIT: 0})
    st = hass.states.get(ENTITY)
    assert st.state == "off" and st.attributes["remaining"] is None


async def test_change_limit_in_options(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    sel = result["data_schema"].schema[next(k for k in result["data_schema"].schema if k == CONF_BLADE_LIMIT)]
    assert sel.config["unit_of_measurement"] == "h" and sel.config["mode"] == "box"
    await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 60, CONF_OUTAGE_GRACE: 5, CONF_BLADE_LIMIT: 800})
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "off"


async def test_translations(hass):
    from homeassistant.helpers.translation import async_get_translations
    from homeassistant.setup import async_setup_component
    await async_setup_component(hass, "binary_sensor", {})
    t = await async_get_translations(hass, "de", "entity", ["greenworks"])
    base = "component.greenworks.entity.binary_sensor.blade_change_due"
    assert t[f"{base}.name"] == "Messerwechsel fällig"
    assert t[f"{base}.state.on"] == "Fällig"
