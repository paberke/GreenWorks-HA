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
    await coordinator.async_load_counters()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: GreenworksConfigEntry) -> None:
    """Einstellungen geaendert: Integration neu laden."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GreenworksConfigEntry) -> bool:
    """Integration entladen."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# Version 0.2.12
