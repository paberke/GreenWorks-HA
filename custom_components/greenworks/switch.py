"""Schalter fuer Greenworks: Winterpause (nur in Home Assistant, steuert nicht den Maeher)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
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
        GreenworksWinterPauseSwitch(coordinator, device_id) for device_id in coordinator.data
    )


class GreenworksWinterPauseSwitch(GreenworksEntity, SwitchEntity):
    """Winterpause: keine Offline-Hinweise, Problem-Sensor bleibt auf OK.

    Aendert nur die Anzeige in Home Assistant. Am Maeher wird nichts geschaltet.
    """

    _attr_translation_key = "winter_pause"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "winter_pause")

    @property
    def is_on(self) -> bool:
        return self.coordinator.winter_pause(self._device_id)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.async_set_winter_pause(self._device_id, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.async_set_winter_pause(self._device_id, False)


# Version 0.3.1
