"""Binaersensoren fuer Greenworks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .api import GreenworksMower
from .const import CONF_BLADE_LIMIT, DEFAULT_BLADE_LIMIT
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity


@dataclass(frozen=True, kw_only=True)
class GreenworksBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[GreenworksMower], bool | None]


BINARY_SENSORS: tuple[GreenworksBinaryDescription, ...] = (
    GreenworksBinaryDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.online,
    ),
    GreenworksBinaryDescription(
        key="rain_sensor",
        translation_key="rain_sensor",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.rain_sensor,
    ),
    GreenworksBinaryDescription(
        key="frost_sensor",
        translation_key="frost_sensor",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.frost_sensor,
    ),
)


class GreenworksBladeChangeSensor(GreenworksEntity, BinarySensorEntity):
    """An, sobald die Messer-Laufzeit die eingestellte Grenze erreicht."""

    _attr_translation_key = "blade_change_due"

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "blade_change_due")

    @property
    def _limit_hours(self) -> int:
        options = self.coordinator.config_entry.options
        return int(options.get(CONF_BLADE_LIMIT, DEFAULT_BLADE_LIMIT))

    def _blade_hours(self) -> float | None:
        mower = self.mower
        if mower is None or mower.blade_time is None:
            return None
        return (mower.blade_time + mower.counted_cutting) / 3600

    @property
    def is_on(self) -> bool | None:
        hours, limit = self._blade_hours(), self._limit_hours
        if limit <= 0:
            return False  # Erinnerung ausgeschaltet
        return None if hours is None else hours >= limit

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        hours, limit = self._blade_hours(), self._limit_hours
        return {
            "limit": limit,
            "remaining": None
            if hours is None or limit <= 0
            else max(0.0, round(limit - hours, 1)),
        }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        GreenworksBinarySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in BINARY_SENSORS
    ]
    entities += [GreenworksBladeChangeSensor(coordinator, device_id) for device_id in coordinator.data]
    async_add_entities(entities)


class GreenworksBinarySensor(GreenworksEntity, BinarySensorEntity):
    entity_description: GreenworksBinaryDescription

    def __init__(
        self,
        coordinator: GreenworksCoordinator,
        device_id: int,
        description: GreenworksBinaryDescription,
    ) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        mower = self.mower
        return None if mower is None else self.entity_description.value_fn(mower)


# Version 0.2.14
