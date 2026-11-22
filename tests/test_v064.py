"""0.6.4: Nie personenbezogene Daten in Log (auch Debug), Fehlermeldungen oder Diagnose."""

import json
import logging
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.greenworks.const import BASE_URL, DOMAIN
from custom_components.greenworks.diagnostics import async_get_config_entry_diagnostics

from .test_greenworks import DID, PID, PROPERTIES, UID
from .test_v030 import _refresh, eid
from .test_v050 import CHARGING, CONTROL, _connect

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

    # Befehl mit PIN (Maeher antwortet nicht)
    control = _connect(entry)
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
