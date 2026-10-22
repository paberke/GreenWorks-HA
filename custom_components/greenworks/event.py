"""Ereignis fuer Greenworks: neuer Fehler des Maehers."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity
from .error_texts import error_text

PARALLEL_UPDATES = 0

EVENT_ERROR = "error"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksErrorEvent(coordinator, device_id) for device_id in coordinator.data
    )


class GreenworksErrorEvent(GreenworksEntity, EventEntity):
    """Loest einmal pro neuem Fehler aus (mit Code, Klartext und Uhrzeit)."""

    _attr_translation_key = "error"
    _attr_event_types = [EVENT_ERROR]

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "error")
        self._last_seen: datetime | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Zuletzt gemeldeten Fehler wiederherstellen: so wird ein Fehler, der waehrend
        # eines Neustarts passiert ist, nachgeholt, alte Fehler aber nicht erneut gemeldet.
        last = await self.async_get_last_state()
        if last is not None and last.attributes.get("time"):
            self._last_seen = dt_util.parse_datetime(str(last.attributes["time"]))
        mower = self.mower
        if self._last_seen is None and mower is not None:
            self._last_seen = mower.last_error_time
        self._check_new_error()

    @callback
    def _check_new_error(self) -> bool:
        mower = self.mower
        if mower is None or mower.last_error_time is None or mower.last_error_code is None:
            return False
        if self._last_seen is not None and mower.last_error_time <= self._last_seen:
            return False
        self._last_seen = mower.last_error_time
        self._trigger_event(
            EVENT_ERROR,
            {
                "code": mower.last_error_code,
                "text": error_text(mower.last_error_code, self.hass.config.language),
                "time": mower.last_error_time.isoformat(),
            },
        )
        self.async_write_ha_state()
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        if not self._check_new_error():
            super()._handle_coordinator_update()


# Version 0.3.0
