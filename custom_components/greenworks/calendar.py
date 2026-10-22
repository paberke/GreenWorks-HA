"""Kalender fuer Greenworks: der Maehplan als Termine (nur Anzeige)."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .coordinator import GreenworksConfigEntry, GreenworksCoordinator
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksScheduleCalendar(coordinator, device_id) for device_id in coordinator.data
    )


class GreenworksScheduleCalendar(GreenworksEntity, CalendarEntity):
    """Maehfenster aus dem Maehplan der App als Kalendertermine."""

    _attr_translation_key = "calendar"

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "calendar")

    def _summary(self) -> str:
        return "Mähen" if (self.hass.config.language or "").startswith("de") else "Mowing"

    def _events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        """Alle Maehfenster, die sich mit dem Zeitraum [start, end) ueberschneiden."""
        mower = self.mower
        if mower is None or not mower.schedule:
            return []
        events: list[CalendarEvent] = []
        # einen Tag frueher beginnen, damit Fenster ueber Mitternacht dabei sind
        day = dt_util.start_of_local_day(dt_util.as_local(start)) - timedelta(days=1)
        last = dt_util.as_local(end)
        while day < last:
            for begin, length in mower.schedule.get(day.weekday(), []):
                if length <= 0:
                    continue
                ev_start = dt_util.as_local(day + timedelta(minutes=begin))
                ev_end = ev_start + timedelta(minutes=length)
                if ev_end > start and ev_start < end:
                    events.append(
                        CalendarEvent(start=ev_start, end=ev_end, summary=self._summary())
                    )
            day = dt_util.start_of_local_day(day + timedelta(days=1, hours=2))
        events.sort(key=lambda e: e.start)
        return events

    @property
    def event(self) -> CalendarEvent | None:
        """Laufendes oder naechstes Maehfenster (innerhalb einer Woche)."""
        now = dt_util.now()
        upcoming = self._events(now, now + timedelta(days=8))
        return upcoming[0] if upcoming else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return self._events(start_date, end_date)


# Version 0.3.1
