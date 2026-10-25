"""Klartexte der Fehlercodes (Englisch, Deutsch).

Englisch: aus der Greenworks-Connect-App. Deutsch: Codes 13, 34, 47, 53, 59, 64
wie in der deutschen App-Fehlerliste, die uebrigen sinngemaess uebersetzt.
"""

from __future__ import annotations

ERRORS = {
    1: ("Collision sensor failure", "Kollisionssensor ausgefallen"),
    2: ("Collision sensor defect or mower is stuck", "Kollisionssensor defekt oder Mäher steckt fest"),
    3: ("Front collision sensor defect or mower stuck when starting", "Vorderer Kollisionssensor defekt oder Mäher steckt beim Start fest"),
    4: ("Rear collision sensor defect or mower is stuck", "Hinterer Kollisionssensor defekt oder Mäher steckt fest"),
    5: ("Temporary lifted", "Kurzzeitig angehoben"),
    6: ("Lift sensor defect. Unexpected signal from a lift sensor", "Hebesensor defekt. Unerwartetes Signal von einem Hebesensor"),
    7: ("Lift sensor defect or mower lifted", "Hebesensor defekt oder Mäher angehoben"),
    8: ("Front lift sensor defect or mower lifted when starting", "Vorderer Hebesensor defekt oder Mäher beim Start angehoben"),
    9: ("Rear lift sensor defect or mower lifted when starting", "Hinterer Hebesensor defekt oder Mäher beim Start angehoben"),
    10: ("Stop button defect", "Stopp-Taste defekt"),
    11: ("Safety key system error", "Fehler im Sicherheitsschlüssel-System"),
    12: ("Tilt sensor defect", "Neigungssensor defekt"),
    13: ("Too high inclination", "Zu starke Neigung"),
    14: ("Mower is upside down", "Mäher liegt auf dem Kopf"),
    15: ("Too high current or voltage from PSU", "Zu hoher Strom oder zu hohe Spannung vom Netzteil"),
    16: ("No boundary signal detected when starting", "Beim Start kein Begrenzungssignal erkannt"),
    17: ("Interference with other installation", "Störung durch eine andere Anlage"),
    18: ("Guide 1 not found", "Leitdraht 1 nicht gefunden"),
    19: ("Guide 2 not found", "Leitdraht 2 nicht gefunden"),
    20: ("Front right loop sensor defect", "Schleifensensor vorne rechts defekt"),
    21: ("Front left loop sensor defect", "Schleifensensor vorne links defekt"),
    22: ("Rear loop sensor defect", "Hinterer Schleifensensor defekt"),
    23: ("Communication problem with the charging station", "Kommunikationsproblem mit der Ladestation"),
    24: ("No communication with communication module", "Keine Verbindung zum Kommunikationsmodul"),
    25: ("No communication with GNSS module", "Keine Verbindung zum GPS-Modul"),
    26: ("Weak GNSS signal", "Schwaches GPS-Signal"),
    27: ("SIM card problem", "Problem mit der SIM-Karte"),
    28: ("Communication problem with cutting MCU", "Kommunikationsproblem mit der Mähwerk-Steuerung"),
    29: ("Internal error", "Interner Fehler"),
    30: ("Internal error", "Interner Fehler"),
    31: ("Internal error. Mower is reset to factory settings", "Interner Fehler. Mäher wurde auf Werkseinstellungen zurückgesetzt"),
    32: ("Right wheel motor defective", "Rechter Radmotor defekt"),
    33: ("Right wheel motor overloaded", "Rechter Radmotor überlastet"),
    34: ("Right wheel motor blocked", "Rechter Radmotor blockiert"),
    35: ("Right wheel motor drive system defect", "Antrieb des rechten Radmotors defekt"),
    36: ("Left wheel motor defective", "Linker Radmotor defekt"),
    37: ("Left wheel motor overloaded", "Linker Radmotor überlastet"),
    38: ("Left wheel motor blocked", "Linker Radmotor blockiert"),
    39: ("Left wheel motor drive system defect", "Antrieb des linken Radmotors defekt"),
    40: ("Cutting motor defective", "Mähmotor defekt"),
    41: ("Cutting motor overloaded", "Mähmotor überlastet"),
    42: ("Cutting motor blocked", "Mähmotor blockiert"),
    43: ("Cutting motor drive system defect", "Antrieb des Mähmotors defekt"),
    44: ("Outside working area", "Außerhalb des Arbeitsbereichs"),
    45: ("The battery is not compatible with this mower", "Der Akku ist mit diesem Mäher nicht kompatibel"),
    46: ("Battery communication problem", "Kommunikationsproblem mit dem Akku"),
    47: ("Battery empty", "Akku leer"),
    48: ("Battery temperature too high", "Akkutemperatur zu hoch"),
    49: ("Battery temperature too low", "Akkutemperatur zu niedrig"),
    50: ("Battery over-voltage", "Überspannung am Akku"),
    51: ("Battery over-current", "Überstrom am Akku"),
    52: ("Mower has no drive", "Mäher hat keinen Antrieb"),
    53: ("Mower is stuck", "Steckengeblieben"),
    54: ("Charging station blocked. The mower cannot dock", "Ladestation blockiert. Der Mäher kann nicht andocken"),
    55: ("Stuck in charging station", "Steckt in der Ladestation fest"),
    56: ("Main switch alarm. Mower turned off without PIN code", "Hauptschalter-Alarm. Mäher ohne PIN-Code ausgeschaltet"),
    57: ("Lift sensor alarm. The mower is lifted", "Hebesensor-Alarm. Der Mäher wurde angehoben"),
    58: ("Geofence alarm. The mower is outside the geofence area", "Geofence-Alarm. Der Mäher ist außerhalb des Geofence-Bereichs"),
    59: ("No boundary signal", "Begrenzungssignal verloren"),
    60: ("Lost connection to charging station. Loop signal still detected", "Verbindung zur Ladestation verloren. Schleifensignal wird noch erkannt"),
    61: ("No power in charging station", "Kein Strom an der Ladestation"),
    62: ("Interference with loop signal from other installation. Change loop signal code", "Störung des Schleifensignals durch eine andere Anlage. Schleifensignal-Code ändern"),
    63: ("Mower software is updated", "Mäher-Software wurde aktualisiert"),
    64: ("Mower started with safety key. Press STOP then START on mower", "Mit Sicherheitsschlüssel gestartet – erst STOP, dann START am Mäher drücken"),
    65: ("Front loop sensor defect", "Vorderer Schleifensensor defekt"),
    66: ("Cutting motor brake defect", "Bremse des Mähmotors defekt"),
    67: ("Too low charging current", "Ladestrom zu niedrig"),
    68: ("Charging system defect in mower", "Ladesystem im Mäher defekt"),
    69: ("Week timer enabled, but clock is not set", "Wochenplan aktiv, aber Uhrzeit nicht eingestellt"),
}


def error_text(code: int | None, language: str | None) -> str | None:
    """Klartext zum Fehlercode in der Sprache von Home Assistant (de, sonst en)."""
    if code is None:
        return None
    texts = ERRORS.get(code)
    if texts is None:
        return f"Unbekannter Fehler {code}" if (language or "").startswith("de") else f"Unknown error {code}"
    return texts[1] if (language or "").startswith("de") else texts[0]
# Version 0.4.1
