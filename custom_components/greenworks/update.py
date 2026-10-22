"""Software-Update-Anzeige fuer Greenworks (ohne Installieren-Knopf)."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    # Nur anlegen, wenn der Update-Server von Greenworks geantwortet hat
    async_add_entities(
        GreenworksFirmwareUpdate(coordinator, device_id)
        for device_id in coordinator.data
        if coordinator.firmware_info.get(device_id) is not None
    )


class GreenworksFirmwareUpdate(GreenworksEntity, UpdateEntity):
    """Zeigt an, ob es neue Maeher-Software gibt. Installiert wird ueber die App."""

    _attr_translation_key = "firmware_update"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "firmware_update")

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.firmware_info.get(self._device_id) is not None

    @property
    def installed_version(self) -> str | None:
        mower = self.mower
        return mower.firmware_full if mower else None

    @property
    def latest_version(self) -> str | None:
        info = self.coordinator.firmware_info.get(self._device_id) or {}
        if info.get("need_update"):
            return str(info.get("target_version") or "neu")
        return self.installed_version

    @property
    def release_summary(self) -> str | None:
        info = self.coordinator.firmware_info.get(self._device_id) or {}
        if not info.get("need_update"):
            return None
        if (self.hass.config.language or "").startswith("de"):
            return "Bitte über die Greenworks-App installieren (Seite „Software“)."
        return "Please install it with the Greenworks app (page “Software”)."


# Version 0.3.0
