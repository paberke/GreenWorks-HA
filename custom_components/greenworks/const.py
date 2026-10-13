"""Konstanten fuer die Greenworks-Integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "greenworks"
VERSION: Final = "0.2.4"

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

# Hauptzustand des Maehers (mower_main_state)
MOWER_STATES: Final[dict[int, str]] = {
    1: "stop_button_pressed",
    2: "parked_by_user",
    3: "paused",
    4: "mowing",
    5: "leaving_station",
    6: "searching_station",
    7: "charging",
    8: "error",
    # Bedeutung von 9 noch unklar (alte Bibliothek: "getrennt", beim Test-
    # Maeher aber auch bei bestehender Verbindung gemeldet)
    9: "state_9",
}

# Zustaende, in denen next_start das ENDE des Maehfensters meint
MOWING_STATES: Final = frozenset({4, 5})

# Fehlercodes laut Fehlerliste der Greenworks-App (Optimow 10).
# Werte sind Uebersetzungs-Schluessel (Texte in translations/*.json).
# Achtung: ob die event_id aus Datenpunkt 33 dieselbe Nummerierung nutzt,
# ist noch nicht bestaetigt - deshalb nur als Attribut "possible_meaning".
ERROR_CODES: Final[dict[int, str]] = {
    13: "tilt_too_steep",
    34: "right_wheel_motor_blocked",
    47: "battery_empty",
    53: "stuck",
    59: "boundary_signal_lost",
    64: "started_with_safety_key",
}

# Version 0.2.4
