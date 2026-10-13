"""Diagnosedaten (Einstellungen > Geraete > Diagnose herunterladen)."""

from __future__ import annotations

from dataclasses import asdict
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
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GreenworksConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "mowers": {
            str(dev_id): async_redact_data(asdict(mower), TO_REDACT)
            for dev_id, mower in (coordinator.data or {}).items()
        },
    }


# Version 0.2.3
