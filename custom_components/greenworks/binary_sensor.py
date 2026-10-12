"""Binaersensoren fuer Greenworks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GreenworksMower
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import GreenworksEntity


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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksBinarySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in BINARY_SENSORS
    )


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


# Version 0.2.1
