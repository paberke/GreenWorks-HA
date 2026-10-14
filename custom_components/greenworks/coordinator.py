"""DataUpdateCoordinator fuer Greenworks."""

from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import GreenworksAuthError, GreenworksClient, GreenworksError, GreenworksMower
from .const import DOMAIN, OUTAGE_GRACE, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type GreenworksConfigEntry = ConfigEntry[GreenworksCoordinator]


class GreenworksCoordinator(DataUpdateCoordinator[dict[int, GreenworksMower]]):
    """Holt regelmaessig die Daten aller Maeher des Kontos."""

    config_entry: GreenworksConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: GreenworksConfigEntry, client: GreenworksClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        # Beginn der aktuellen Stoerung (None = letzte Abfrage war erfolgreich)
        self._failing_since: datetime | None = None

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
            if self.data and now - self._failing_since < OUTAGE_GRACE:
                _LOGGER.debug("Greenworks-Cloud kurz nicht erreichbar, behalte letzte Werte: %s", err)
                return self.data
            raise UpdateFailed(str(err)) from err
        if self._failing_since is not None:
            _LOGGER.debug("Greenworks-Cloud wieder erreichbar")
        self._failing_since = None
        return mowers


# Version 0.2.10
