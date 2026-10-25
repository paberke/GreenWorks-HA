"""Statustext wie oben in der Greenworks-App, z. B. "Nach Zeitplan geparkt bis Fr. 09:00"."""

from __future__ import annotations

from datetime import datetime

from homeassistant.util import dt as dt_util

from .api import GreenworksMower
from .const import MOWING_STATES, PROBLEM_STATES, STATUS_OFFLINE, STATUS_WINTER_PAUSE, status_key
from .error_texts import error_text

# Status -> (Englisch, Deutsch), wie in translations/*.json
STATUS_NAMES: dict[str, tuple[str, str]] = {
    "alarm": ("Alarm", "Alarm"),
    "charging": ("Charging", "Lädt"),
    "energy_saving": ("Energy-saving mode", "Energiesparmodus"),
    "error": ("Error", "Fehler"),
    "fatal_error": ("Fatal error", "Schwerer Fehler"),
    "leaving_station": ("Leaving charging station", "Verlässt Station"),
    "mowing": ("Mowing", "Mäht"),
    "mowing_secondary_area": ("Mowing secondary area", "Mäht Nebenfläche"),
    "offline": ("Offline", "Offline"),
    "parked": ("Parked", "Geparkt"),
    "parked_by_frost_guard": ("Parked by frost guard", "Vom Frostschutz geparkt"),
    "parked_by_rain_guard": ("Parked by rain guard", "Vom Regenschutz geparkt"),
    "parked_by_schedule": ("Parked by schedule", "Nach Zeitplan geparkt"),
    "parked_by_user": ("Parked by user", "Vom Benutzer geparkt"),
    "parked_max_cutting_time": ("Max day cutting time reached", "Maximale Tagesmähzeit erreicht"),
    "paused": ("Paused", "Pausiert"),
    "recovery": ("Recovering from error", "Wiederherstellung nach Fehler"),
    "searching_station": ("Searching for charging station", "Sucht Station"),
    "starting_up": ("Starting up", "Startet"),
    "stop_button_pressed": ("Stop button pressed", "Stopp-Taste gedrückt"),
    "unknown": ("Unknown", "Unbekannt"),
    "winter_pause": ("Winter pause", "Winterpause"),
}

_DAYS = {
    "en": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
    "de": ("Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."),
}
_WORDS = {
    "en": {"until": "until", "further": "until further notice", "mowing_until": "Mowing until", "today": "", "error": "error"},
    "de": {"until": "bis", "further": "bis auf Weiteres", "mowing_until": "Mäht bis", "today": "", "error": "Fehler"},
}
# Status, bei denen die App "... bis <Zeit>" anhaengt
_WITH_UNTIL = {
    "parked_by_schedule",
    "parked_by_user",
    "parked_by_rain_guard",
    "parked_by_frost_guard",
    "parked_max_cutting_time",
    "charging",
    "energy_saving",
}


def _when(value: datetime, lang: str, now: datetime) -> str:
    """Heute nur die Uhrzeit, in der naechsten Woche Wochentag + Uhrzeit, sonst Datum."""
    local = dt_util.as_local(value)
    today = dt_util.as_local(now).date()
    if local.date() == today:
        return f"{local:%H:%M}"
    if 0 < (local.date() - today).days < 7:
        return f"{_DAYS[lang][local.weekday()]} {local:%H:%M}"
    return f"{local:%d.%m.%Y %H:%M}" if lang == "de" else f"{local:%Y-%m-%d %H:%M}"


def status_text(m: GreenworksMower, language: str | None, now: datetime | None = None) -> str | None:
    lang = "de" if (language or "").startswith("de") else "en"
    idx = 1 if lang == "de" else 0
    words = _WORDS[lang]
    now = now or dt_util.utcnow()
    if m.online is False:
        key = STATUS_WINTER_PAUSE if m.winter_pause else STATUS_OFFLINE
        return STATUS_NAMES[key][idx]
    key = status_key(m.state_code, m.park_reason)
    if key is None:
        return None
    name = STATUS_NAMES.get(key, STATUS_NAMES["unknown"])[idx]
    if m.state_code in PROBLEM_STATES and m.last_error_code:
        return f"{name}: {error_text(m.last_error_code, language)} ({words['error']} {m.last_error_code})"
    if m.state_code in MOWING_STATES and m.state_code != 5 and m.next_start:
        return f"{words['mowing_until']} {_when(m.next_start, lang, now)}"
    if key in _WITH_UNTIL:
        if m.next_start:
            return f"{name} {words['until']} {_when(m.next_start, lang, now)}"
        if key == "parked_by_user":
            return f"{name} {words['further']}"
    return name


# Version 0.4.0
