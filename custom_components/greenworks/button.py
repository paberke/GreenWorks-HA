"""Knoepfe fuer Greenworks: alle Auswahlen der App (Parken, Start, Pause,
Maehen ohne Unterbrechung).

Nur aktiv bei "Lesen und steuern" (Knopf "Konfigurieren"), sonst deaktiviert.
Wie in der App sind Knoepfe gesperrt, die im aktuellen Zustand nicht gehen.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .api import GreenworksMower
from .const import DOMAIN
from .control import (
    continuous_payload,
    minutes_until_midnight,
    park_payload,
    pause_payload,
    start_payload,
)
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity

PARALLEL_UPDATES = 1

# Eigene Zeiten (Zahlenfelder), Standard wenn noch nichts eingestellt ist
CUSTOM_PARK_HOURS = "park_hours"
CUSTOM_CONTINUOUS_DAYS = "continuous_days"
DEFAULT_CUSTOM = {CUSTOM_PARK_HOURS: 3, CUSTOM_CONTINUOUS_DAYS: 3}

# Geparkt durch Zeitplan, Regen- oder Frostschutz: nur "bis auf Weiteres"
_PARK_ONLY_UNTIL_FURTHER_NOTICE = frozenset({2, 5, 6})


def can_start(m: GreenworksMower) -> bool:
    """Start / Zeitplan fortsetzen: pausiert oder vom Benutzer geparkt."""
    return m.state_code == 3 or (m.state_code == 2 and m.park_reason == 4)


def can_pause(m: GreenworksMower) -> bool:
    """Pause: maeht, verlaesst die Station oder sucht sie."""
    return m.state_code in (4, 5, 6)


def can_park(m: GreenworksMower) -> bool:
    """Parken: wie der Park-Knopf der App."""
    if m.state_code in (1, 3, 7):
        return True
    return m.state_code == 2 and m.park_reason in (1, 2, 5, 6)


def can_park_timed(m: GreenworksMower) -> bool:
    """2 Stunden / Rest des Tages / eigene Zeit: nicht im Zeitplan-, Regen- oder Frost-Parken."""
    return can_park(m) and not (
        m.state_code == 2 and m.park_reason in _PARK_ONLY_UNTIL_FURTHER_NOTICE
    )


def can_mow_continuously(m: GreenworksMower) -> bool:
    """Maehen ohne Unterbrechung einschalten: nicht waehrend der Nebenflaeche."""
    return m.state_code is not None and m.state_code != 12


def _always(m: GreenworksMower) -> bool:
    return True


@dataclass(frozen=True, kw_only=True)
class GreenworksButtonDescription(ButtonEntityDescription):
    """Knopf mit dem Befehl, den er schickt, und wann er geht."""

    payload: Callable[[GreenworksCoordinator, int], str]
    allowed: Callable[[GreenworksMower], bool] = _always


def _custom(coordinator: GreenworksCoordinator, device_id: int, key: str) -> int:
    return coordinator.custom_values.get((device_id, key), DEFAULT_CUSTOM[key])


BUTTONS: tuple[GreenworksButtonDescription, ...] = (
    GreenworksButtonDescription(
        key="start",
        translation_key="start",
        payload=lambda c, d: start_payload(),
        allowed=can_start,
    ),
    GreenworksButtonDescription(
        key="pause",
        translation_key="pause",
        payload=lambda c, d: pause_payload(),
        allowed=can_pause,
    ),
    GreenworksButtonDescription(
        key="park_until_further_notice",
        translation_key="park_until_further_notice",
        payload=lambda c, d: park_payload(None),
        allowed=can_park,
    ),
    GreenworksButtonDescription(
        key="park_2h",
        translation_key="park_2h",
        payload=lambda c, d: park_payload(120),
        allowed=can_park_timed,
    ),
    GreenworksButtonDescription(
        key="park_rest_of_day",
        translation_key="park_rest_of_day",
        payload=lambda c, d: park_payload(minutes_until_midnight()),
        allowed=can_park_timed,
    ),
    GreenworksButtonDescription(
        key="park_custom",
        translation_key="park_custom",
        payload=lambda c, d: park_payload(_custom(c, d, CUSTOM_PARK_HOURS) * 60),
        allowed=can_park_timed,
    ),
    GreenworksButtonDescription(
        key="continuous_2_days",
        translation_key="continuous_2_days",
        payload=lambda c, d: continuous_payload(2 * 1440),
        allowed=can_mow_continuously,
    ),
    GreenworksButtonDescription(
        key="continuous_1_week",
        translation_key="continuous_1_week",
        payload=lambda c, d: continuous_payload(7 * 1440),
        allowed=can_mow_continuously,
    ),
    GreenworksButtonDescription(
        key="continuous_custom",
        translation_key="continuous_custom",
        payload=lambda c, d: continuous_payload(
            _custom(c, d, CUSTOM_CONTINUOUS_DAYS) * 1440
        ),
        allowed=can_mow_continuously,
    ),
    GreenworksButtonDescription(
        key="continuous_off",
        translation_key="continuous_off",
        payload=lambda c, d: continuous_payload(0),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksButton(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in BUTTONS
    )


class GreenworksButton(GreenworksEntity, ButtonEntity):
    """Schickt beim Druecken einen Befehl an den Maeher."""

    entity_description: GreenworksButtonDescription

    def __init__(
        self,
        coordinator: GreenworksCoordinator,
        device_id: int,
        description: GreenworksButtonDescription,
    ) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        mower = self.mower
        return (
            super().available
            and mower is not None
            and mower.online is not False
            and self.entity_description.allowed(mower)
        )

    async def async_press(self) -> None:
        control = self.coordinator.control
        if control is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_disabled"
            )
        await control.async_send(
            self._device_id,
            self.entity_description.payload(self.coordinator, self._device_id),
        )
        await self.coordinator.async_request_refresh()


# Version 0.6.1
