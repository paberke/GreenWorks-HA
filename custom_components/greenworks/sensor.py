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
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import WEEKDAYS, GreenworksMower
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


_DAY_SHORT = {
    "de": ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"),
    "en": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
}


def _lang(lang: str | None) -> str:
    return "de" if (lang or "").startswith("de") else "en"


def _hhmm(minutes: int) -> str:
    minutes %= 1440
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _day_windows(m: GreenworksMower, day: int) -> str:
    windows = (m.schedule or {}).get(day) or []
    return ", ".join(f"{_hhmm(start)}–{_hhmm(start + length)}" for start, length in windows)


def _schedule_summary(m: GreenworksMower, lang: str) -> str | None:
    """Kurzform des Maehplans, z. B. 'Mo–Fr 09:00–12:30'."""
    if m.schedule is None:
        return None
    short = _DAY_SHORT[_lang(lang)]
    groups: list[tuple[int, int, str]] = []
    for day in range(7):
        text = _day_windows(m, day)
        if groups and text and groups[-1][2] == text and groups[-1][1] == day - 1:
            groups[-1] = (groups[-1][0], day, text)
        elif text:
            groups.append((day, day, text))
    if not groups:
        return "Kein Mähplan" if _lang(lang) == "de" else "No schedule"
    parts = [
        f"{short[a]}{'' if a == b else (', ' if b == a + 1 else '–') + short[b]} {text}"
        for a, b, text in groups
    ]
    return "; ".join(parts)[:255]


def _schedule_attrs(m: GreenworksMower, lang: str) -> dict[str, Any]:
    if m.schedule is None:
        return {}
    attrs: dict[str, Any] = {day: (_day_windows(m, i) or "–") for i, day in enumerate(WEEKDAYS)}
    attrs["updated"] = m.schedule_time.isoformat() if m.schedule_time else None
    return attrs


def _error_attrs(m: GreenworksMower, lang: str) -> dict[str, Any]:
    attrs: dict[str, Any] = {"text": error_text(m.last_error_code, lang)}
    if m.error_history is not None:
        attrs["history"] = [
            f"{dt_util.as_local(when).strftime('%d.%m.%Y %H:%M')} – {error_text(code, lang)} ({code})"
            for when, code in m.error_history
        ]
        attrs["history_updated"] = (
            m.error_history_time.isoformat() if m.error_history_time else None
        )
    return attrs


_WIRE_NAMES = {
    "de": {0: "Leitdraht 1", 1: "Leitdraht 2", 2: "Begrenzungsdraht, rechts herum", 3: "Begrenzungsdraht, links herum"},
    "en": {0: "Guide wire 1", 1: "Guide wire 2", 2: "Boundary wire, right direction", 3: "Boundary wire, left direction"},
}


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _range(m: GreenworksMower, name: str) -> str | None:
    pair = (m.wire_corridor or {}).get(name)
    return f"{pair[0]}–{pair[1]}" if pair else None


def _start_point_attrs(m: GreenworksMower, lang: str) -> dict[str, Any]:
    if m.start_points is None:
        return {}
    names = _WIRE_NAMES[_lang(lang)]
    attrs: dict[str, Any] = {}
    for num, how, dist, often in m.start_points:
        wire = names.get(how, names[0])
        attrs[f"point_{num}"] = f"{wire}, {dist} m, {often} %"
    attrs["charging_station"] = f"{max(0, 100 - sum(p[3] for p in m.start_points))} %"
    attrs["updated"] = _iso(m.start_points_time)
    return attrs


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
        attr_fn=_error_attrs,
    ),
    GreenworksSensorDescription(
        key="last_error_time",
        translation_key="last_error_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda m: m.last_error_time,
    ),
    GreenworksSensorDescription(
        key="schedule",
        translation_key="schedule",
        value_fn=lambda m: None,  # wird sprachabhaengig in native_value gebildet
        attr_fn=_schedule_attrs,
    ),
    GreenworksSensorDescription(
        key="software",
        translation_key="software",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.firmware,
        attr_fn=lambda m, lang: {
            "cutting_unit": m.sw_cutting,
            "charging_station": m.sw_charging_station,
        },
    ),
    GreenworksSensorDescription(
        key="drive_past_wire",
        translation_key="drive_past_wire",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.drive_past_wire / 10 if m.drive_past_wire else None,
        attr_fn=lambda m, lang: {"updated": _iso(m.drive_past_wire_time)} if m.drive_past_wire else {},
    ),
    GreenworksSensorDescription(
        key="wire_distance",
        translation_key="wire_distance",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: _range(m, "boundary"),
        attr_fn=lambda m, lang: {
            "guide_wire_1": _range(m, "guide_1"),
            "guide_wire_2": _range(m, "guide_2"),
            "updated": _iso(m.wire_corridor_time),
        } if m.wire_corridor else {},
    ),
    GreenworksSensorDescription(
        key="start_points",
        translation_key="start_points",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: len(m.start_points) if m.start_points is not None else None,
        attr_fn=_start_point_attrs,
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
        if mower is None:
            return None
        if self.entity_description.key == "schedule":
            return _schedule_summary(mower, self.hass.config.language)
        return self.entity_description.value_fn(mower)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        mower = self.mower
        if mower is None or self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(mower, self.hass.config.language)


# Version 0.2.9
