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
from .const import CONF_BLADE_LIMIT, DEFAULT_BLADE_LIMIT, PROBLEM_STATES, status_key
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity
from .error_texts import error_text

PARALLEL_UPDATES = 0

_REASONS = {
    "de": {"offline": "Offline", "winter_pause": "Winterpause", "error": "Fehler", "fatal": "Schwerer Fehler", "alarm": "Alarm"},
    "en": {"offline": "Offline", "winter_pause": "Winter pause", "error": "Error", "fatal": "Fatal error", "alarm": "Alarm"},
}


def _has_problem(m: GreenworksMower) -> bool | None:
    """Problem = offline (ausser in der Winterpause) oder Fehler/Alarm."""
    if m.online is False:
        return not m.winter_pause
    if m.state_code is None:
        return None
    return m.state_code in PROBLEM_STATES


def problem_reason(m: GreenworksMower, lang: str | None) -> str | None:
    """Kurzer Grund fuer den Problem-Sensor, z. B. 'Zu starke Neigung (Fehler 13)'."""
    de = (lang or "").startswith("de")
    texts = _REASONS["de" if de else "en"]
    if m.online is False:
        return texts["winter_pause"] if m.winter_pause else texts["offline"]
    if m.state_code not in PROBLEM_STATES:
        return texts["winter_pause"] if m.winter_pause else None
    code = m.last_error_code
    if code:
        return f"{error_text(code, lang)} ({'Fehler' if de else 'error'} {code})"
    return texts[{8: "error", 9: "fatal", 11: "alarm"}[m.state_code]]


@dataclass(frozen=True, kw_only=True)
class GreenworksBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[GreenworksMower], bool | None]


BINARY_SENSORS: tuple[GreenworksBinaryDescription, ...] = (
    GreenworksBinaryDescription(
        key="problem",
        translation_key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=_has_problem,
    ),
    GreenworksBinaryDescription(
        key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda m: None
        if m.state_code is None
        else m.online is not False and status_key(m.state_code, m.park_reason) == "charging",
    ),
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

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        mower = self.mower
        if mower is None or self.entity_description.key != "problem":
            return None
        return {"reason": problem_reason(mower, self.hass.config.language)}


# Version 0.3.0
