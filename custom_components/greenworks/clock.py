"""Uhr des Maehers automatisch stellen (Sommer-/Winterzeit), wie die Greenworks-App.

Der Maeher stellt die Zeitumstellung nicht selbst um. Die App fragt auf der
Seite Zeitplan die Uhr des Maehers ab (9c0000) und bietet bei einer
Abweichung "Fehlerhafte Uhrzeit" an. Mit OK schickt sie die aktuelle Zeit
(9a0008): UTC-Sekunden und Zeitzonen-Versatz in Sekunden, je 4 Byte mit dem
niedrigen Byte zuerst.

Diese Integration macht das selbst: regelmaessig pruefen und bei einer
Abweichung stellen. Massgeblich ist die Zeitzone, die in Home Assistant
eingestellt ist. Nur bei "Lesen und steuern", nur wenn der Maeher online ist
und gerade nicht maeht. Es wird nur die Uhrzeit gesendet, sonst nichts.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import GreenworksCoordinator

_LOGGER = logging.getLogger(__name__)

# Wie die App (RLM1ScheduleFragment)
TIME_REQUEST = "0007000900546000A0039c0000"
TIME_QUERY_KEY = "9c0000"
TIME_SET_HEAD = "0007001100566000A00b9a0008"

# Ab dieser Abweichung wird gestellt (die App meldet erst ab 15 Minuten)
MAX_DRIFT = 300  # Sekunden
# Zeitzonen-Versatz: Unterschiede kommen nur in ganzen Viertelstunden vor
MAX_OFFSET_DIFF = 60  # Sekunden
CHECK_INTERVAL = timedelta(hours=1)
FIRST_CHECK_DELAY = 120  # Sekunden nach dem Start (Steuerkanal verbindet erst)
VERIFY_DELAY = 5  # Sekunden bis zum Nachlesen
# Waehrend dieser Zustaende nie stellen: maeht, verlaesst / sucht die Station, Nebenflaeche
_BUSY_STATES = frozenset({4, 5, 6, 12})


def le32(value: int) -> str:
    """Zahl als 4 Byte, niedriges Byte zuerst; negativ im Zweierkomplement.

    Wie StringUtils.getEightLen bzw. getBig(Integer.toHexString(x)) der App.
    """
    if not -(2**31) <= value < 2**32:
        raise ValueError(value)
    return (value & 0xFFFFFFFF).to_bytes(4, "little").hex()


def ha_offset(now: datetime | None = None) -> int:
    """Versatz der in Home Assistant eingestellten Zeitzone in Sekunden (mit Sommerzeit)."""
    now = now or dt_util.now()
    offset = now.utcoffset()
    return int(offset.total_seconds()) if offset is not None else 0


def set_time_payload(now: datetime | None = None) -> str:
    """Befehl "Uhrzeit stellen" mit der aktuellen Zeit von Home Assistant."""
    now = now or dt_util.now()
    return TIME_SET_HEAD + le32(int(now.timestamp())) + le32(ha_offset(now))


def _number(response: dict[str, Any], key: str) -> int | None:
    value = response.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def clock_wrong(response: Any, now: datetime | None = None) -> bool | None:
    """Geht die Uhr des Maehers falsch? None = Antwort nicht verwertbar.

    Ohne verwertbare Antwort wird nie gestellt (z. B. andere Modelle, die die
    Abfrage anders oder gar nicht beantworten).
    """
    if not isinstance(response, dict):
        return None
    mower_utc = _number(response, "utc_time")
    mower_offset = _number(response, "time_zone_offset")
    if mower_utc is None or mower_offset is None:
        return None
    now = now or dt_util.now()
    return (
        abs(ha_offset(now) - mower_offset) > MAX_OFFSET_DIFF
        or abs(int(now.timestamp()) - mower_utc) > MAX_DRIFT
    )


def _reply_response(reply: Any) -> Any:
    return reply.get("response") if isinstance(reply, dict) else None


class GreenworksClock:
    """Prueft regelmaessig die Uhr aller Maeher und stellt sie bei Bedarf."""

    def __init__(self, hass: HomeAssistant, coordinator: GreenworksCoordinator) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._locks: dict[int, asyncio.Lock] = {}
        self._unsubs: list[Callable[[], None]] = []

    @callback
    def async_start(self) -> Callable[[], None]:
        """Pruefung kurz nach dem Start und danach stuendlich."""
        self._unsubs.append(
            async_call_later(self._hass, FIRST_CHECK_DELAY, self._async_check_all)
        )
        self._unsubs.append(
            async_track_time_interval(self._hass, self._async_check_all, CHECK_INTERVAL)
        )
        return self.async_stop

    @callback
    def async_stop(self) -> None:
        while self._unsubs:
            self._unsubs.pop()()

    def _lock(self, device_id: int) -> asyncio.Lock:
        return self._locks.setdefault(device_id, asyncio.Lock())

    async def _async_check_all(self, _now: Any = None) -> None:
        for device_id in list(self._coordinator.data or {}):
            await self.async_check(device_id)

    def _ready(self, device_id: int) -> bool:
        control = self._coordinator.control
        mower = (self._coordinator.data or {}).get(device_id)
        return (
            control is not None
            and control.connected
            and mower is not None
            and mower.online is not False
            and mower.state_code not in _BUSY_STATES
        )

    async def async_check(self, device_id: int) -> None:
        """Automatisch: Uhr abfragen und nur bei Abweichung stellen. Fehler nur ins Debug-Log."""
        if not self._ready(device_id):
            return
        lock = self._lock(device_id)
        if lock.locked():
            return
        async with lock:
            try:
                wrong = clock_wrong(await self._async_read(device_id))
                if not wrong:
                    return
                _LOGGER.debug("Uhr von Maeher %s weicht ab, stelle sie", device_id)
                await self._async_set(device_id)
            except HomeAssistantError as err:
                _LOGGER.debug(
                    "Uhr von Maeher %s nicht geprueft/gestellt: %s",
                    device_id,
                    err.translation_key,
                )

    async def async_set_now(self, device_id: int) -> None:
        """Von Hand (Taste / Aktion): immer stellen; Fehler gehen an den Benutzer."""
        control = self._coordinator.control
        if control is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_disabled"
            )
        async with self._lock(device_id):
            await self._async_set(device_id)

    async def _async_read(self, device_id: int, timeout: float | None = None) -> Any:
        control = self._coordinator.control
        return _reply_response(
            await control.async_query(device_id, TIME_REQUEST, TIME_QUERY_KEY, timeout)
        )

    async def _async_set(self, device_id: int) -> None:
        """Stellen und durch Nachlesen kontrollieren.

        Die App wertet die Antwort auf das Stellen nicht aus; entscheidend ist
        darum, ob die Uhr danach stimmt.
        """
        control = self._coordinator.control
        failure: HomeAssistantError | None = None
        try:
            await control.async_send(device_id, set_time_payload())
        except HomeAssistantError as err:
            if err.translation_key not in ("control_rejected", "control_no_reply"):
                raise
            failure = err
        await asyncio.sleep(VERIFY_DELAY)
        try:
            wrong = clock_wrong(await self._async_read(device_id))
        except HomeAssistantError:
            wrong = None
        if wrong is False:
            self._log_success(device_id)
            return
        if wrong is None and failure is None:
            # Bestaetigt, aber nicht nachlesbar: als erledigt werten
            self._log_success(device_id)
            return
        raise failure or HomeAssistantError(
            translation_domain=DOMAIN, translation_key="clock_not_set"
        )

    @callback
    def _log_success(self, device_id: int) -> None:
        mower = (self._coordinator.data or {}).get(device_id)
        name = mower.name if mower is not None else str(device_id)
        now = dt_util.now().strftime("%H:%M")
        german = (self._hass.config.language or "").startswith("de")
        message = (
            f"hat die Uhrzeit des Mähers auf {now} gestellt"
            if german
            else f"set the mower clock to {now}"
        )
        _LOGGER.info("Uhr von Maeher %s gestellt", name)
        entity_id = er.async_get(self._hass).async_get_entity_id(
            "lawn_mower", DOMAIN, f"{device_id}_mower"
        )
        self._hass.bus.async_fire(
            "logbook_entry",
            {
                "name": name,
                "message": message,
                "domain": DOMAIN,
                **({"entity_id": entity_id} if entity_id else {}),
            },
        )


# Version 0.7.0
