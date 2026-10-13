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
from .const import ERROR_OPTIONS, MOWING_STATES, STATUS_OPTIONS, error_key, status_key
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import GreenworksEntity
from .error_texts import error_text


def _hours(seconds: int | None) -> float | None:
    return round(seconds / 3600, 1) if seconds is not None else None


def _is_mowing(m: GreenworksMower) -> bool:
    return m.state_code in MOWING_STATES


def _next_start(m: GreenworksMower):
    """Naechster Start: nur wenn der Maeher NICHT maeht.
    Beim Laden mitten im Fenster ist das eine Schaetzung des Maehers."""
    return None if _is_mowing(m) else m.next_start


def _mowing_end(m: GreenworksMower):
    """Maehende: beim Maehen liefert die Cloud im selben Feld das Fensterende."""
    return m.next_start if _is_mowing(m) else None


@dataclass(frozen=True, kw_only=True)
class GreenworksSensorDescription(SensorEntityDescription):
    value_fn: Callable[[GreenworksMower], Any]
    # Zweites Argument: Sprache von Home Assistant (z. B. "de")
    attr_fn: Callable[[GreenworksMower, str], dict[str, Any]] | None = None


SENSORS: tuple[GreenworksSensorDescription, ...] = (
    GreenworksSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=STATUS_OPTIONS,
        value_fn=lambda m: status_key(m.state_code, m.park_reason),
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
        value_fn=_next_start,
    ),
    GreenworksSensorDescription(
        key="mowing_end",
        translation_key="mowing_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_mowing_end,
    ),
    GreenworksSensorDescription(
        key="last_error",
        translation_key="last_error",
        value_fn=lambda m: m.last_error_code,
        attr_fn=lambda m, lang: {"meaning": error_key(m.last_error_code)},
    ),
    GreenworksSensorDescription(
        key="last_error_text",
        translation_key="last_error_text",
        device_class=SensorDeviceClass.ENUM,
        options=ERROR_OPTIONS,
        value_fn=lambda m: error_key(m.last_error_code),
        # Klartext als Attribut, damit er in Benachrichtigungen nutzbar ist
        attr_fn=lambda m, lang: {"text": error_text(m.last_error_code, lang)},
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
        key="blade_time",
        translation_key="blade_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda m: _hours(m.blade_time),
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
        key="statistics_time",
        translation_key="statistics_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.statistics_time,
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

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        mower = self.mower
        if mower is None or self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(mower, self.hass.config.language)


# Version 0.2.8b1
