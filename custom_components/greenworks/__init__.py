"""Greenworks-Maehroboter fuer Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GreenworksClient
from .const import (
    CONF_GROUPS,
    DEFAULT_GROUPS_EXISTING,
    DOMAIN,
    ENTITY_GROUPS,
    REMOVED_ENTITIES,
)
from .coordinator import (
    GreenworksConfigEntry,
    GreenworksCoordinator,
    enabled_groups,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
    Platform.DEVICE_TRACKER,
    Platform.EVENT,
    Platform.LAWN_MOWER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_migrate_entry(hass: HomeAssistant, entry: GreenworksConfigEntry) -> bool:
    """Bestehende Einrichtungen auf 0.3.0 heben: alle bisherigen Gruppen bleiben an."""
    if entry.version == 1 and entry.minor_version < 2:
        options = dict(entry.options)
        options.setdefault(CONF_GROUPS, list(DEFAULT_GROUPS_EXISTING))
        hass.config_entries.async_update_entry(entry, options=options, minor_version=2)
        _LOGGER.debug("Greenworks-Einrichtung auf Version 1.2 umgestellt")
    return True


@callback
def _async_sync_groups(hass: HomeAssistant, entry: GreenworksConfigEntry) -> None:
    """Entitaeten ausgeschalteter Gruppen deaktivieren, eingeschalteter wieder aktivieren.

    Nichts wird geloescht: die Entity-IDs bleiben gleich, wenn man eine Gruppe
    spaeter wieder einschaltet. Von Hand deaktivierte Entitaeten bleiben, wie sie sind.
    """
    groups = enabled_groups(entry)
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        _, _, key = entity.unique_id.partition("_")
        if key in REMOVED_ENTITIES:
            # in 0.3.0 angelegt, ab 0.3.1 entfernt (Software-Update-Anzeige)
            registry.async_remove(entity.entity_id)
            continue
        group = ENTITY_GROUPS.get(key)
        if group is None:
            continue
        if group in groups:
            if entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION:
                registry.async_update_entity(entity.entity_id, disabled_by=None)
        elif entity.disabled_by is None:
            registry.async_update_entity(
                entity.entity_id, disabled_by=er.RegistryEntryDisabler.INTEGRATION
            )
            # Den alten Zustand ("nicht verfuegbar") nicht stehen lassen
            hass.states.async_remove(entity.entity_id)


async def async_setup_entry(hass: HomeAssistant, entry: GreenworksConfigEntry) -> bool:
    """Integration aus einem Konfigurationseintrag einrichten."""
    client = GreenworksClient(
        async_get_clientsession(hass), entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
    )
    coordinator = GreenworksCoordinator(hass, entry, client)
    await coordinator.async_load_counters()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    _async_sync_groups(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: GreenworksConfigEntry) -> None:
    """Einstellungen geaendert: Integration neu laden."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GreenworksConfigEntry) -> bool:
    """Integration entladen."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_flush()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: GreenworksConfigEntry) -> None:
    """Integration entfernt: eigene Hinweise unter "Reparaturen" aufraeumen."""
    for domain, issue_id in list(ir.async_get(hass).issues):
        if domain == DOMAIN:
            ir.async_delete_issue(hass, DOMAIN, issue_id)


# Version 0.4.0
