"""GPS-Position des Maehers (standardmaessig deaktiviert)."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant

from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity


PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksTracker(coordinator, device_id) for device_id in coordinator.data
    )


class GreenworksTracker(GreenworksEntity, TrackerEntity):
    """Position des Maehers fuer die Karte."""

    _attr_translation_key = "position"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "position")

    @property
    def latitude(self) -> float | None:
        mower = self.mower
        return mower.latitude if mower else None

    @property
    def longitude(self) -> float | None:
        mower = self.mower
        return mower.longitude if mower else None

    @property
    def location_accuracy(self) -> float:
        mower = self.mower
        return (mower.gps_accuracy if mower else None) or 0


# Version 0.4.0
