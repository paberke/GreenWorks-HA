"""Zahlenfelder fuer die eigenen Zeiten der App (nur bei "Lesen und steuern").

Sie aendern nichts am Maeher, sondern legen nur fest, wie lange die Knoepfe
"Parken fuer eigene Zeit" und "Maehen ohne Unterbrechung: eigene Zeit" wirken.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant

from .button import CUSTOM_CONTINUOUS_DAYS, CUSTOM_PARK_HOURS, DEFAULT_CUSTOM
from .control import MAX_CONTINUOUS_DAYS, MAX_PARK_HOURS
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class GreenworksNumberDescription(NumberEntityDescription):
    """Zahlenfeld mit Standardwert."""

    default: int


NUMBERS: tuple[GreenworksNumberDescription, ...] = (
    GreenworksNumberDescription(
        key=CUSTOM_PARK_HOURS,
        translation_key=CUSTOM_PARK_HOURS,
        native_min_value=1,
        native_max_value=MAX_PARK_HOURS,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        default=DEFAULT_CUSTOM[CUSTOM_PARK_HOURS],
    ),
    GreenworksNumberDescription(
        key=CUSTOM_CONTINUOUS_DAYS,
        translation_key=CUSTOM_CONTINUOUS_DAYS,
        native_min_value=1,
        native_max_value=MAX_CONTINUOUS_DAYS,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.DAYS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        default=DEFAULT_CUSTOM[CUSTOM_CONTINUOUS_DAYS],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksNumber(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in NUMBERS
    )


class GreenworksNumber(GreenworksEntity, RestoreNumber):
    """Eigene Zeit, wird in Home Assistant gespeichert."""

    entity_description: GreenworksNumberDescription

    def __init__(
        self,
        coordinator: GreenworksCoordinator,
        device_id: int,
        description: GreenworksNumberDescription,
    ) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def _store_key(self) -> tuple[int, str]:
        return (self._device_id, self.entity_description.key)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        value = self.entity_description.default
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            minimum = int(self.entity_description.native_min_value or 1)
            maximum = int(self.entity_description.native_max_value or value)
            value = min(max(int(last.native_value), minimum), maximum)
        self.coordinator.custom_values[self._store_key] = value

    @property
    def native_value(self) -> float:
        return self.coordinator.custom_values.get(
            self._store_key, self.entity_description.default
        )

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.custom_values[self._store_key] = int(value)
        self.async_write_ha_state()


# Version 0.5.0
