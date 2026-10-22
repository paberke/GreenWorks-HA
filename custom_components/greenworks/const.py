"""Konstanten fuer die Greenworks-Integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "greenworks"
VERSION: Final = "0.3.1"

BASE_URL: Final = "https://xapi.globetools.systems/v2/"
CORP_ID: Final = "100fa2b00b622800"

UPDATE_INTERVAL: Final = timedelta(seconds=60)
# So lange werden bei Verbindungsproblemen die letzten Werte weiter angezeigt
OUTAGE_GRACE: Final = timedelta(minutes=5)

# Einstellungen (Knopf "Konfigurieren")
CONF_OUTAGE_GRACE: Final = "outage_grace"  # Minuten
DEFAULT_SCAN_INTERVAL: Final = 60  # Sekunden
DEFAULT_OUTAGE_GRACE: Final = 5  # Minuten
SCAN_INTERVAL_RANGE: Final = (30, 600)
OUTAGE_GRACE_RANGE: Final = (1, 60)
CONF_BLADE_LIMIT: Final = "blade_limit"  # Stunden, 0 = Erinnerung aus
DEFAULT_BLADE_LIMIT: Final = 150
BLADE_LIMIT_RANGE: Final = (0, 1000)
CONF_OFFLINE_HOURS: Final = "offline_hours"  # Stunden, 0 = Hinweis aus
DEFAULT_OFFLINE_HOURS: Final = 1
OFFLINE_HOURS_RANGE: Final = (0, 72)

# Gruppen von Entitaeten, die man ein- und ausschalten kann (Standard ist immer an)
CONF_GROUPS: Final = "groups"
GROUP_STANDARD: Final = "standard"
GROUP_ERRORS: Final = "errors_detailed"
GROUP_STATISTICS: Final = "statistics"
GROUP_APP_SETTINGS: Final = "app_settings"
GROUP_DIAGNOSTICS: Final = "diagnostics"
GROUP_CALENDAR: Final = "calendar"
GROUP_POSITION: Final = "position"
OPTIONAL_GROUPS: Final = (
    GROUP_ERRORS,
    GROUP_STATISTICS,
    GROUP_APP_SETTINGS,
    GROUP_DIAGNOSTICS,
    GROUP_CALENDAR,
    GROUP_POSITION,
)
# Neue Einrichtung: nur Standard
DEFAULT_GROUPS_NEW: Final[list[str]] = []
# Bestehende Einrichtung (vor 0.3.0): alles wie bisher, Kalender neu und aus,
# Position war schon immer standardmaessig aus
DEFAULT_GROUPS_EXISTING: Final[list[str]] = [
    GROUP_ERRORS,
    GROUP_STATISTICS,
    GROUP_APP_SETTINGS,
    GROUP_DIAGNOSTICS,
]

# Welche Entitaet (Schluessel in der unique_id) gehoert zu welcher Gruppe
ENTITY_GROUPS: Final[dict[str, str]] = {
    # Standard
    "mower": GROUP_STANDARD,
    "status": GROUP_STANDARD,
    "battery": GROUP_STANDARD,
    "next_start": GROUP_STANDARD,
    "mowing_end": GROUP_STANDARD,
    "online": GROUP_STANDARD,
    "problem": GROUP_STANDARD,
    "charging": GROUP_STANDARD,
    "error": GROUP_STANDARD,
    "winter_pause": GROUP_STANDARD,
    "blade_time": GROUP_STANDARD,
    "blade_change_due": GROUP_STANDARD,
    # Fehler ausfuehrlich
    "last_error": GROUP_ERRORS,
    "last_error_text": GROUP_ERRORS,
    "last_error_time": GROUP_ERRORS,
    "fatal_errors": GROUP_ERRORS,
    # Statistik
    "cutting_time": GROUP_STATISTICS,
    "running_time": GROUP_STATISTICS,
    "charging_time": GROUP_STATISTICS,
    "statistics_time": GROUP_STATISTICS,
    "status_time": GROUP_STATISTICS,
    # Einstellungen aus der App
    "schedule": GROUP_APP_SETTINGS,
    "drive_past_wire": GROUP_APP_SETTINGS,
    "wire_distance": GROUP_APP_SETTINGS,
    "start_points": GROUP_APP_SETTINGS,
    "rain_sensor": GROUP_APP_SETTINGS,
    "frost_sensor": GROUP_APP_SETTINGS,
    # Diagnose
    "software": GROUP_DIAGNOSTICS,
    "signal_quality": GROUP_DIAGNOSTICS,
    # Kalender und Position
    "calendar": GROUP_CALENDAR,
    "position": GROUP_POSITION,
}

# Entitaeten, die es nicht mehr gibt (werden beim Start aus der Registry entfernt)
REMOVED_ENTITIES: Final = frozenset({"firmware_update"})

# Hauptzustaende, die als Problem gelten (Fehler, schwerer Fehler, Alarm)
PROBLEM_STATES: Final = frozenset({8, 9, 11})

# Zustaende, in denen die Maehzeit mitgezaehlt wird (Maehen, Nebenflaeche)
COUNTED_STATES: Final = frozenset({4, 12})

# "Kein Termin" wird von der Cloud als 0xFFFFFFFF gemeldet
NO_TIMESTAMP: Final = 4294967295

# Datenpunkte aus product/{pid}/v_device/{id}
DP_STATUS_A: Final = "31"
DP_STATUS_B: Final = "32"
DP_LAST_ERROR: Final = "33"
DP_POSITION: Final = "34"
DP_STATISTICS: Final = "48"
DP_FIRMWARE: Final = "117"
DP_ERROR_HISTORY: Final = "52"
DP_SCHEDULE_WRITE: Final = "124"
DP_SCHEDULE_READ: Final = "125"
# Einstellungen: jeweils gesetzt (Anfrage) und gelesen (Antwort); der neueste zaehlt
DP_DRIVE_PAST_WIRE: Final = ("89", "90")
DP_WIRE_CORRIDOR: Final = ("55", "56", "122")
DP_START_POINTS: Final = ("58", "59", "60", "123")

# Hauptzustand des Maehers (mower_main_state), Bedeutung laut Greenworks-App
MOWER_STATES: Final[dict[int, str]] = {
    0: "starting_up",
    1: "stop_button_pressed",
    2: "parked",
    3: "paused",
    4: "mowing",
    5: "leaving_station",
    6: "searching_station",
    7: "charging",
    8: "error",
    9: "fatal_error",
    10: "recovery",
    11: "alarm",
    12: "mowing_secondary_area",
}

# Bei Zustand 2 (geparkt) nennt source_for_next_start den Grund
PARK_REASONS: Final[dict[int, str]] = {
    1: "charging",
    2: "parked_by_schedule",
    3: "parked_max_cutting_time",
    4: "parked_by_user",
    5: "parked_by_rain_guard",
    6: "parked_by_frost_guard",
    7: "energy_saving",
}

# Eigene Zustaende: Maeher nicht mit der Cloud verbunden / Winterpause eingeschaltet
STATUS_OFFLINE: Final = "offline"
STATUS_WINTER_PAUSE: Final = "winter_pause"

LAST_STATUS_OPTIONS: Final = sorted(
    {*MOWER_STATES.values(), *PARK_REASONS.values(), "unknown"}
)
STATUS_OPTIONS: Final = sorted({*LAST_STATUS_OPTIONS, STATUS_OFFLINE, STATUS_WINTER_PAUSE})


def status_key(state: int | None, park_reason: int | None) -> str | None:
    """Zustand (und bei 'geparkt' den Grund) in einen Status-Schluessel umwandeln."""
    if state is None:
        return None
    if state == 2 and park_reason in PARK_REASONS:
        return PARK_REASONS[park_reason]
    return MOWER_STATES.get(state, "unknown")


# Zustaende, in denen next_start das ENDE des Maehfensters meint
MOWING_STATES: Final = frozenset({4, 5, 12})

# Fehlercodes des Maehers (gleiche Nummerierung wie die Fehlerliste der App).
# Die Texte stehen in translations/*.json unter dem Schluessel "e<Nummer>".
ERROR_CODE_MAX: Final = 69
ERROR_OPTIONS: Final = [f"e{n}" for n in range(1, ERROR_CODE_MAX + 1)] + ["unknown"]


def error_key(code: int | None) -> str | None:
    """Fehlercode in den Uebersetzungs-Schluessel umwandeln."""
    if code is None:
        return None
    return f"e{code}" if 1 <= code <= ERROR_CODE_MAX else "unknown"

# Version 0.3.1
