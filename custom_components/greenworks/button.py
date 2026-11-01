"""Knoepfe fuer Greenworks: Parken und Maehen ohne Unterbrechung.

Nur aktiv bei "Lesen und steuern" (Knopf "Konfigurieren"), sonst deaktiviert.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .control import continuous_payload, minutes_until_midnight, park_payload
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class GreenworksButtonDescription(ButtonEntityDescription):
    """Knopf mit dem Befehl, den er schickt."""

    payload: Callable[[], str]


BUTTONS: tuple[GreenworksButtonDescription, ...] = (
    GreenworksButtonDescription(
        key="park_2h", translation_key="park_2h", payload=lambda: park_payload(120)
    ),
    GreenworksButtonDescription(
        key="park_rest_of_day",
        translation_key="park_rest_of_day",
        payload=lambda: park_payload(minutes_until_midnight()),
    ),
    GreenworksButtonDescription(
        key="continuous_2_days",
        translation_key="continuous_2_days",
        payload=lambda: continuous_payload(2 * 1440),
    ),
    GreenworksButtonDescription(
        key="continuous_1_week",
        translation_key="continuous_1_week",
        payload=lambda: continuous_payload(7 * 1440),
    ),
    GreenworksButtonDescription(
        key="continuous_off",
        translation_key="continuous_off",
        payload=lambda: continuous_payload(0),
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
        return super().available and mower is not None and mower.online is not False

    async def async_press(self) -> None:
        control = self.coordinator.control
        if control is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_disabled"
            )
        await control.async_send(self._device_id, self.entity_description.payload())
        await self.coordinator.async_request_refresh()


# Version 0.5.0
