"""0.5.0: alle Auswahlen der App, Sperren wie in der App, Anzeige
"Maehen ohne Unterbrechung"."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from custom_components.greenworks.api import GreenworksMower
from custom_components.greenworks.button import (
    can_mow_continuously,
    can_park,
    can_park_timed,
    can_pause,
    can_start,
)

from .test_greenworks import DID, dp
from .test_v030 import _refresh, _setup, cloud, eid
from .test_v050 import CHARGING, CONTROL, _connect, _press_and_reply, _state


def _m(state, reason=None):
    return GreenworksMower(device_id=1, product_id="p", name="m", state_code=state,
                           park_reason=reason)


# --- Wann welcher Knopf geht (wie die App) ---------------------------------------

@pytest.mark.parametrize(
    ("state", "reason", "start", "pause", "park", "timed", "continuous"),
    [
        (2, 2, False, False, True, False, True),   # nach Zeitplan geparkt
        (2, 5, False, False, True, False, True),   # Regenschutz
        (2, 6, False, False, True, False, True),   # Frostschutz
        (2, 4, True, False, False, False, True),   # vom Benutzer geparkt
        (2, 1, False, False, True, True, True),    # geparkt zum Laden
        (2, 3, False, False, False, False, True),  # max. Maehzeit erreicht
        (7, 0, False, False, True, True, True),    # laedt
        (3, 0, True, False, True, True, True),     # pausiert
        (4, 0, False, True, False, False, True),   # maeht
        (5, 0, False, True, False, False, True),   # verlaesst Station
        (6, 0, False, True, False, False, True),   # sucht Station
        (12, 0, False, False, False, False, False),  # Nebenflaeche
        (8, 0, False, False, False, False, True),  # Fehler
    ],
)
def test_rules_like_app(state, reason, start, pause, park, timed, continuous):
    m = _m(state, reason)
    assert can_start(m) is start
    assert can_pause(m) is pause
    assert can_park(m) is park
    assert can_park_timed(m) is timed
    assert can_mow_continuously(m) is continuous


async def test_schedule_parked_only_until_further_notice(hass, aioclient_mock):
    """Testdaten: nach Zeitplan geparkt -> Zeit-Parken gesperrt, wie in der App."""
    entry = await _setup(hass, aioclient_mock, options=CONTROL)
    control = _connect(entry)
    for key in ("park_2h", "park_rest_of_day", "park_custom", "start", "pause"):
        assert hass.states.get(eid(hass, "button", key)).state == STATE_UNAVAILABLE
    for key in ("park_until_further_notice", "continuous_2_days", "continuous_off"):
        assert hass.states.get(eid(hass, "button", key)).state != STATE_UNAVAILABLE
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            "greenworks", "park",
            {"entity_id": eid(hass, "lawn_mower", "mower"), "hours": 2}, blocking=True)
    assert err.value.translation_key == "park_timed_not_possible"
    control._mqtt.publish.assert_not_called()


async def test_buttons_follow_state(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=_state(4))
    assert hass.states.get(eid(hass, "button", "pause")).state != STATE_UNAVAILABLE
    assert hass.states.get(eid(hass, "button", "start")).state == STATE_UNAVAILABLE
    cloud(aioclient_mock, datapoints=_state(2, 4))
    await _refresh(hass, entry)
    assert hass.states.get(eid(hass, "button", "start")).state != STATE_UNAVAILABLE
    assert hass.states.get(eid(hass, "button", "pause")).state == STATE_UNAVAILABLE


@pytest.mark.parametrize(
    ("button", "number", "value", "sent"),
    [
        ("park_custom", "park_hours", 5, "e600022c01"),          # 300 Minuten
        ("continuous_custom", "continuous_days", 4, "4a0103801601"),  # 5760 Minuten
    ],
)
async def test_custom_time(hass, aioclient_mock, button, number, value, sent):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    number_id = eid(hass, "number", number)
    assert float(hass.states.get(number_id).state) == 3  # Standard
    await hass.services.async_call(
        "number", "set_value", {"entity_id": number_id, "value": value}, blocking=True)
    assert float(hass.states.get(number_id).state) == value

    async def call():
        await hass.services.async_call(
            "button", "press", {"entity_id": eid(hass, "button", button)}, blocking=True)

    await _press_and_reply(hass, control, call, sent)
    assert control._mqtt.publish.call_args_list[0].args[1].hex().endswith(sent)


async def test_number_range(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, options=CONTROL)
    state = hass.states.get(eid(hass, "number", "park_hours"))
    assert state.attributes["min"] == 1 and state.attributes["max"] == 24
    state = hass.states.get(eid(hass, "number", "continuous_days"))
    assert state.attributes["min"] == 1 and state.attributes["max"] == 24
    # keine "Einstellung": stehen unter Steuerung direkt bei ihrer Taste
    from homeassistant.helpers import entity_registry as er
    reg = er.async_get(hass)
    for key in ("park_hours", "continuous_days"):
        assert reg.async_get(eid(hass, "number", key)).entity_category is None


# --- Anzeige "Maehen ohne Unterbrechung" --------------------------------------------

def _iso(delta):
    return (dt_util.utcnow() + delta).isoformat().replace("+00:00", "Z")


def _set_dp(minutes, option, when, code=0):
    return {"129": dp({"time_minute": minutes, "override_option": option,
                       "request_time": when, "request_payload": "4a0103"},
                      {"return_code": code, "response_time": when})}


async def test_continuous_from_last_command(hass, aioclient_mock):
    """Befehl vor 1 Stunde fuer 1 Woche -> an, Ende in knapp 7 Tagen."""
    dps = _state(2, 4, **_set_dp(10080, 1, _iso(-timedelta(hours=1))))
    await _setup(hass, aioclient_mock, datapoints=dps)  # auch bei "Nur lesen"
    state = hass.states.get(eid(hass, "binary_sensor", "continuous_mowing"))
    assert state.state == "on"
    until = dt_util.parse_datetime(state.attributes["until"])
    assert timedelta(days=6, hours=22) < until - dt_util.utcnow() < timedelta(days=7)


async def test_continuous_query_is_newer(hass, aioclient_mock):
    """Neuere Abfrage (130) sagt: aus."""
    dps = _state(2, 2, **_set_dp(10080, 1, _iso(-timedelta(hours=2))))
    dps["130"] = dp({"request_time": _iso(-timedelta(minutes=5)), "request_payload": "4c0100"},
                    {"return_code": 0, "time_minute": 0, "override_option": 0,
                     "response_time": _iso(-timedelta(minutes=5))})
    await _setup(hass, aioclient_mock, datapoints=dps)
    state = hass.states.get(eid(hass, "binary_sensor", "continuous_mowing"))
    assert state.state == "off"
    assert state.attributes["until"] is None


@pytest.mark.parametrize(
    ("minutes", "option", "ago", "code", "expected"),
    [
        (0, 0, timedelta(minutes=1), 0, "off"),        # ausgeschaltet
        (2880, 1, timedelta(days=3), 0, "off"),        # abgelaufen
        (2880, 1, timedelta(minutes=1), 1, "unknown"),  # vom Maeher abgelehnt
        (2880, 2, timedelta(minutes=1), 0, "on"),
    ],
)
async def test_continuous_cases(hass, aioclient_mock, minutes, option, ago, code, expected):
    dps = _state(2, 2, **_set_dp(minutes, option, _iso(-ago), code))
    await _setup(hass, aioclient_mock, datapoints=dps)
    assert hass.states.get(eid(hass, "binary_sensor", "continuous_mowing")).state == expected


async def test_continuous_while_mowing(hass, aioclient_mock):
    """Beim Maehen meldet der Status Grund 52 und als naechsten Start das Ende."""
    end = int((dt_util.utcnow() + timedelta(days=1)).timestamp())
    dps = _state(4, 52)
    dps["32"] = dp({"mower_main_state": 4, "next_start": end, "battery_status": 80,
                    "source_for_next_start": 52, "request_time": _iso(-timedelta(minutes=1))})
    await _setup(hass, aioclient_mock, datapoints=dps)
    state = hass.states.get(eid(hass, "binary_sensor", "continuous_mowing"))
    assert state.state == "on"
    assert int(dt_util.parse_datetime(state.attributes["until"]).timestamp()) == end


async def test_continuous_reply_from_mower(hass, aioclient_mock):
    """Antwort auf die Abfrage ueber den Steuerkanal zeigt sofort den neuen Stand."""
    entry = await _setup(hass, aioclient_mock, options=CONTROL)
    control = _connect(entry)
    sensor = eid(hass, "binary_sensor", "continuous_mowing")
    body = (b'{"request":{"request_payload":"4c0100"},'
            b'"response":{"return_code":0,"time_minute":2000,"override_option":1}}')
    control._on_message(None, None, SimpleNamespace(topic=f"$6/{DID}", payload=b"\x00\x06" + body))
    await hass.async_block_till_done()
    assert hass.states.get(sensor).state == "on"
    # die naechste Cloud-Abfrage (aelterer Stand) ueberschreibt das nicht
    await _refresh(hass, entry)
    assert hass.states.get(sensor).state == "on"
    body = (b'{"request":{"request_payload":"4c0100"},'
            b'"response":{"return_code":0,"time_minute":0,"override_option":0}}')
    control._on_message(None, None, SimpleNamespace(topic=f"$6/{DID}", payload=b"\x00\x06" + body))
    await hass.async_block_till_done()
    assert hass.states.get(sensor).state == "off"
