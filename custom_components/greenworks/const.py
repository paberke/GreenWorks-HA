"""Konstanten fuer die Greenworks-Integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "greenworks"
VERSION: Final = "0.2.0"

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

# Version 0.2.0
