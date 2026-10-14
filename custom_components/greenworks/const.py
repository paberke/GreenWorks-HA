"""Konstanten fuer die Greenworks-Integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "greenworks"
VERSION: Final = "0.2.8b1"

BASE_URL: Final = "https://xapi.globetools.systems/v2/"
CORP_ID: Final = "100fa2b00b622800"

UPDATE_INTERVAL: Final = timedelta(seconds=60)

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

STATUS_OPTIONS: Final = sorted(
    {*MOWER_STATES.values(), *PARK_REASONS.values(), "unknown"}
)


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

# Version 0.2.8b1
