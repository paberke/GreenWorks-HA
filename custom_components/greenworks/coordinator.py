"""DataUpdateCoordinator fuer Greenworks."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import GreenworksAuthError, GreenworksClient, GreenworksError, GreenworksMower
from .const import (
    CONF_OUTAGE_GRACE,
    COUNTED_STATES,
    DEFAULT_OUTAGE_GRACE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

type GreenworksConfigEntry = ConfigEntry[GreenworksCoordinator]


class GreenworksCoordinator(DataUpdateCoordinator[dict[int, GreenworksMower]]):
    """Holt regelmaessig die Daten aller Maeher des Kontos."""

    config_entry: GreenworksConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: GreenworksConfigEntry, client: GreenworksClient
    ) -> None:
        interval = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.client = client
        self._outage_grace = timedelta(
            minutes=int(entry.options.get(CONF_OUTAGE_GRACE, DEFAULT_OUTAGE_GRACE))
        )
        # Beginn der aktuellen Stoerung (None = letzte Abfrage war erfolgreich)
        self._failing_since: datetime | None = None
        # Mitgezaehlte Maehzeit je Maeher, wird dauerhaft gespeichert:
        # {"<device_id>": {"stats": <Zeitpunkt der echten Statistik>, "seconds": <gezaehlt>}}
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.counters.{entry.entry_id}")
        self._counters: dict[str, dict[str, Any]] = {}
        self._last_success: datetime | None = None

    async def async_load_counters(self) -> None:
        """Gespeicherte Zaehler laden (vor der ersten Abfrage)."""
        data = await self._store.async_load()
        if isinstance(data, dict):
            self._counters = data

    def _count_mowing(self, mowers: dict[int, GreenworksMower], now: datetime) -> None:
        """Maehzeit seit der letzten echten Statistik mitzaehlen.

        Gezaehlt wird nur die Zeit zwischen zwei Abfragen, bei denen der Maeher
        beide Male maehte (eher zu wenig als zu viel). Kommt eine neue echte
        Statistik, beginnt die Zaehlung von vorn.
        """
        elapsed = 0.0
        if self._last_success is not None:
            # nach laengeren Luecken nicht blind hochrechnen
            limit = 3 * self.update_interval.total_seconds()
            elapsed = min((now - self._last_success).total_seconds(), limit)
        for dev_id, mower in mowers.items():
            key = str(dev_id)
            counter = self._counters.setdefault(key, {"stats": None, "seconds": 0.0})
            stats = mower.statistics_time.isoformat() if mower.statistics_time else None
            if counter.get("stats") != stats:
                counter["stats"], counter["seconds"] = stats, 0.0
            else:
                prev = (self.data or {}).get(dev_id)
                if (
                    elapsed > 0
                    and prev is not None
                    and prev.online is not False
                    and mower.online is not False
                    and prev.state_code in COUNTED_STATES
                    and mower.state_code in COUNTED_STATES
                ):
                    counter["seconds"] = float(counter.get("seconds", 0)) + elapsed
            mower.counted_cutting = int(counter.get("seconds", 0))
        self._store.async_delay_save(lambda: self._counters, 60)

    async def _async_update_data(self) -> dict[int, GreenworksMower]:
        try:
            mowers = await self.client.async_get_mowers()
        except GreenworksAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GreenworksError as err:
            now = dt_util.utcnow()
            if self._failing_since is None:
                self._failing_since = now
            # Kurze Aussetzer (z. B. DNS, Cloud kurz weg): letzte Werte behalten
            if self.data and now - self._failing_since < self._outage_grace:
                _LOGGER.debug("Greenworks-Cloud kurz nicht erreichbar, behalte letzte Werte: %s", err)
                return self.data
            raise UpdateFailed(str(err)) from err
        if self._failing_since is not None:
            _LOGGER.debug("Greenworks-Cloud wieder erreichbar")
        self._failing_since = None
        now = dt_util.utcnow()
        self._count_mowing(mowers, now)
        self._last_success = now
        return mowers


# Version 0.2.12
