"""0.5.0: Steuerung (Parken, Starten, Pause, Maehen ohne Unterbrechung)."""

from datetime import datetime
import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.greenworks import control as ctl
from custom_components.greenworks.const import DOMAIN

from .test_greenworks import DATAPOINTS, DID, dp
from .test_v030 import _setup, eid

CONTROL = {"control": "read_and_control"}
STATUS_REQUEST = "0007000900406000a003500000"
CONTINUOUS_REQUEST = "0007000900346000a0034c0100"


def _state(state, reason=0, **extra):
    """Datenpunkte mit anderem Zustand (Status-Datenpunkt 32 ist der neueste)."""
    dps = dict(DATAPOINTS)
    dps["32"] = dp({"mower_main_state": state, "next_start": 1791874800, "battery_status": 99,
                    "source_for_next_start": reason, "request_time": "2026-10-12T20:01:35.126Z"})
    dps.update(extra)
    return dps


# Laedt in der Station: alle Park-Varianten moeglich
CHARGING = _state(7)


# --- Befehle: genau wie die Greenworks-App ------------------------------------

def test_payloads_match_app():
    assert ctl.park_payload(None) == "0007000b003e6000A005e60002feff"
    assert ctl.park_payload(120) == "0007000b003e6000A005e600027800"
    assert ctl.start_payload() == "0007000d003a6000A007e4000400000000"
    assert ctl.pause_payload() == "0007000b00386000A005e200020000"
    assert ctl.continuous_payload(2880) == "0007000c00366000A0064a0103400b01"
    assert ctl.continuous_payload(10080) == "0007000c00366000A0064a0103602701"
    assert ctl.continuous_payload(0) == "0007000c00366000A0064a0103000000"


def test_le16_and_rest_of_day():
    assert ctl.le16(120) == "7800"
    assert ctl.le16(0x1234) == "3412"
    with pytest.raises(ValueError):
        ctl.le16(70000)
    assert ctl.minutes_until_midnight(datetime(2026, 11, 1, 22, 0)) == 119
    assert ctl.minutes_until_midnight(datetime(2026, 11, 1, 23, 59, 30)) == 1


def test_parse_reply():
    raw = b"\x00\x06\x01\x51" + b'{"request":{"request_payload":"e60002feff"},"response":{"return_code":0}}'
    assert ctl.parse_reply(raw)["request"]["request_payload"] == "e60002feff"
    assert ctl.parse_reply(b"\x00\x01kein json") is None
    assert ctl.parse_reply(b"{kaputt") is None


# --- Nur lesen (Standard) -----------------------------------------------------

async def test_read_only_is_default(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    assert entry.runtime_data.control is None
    mower = hass.states.get(eid(hass, "lawn_mower", "mower"))
    assert mower.attributes["supported_features"] == 0
    reg = er.async_get(hass)
    for key in ("start", "pause", "park_until_further_notice", "park_2h", "park_rest_of_day",
                "park_custom", "continuous_2_days", "continuous_1_week", "continuous_custom",
                "continuous_off"):
        entity_id = eid(hass, "button", key)
        assert entity_id is not None and reg.async_get(entity_id).disabled_by is not None
    for key in ("park_hours", "continuous_days"):
        entity_id = eid(hass, "number", key)
        assert entity_id is not None and reg.async_get(entity_id).disabled_by is not None
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN, "park", {"entity_id": mower.entity_id, "hours": 2}, blocking=True)
    assert err.value.translation_key == "control_disabled"


# --- Lesen und steuern ----------------------------------------------------------

def _connect(entry):
    """Steuerkanal so tun lassen, als waere er verbunden."""
    control = entry.runtime_data.control
    control._mqtt = MagicMock()
    control.connected = True
    return control


def _reply(control, payload, code=0):
    body = ('{"request":{"request_payload":"%s"},"response":{"return_code":%d}}'
            % (payload, code)).encode()
    control._on_message(None, None, SimpleNamespace(topic=f"$6/{DID}", payload=b"\x00\x06" + body))


async def _press_and_reply(hass, control, call, reply_payload, code=0):
    async def answer(*args):
        _reply(control, reply_payload, code)
    control._mqtt.publish.side_effect = lambda *a: hass.loop.call_soon_threadsafe(
        lambda: hass.async_create_task(answer()))
    await call()


async def test_controls_present(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL)
    assert entry.runtime_data.control is not None
    mower = hass.states.get(eid(hass, "lawn_mower", "mower"))
    assert mower.attributes["supported_features"] != 0
    assert hass.states.get(eid(hass, "button", "park_2h")) is not None


@pytest.mark.parametrize(
    ("service", "data", "sent", "reply"),
    [
        ("lawn_mower.dock", {}, "e60002feff", "e60002feff"),
        ("lawn_mower.start_mowing", {}, "e4000400000000", "e4000400000000"),
        ("lawn_mower.pause", {}, "e200020000", "e200020000"),
        ("greenworks.park", {"hours": 3}, "e60002b400", "e60002b400"),
        ("greenworks.park", {}, "e60002feff", "e60002feff"),
        ("greenworks.mow_continuously", {"days": 2}, "4a0103400b01", "4a0103400b01"),
        ("greenworks.mow_continuously", {"days": 0}, "4a0103000000", "4a0103000000"),
    ],
)
async def test_commands(hass, aioclient_mock, service, data, sent, reply):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    mower_id = eid(hass, "lawn_mower", "mower")
    domain, name = service.split(".")

    async def call():
        await hass.services.async_call(
            domain, name, {"entity_id": mower_id, **data}, blocking=True)

    await _press_and_reply(hass, control, call, reply)
    first = control._mqtt.publish.call_args_list[0].args
    assert first[0] == f"$7/{DID}"
    assert first[1].hex().endswith(sent)
    assert first[2] == 1
    # Danach wie in der App: Status bzw. "Maehen ohne Unterbrechung" neu abfragen
    follow_up = CONTINUOUS_REQUEST if sent.startswith("4a0103") else STATUS_REQUEST
    assert control._mqtt.publish.call_args_list[1].args[1].hex() == follow_up


async def test_button_press(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)

    async def call():
        await hass.services.async_call(
            "button", "press", {"entity_id": eid(hass, "button", "park_2h")}, blocking=True)

    await _press_and_reply(hass, control, call, "e600027800")
    assert control._mqtt.publish.call_args_list[0].args[1].hex().endswith("e600027800")


async def test_rejected(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL)
    control = _connect(entry)

    async def call():
        await hass.services.async_call(
            "lawn_mower", "dock", {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)

    with pytest.raises(HomeAssistantError) as err:
        await _press_and_reply(hass, control, call, "e60002feff", code=1)
    assert err.value.translation_key == "control_rejected"
    assert control._mqtt.publish.call_count == 1  # kein Status-Nachfragen


async def test_no_reply(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL)
    control = _connect(entry)
    with patch.object(ctl, "CONFIRM_TIMEOUT", 0.05), pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            "lawn_mower", "pause", {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)
    assert err.value.translation_key == "control_no_reply"
    assert control._waiting == {}


async def test_other_reply_is_ignored(hass, aioclient_mock):
    """Statusmeldungen und Antworten fuer andere Befehle bestaetigen nichts."""
    entry = await _setup(hass, aioclient_mock, options=CONTROL)
    control = _connect(entry)

    async def call():
        await hass.services.async_call(
            "lawn_mower", "pause", {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)

    with patch.object(ctl, "CONFIRM_TIMEOUT", 0.2), pytest.raises(HomeAssistantError):
        await _press_and_reply(hass, control, call, "52000a025089e86a63020000f2")


async def test_not_connected(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, options=CONTROL)
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            "lawn_mower", "dock", {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)
    assert err.value.translation_key == "control_not_connected"


async def test_service_ranges(hass, aioclient_mock):
    import voluptuous as vol
    await _setup(hass, aioclient_mock, options=CONTROL)
    mower_id = eid(hass, "lawn_mower", "mower")
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, "park", {"entity_id": mower_id, "hours": 0}, blocking=True)
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, "mow_continuously", {"entity_id": mower_id, "days": 25}, blocking=True)
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, "park", {"entity_id": mower_id, "hours": 25}, blocking=True)


async def test_switch_on_in_options(hass, aioclient_mock):
    """Umschalten unter "Konfigurieren": Knoepfe werden aktiviert, Kanal startet."""
    entry = await _setup(hass, aioclient_mock)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"control": "read_and_control"})
    await hass.async_block_till_done()
    assert entry.options["control"] == "read_and_control"
    assert entry.runtime_data.control is not None
    reg = er.async_get(hass)
    assert reg.async_get(eid(hass, "button", "park_2h")).disabled_by is None


# --- Verbindung (paho wird nachgestellt) -----------------------------------------

def _api(authorize="abc", user_id=4711):
    return SimpleNamespace(authorize=authorize, user_id=user_id)


@pytest.mark.real_control
async def test_connect_without_authorize(hass, caplog):
    control = ctl.GreenworksControl(hass, _api(authorize=None), [1])
    with patch("paho.mqtt.client.Client") as client_cls:
        await control.async_start()
    client_cls.assert_not_called()
    assert "Steuerung nicht moeglich" in caplog.text


@pytest.mark.real_control
async def test_connect_and_subscribe(hass):
    control = ctl.GreenworksControl(hass, _api(), [123])
    fake = MagicMock()
    with patch("paho.mqtt.client.Client", return_value=fake):
        await control.async_start()
    user, password = fake.username_pw_set.call_args.args
    assert (user, password) == ("4711", hashlib.md5(b"4711abc").hexdigest())
    fake.connect_async.assert_called_once_with(ctl.MQTT_HOST, ctl.MQTT_PORT, keepalive=60)
    control._on_connect(fake, None, None, SimpleNamespace(is_failure=False), None)
    fake.subscribe.assert_called_once_with("$6/123", qos=1)
    assert control.connected
    control._on_disconnect(fake, None, None, SimpleNamespace(is_failure=True), None)
    assert not control.connected
    control._on_connect(fake, None, None, SimpleNamespace(is_failure=True), None)
    assert not control.connected
    fake.publish.assert_not_called()  # Verbinden allein schickt nie etwas
    await control.async_stop()
    fake.disconnect.assert_called_once()
    fake.loop_stop.assert_called_once()


@pytest.mark.real_control
async def test_old_paho(hass):
    """HA 2025.2 bringt paho 1.x ohne CallbackAPIVersion mit."""
    control = ctl.GreenworksControl(hass, _api(), [7])
    fake = MagicMock()
    fake_module = SimpleNamespace(Client=MagicMock(return_value=fake))
    with patch.dict("sys.modules", {"paho.mqtt.client": fake_module}), patch(
        "paho.mqtt.client", fake_module, create=True
    ):
        await control.async_start()
    assert "callback_api_version" not in fake_module.Client.call_args.kwargs
    fake.on_connect(fake, None, {}, 0)
    fake.subscribe.assert_called_once_with("$6/7", qos=1)
    fake.on_disconnect(fake, None, 1)
    assert not control.connected
    fake.publish.assert_not_called()


async def test_options_link_placeholder(hass, aioclient_mock):
    """Link auf "Getestete Maeher": ein Platzhalter fuer alle Sprachen."""
    import json
    from pathlib import Path
    entry = await _setup(hass, aioclient_mock)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["description_placeholders"]["tested_mowers_url"].endswith("#tested-mowers")
    hass.config.language = "de"
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["description_placeholders"]["tested_mowers_url"].endswith("#getestete-maher")
    base = Path(__file__).parent.parent / "custom_components" / "greenworks"
    for name in ("strings.json", "translations/en.json", "translations/de.json"):
        text = json.loads((base / name).read_text())["options"]["step"]["init"][
            "data_description"]["control"]
        assert "{tested_mowers_url}" in text
