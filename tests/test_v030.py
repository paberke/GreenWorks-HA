"""0.3.0: Gruppen, Problem, Laedt, Winterpause, Fehler-Ereignis, Kalender,
Hinweise unter Reparaturen, Software-Update."""

import copy
from datetime import timedelta
import json

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.const import (
    BASE_URL,
    CONF_GROUPS,
    CONF_OFFLINE_HOURS,
    DOMAIN,
    FIRMWARE_URL,
)

from .test_greenworks import DATAPOINTS, DID, PID, PROPERTIES, UID, mock_cloud

FW_URL = f"{FIRMWARE_URL}api/Update/v2/DeviceSwUpdateLink/RLM2/100.2.1/6.65.1775739325"


def cloud(aioclient_mock, *, online=True, datapoints=None, firmware=None):
    """Cloud nachstellen; firmware=None -> Update-Server antwortet nicht."""
    aioclient_mock.clear_requests()
    mock_cloud(aioclient_mock)
    aioclient_mock.clear_requests()
    aioclient_mock.post(f"{BASE_URL}user_auth", json={
        "access_token": "tok", "refresh_token": "ref", "user_id": UID, "expire_in": 7200})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", json={"list": [
        {"id": DID, "product_id": PID, "name": "Testmaeher", "sn": "SN0000001", "is_online": online}]})
    aioclient_mock.get(f"{BASE_URL}product/{PID}/device/{DID}/property", json=PROPERTIES)
    dps = copy.deepcopy(datapoints or DATAPOINTS)
    dps["online"] = online
    # Geraetekennung und volle Version fuer die Update-Pruefung
    dps["25"] = json.dumps({"request": {}, "response": {
        "device_group_no": 100, "sub_device_no": 2, "variant_no": 1}})
    if datapoints is None:
        dps["117"] = json.dumps({"request": {
            "mower_main_application_major_sw_version": 6, "mower_main_application_minor_sw_version": 65,
            "mower_main_application_build_no": 1775739325}})
    aioclient_mock.get(f"{BASE_URL}product/{PID}/v_device/{DID}", json=dps)
    if firmware is not None:
        aioclient_mock.post(FW_URL, json=firmware)


def eid(hass, domain, key):
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, f"{DID}_{key}")


async def _setup(hass, aioclient_mock, *, options=None, minor_version=1, **kw):
    cloud(aioclient_mock, **kw)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=str(UID), minor_version=minor_version,
                            options=options if options is not None else {},
                            data={CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _refresh(hass, entry):
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


# --- Gruppen -------------------------------------------------------------------

async def test_new_install_standard_only(hass, aioclient_mock):
    """Neue Einrichtung: nur Standard ist an, der Rest ist angelegt, aber deaktiviert."""
    cloud(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    assert result["step_id"] == "groups"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry"
    assert result["options"] == {CONF_GROUPS: []}
    await hass.async_block_till_done()
    reg = er.async_get(hass)
    assert hass.states.get(eid(hass, "sensor", "status")) is not None
    assert hass.states.get(eid(hass, "binary_sensor", "problem")) is not None
    for domain, key in (("sensor", "schedule"), ("sensor", "cutting_time"), ("sensor", "software"),
                        ("calendar", "calendar"), ("device_tracker", "position")):
        entity = reg.async_get(eid(hass, domain, key))
        assert entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION, key


async def test_new_install_with_groups(hass, aioclient_mock):
    cloud(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "t@e.de", CONF_PASSWORD: "x"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_GROUPS: ["calendar", "statistics"]})
    await hass.async_block_till_done()
    assert hass.states.get(eid(hass, "calendar", "calendar")) is not None
    assert hass.states.get(eid(hass, "sensor", "cutting_time")) is not None
    assert hass.states.get(eid(hass, "sensor", "schedule")) is None


async def test_existing_install_keeps_everything(hass, aioclient_mock):
    """Bestehende Einrichtung (vor 0.3.0): alles bleibt, nur der Kalender ist neu und aus."""
    entry = await _setup(hass, aioclient_mock)
    assert entry.minor_version == 2
    assert entry.options[CONF_GROUPS] == ["errors_detailed", "statistics", "app_settings", "diagnostics"]
    for domain, key in (("sensor", "schedule"), ("sensor", "cutting_time"), ("sensor", "software"),
                        ("sensor", "last_error"), ("binary_sensor", "rain_sensor")):
        assert hass.states.get(eid(hass, domain, key)) is not None, key
    reg = er.async_get(hass)
    assert reg.async_get(eid(hass, "calendar", "calendar")).disabled_by is not None
    assert reg.async_get(eid(hass, "device_tracker", "position")).disabled_by is not None


async def test_toggle_group_keeps_entity_ids(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    reg = er.async_get(hass)
    schedule = eid(hass, "sensor", "schedule")
    # Gruppe "Einstellungen aus der App" ausschalten
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_GROUPS: ["errors_detailed", "statistics", "diagnostics"]})
    await hass.async_block_till_done()
    assert reg.async_get(schedule).disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert hass.states.get(schedule) is None
    # wieder einschalten: gleiche Entity-ID, wieder aktiv
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_GROUPS: ["errors_detailed", "statistics", "diagnostics", "app_settings"]})
    await hass.async_block_till_done()
    assert eid(hass, "sensor", "schedule") == schedule
    assert reg.async_get(schedule).disabled_by is None
    assert hass.states.get(schedule) is not None


async def test_user_disabled_entity_stays_disabled(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    reg = er.async_get(hass)
    software = eid(hass, "sensor", "software")
    reg.async_update_entity(software, disabled_by=er.RegistryEntryDisabler.USER)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert reg.async_get(software).disabled_by is er.RegistryEntryDisabler.USER


# --- Problem, Laedt, Winterpause ---------------------------------------------------

async def test_problem_with_error_reason(hass, aioclient_mock):
    hass.config.language = "de"
    dps = copy.deepcopy(DATAPOINTS)
    dps["33"] = json.dumps({"request": {
        "current_mower_main_state": 9, "event_id": 13, "timestamp_for_error": 1791568428,
        "request_time": "2026-10-13T07:29:20.263Z"}, "response": {"return_code": 0}})
    await _setup(hass, aioclient_mock, datapoints=dps)
    st = hass.states.get(eid(hass, "binary_sensor", "problem"))
    assert st.state == "on"                                    # Zustand 9 = schwerer Fehler
    assert st.attributes["reason"] == "Zu starke Neigung (Fehler 13)"
    assert hass.states.get(eid(hass, "binary_sensor", "charging")).state == "off"


async def test_problem_ok_and_charging(hass, aioclient_mock):
    dps = copy.deepcopy(DATAPOINTS)
    dps.pop("33")
    dps["31"] = json.dumps({"request": {"request_time": "2026-10-12T20:00:00Z"}, "response": {
        "mower_main_state": 7, "next_start": 4294967295, "battery_status": 80}})
    dps.pop("32")
    await _setup(hass, aioclient_mock, datapoints=dps)
    st = hass.states.get(eid(hass, "binary_sensor", "problem"))
    assert st.state == "off" and st.attributes["reason"] is None
    assert hass.states.get(eid(hass, "binary_sensor", "charging")).state == "on"


async def test_offline_problem_and_winter_pause(hass, aioclient_mock):
    hass.config.language = "de"
    entry = await _setup(hass, aioclient_mock, online=False)
    problem = eid(hass, "binary_sensor", "problem")
    status = eid(hass, "sensor", "status")
    switch = eid(hass, "switch", "winter_pause")
    assert hass.states.get(problem).state == "on"
    assert hass.states.get(problem).attributes["reason"] == "Offline"
    assert hass.states.get(status).state == "offline"
    assert hass.states.get(switch).state == "off"
    await hass.services.async_call("switch", "turn_on", {"entity_id": switch}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(switch).state == "on"
    assert hass.states.get(problem).state == "off"
    assert hass.states.get(problem).attributes["reason"] == "Winterpause"
    assert hass.states.get(status).state == "winter_pause"
    # bleibt nach einem Neuladen erhalten
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(switch).state == "on"
    assert hass.states.get(status).state == "winter_pause"


# --- Hinweise unter Reparaturen ----------------------------------------------------

async def test_offline_repair_issue(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, online=False)
    issues = ir.async_get(hass)
    issue_id = f"mower_offline_{DID}"
    assert issues.async_get_issue(DOMAIN, issue_id) is None      # gerade erst offline
    # So tun, als waere er seit 2 Stunden offline
    coordinator = entry.runtime_data
    coordinator._counters[str(DID)]["offline_since"] = (
        dt_util.utcnow() - timedelta(hours=2)).isoformat()
    await _refresh(hass, entry)
    issue = issues.async_get_issue(DOMAIN, issue_id)
    assert issue is not None and issue.translation_key == "mower_offline"
    # Winterpause: Hinweis verschwindet
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": eid(hass, "switch", "winter_pause")}, blocking=True)
    assert issues.async_get_issue(DOMAIN, issue_id) is None
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": eid(hass, "switch", "winter_pause")}, blocking=True)
    assert issues.async_get_issue(DOMAIN, issue_id) is not None
    # wieder online: Hinweis verschwindet von selbst
    cloud(aioclient_mock, online=True)
    await _refresh(hass, entry)
    assert issues.async_get_issue(DOMAIN, issue_id) is None


async def test_offline_repair_switched_off(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, online=False, options={CONF_OFFLINE_HOURS: 0})
    entry.runtime_data._counters[str(DID)]["offline_since"] = (
        dt_util.utcnow() - timedelta(hours=50)).isoformat()
    await _refresh(hass, entry)
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"mower_offline_{DID}") is None


async def test_cloud_repair_issue(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    aioclient_mock.clear_requests()
    aioclient_mock.post(f"{BASE_URL}user_auth", json={
        "access_token": "tok", "refresh_token": "ref", "user_id": UID, "expire_in": 7200})
    aioclient_mock.get(f"{BASE_URL}user/{UID}/subscribe/devices", status=500)
    coordinator = entry.runtime_data
    coordinator._failing_since = dt_util.utcnow() - timedelta(hours=3)
    await _refresh(hass, entry)
    assert ir.async_get(hass).async_get_issue(DOMAIN, "cloud_unreachable") is not None
    cloud(aioclient_mock)
    await _refresh(hass, entry)
    assert ir.async_get(hass).async_get_issue(DOMAIN, "cloud_unreachable") is None


# --- Fehler-Ereignis ---------------------------------------------------------------

async def test_error_event(hass, aioclient_mock):
    hass.config.language = "de"
    entry = await _setup(hass, aioclient_mock)
    event = eid(hass, "event", "error")
    assert hass.states.get(event).state == "unknown"            # alter Fehler: kein Ereignis
    dps = copy.deepcopy(DATAPOINTS)
    dps["33"] = json.dumps({"request": {
        "current_mower_main_state": 8, "event_id": 2, "timestamp_for_error": 1791568428 + 86400,
        "request_time": "2026-10-11T07:29:20.263Z"}, "response": {"return_code": 0}})
    cloud(aioclient_mock, datapoints=dps)
    await _refresh(hass, entry)
    st = hass.states.get(event)
    assert st.state != "unknown"
    assert st.attributes["event_type"] == "error"
    assert st.attributes["code"] == 2
    assert st.attributes["text"] == "Kollisionssensor defekt oder Mäher steckt fest"
    # gleicher Fehler noch einmal: kein neues Ereignis
    first = st.state
    await _refresh(hass, entry)
    assert hass.states.get(event).state == first


# --- Kalender ------------------------------------------------------------------------

async def test_calendar_events(hass, aioclient_mock):
    hass.config.language = "de"
    dps = copy.deepcopy(DATAPOINTS)
    dps["125"] = json.dumps({"request": {"request_time": "2026-10-13T12:45:09.274Z"}, "response": {
        "monday_timer_1_start_time_hour": 9, "monday_timer_1_start_time_minute": 0,
        "monday_timer_1_length_minutes": 210, "monday_timer_1_timer_mode": 1,
        "monday_timer_2_start_time_hour": 23, "monday_timer_2_start_time_minute": 0,
        "monday_timer_2_length_minutes": 120, "monday_timer_2_timer_mode": 1,
        "response_time": "2026-10-13T12:45:10Z"}})
    await _setup(hass, aioclient_mock, datapoints=dps,
                 options={CONF_GROUPS: ["calendar"]}, minor_version=2)
    cal = eid(hass, "calendar", "calendar")
    assert hass.states.get(cal) is not None
    # Montag, 19.10.2026 bis Dienstag, 20.10.2026 12:00
    start = dt_util.as_local(dt_util.parse_datetime("2026-10-19T00:00:00+02:00"))
    end = start + timedelta(hours=36)
    result = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": cal, "start_date_time": start.isoformat(), "end_date_time": end.isoformat()},
        blocking=True, return_response=True)
    events = result[cal]["events"]
    assert [(e["summary"], e["start"][11:16], e["end"][11:16]) for e in events] == [
        ("Mähen", "09:00", "12:30"),
        ("Mähen", "23:00", "01:00"),            # ueber Mitternacht
    ]
    assert events[1]["end"].startswith("2026-10-20")


# --- Software-Update -------------------------------------------------------------------

async def test_firmware_update_available(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, firmware={
        "isNeedUpdate": True, "targetVersion": "6.70.1790000000", "currentVersion": "6.65.1775739325"})
    st = hass.states.get(eid(hass, "update", "firmware_update"))
    assert st.state == "on"
    assert st.attributes["installed_version"] == "6.65.1775739325"
    assert st.attributes["latest_version"] == "6.70.1790000000"
    assert st.attributes["release_summary"]


async def test_firmware_up_to_date(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, firmware={"isNeedUpdate": False})
    assert hass.states.get(eid(hass, "update", "firmware_update")).state == "off"


async def test_firmware_server_not_answering(hass, aioclient_mock):
    """Antwortet der Update-Server nicht, gibt es einfach keinen Update-Eintrag."""
    entry = await _setup(hass, aioclient_mock)
    assert entry.state is ConfigEntryState.LOADED
    assert eid(hass, "update", "firmware_update") is None


async def test_firmware_only_with_diagnostics_group(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, firmware={"isNeedUpdate": False},
                 options={CONF_GROUPS: []}, minor_version=2)
    assert not any(c[1].host == "gfuapi.globetools.systems" for c in aioclient_mock.mock_calls)
    assert eid(hass, "update", "firmware_update") is None


async def test_remove_entry_cleans_issues(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, online=False)
    entry.runtime_data._counters[str(DID)]["offline_since"] = (
        dt_util.utcnow() - timedelta(hours=2)).isoformat()
    await _refresh(hass, entry)
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"mower_offline_{DID}") is not None
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"mower_offline_{DID}") is None


async def test_software_reported_time(hass, aioclient_mock):
    """Software-Sensor: Zeitpunkt, zu dem der Maeher die Version selbst gemeldet hat."""
    dps = copy.deepcopy(DATAPOINTS)
    dps["117"] = json.dumps({"request": {
        "mower_main_application_major_sw_version": 6, "mower_main_application_minor_sw_version": 65,
        "request_time": "2026-10-13T17:53:17.706Z"}})
    await _setup(hass, aioclient_mock, datapoints=dps)
    st = hass.states.get(eid(hass, "sensor", "software"))
    assert st.state == "6.65"
    assert st.attributes["updated"].startswith("2026-10-13T17:53:17")
