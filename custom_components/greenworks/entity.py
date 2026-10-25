"""Gemeinsame Basis fuer alle Greenworks-Entitaeten."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

try:  # ab Home Assistant 2025.3
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
except ImportError:  # aeltere Versionen
    from homeassistant.helpers.entity_platform import (  # type: ignore[assignment]
        AddEntitiesCallback as AddConfigEntryEntitiesCallback,
    )

from .api import GreenworksMower
from .const import DOMAIN, ENTITY_GROUPS, GROUP_STANDARD
from .coordinator import GreenworksCoordinator, enabled_groups


def _hw_version(mower: GreenworksMower | None) -> str | None:
    """z. B. 'Rev. 1 (2019-02)' aus den Geraetedaten des Maehers."""
    if mower is None or (mower.revision is None and mower.production_date is None):
        return None
    parts = []
    if mower.revision is not None:
        parts.append(f"Rev. {mower.revision}")
    if mower.production_date is not None:
        parts.append(f"({mower.production_date:%Y-%m})")
    return " ".join(parts)


class GreenworksEntity(CoordinatorEntity[GreenworksCoordinator]):
    """Basisklasse: ordnet die Entitaet dem Maeher-Geraet zu."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int, key: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{key}"
        # Neue Entitaeten nur aktivieren, wenn ihre Gruppe eingeschaltet ist
        group = ENTITY_GROUPS.get(key, GROUP_STANDARD)
        self._attr_entity_registry_enabled_default = group in enabled_groups(
            coordinator.config_entry
        )
        mower = self.mower
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device_id))},
            manufacturer="Greenworks",
            model=(mower.model if mower else None) or "Robotermaeher",
            name=mower.name if mower else "Greenworks",
            serial_number=mower.serial if mower else None,
            model_id=mower.part_number if mower else None,
            hw_version=_hw_version(mower),
            sw_version=mower.firmware if mower else None,
        )

    @property
    def mower(self) -> GreenworksMower | None:
        return (self.coordinator.data or {}).get(self._device_id)

    @property
    def available(self) -> bool:
        return super().available and self.mower is not None


# Version 0.4.0
