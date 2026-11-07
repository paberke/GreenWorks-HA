"""Testzweig Maehplan: Maehplan setzen wie die App, PIN fuer das Starten."""

from datetime import timedelta
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from custom_components.greenworks import control as ctl, schedule as sch
from custom_components.greenworks.const import DOMAIN
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .test_greenworks import DID
from .test_v030 import _setup, eid
from .test_v050 import CHARGING, CONTROL, _connect

SAMPLE = json.loads((Path(__file__).parent / "fixtures" / "sample_mower.json").read_text())
# Echter Speicherbefehl der App (Datenpunkt 124): Werte und daraus gebauter Befehl
APP_REQUEST = SAMPLE["datapoints"]["124"]["request"]
APP_FIELDS = {k: v for k, v in APP_REQUEST.items() if "_timer_" in k}
APP_PAYLOAD = APP_REQUEST["request_payload"]
READ = "0007000900306000a003420100"


# --- Befehl genau wie die App ---------------------------------------------------

def test_save_payload_matches_app():
    """Aus den Werten des App-Befehls entsteht Byte fuer Byte derselbe Befehl."""
    assert APP_PAYLOAD.startswith("400146")
    assert sch.save_payload(sch.fields_from_reply(APP_FIELDS)) == (
        "0007004f00326000A049" + APP_PAYLOAD
    )
    # Laenge passt zum Kopf: 0x49 = 3 + 70 Byte
    assert len(sch.save_payload(APP_FIELDS)) // 2 - 10 == 0x49


def test_start_payload_with_pin():
    assert ctl.start_payload() == "0007000d003a6000A007e4000400000000"
    assert ctl.start_payload(None) == ctl.start_payload()
    # wie die App nach der PIN-Abfrage: e400040000 + PIN, niedriges Byte zuerst
    assert ctl.start_payload(1234) == "0007000d003a6000A007e400040000d204"
    assert ctl.start_payload(7) == "0007000d003a6000A007e4000400000700"


def test_apply_days_changes_only_selected_days():
    fields = sch.fields_from_reply(APP_FIELDS)
    new = sch.apply_days(fields, ["saturday"], [(14 * 60, 19 * 60)])
    changed = {k for k in fields if fields[k] != new[k]}
    assert changed == {
        "saturday_timer_1_start_time_hour",
        "saturday_timer_1_length_minutes",
        "saturday_timer_1_timer_mode",
    }
    assert new["saturday_timer_1_length_minutes"] == 300
    # Tag ohne Zeiten = an diesem Tag nicht maehen
    off = sch.apply_days(fields, ["monday"], [])
    assert sch.active_windows(off)["monday"] == []
    assert sch.active_windows(off)["tuesday"] == sch.active_windows(fields)["tuesday"]
    # zwei Fenster, in beliebiger Reihenfolge
    two = sch.apply_days(fields, ["friday"], [(15 * 60, 18 * 60), (9 * 60, 11 * 60 + 30)])
    assert sch.active_windows(two)["friday"] == [(9, 0, 150), (15, 0, 180)]


@pytest.mark.parametrize(
    ("windows", "key"),
    [
        ([(600, 600)], "schedule_end_before_start"),
        ([(700, 600)], "schedule_end_before_start"),
        ([(600, 1440)], "schedule_end_before_start"),
        ([(-1, 60)], "schedule_end_before_start"),
        ([(600, 720), (700, 800)], "schedule_overlap"),
        ([(600, 720), (500, 900)], "schedule_overlap"),
        ([(1, 2), (3, 4), (5, 6)], "schedule_invalid"),
    ],
)
def test_check_windows(windows, key):
    with pytest.raises(sch.ScheduleError) as err:
        sch.check_windows(windows)
    assert err.value.key == key


def test_check_windows_ok():
    assert sch.check_windows([(600, 720), (720, 800)]) == [(600, 720), (720, 800)]
    assert sch.check_windows([(0, 1439)]) == [(0, 1439)]
    assert sch.check_windows([]) == []


@pytest.mark.parametrize(
    "broken",
    [
        None,
        {},
        {**APP_FIELDS, "sunday_timer_2_timer_mode": None},
        {k: v for k, v in APP_FIELDS.items() if k != "monday_timer_1_length_minutes"},
        {**APP_FIELDS, "monday_timer_1_length_minutes": 70000},
        {**APP_FIELDS, "monday_timer_1_start_time_hour": "9"},
        {**APP_FIELDS, "monday_timer_1_timer_mode": True},
    ],
)
def test_incomplete_reply_is_refused(broken):
    with pytest.raises(sch.ScheduleError) as err:
        sch.fields_from_reply(broken)
    assert err.value.key == "schedule_read_failed"


def test_apply_days_rejects_unknown_day():
    with pytest.raises(sch.ScheduleError):
        sch.apply_days(sch.fields_from_reply(APP_FIELDS), ["someday"], [])


# --- Aktion "Maehplan setzen" ---------------------------------------------------

class FakeMower:
    """Antwortet wie der Maeher: liest und speichert den Plan."""

    def __init__(self, hass, control, fields, *, read_ok=True, store=True, save_code=0):
        self.hass, self.control = hass, control
        self.fields = dict(fields)
        self.read_ok, self.store, self.save_code = read_ok, store, save_code
        self.sent: list[str] = []
        control._mqtt.publish.side_effect = self.publish

    def publish(self, topic, payload, qos):
        assert topic == f"$7/{DID}" and qos == 1
        hexed = payload.hex()
        self.sent.append(hexed)
        body = hexed[20:]
        if body.startswith("420100"):
            response = dict(self.fields) if self.read_ok else {"return_code": 0}
            self._reply("420100", {**response, "return_code": 0})
        elif body.startswith("400146"):
            if self.store and self.save_code == 0:
                self.fields = _decode(body)
            self._reply(body, {"return_code": self.save_code})

    def _reply(self, request, response):
        raw = json.dumps({"request": {"request_payload": request}, "response": response})
        msg = SimpleNamespace(topic=f"$6/{DID}", payload=b"\x00\x06" + raw.encode())
        self.hass.loop.call_soon_threadsafe(self.control._on_message, None, None, msg)

    @property
    def saves(self):
        return [p for p in self.sent if p[20:].startswith("400146")]


def _decode(body: str) -> dict:
    data = bytes.fromhex(body[6:])
    fields = {}
    for d, day in enumerate(sch.WEEKDAYS):
        for s, slot in enumerate(sch.SLOTS):
            o = d * 10 + s * 5
            fields[f"{day}_timer_{slot}_start_time_hour"] = data[o]
            fields[f"{day}_timer_{slot}_start_time_minute"] = data[o + 1]
            fields[f"{day}_timer_{slot}_length_minutes"] = data[o + 2] | data[o + 3] << 8
            fields[f"{day}_timer_{slot}_timer_mode"] = data[o + 4]
    return fields


async def _call(hass, **data):
    await hass.services.async_call(
        DOMAIN, "set_schedule",
        {"entity_id": eid(hass, "lawn_mower", "mower"), **data}, blocking=True)


async def _ready(hass, aioclient_mock, **kw):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    return entry, control, FakeMower(hass, control, APP_FIELDS, **kw)


async def test_set_schedule_flow(hass, aioclient_mock):
    """Lesen, nur Mo+Do aendern, speichern, nochmal lesen und vergleichen."""
    _, _, mower = await _ready(hass, aioclient_mock)
    before = dict(mower.fields)
    await _call(hass, weekdays=["monday", "thursday"], start_1="14:00:00", end_1="19:00:00")
    assert mower.sent[0] == READ
    assert len(mower.saves) == 1
    assert mower.sent[-1] == READ  # Kontrolle nach dem Speichern
    for day in sch.WEEKDAYS:
        expected = (
            [(14, 0, 300)] if day in ("monday", "thursday")
            else sch.active_windows(before)[day]
        )
        assert sch.active_windows(mower.fields)[day] == expected
    # nicht beruehrte Tage: Byte fuer Byte gleich
    old, new = sch.save_payload(before)[26:], mower.saves[0][26:]
    for d, day in enumerate(sch.WEEKDAYS):
        if day not in ("monday", "thursday"):
            assert old[d * 20:(d + 1) * 20].lower() == new[d * 20:(d + 1) * 20]


async def test_set_schedule_two_windows_and_off(hass, aioclient_mock):
    _, _, mower = await _ready(hass, aioclient_mock)
    await _call(hass, weekdays=["saturday"], start_1="09:00", end_1="11:30",
                start_2="15:00", end_2="18:00")
    assert sch.active_windows(mower.fields)["saturday"] == [(9, 0, 150), (15, 0, 180)]
    await _call(hass, weekdays=["saturday", "monday"])
    assert sch.active_windows(mower.fields)["saturday"] == []
    assert sch.active_windows(mower.fields)["monday"] == []


async def test_set_schedule_same_plan_sends_nothing(hass, aioclient_mock):
    _, _, mower = await _ready(hass, aioclient_mock)
    await _call(hass, weekdays=["monday"], start_1="09:00", end_1="12:30")
    assert mower.saves == [] and mower.sent == [READ]


@pytest.mark.parametrize(
    ("data", "key"),
    [
        ({"start_1": "14:00"}, "schedule_incomplete"),
        ({"end_2": "14:00"}, "schedule_incomplete"),
        ({"start_1": "19:00", "end_1": "14:00"}, "schedule_end_before_start"),
        ({"start_1": "14:00", "end_1": "00:00"}, "schedule_end_before_start"),
        ({"start_1": "10:00", "end_1": "14:00", "start_2": "13:00", "end_2": "15:00"},
         "schedule_overlap"),
    ],
)
async def test_set_schedule_invalid_sends_nothing(hass, aioclient_mock, data, key):
    _, _, mower = await _ready(hass, aioclient_mock)
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], **data)
    assert err.value.translation_key == key
    assert mower.sent == []


async def test_set_schedule_read_failed_sends_nothing(hass, aioclient_mock):
    _, _, mower = await _ready(hass, aioclient_mock, read_ok=False)
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], start_1="14:00", end_1="19:00")
    assert err.value.translation_key == "schedule_read_failed"
    assert mower.saves == []


async def test_set_schedule_no_reply_sends_nothing(hass, aioclient_mock, monkeypatch):
    entry, control, mower = await _ready(hass, aioclient_mock)
    control._mqtt.publish.side_effect = lambda *a: mower.sent.append(a[1].hex())
    monkeypatch.setattr(ctl, "CONFIRM_TIMEOUT", 0.05)
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], start_1="14:00", end_1="19:00")
    assert err.value.translation_key == "control_no_reply"
    assert mower.sent == [READ]
    assert control._queries == {}


async def test_set_schedule_not_confirmed(hass, aioclient_mock):
    """Maeher bestaetigt, liest aber den alten Plan zurueck: Fehler melden."""
    _, _, mower = await _ready(hass, aioclient_mock, store=False)
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], start_1="14:00", end_1="19:00")
    assert err.value.translation_key == "schedule_not_confirmed"


async def test_set_schedule_rejected(hass, aioclient_mock):
    _, _, mower = await _ready(hass, aioclient_mock, save_code=1)
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], start_1="14:00", end_1="19:00")
    assert err.value.translation_key == "control_rejected"
    assert mower.sent[-1] == READ  # trotzdem nachgesehen


async def test_set_schedule_reply_without_code_but_saved(hass, aioclient_mock):
    """Antwort ohne return_code, Plan aber gespeichert: zaehlt, was gelesen wird."""
    _, _, mower = await _ready(hass, aioclient_mock)
    original = mower.publish

    def publish(topic, payload, qos):
        body = payload.hex()[20:]
        if body.startswith("400146"):
            mower.sent.append(payload.hex())
            mower.fields = _decode(body)
            mower._reply(body, {"response_payload": "41010100"})
            return
        original(topic, payload, qos)
    mower.control._mqtt.publish.side_effect = publish
    await _call(hass, weekdays=["monday"], start_1="14:00", end_1="19:00")
    assert sch.active_windows(mower.fields)["monday"] == [(14, 0, 300)]


async def test_set_schedule_blocked_while_continuous(hass, aioclient_mock):
    entry, _, mower = await _ready(hass, aioclient_mock)
    entry.runtime_data.async_set_continuous(DID, dt_util.utcnow() + timedelta(days=1))
    await hass.async_block_till_done()
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], start_1="14:00", end_1="19:00")
    assert err.value.translation_key == "schedule_continuous_active"
    assert mower.sent == []


async def test_set_schedule_needs_control(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], start_1="14:00", end_1="19:00")
    assert err.value.translation_key == "control_disabled"


async def test_set_schedule_bad_day(hass, aioclient_mock):
    import voluptuous as vol
    await _ready(hass, aioclient_mock)
    with pytest.raises(vol.Invalid):
        await _call(hass, weekdays=["someday"], start_1="14:00", end_1="19:00")
    with pytest.raises(vol.Invalid):
        await _call(hass, weekdays=[], start_1="14:00", end_1="19:00")


# --- PIN ------------------------------------------------------------------------

async def _options(hass, entry, **data):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    return await hass.config_entries.options.async_configure(
        result["flow_id"], {"control": "read_and_control", **data})


async def test_pin_option(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    for bad in ("123", "12345", "12a4"):
        result = await _options(hass, entry, pin=bad)
        assert result["errors"] == {"pin": "pin_invalid"}
    result = await _options(hass, entry, pin="0042")
    await hass.async_block_till_done()
    assert entry.options["pin"] == "0042"
    # leer = keine PIN
    await _options(hass, entry, pin="")
    await hass.async_block_till_done()
    assert "pin" not in entry.options


async def test_start_without_pin_unchanged(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options=CONTROL, datapoints=CHARGING)
    control = _connect(entry)
    sent = []

    def publish(topic, payload, qos):
        sent.append(payload.hex())
        if len(sent) == 1:
            raw = b'{"request":{"request_payload":"e4000400000000"},"response":{"return_code":0}}'
            hass.loop.call_soon_threadsafe(control._on_message, None, None,
                                           SimpleNamespace(topic=f"$6/{DID}", payload=raw))
    control._mqtt.publish.side_effect = publish
    await hass.services.async_call("lawn_mower", "start_mowing",
                                   {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)
    assert sent[0].endswith("e4000400000000")


async def test_start_with_pin(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, options={**CONTROL, "pin": "1234"},
                         datapoints=CHARGING)
    control = _connect(entry)
    sent = []

    def publish(topic, payload, qos):
        sent.append(payload.hex())
        if len(sent) == 1:
            raw = b'{"request":{"request_payload":"e400040000d204"},"response":{"return_code":0}}'
            hass.loop.call_soon_threadsafe(control._on_message, None, None,
                                           SimpleNamespace(topic=f"$6/{DID}", payload=raw))
    control._mqtt.publish.side_effect = publish
    await hass.services.async_call("lawn_mower", "start_mowing",
                                   {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)
    assert sent[0].endswith("e400040000d204")


async def test_diagnostics_hide_pin(hass, aioclient_mock):
    from custom_components.greenworks import diagnostics

    from .test_greenworks import dp
    dps = dict(CHARGING)
    dps["96"] = dp({"request_time": "2026-11-01T10:00:00Z",
                    "request_payload": "e400040000a520"})
    entry = await _setup(hass, aioclient_mock, options={**CONTROL, "pin": "8357"},
                         datapoints=dps)
    diag = await diagnostics.async_get_config_entry_diagnostics(hass, entry)
    text = json.dumps(diag, default=str)
    assert "8357" not in text and "a520" not in text
    assert diag["options"]["pin"] == "**REDACTED**"
    assert "e40004**REDACTED**" in text
    assert diagnostics._hide_pin({"request_payload": "DA0104ffff1234"}) == {
        "request_payload": "DA0104**REDACTED**"}
    assert diagnostics._hide_pin([{"request_payload": "e60002feff"}]) == [
        {"request_payload": "e60002feff"}]


async def test_set_schedule_save_without_confirmation_but_saved(hass, aioclient_mock, monkeypatch):
    """Live gesehen: Plan gespeichert, Bestaetigung kam nicht. Nachlesen entscheidet."""
    from custom_components.greenworks import lawn_mower as lm
    monkeypatch.setattr(lm, "SAVE_CONFIRM_TIMEOUT", 0.05)
    _, _, mower = await _ready(hass, aioclient_mock)
    original = mower.publish

    def publish(topic, payload, qos):
        body = payload.hex()[20:]
        if body.startswith("400146"):
            mower.sent.append(payload.hex())
            mower.fields = _decode(body)  # gespeichert, aber keine Antwort
            return
        original(topic, payload, qos)
    mower.control._mqtt.publish.side_effect = publish
    await _call(hass, weekdays=["monday"], start_1="14:00", end_1="18:00")
    assert sch.active_windows(mower.fields)["monday"] == [(14, 0, 240)]
    assert mower.sent[-1] == READ


async def test_set_schedule_save_without_confirmation_not_saved(hass, aioclient_mock, monkeypatch):
    from custom_components.greenworks import lawn_mower as lm
    monkeypatch.setattr(lm, "SAVE_CONFIRM_TIMEOUT", 0.05)
    _, _, mower = await _ready(hass, aioclient_mock)
    original = mower.publish

    def publish(topic, payload, qos):
        if payload.hex()[20:].startswith("400146"):
            mower.sent.append(payload.hex())
            return
        original(topic, payload, qos)
    mower.control._mqtt.publish.side_effect = publish
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], start_1="14:00", end_1="18:00")
    assert err.value.translation_key == "schedule_not_confirmed"


async def test_set_schedule_check_read_times_out(hass, aioclient_mock, monkeypatch):
    _, control, mower = await _ready(hass, aioclient_mock)
    original = mower.publish
    reads = []

    def publish(topic, payload, qos):
        if payload.hex()[20:].startswith("420100"):
            reads.append(1)
            if len(reads) > 1:
                mower.sent.append(payload.hex())
                return  # Kontrolle bleibt unbeantwortet
        original(topic, payload, qos)
    control._mqtt.publish.side_effect = publish
    monkeypatch.setattr(ctl, "CONFIRM_TIMEOUT", 0.3)
    with pytest.raises(HomeAssistantError) as err:
        await _call(hass, weekdays=["monday"], start_1="14:00", end_1="18:00")
    assert err.value.translation_key == "schedule_not_confirmed"


def test_parse_reply_header_with_brace():
    """Laengenbyte 0x7b ("{") im Kopf darf die Antwort nicht verschlucken."""
    body = b'{"request":{"request_payload":"400146"},"response":{"return_code":0}}'
    assert ctl.parse_reply(b"\x00\x06\x08{" + body)["response"]["return_code"] == 0
    assert ctl.parse_reply(b"{{{{{{") is None
