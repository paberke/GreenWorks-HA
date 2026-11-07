"""Maeher-Entitaet (lawn_mower) fuer Greenworks."""

from __future__ import annotations

import asyncio
from datetime import time
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.util import dt as dt_util

from .button import can_park_timed
from .const import CONF_PIN, DOMAIN, status_key
from .control import (
    MAX_CONTINUOUS_DAYS,
    MAX_PARK_HOURS,
    continuous_payload,
    park_payload,
    pause_payload,
    start_payload,
)
from .coordinator import GreenworksConfigEntry, GreenworksCoordinator, control_enabled
from .entity import AddConfigEntryEntitiesCallback, GreenworksEntity
from .schedule import (
    READ_KEY,
    READ_REQUEST,
    WEEKDAYS,
    ScheduleError,
    active_windows,
    apply_days,
    check_windows,
    fields_from_reply,
    save_payload,
)

SERVICE_PARK = "park"
SERVICE_MOW_CONTINUOUSLY = "mow_continuously"
ATTR_HOURS = "hours"
ATTR_DAYS = "days"
SERVICE_SET_SCHEDULE = "set_schedule"
ATTR_WEEKDAYS = "weekdays"
WINDOW_FIELDS = (("start_1", "end_1"), ("start_2", "end_2"))
# Speichern dauert am Maeher laenger als die anderen Befehle
SAVE_CONFIRM_TIMEOUT = 60
# Kontrolle nach dem Speichern: Pause davor (s), Versuche, Wartezeit je Versuch (s)
CHECK_DELAY = 5
CHECK_ATTEMPTS = 2
CHECK_TIMEOUT = 20

_RETURNING = getattr(LawnMowerActivity, "RETURNING", LawnMowerActivity.MOWING)

ACTIVITY_MAP: dict[int, LawnMowerActivity] = {
    1: LawnMowerActivity.PAUSED,  # Stopp-Taste gedrueckt
    2: LawnMowerActivity.DOCKED,  # geparkt (Grund siehe Status)
    3: LawnMowerActivity.PAUSED,
    4: LawnMowerActivity.MOWING,
    5: LawnMowerActivity.MOWING,  # verlaesst die Station
    6: _RETURNING,  # sucht die Station
    7: LawnMowerActivity.DOCKED,  # laedt
    8: LawnMowerActivity.ERROR,
    9: LawnMowerActivity.ERROR,  # schwerer Fehler
    10: LawnMowerActivity.ERROR,  # Wiederherstellung nach Fehler
    11: LawnMowerActivity.ERROR,  # Alarm (z. B. angehoben, Geofence)
    12: LawnMowerActivity.MOWING,  # maeht Nebenflaeche
}


PARALLEL_UPDATES = 0
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreenworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GreenworksLawnMower(coordinator, device_id) for device_id in coordinator.data
    )
    platform = entity_platform.async_get_current_platform()
    # Eigene Zeiten (nur bei "Lesen und steuern" wirksam)
    platform.async_register_entity_service(
        SERVICE_PARK,
        {
            vol.Optional(ATTR_HOURS): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=MAX_PARK_HOURS)
            )
        },
        "async_park",
    )
    platform.async_register_entity_service(
        SERVICE_MOW_CONTINUOUSLY,
        {
            vol.Required(ATTR_DAYS): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=MAX_CONTINUOUS_DAYS)
            )
        },
        "async_mow_continuously",
    )
    platform.async_register_entity_service(
        SERVICE_SET_SCHEDULE,
        {
            vol.Required(ATTR_WEEKDAYS): vol.All(
                cv.ensure_list, [vol.In(WEEKDAYS)], vol.Length(min=1)
            ),
            **{
                vol.Optional(field): cv.time
                for pair in WINDOW_FIELDS
                for field in pair
            },
        },
        "async_set_schedule",
    )


def _schedule_error(key: str) -> HomeAssistantError:
    return HomeAssistantError(translation_domain=DOMAIN, translation_key=key)


class GreenworksLawnMower(GreenworksEntity, LawnMowerEntity):
    """Der Maehroboter selbst. Steuern nur bei "Lesen und steuern"."""

    _attr_name = None

    def __init__(self, coordinator: GreenworksCoordinator, device_id: int) -> None:
        super().__init__(coordinator, device_id, "mower")
        self._schedule_lock = asyncio.Lock()
        if control_enabled(coordinator.config_entry):
            self._attr_supported_features = (
                LawnMowerEntityFeature.START_MOWING
                | LawnMowerEntityFeature.PAUSE
                | LawnMowerEntityFeature.DOCK
            )
        else:
            self._attr_supported_features = LawnMowerEntityFeature(0)

    def _control(self) -> Any:
        control = self.coordinator.control
        if control is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_disabled"
            )
        return control

    async def _async_command(self, payload: str) -> None:
        await self._control().async_send(self._device_id, payload)
        await self.coordinator.async_request_refresh()

    async def async_start_mowing(self) -> None:
        """Maehen starten bzw. Zeitplan fortsetzen (mit PIN, falls eingetragen)."""
        pin = self.coordinator.config_entry.options.get(CONF_PIN)
        await self._async_command(start_payload(int(pin) if pin else None))

    async def async_pause(self) -> None:
        await self._async_command(pause_payload())

    async def async_dock(self) -> None:
        """Zur Station und dort bleiben (Parken bis auf Weiteres)."""
        await self._async_command(park_payload(None))

    async def async_park(self, hours: int | None = None) -> None:
        """Parken fuer X Stunden, ohne Angabe bis auf Weiteres."""
        mower = self.mower
        if (
            hours is not None
            and self.coordinator.control is not None
            and mower is not None
            and not can_park_timed(mower)
        ):
            # Wie in der App: im Zeitplan-, Regen- oder Frost-Parken nur bis auf Weiteres
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="park_timed_not_possible"
            )
        await self._async_command(park_payload(None if hours is None else hours * 60))

    async def async_mow_continuously(self, days: int) -> None:
        """Maehen ohne Unterbrechung fuer X Tage, 0 = aus."""
        await self._async_command(continuous_payload(days * 1440))

    async def async_set_schedule(self, weekdays: list[str], **times: time) -> None:
        """Maehplan fuer die gewaehlten Tage setzen, alle anderen Tage bleiben.

        Ablauf: pruefen, Plan frisch vom Maeher lesen, nur die gewaehlten Tage
        ersetzen, speichern, erneut lesen und vergleichen. Schlaegt ein Schritt
        fehl, wird abgebrochen (vor dem Speichern: es wurde nichts gesendet).
        """
        # Nie zwei Speichervorgaenge gleichzeitig (z. B. doppelt gedrueckt)
        async with self._schedule_lock:
            await self._async_set_schedule(weekdays, times)

    async def _async_set_schedule(self, weekdays: list[str], times: dict[str, time]) -> None:
        control = self._control()
        mower = self.mower
        until = mower.continuous_until if mower else None
        if until is not None and until > dt_util.utcnow():
            # Wie in der App: waehrend "Maehen ohne Unterbrechung" gesperrt
            raise _schedule_error("schedule_continuous_active")
        windows: list[tuple[int, int]] = []
        for start_key, end_key in WINDOW_FIELDS:
            start, end = times.get(start_key), times.get(end_key)
            if start is None and end is None:
                continue
            if start is None or end is None:
                raise _schedule_error("schedule_incomplete")
            windows.append((start.hour * 60 + start.minute, end.hour * 60 + end.minute))
        try:
            check_windows(windows)
            current = fields_from_reply(
                (await control.async_query(self._device_id, READ_REQUEST, READ_KEY)).get(
                    "response"
                )
            )
            wanted = apply_days(current, weekdays, windows)
        except ScheduleError as err:
            raise _schedule_error(err.key) from err
        if wanted != current:
            await self._async_save_schedule(control, wanted)
        await self.coordinator.async_request_refresh()

    async def _async_save_schedule(self, control: Any, wanted: dict[str, int]) -> None:
        """Speichern und kontrollieren.

        Live gesehen (Optimow 10): Der Maeher bestaetigt das Speichern, beantwortet
        aber eine Abfrage direkt danach oft nicht. Darum: kurz warten, bis zu zweimal
        nachlesen. Ergebnis:
        - nachgelesen und gleich: in Ordnung
        - nachgelesen und anders: Fehler
        - nicht nachlesbar: in Ordnung nur, wenn der Maeher das Speichern bestaetigt hat
        """
        confirmed = True
        failure: HomeAssistantError | None = None
        try:
            await control.async_send(
                self._device_id, save_payload(wanted), SAVE_CONFIRM_TIMEOUT
            )
        except HomeAssistantError as err:
            if err.translation_key not in ("control_rejected", "control_no_reply"):
                raise
            confirmed = False
            failure = (
                err
                if err.translation_key == "control_rejected"
                else _schedule_error("schedule_not_confirmed")
            )
        for attempt in range(CHECK_ATTEMPTS):
            await asyncio.sleep(CHECK_DELAY)
            try:
                saved = fields_from_reply(
                    (
                        await control.async_query(
                            self._device_id, READ_REQUEST, READ_KEY, CHECK_TIMEOUT
                        )
                    ).get("response")
                )
            except (ScheduleError, HomeAssistantError) as err:
                _LOGGER.debug("Maehplan nachlesen, Versuch %s: %s", attempt + 1, err)
                continue
            if active_windows(saved) != active_windows(wanted):
                raise failure or _schedule_error("schedule_not_confirmed")
            return
        if not confirmed:
            raise failure or _schedule_error("schedule_not_confirmed")
        _LOGGER.info(
            "Maehplan gespeichert (vom Maeher bestaetigt), Nachlesen nicht moeglich"
        )

    @property
    def available(self) -> bool:
        """Nicht verfuegbar, solange der Maeher offline ist."""
        mower = self.mower
        return super().available and mower is not None and mower.online is not False

    @property
    def activity(self) -> LawnMowerActivity | None:
        mower = self.mower
        if mower is None or mower.state_code is None:
            return None
        return ACTIVITY_MAP.get(mower.state_code)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        mower = self.mower
        if mower is None:
            return {}
        return {
            "status_code": mower.state_code,
            "status": status_key(mower.state_code, mower.park_reason),
            "park_reason_code": mower.park_reason,
            "sub_status_code": mower.sub_state_code,
        }


# Version 0.5.0
