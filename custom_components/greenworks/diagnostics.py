"""Diagnosedaten (Einstellungen > Geraete > Diagnose herunterladen)."""

from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .coordinator import GreenworksConfigEntry

TO_REDACT = {
    CONF_EMAIL,
    CONF_PASSWORD,
    "serial",
    "sn",
    "serial_number",
    "mower_serial_number",
    "latitude",
    "longitude",
    "geofence_latitude",
    "geofence_longitude",
    "mac",
    "ip",
    "return_code",
    "loop_code",
    "cm_id",
    "pin",
}

# Datenpunkte ab 225 sind Fertigungs-/Geraetedaten als Text (u. a. Seriennummer,
# Teilenummern, SIM-Kartennummer) - komplett unkenntlich machen.
RAW_ID_DATAPOINT_MIN = 225


# Befehle, in denen die PIN des Maehers steht (Starten mit PIN, PIN aendern):
# nur der Befehlsanfang bleibt sichtbar
_PIN_PAYLOAD = re.compile(
    r'("request_payload"\s*:\s*"(?:e40004|da0104))[0-9a-f]*', re.IGNORECASE
)


def _hide_pin(value: Any) -> Any:
    """PIN aus gespeicherten Befehlen entfernen (Datenpunkte sind JSON-Text)."""
    if isinstance(value, str):
        return _PIN_PAYLOAD.sub(r"\1**REDACTED**", value)
    if isinstance(value, dict):
        return {
            key: (
                item[:6] + "**REDACTED**"
                if key == "request_payload"
                and isinstance(item, str)
                and item.lower().startswith(("e40004", "da0104"))
                else _hide_pin(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_hide_pin(item) for item in value]
    return value


def _redact_mower(mower: dict[str, Any]) -> dict[str, Any]:
    raw = mower.get("raw_datapoints")
    if isinstance(raw, dict):
        mower["raw_datapoints"] = {
            key: (
                "**REDACTED**"
                if key.isdigit() and int(key) >= RAW_ID_DATAPOINT_MIN
                else _hide_pin(value)
            )
            for key, value in raw.items()
        }
    return async_redact_data(mower, TO_REDACT)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GreenworksConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "mowers": {
            str(dev_id): _redact_mower(asdict(mower))
            for dev_id, mower in (coordinator.data or {}).items()
        },
    }


# Version 0.6.0
