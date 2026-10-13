"""Gemeinsame Basis fuer alle Greenworks-Entitaeten."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import GreenworksMower
from .const import DOMAIN
from .coordinator import GreenworksCoordinator


class GreenworksEntity(CoordinatorEntity[GreenworksCoordinator]):
    """Basisklasse: ordnet die Entitaet dem Maeher-Geraet zu."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int, key: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{key}"
        mower = self.mower
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device_id))},
            manufacturer="Greenworks",
            model=(mower.model if mower else None) or "Robotermaeher",
            name=mower.name if mower else "Greenworks",
            serial_number=mower.serial if mower else None,
            sw_version=mower.firmware if mower else None,
        )

    @property
    def mower(self) -> GreenworksMower | None:
        return (self.coordinator.data or {}).get(self._device_id)

    @property
    def available(self) -> bool:
        return super().available and self.mower is not None


# Version 0.2.7
