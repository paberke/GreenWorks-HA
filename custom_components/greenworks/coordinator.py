"""DataUpdateCoordinator fuer Greenworks."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GreenworksAuthError, GreenworksClient, GreenworksError, GreenworksMower
from .const import DOMAIN, UPDATE_INTERVAL

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

    async def _async_update_data(self) -> dict[int, GreenworksMower]:
        try:
            return await self.client.async_get_mowers()
        except GreenworksAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GreenworksError as err:
            raise UpdateFailed(str(err)) from err


# Version 0.2.1
