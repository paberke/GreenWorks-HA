"""Maeher-Entitaet (lawn_mower) fuer Greenworks."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_platform

from .button import can_park_timed
from .const import DOMAIN, status_key
from .control import (
    MAX_CONTINUOUS_DAYS,
    MAX_PARK_HOURS,
    continuous_payload,
    park_payload,
    pause_payload,
    start_payload,
)
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator, control_enabled
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity

SERVICE_PARK = "park"
SERVICE_MOW_CONTINUOUSLY = "mow_continuously"
ATTR_HOURS = "hours"
ATTR_DAYS = "days"

_RETURNING = getattr(LawnMowerActivity, "RETURNING", LawnMowerActivity.MOWING)

ACTIVITY_MAP: dict[int, LawnMowerActivity] = {
    1: LawnMowerActivity.PAUSED,  # Stopp-Taste gedrueckt
    2: LawnMowerActivity.DOCKED,  # geparkt (Grund siehe Status)
    3: LawnMowerActivity.PAUSED,
    4: LawnMowerActivity.MOWING,
    5: LawnMowerActivity.MOWING,  # verlaesst die Station
    6: _RETURNING,  # sucht die Station
    7: LawnMowerActivity.DOCKED,  # laedt
    8: LawnMowerActivity.ERROR,
    9: LawnMowerActivity.ERROR,  # schwerer Fehler
    10: LawnMowerActivity.ERROR,  # Wiederherstellung nach Fehler
    11: LawnMowerActivity.ERROR,  # Alarm (z. B. angehoben, Geofence)
    12: LawnMowerActivity.MOWING,  # maeht Nebenflaeche
}


PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksLawnMower(coordinator, device_id) for device_id in coordinator.data
    )
    platform = entity_platform.async_get_current_platform()
    # Eigene Zeiten (nur bei "Lesen und steuern" wirksam)
    platform.async_register_entity_service(
        SERVICE_PARK,
        {
            vol.Optional(ATTR_HOURS): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=MAX_PARK_HOURS)
            )
        },
        "async_park",
    )
    platform.async_register_entity_service(
        SERVICE_MOW_CONTINUOUSLY,
        {
            vol.Required(ATTR_DAYS): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=MAX_CONTINUOUS_DAYS)
            )
        },
        "async_mow_continuously",
    )


class GreenworksLawnMower(GreenworksEntity, LawnMowerEntity):
    """Der Maehroboter selbst. Steuern nur bei "Lesen und steuern"."""

    _attr_name = None

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "mower")
        if control_enabled(coordinator.config_entry):
            self._attr_supported_features = (
                LawnMowerEntityFeature.START_MOWING
                | LawnMowerEntityFeature.PAUSE
                | LawnMowerEntityFeature.DOCK
            )
        else:
            self._attr_supported_features = LawnMowerEntityFeature(0)

    async def _async_command(self, payload: str) -> None:
        control = self.coordinator.control
        if control is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_disabled"
            )
        await control.async_send(self._device_id, payload)
        await self.coordinator.async_request_refresh()

    async def async_start_mowing(self) -> None:
        """Maehen starten bzw. Zeitplan fortsetzen."""
        await self._async_command(start_payload())

    async def async_pause(self) -> None:
        await self._async_command(pause_payload())

    async def async_dock(self) -> None:
        """Zur Station und dort bleiben (Parken bis auf Weiteres)."""
        await self._async_command(park_payload(None))

    async def async_park(self, hours: int | None = None) -> None:
        """Parken fuer X Stunden, ohne Angabe bis auf Weiteres."""
        mower = self.mower
        if (
            hours is not None
            and self.coordinator.control is not None
            and mower is not None
            and not can_park_timed(mower)
        ):
            # Wie in der App: im Zeitplan-, Regen- oder Frost-Parken nur bis auf Weiteres
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="park_timed_not_possible"
            )
        await self._async_command(park_payload(None if hours is None else hours * 60))

    async def async_mow_continuously(self, days: int) -> None:
        """Maehen ohne Unterbrechung fuer X Tage, 0 = aus."""
        await self._async_command(continuous_payload(days * 1440))

    @property
    def available(self) -> bool:
        """Nicht verfuegbar, solange der Maeher offline ist."""
        mower = self.mower
        return super().available and mower is not None and mower.online is not False

    @property
    def activity(self) -> LawnMowerActivity | None:
        mower = self.mower
        if mower is None or mower.state_code is None:
            return None
        return ACTIVITY_MAP.get(mower.state_code)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        mower = self.mower
        if mower is None:
            return {}
        return {
            "status_code": mower.state_code,
            "status": status_key(mower.state_code, mower.park_reason),
            "park_reason_code": mower.park_reason,
            "sub_status_code": mower.sub_state_code,
        }


# Version 0.5.0
