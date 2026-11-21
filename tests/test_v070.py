"""0.7.0: Uhr des Maehers automatisch stellen; nie personenbezogene Daten in Log,
Fehlermeldungen oder Diagnose."""

import json
import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.greenworks import clock as clk
from custom_components.greenworks.const import BASE_URL, DOMAIN
from custom_components.greenworks.diagnostics import async_get_config_entry_diagnostics

from .test_greenworks import DID, PID, UID
from .test_v030 import _refresh, _setup, eid
from .test_v050 import CHARGING, CONTROL, _connect, _state

MOWING = _state(4)
BERLIN_SUMMER = datetime(2026, 7, 1, 12, 0, tzinfo=timezone(timedelta(hours=2)))
BERLIN_WINTER = datetime(2026, 11, 21, 12, 0, tzinfo=timezone(timedelta(hours=1)))


# --- Befehl wie die App -------------------------------------------------------

def test_le32_like_app():
    # StringUtils.getEightLen: 4 Byte, niedriges Byte zuerst
    assert clk.le32(0x12345678) == "78563412"
    assert clk.le32(3600) == "100e0000"
    # negativ wie getBig(Integer.toHexString(-3600)) = Zweierkomplement
    assert clk.le32(-3600) == "f0f1ffff"
    with pytest.raises(ValueError):
        clk.le32(2**32)


def test_set_time_payload():
    payload = clk.set_time_payload(BERLIN_WINTER)
    ts = int(BERLIN_WINTER.timestamp())
    assert payload == "0007001100566000A00b9a0008" + clk.le32(ts) + "100e0000"
    # Kopf: 11 Byte Daten (9a0008 + 2 x 4 Byte)
    assert len(bytes.fromhex(payload[20:])) == 0x0B
    assert clk.set_time_payload(BERLIN_SUMMER).endswith("201c0000")  # 7200 s


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        # stimmt
        ({"utc_time": 0, "time_zone_offset": 3600}, False),
        # nach der Zeitumstellung: Versatz noch Sommerzeit
        ({"utc_time": 0, "time_zone_offset": 7200}, True),
        # Uhr 6 Minuten daneben
        ({"utc_time": -360, "time_zone_offset": 3600}, True),
        # 4 Minuten: noch in Ordnung
        ({"utc_time": 240, "time_zone_offset": 3600}, False),
        # nicht verwertbar: nie stellen
        ({"time_zone_offset": 3600}, None),
        ({"utc_time": "x", "time_zone_offset": 3600}, None),
        (None, None),
    ],
)
def test_clock_wrong(response, expected):
    if isinstance(response, dict) and isinstance(response.get("utc_time"), int):
        response = {**response, "utc_time": int(BERLIN_WINTER.timestamp()) + response["utc_time"]}
    assert clk.clock_wrong(response, BERLIN_WINTER) is expected


# --- Ablauf in Home Assistant ------------------------------------------------

def _answer(control, hass, mower_time):
    """Maeher nachstellen: beantwortet Uhr lesen (9c0000) und Uhr stellen (9a0008)."""
    sent = []

    def publish(topic, payload, qos):
        hexed = payload.hex()
        sent.append(hexed)
        body = hexed[20:]
        if body.startswith("9c0000"):
            reply = {"request": {"request_payload": "9c0000"},
                     "response": {"return_code": 0, **mower_time}}
        elif body.startswith("9a0008"):
            utc = int.from_bytes(bytes.fromhex(body[6:14]), "little")
            off = int.from_bytes(bytes.fromhex(body[14:22]), "little", signed=True)
            mower_time.update(utc_time=utc, time_zone_offset=off)
            reply = {"request": {"request_payload": body}, "response": {"return_code": 0}}
        else:
            return
        raw = b"\x00\x06" + json.dumps(reply).encode()
        hass.loop.call_soon_threadsafe(
            control._on_message, None, None, SimpleNamespace(topic=f"$6/{DID}", payload=raw))

    control._mqtt.publish.side_effect = publish
    return sent


def _bodies(sent):
    return [s[20:26] for s in sent]


@pytest.fixture(autouse=True)
def fast_verify():
    with patch.object(clk, "VERIFY_DELAY", 0):
        yield


async def test_read_only_never_touches_clock(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, datapoints=CHARGING)
    assert entry.runtime_data.clock is None
    button = eid(hass, "button", "set_time")
    assert er.async_get(hass).async_get(button).disabled_by is not None
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN, "set_time", {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)
    assert err.value.translation_key == "control_disabled"


async def test_auto_sets_wrong_clock(hass, aioclient_mock):
    await hass.config.async_update(time_zone="Europe/Berlin")
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    now = int(datetime.now(timezone.utc).timestamp())
    # Maeher noch auf Sommerzeit (wie nach der Umstellung im Oktober)
    mower_time = {"utc_time": now, "time_zone_offset": clk.ha_offset() + 3600}
    sent = _answer(control, hass, mower_time)
    await entry.runtime_data.clock.async_check(DID)
    await hass.async_block_till_done()
    assert _bodies(sent)[:2] == ["9c0000", "9a0008"]
    assert mower_time["time_zone_offset"] == clk.ha_offset()
    # danach nachgelesen
    assert "9c0000" in _bodies(sent)[2:]


async def test_auto_leaves_correct_clock(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    now = int(datetime.now(timezone.utc).timestamp())
    sent = _answer(control, hass, {"utc_time": now, "time_zone_offset": clk.ha_offset()})
    await entry.runtime_data.clock.async_check(DID)
    assert _bodies(sent) == ["9c0000"]


async def test_auto_never_sets_on_unknown_reply(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    sent = _answer(control, hass, {})
    await entry.runtime_data.clock.async_check(DID)
    assert _bodies(sent) == ["9c0000"]


@pytest.mark.parametrize(("datapoints", "online"), [(MOWING, True), (CHARGING, False)])
async def test_auto_waits_while_mowing_or_offline(hass, aioclient_mock, datapoints, online):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=datapoints,
                         online=online)
    control = _connect(entry)
    sent = _answer(control, hass, {"utc_time": 0, "time_zone_offset": 0})
    await entry.runtime_data.clock.async_check(DID)
    assert sent == []


async def test_auto_errors_only_debug(hass, aioclient_mock, caplog):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    control._mqtt.publish.side_effect = None  # Maeher antwortet nicht
    with patch("custom_components.greenworks.control.CONFIRM_TIMEOUT", 0.01):
        await entry.runtime_data.clock.async_check(DID)
    assert "Uhr von Maeher" in caplog.text
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING
                and r.name == "custom_components.greenworks.clock"]


async def test_button_and_action_set_clock(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    now = int(datetime.now(timezone.utc).timestamp())
    events = []
    hass.bus.async_listen("logbook_entry", events.append)
    sent = _answer(control, hass, {"utc_time": now, "time_zone_offset": clk.ha_offset()})
    # Von Hand wird immer gestellt, auch wenn die Uhr stimmt
    await hass.services.async_call(
        "button", "press", {"entity_id": eid(hass, "button", "set_time")}, blocking=True)
    assert _bodies(sent)[0] == "9a0008"
    sent.clear()
    await hass.services.async_call(
        DOMAIN, "set_time", {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)
    assert _bodies(sent)[0] == "9a0008"
    await hass.async_block_till_done()
    assert len(events) == 2
    assert events[0].data["entity_id"] == eid(hass, "lawn_mower", "mower")


async def test_set_clock_not_confirmed(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    sent = []

    def publish(topic, payload, qos):
        body = payload.hex()[20:]
        sent.append(body[:6])
        if body.startswith("9a0008"):
            reply = {"request": {"request_payload": body}, "response": {"return_code": 0}}
        elif body.startswith("9c0000"):
            # Uhr stimmt danach immer noch nicht
            reply = {"request": {"request_payload": "9c0000"},
                     "response": {"utc_time": 1, "time_zone_offset": 0}}
        else:
            return
        raw = json.dumps(reply).encode()
        hass.loop.call_soon_threadsafe(
            control._on_message, None, None, SimpleNamespace(topic=f"$6/{DID}", payload=raw))

    control._mqtt.publish.side_effect = publish
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            "button", "press", {"entity_id": eid(hass, "button", "set_time")}, blocking=True)
    assert err.value.translation_key == "clock_not_set"


# --- Datenschutz: nie personenbezogene Daten ausgeben -----------------------

EMAIL = "privat.person@example.org"
PASSWORD = "GeheimesPasswort123"
TOKEN = "zugangstoken-abc"
REFRESH = "erneuerungstoken-def"
AUTHORIZE = "steuerschluessel-ghi"
SERIAL = "SN9876543210"
PIN = "8357"
SECRETS = (EMAIL, PASSWORD, TOKEN, REFRESH, AUTHORIZE, SERIAL, PIN, "a520", str(UID))


def _assert_clean(text: str) -> None:
    for secret in SECRETS:
        assert secret not in text, secret


async def test_no_personal_data_in_log_errors_or_diagnostics(hass, aioclient_mock, caplog):
    caplog.set_level(logging.DEBUG)
    from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from .test_greenworks import PROPERTIES

    aioclient_mock.post(f"{BASE_URL}user_auth", json={
        "access_token": TOKEN, "refresh_token": REFRESH, "user_id": UID,
        "expire_in": 7200, "authorize": AUTHORIZE, "email": EMAIL})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", json={"list": [
        {"id": DID, "product_id": PID, "name": "Testmaeher", "sn": SERIAL, "is_online": True,
         "user_id": UID, "email": EMAIL}]})
    aioclient_mock.get(f"{BASE_URL}product/{PID}/device/{DID}/property",
                       json={**PROPERTIES, "sn": SERIAL, "owner_id": UID})
    aioclient_mock.get(f"{BASE_URL}product/{PID}/v_device/{DID}", json=CHARGING)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID), title=f"Greenworks ({EMAIL})",
                            options={**CONTROL, "pin": PIN},
                            data={CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Befehl mit PIN und Uhr stellen
    control = _connect(entry)
    now = int(datetime.now(timezone.utc).timestamp())
    _answer(control, hass, {"utc_time": now, "time_zone_offset": clk.ha_offset()})
    await hass.services.async_call(
        "button", "press", {"entity_id": eid(hass, "button", "set_time")}, blocking=True)
    control._mqtt.publish.side_effect = None
    with patch("custom_components.greenworks.control.CONFIRM_TIMEOUT", 0.01), \
            pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "lawn_mower", "start_mowing", {"entity_id": eid(hass, "lawn_mower", "mower")},
            blocking=True)

    # Cloud-Fehler: Meldungen ohne Kennungen
    aioclient_mock.clear_requests()
    aioclient_mock.post(f"{BASE_URL}user_auth", status=403,
                        json={"error": {"code": 1}, "email": EMAIL})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", status=500, json={})
    await _refresh(hass, entry)
    errors = [str(entry.runtime_data.last_exception or "")]

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    _assert_clean(caplog.text)
    _assert_clean(" ".join(errors))
    _assert_clean(json.dumps(diagnostics, default=str))


# --- Fehlertexte der Cloud ohne Kennungen -------------------------------------

def test_safe_path_hides_ids():
    from custom_components.greenworks.api import _safe_path

    assert _safe_path(f"user/{UID}/subscribe/devices") == "user/…/subscribe/devices"
    assert str(DID) not in _safe_path(f"product/{PID}/v_device/{DID}")
    assert PID not in _safe_path(f"product/{PID}/v_device/{DID}")
