"""Greenworks-Maehroboter fuer Home Assistant."""

from __future__ import annotations

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GreenworksClient
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.LAWN_MOWER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: GreenworksConfigEntry) -> bool:
    """Integration aus einem Konfigurationseintrag einrichten."""
    client = GreenworksClient(
        async_get_clientsession(hass), entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
    )
    coordinator = GreenworksCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GreenworksConfigEntry) -> bool:
    """Integration entladen."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# Version 0.2.0
