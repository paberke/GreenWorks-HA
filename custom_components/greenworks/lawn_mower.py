"""Maeher-Entitaet (lawn_mower) fuer Greenworks."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import status_key
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import GreenworksEntity

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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksLawnMower(coordinator, device_id) for device_id in coordinator.data
    )


class GreenworksLawnMower(GreenworksEntity, LawnMowerEntity):
    """Der Maehroboter selbst (vorerst nur Statusanzeige)."""

    _attr_name = None
    _attr_supported_features = LawnMowerEntityFeature(0)

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "mower")

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


# Version 0.2.7
