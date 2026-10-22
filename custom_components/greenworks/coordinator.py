"""DataUpdateCoordinator fuer Greenworks."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import GreenworksAuthError, GreenworksClient, GreenworksError, GreenworksMower
from .const import (
    CONF_GROUPS,
    CONF_OFFLINE_HOURS,
    CONF_OUTAGE_GRACE,
    COUNTED_STATES,
    DEFAULT_GROUPS_EXISTING,
    DEFAULT_OFFLINE_HOURS,
    DEFAULT_OUTAGE_GRACE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    GROUP_STANDARD,
)

_LOGGER = logging.getLogger(__name__)

type GreenworksConfigEntry = ConfigEntry[GreenworksCoordinator]

ISSUE_CLOUD = "cloud_unreachable"


def enabled_groups(entry: ConfigEntry) -> set[str]:
    """Eingeschaltete Gruppen (Standard ist immer dabei)."""
    return {GROUP_STANDARD, *entry.options.get(CONF_GROUPS, DEFAULT_GROUPS_EXISTING)}


def offline_issue_id(device_id: int) -> str:
    return f"mower_offline_{device_id}"


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
        # Ab wie vielen Stunden Ausfall ein Hinweis unter "Reparaturen" erscheint (0 = nie)
        self._offline_hours = int(entry.options.get(CONF_OFFLINE_HOURS, DEFAULT_OFFLINE_HOURS))
        # Beginn der aktuellen Stoerung (None = letzte Abfrage war erfolgreich)
        self._failing_since: datetime | None = None
        # Dauerhaft gespeichert je Maeher:
        # {"<device_id>": {"stats": <Zeitpunkt der echten Statistik>, "seconds": <gezaehlt>,
        #                  "winter_pause": bool, "offline_since": <Zeitpunkt>}}
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.counters.{entry.entry_id}")
        self._counters: dict[str, dict[str, Any]] = {}
        self._last_success: datetime | None = None

    async def async_load_counters(self) -> None:
        """Gespeicherte Zaehler laden (vor der ersten Abfrage)."""
        data = await self._store.async_load()
        if isinstance(data, dict):
            self._counters = data

    def _save(self) -> None:
        self._store.async_delay_save(lambda: self._counters, 60)

    async def async_flush(self) -> None:
        """Gespeicherte Werte sofort schreiben (z. B. beim Entladen)."""
        await self._store.async_save(self._counters)

    def _counter(self, device_id: int) -> dict[str, Any]:
        return self._counters.setdefault(str(device_id), {"stats": None, "seconds": 0.0})

    # --- Winterpause --------------------------------------------------------

    def winter_pause(self, device_id: int) -> bool:
        return bool(self._counters.get(str(device_id), {}).get("winter_pause", False))

    @callback
    def async_set_winter_pause(self, device_id: int, value: bool) -> None:
        """Winterpause ein-/ausschalten (aendert nur Home Assistant, nicht den Maeher)."""
        self._counter(device_id)["winter_pause"] = value
        self.hass.async_create_task(self.async_flush())
        mower = (self.data or {}).get(device_id)
        if mower is not None:
            mower.winter_pause = value
        self._update_issues(dt_util.utcnow())
        self.async_update_listeners()

    # --- Maehzeit mitzaehlen ----------------------------------------------------

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
            counter = self._counter(dev_id)
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

    def _track_online(self, mowers: dict[int, GreenworksMower], now: datetime) -> None:
        """Merken, seit wann ein Maeher offline ist; einmalig ins Protokoll schreiben."""
        for dev_id, mower in mowers.items():
            counter = self._counter(dev_id)
            mower.winter_pause = bool(counter.get("winter_pause", False))
            if mower.online is False:
                if not counter.get("offline_since"):
                    counter["offline_since"] = now.isoformat()
                    _LOGGER.info("Maeher %s ist offline", mower.name)
                mower.offline_since = dt_util.parse_datetime(counter["offline_since"])
            else:
                if counter.pop("offline_since", None):
                    _LOGGER.info("Maeher %s ist wieder online", mower.name)
                mower.offline_since = None

    # --- Hinweise unter "Reparaturen" ------------------------------------------

    def _update_issues(self, now: datetime) -> None:
        limit = timedelta(hours=self._offline_hours) if self._offline_hours > 0 else None
        # Cloud laenger nicht erreichbar
        if limit and self._failing_since and now - self._failing_since >= limit:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                ISSUE_CLOUD,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_CLOUD,
                translation_placeholders={"hours": str(self._offline_hours)},
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_CLOUD)
        # Maeher laenger offline (nicht in der Winterpause)
        for dev_id, mower in (self.data or {}).items():
            issue_id = offline_issue_id(dev_id)
            if (
                limit
                and not mower.winter_pause
                and mower.offline_since is not None
                and now - mower.offline_since >= limit
            ):
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    issue_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="mower_offline",
                    translation_placeholders={
                        "name": mower.name,
                        "hours": str(self._offline_hours),
                    },
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)

    # --- Abfrage ---------------------------------------------------------------

    async def _async_update_data(self) -> dict[int, GreenworksMower]:
        try:
            mowers = await self.client.async_get_mowers()
        except GreenworksAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="auth_failed"
            ) from err
        except GreenworksError as err:
            now = dt_util.utcnow()
            if self._failing_since is None:
                self._failing_since = now
            self._update_issues(now)
            # Kurze Aussetzer (z. B. DNS, Cloud kurz weg): letzte Werte behalten
            if self.data and now - self._failing_since < self._outage_grace:
                _LOGGER.debug("Greenworks-Cloud kurz nicht erreichbar, behalte letzte Werte: %s", err)
                return self.data
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cloud_unreachable",
                translation_placeholders={"error": str(err)},
            ) from err
        if self._failing_since is not None:
            _LOGGER.debug("Greenworks-Cloud wieder erreichbar")
        self._failing_since = None
        now = dt_util.utcnow()
        self._count_mowing(mowers, now)
        self._track_online(mowers, now)
        self._save()
        self._last_success = now
        # Hinweise schon mit den neuen Daten pruefen
        self.data = mowers
        self._update_issues(now)
        return mowers


# Version 0.3.1
