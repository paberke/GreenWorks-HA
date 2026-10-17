"""0.2.5: Zustaende laut App inkl. Park-Grund, Zustand 9 = schwerer Fehler."""

from homeassistant.helpers.translation import async_get_translations
from homeassistant.setup import async_setup_component

from custom_components.greenworks.const import STATUS_OPTIONS, status_key
from custom_components.greenworks.lawn_mower import ACTIVITY_MAP


def test_status_key():
    assert status_key(None, None) is None
    assert status_key(2, 2) == "parked_by_schedule"   # heute live gesehen
    assert status_key(2, 4) == "parked_by_user"
    assert status_key(2, 5) == "parked_by_rain_guard"
    assert status_key(2, 99) == "parked"              # unbekannter Grund
    assert status_key(9, 0) == "fatal_error"          # frueher "Zustand 9"
    assert status_key(4, 2) == "mowing"               # Grund nur bei Zustand 2
    assert status_key(42, None) == "unknown"
    assert "state_9" not in STATUS_OPTIONS


def test_activity_errors():
    for state in (8, 9, 10, 11):
        assert ACTIVITY_MAP[state].value == "error"
    assert ACTIVITY_MAP[12].value == "mowing"


async def test_status_translations(hass):
    await async_setup_component(hass, "sensor", {})
    base = "component.greenworks.entity.sensor.status.state"
    for lang, sched, fatal in (("de", "Nach Zeitplan geparkt", "Schwerer Fehler"),
                               ("en", "Parked by schedule", "Fatal error")):
        t = await async_get_translations(hass, lang, "entity", ["greenworks"])
        for key in STATUS_OPTIONS:
            assert t.get(f"{base}.{key}"), (lang, key)
        assert t[f"{base}.parked_by_schedule"] == sched
        assert t[f"{base}.fatal_error"] == fatal
