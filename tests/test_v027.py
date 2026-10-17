"""0.2.7: Klartext der Fehlermeldung als Attribut 'text'."""

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.const import DOMAIN
from custom_components.greenworks.error_texts import ERRORS, error_text

from .test_greenworks import UID, mock_cloud


def test_error_text():
    assert len(ERRORS) == 69
    assert error_text(13, "de") == "Zu starke Neigung"
    assert error_text(13, "en") == "Too high inclination"
    assert error_text(47, "de-AT") == "Akku leer"
    assert error_text(99, "de") == "Unbekannter Fehler 99"
    assert error_text(None, "de") is None


async def test_text_attribute(hass, aioclient_mock):
    hass.config.language = "de"
    mock_cloud(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID),
                            data={CONF_EMAIL: "test@example.de", CONF_PASSWORD: "geheim"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    st = hass.states.get("sensor.testmaeher_letzte_fehlermeldung")
    assert st.state == "e13"
    assert st.attributes["text"] == "Zu starke Neigung"
    assert hass.states.get("sensor.testmaeher_letzter_fehlercode").attributes["meaning"] == "e13"
