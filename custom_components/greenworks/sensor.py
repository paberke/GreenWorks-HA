"""Sensoren fuer Greenworks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GreenworksMower
from .const import MOWER_STATES
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import GreenworksEntity


def _hours(seconds: int | None) -> float | None:
    return round(seconds / 3600, 1) if seconds is not None else None


@dataclass(frozen=True, kw_only=True)
class GreenworksSensorDescription(SensorEntityDescription):
    value_fn: Callable[[GreenworksMower], Any]


SENSORS: tuple[GreenworksSensorDescription, ...] = (
    GreenworksSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[*MOWER_STATES.values(), "unknown"],
        value_fn=lambda m: (
            None if m.state_code is None else MOWER_STATES.get(m.state_code, "unknown")
        ),
    ),
    GreenworksSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda m: m.battery,
    ),
    GreenworksSensorDescription(
        key="next_start",
        translation_key="next_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda m: m.next_start,
    ),
    GreenworksSensorDescription(
        key="last_error",
        translation_key="last_error",
        value_fn=lambda m: m.last_error_code,
    ),
    GreenworksSensorDescription(
        key="last_error_time",
        translation_key="last_error_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda m: m.last_error_time,
    ),
    GreenworksSensorDescription(
        key="cutting_time",
        translation_key="cutting_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda m: _hours(m.cutting_time),
    ),
    GreenworksSensorDescription(
        key="running_time",
        translation_key="running_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: _hours(m.running_time),
    ),
    GreenworksSensorDescription(
        key="charging_time",
        translation_key="charging_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: _hours(m.charging_time),
    ),
    GreenworksSensorDescription(
        key="fatal_errors",
        translation_key="fatal_errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.fatal_errors,
    ),
    GreenworksSensorDescription(
        key="signal_quality",
        translation_key="signal_quality",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.signal_quality,
    ),
    GreenworksSensorDescription(
        key="status_time",
        translation_key="status_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.status_time,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksSensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSORS
    )


class GreenworksSensor(GreenworksEntity, SensorEntity):
    entity_description: GreenworksSensorDescription

    def __init__(
        self,
        coordinator: GreenworksCoordinator,
        device_id: int,
        description: GreenworksSensorDescription,
    ) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        mower = self.mower
        return None if mower is None else self.entity_description.value_fn(mower)


# Version 0.2.0
