"""0.2.4/0.2.5: Fehlertexte (alle 69 Codes) in Deutsch und Englisch."""

from homeassistant.helpers.translation import async_get_translations
from homeassistant.setup import async_setup_component

from custom_components.greenworks.const import ERROR_OPTIONS, error_key

ATTR = "component.greenworks.entity.sensor.last_error.state_attributes.meaning"
TEXT = "component.greenworks.entity.sensor.last_error_text"


async def test_all_error_texts(hass):
    await async_setup_component(hass, "sensor", {})
    expected = {
        "de": {"e13": "Zu starke Neigung", "e47": "Akku leer", "e53": "Steckengeblieben",
               "e59": "Begrenzungssignal verloren", "unknown": "Unbekannt", "_name": "Bedeutung",
               "_text": "Letzte Fehlermeldung"},
        "en": {"e13": "Too high inclination", "e47": "Battery empty", "e53": "Mower is stuck",
               "e59": "No boundary signal", "unknown": "Unknown", "_name": "Meaning",
               "_text": "Last error message"},
    }
    for lang, exp in expected.items():
        t = await async_get_translations(hass, lang, "entity", ["greenworks"])
        assert len(ERROR_OPTIONS) == 70
        for key in ERROR_OPTIONS:  # jeder Code hat Text an Attribut UND Sensor
            assert t.get(f"{ATTR}.state.{key}"), (lang, key)
            assert t.get(f"{TEXT}.state.{key}"), (lang, key)
        for key, val in exp.items():
            if key == "_name":
                assert t[f"{ATTR}.name"] == val
            elif key == "_text":
                assert t[f"{TEXT}.name"] == val
            else:
                assert t[f"{ATTR}.state.{key}"] == val


def test_error_key():
    assert error_key(None) is None
    assert error_key(1) == "e1" and error_key(69) == "e69"
    assert error_key(0) == "unknown" and error_key(70) == "unknown"
