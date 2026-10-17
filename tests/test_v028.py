"""0.2.8: Messer-Laufzeit wie in der App."""

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.api import _blade_time
from custom_components.greenworks.const import DOMAIN

from .test_greenworks import UID, mock_cloud


def test_blade_time():
    # gleiche Rechnung wie die App: Maehzeit minus Summe der Reset-Staende
    assert _blade_time(3844451, {"BladeUsageTime": [114160, 960193]}) == 3844451 - 1074353
    assert _blade_time(1000, '{"BladeUsageTime": [400]}') == 600   # Cloud liefert Text
    assert _blade_time(1000, None) == 1000                         # nie zurueckgesetzt
    assert _blade_time(1000, {"BladeUsageTime": [5000]}) is None   # unplausibel
    assert _blade_time(1000, {"BladeUsageTime": ["x"]}) is None
    assert _blade_time(None, None) is None


async def test_blade_sensor(hass, aioclient_mock):
    hass.config.language = "de"
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "test@example.de", CONF_PASSWORD: "geheim"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    st = hass.states.get("sensor.testmaeher_messer_laufzeit")
    assert st is not None and st.state == "769.5"
    assert st.attributes["unit_of_measurement"] == "h"


async def test_diagnostics_hide_ids(hass, aioclient_mock):
    from custom_components.greenworks import diagnostics
    from custom_components.greenworks.api import _blade_time as bt
    from .test_greenworks import DATAPOINTS

    DATAPOINTS["237"] = "SN0000001"
    DATAPOINTS["250"] = "0009-030-50C:89490000000000000000"
    try:
        mock_cloud(aioclient_mock)
        entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                                data={CONF_EMAIL: "test@example.de", CONF_PASSWORD: "geheim"})
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        diag = await diagnostics.async_get_config_entry_diagnostics(hass, entry)
        text = str(diag)
        assert "SN0000001" not in text
        assert "89490000000000000000" not in text
        assert "geheim" not in text and "test@example.de" not in text
        raw = next(iter(diag["mowers"].values()))["raw_datapoints"]
        assert raw["237"] == "**REDACTED**" and "32" in raw
    finally:
        DATAPOINTS.pop("237"); DATAPOINTS.pop("250")
    # echter Wert aus Patricks Diagnose: 5x zurueckgesetzt
    assert round(bt(4031182, '{"BladeUsageTime":[114160,960193,1024026,815355,790171]}') / 3600, 1) == 90.9
