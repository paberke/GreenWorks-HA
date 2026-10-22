"""Tipps zu den Fehlercodes: von Claude (KI) geschrieben, KEIN offizieller Greenworks-Text.

Je Code: (Englisch, Deutsch). Wird von tools/error_list.py in ERRORS.md und
ERRORS.de.md geschrieben.
"""

_SUPPORT = (
    "Restart the mower. If the error comes back, contact Greenworks support.",
    "Mäher neu starten. Kommt der Fehler wieder, den Greenworks-Support kontaktieren.",
)
_STUCK = (
    "Free the mower and check the spot (roots, holes, edges, toys). Fence off problem areas with the boundary wire if needed.",
    "Mäher befreien und die Stelle prüfen (Wurzeln, Löcher, Kanten, Spielzeug). Problemstellen bei Bedarf mit dem Begrenzungsdraht ausgrenzen.",
)
_LIFT = (
    "Check that nothing lifts the mower (bumps, branches, children, animals). If it happens on flat ground, contact Greenworks support.",
    "Prüfen, ob etwas den Mäher anhebt (Bodenwellen, Äste, Kinder, Tiere). Passiert es auf ebenem Boden, den Greenworks-Support kontaktieren.",
)
_WHEEL = (
    "Switch off the mower and check the wheel for grass, mud or objects. Clean it and restart. If it persists, contact Greenworks support.",
    "Mäher ausschalten und das Rad auf Gras, Schlamm oder Fremdkörper prüfen. Reinigen und neu starten. Bleibt der Fehler, den Greenworks-Support kontaktieren.",
)
_WHEEL_OVERLOAD = (
    "Usually too steep, too wet or too long grass. Clean the wheel, let the mower cool down and try again later.",
    "Meist zu steil, zu nass oder zu hohes Gras. Rad reinigen, Mäher abkühlen lassen und später erneut versuchen.",
)
_BLADE = (
    "Switch off the mower (gloves!) and check the blade disc for grass, stones or other objects. If it persists, contact Greenworks support.",
    "Mäher ausschalten (Handschuhe!) und die Messerscheibe auf Gras, Steine oder Fremdkörper prüfen. Bleibt der Fehler, den Greenworks-Support kontaktieren.",
)
_LOOP = (
    "Check the charging station has power and its light is on, and that the boundary wire is connected and not broken.",
    "Prüfen, ob die Ladestation Strom hat und ihre Leuchte an ist und ob der Begrenzungsdraht angeschlossen und nicht unterbrochen ist.",
)
_SENSOR = (
    "Possibly a sensor defect. Restart the mower; if it persists, contact Greenworks support.",
    "Möglicherweise ein Sensordefekt. Mäher neu starten; bleibt der Fehler, den Greenworks-Support kontaktieren.",
)

TIPS: dict[int, tuple[str, str]] = {
    1: _SENSOR,
    2: _STUCK,
    3: _STUCK,
    4: _STUCK,
    5: _LIFT,
    6: _SENSOR,
    7: _LIFT,
    8: _LIFT,
    9: _LIFT,
    10: _SENSOR,
    11: _SUPPORT,
    12: _SENSOR,
    13: (
        "The slope is too steep at this spot. Fence it off with the boundary wire or move the wire.",
        "Der Hang ist an dieser Stelle zu steil. Bereich mit dem Begrenzungsdraht ausgrenzen oder den Draht versetzen.",
    ),
    14: (
        "Turn the mower over carefully, check it for damage and restart it.",
        "Mäher vorsichtig umdrehen, auf Schäden prüfen und neu starten.",
    ),
    15: (
        "Check the power supply of the charging station. If it persists, contact Greenworks support.",
        "Netzteil der Ladestation prüfen. Bleibt der Fehler, den Greenworks-Support kontaktieren.",
    ),
    16: _LOOP,
    17: (
        "Another robotic mower nearby may disturb the signal. Change the loop signal code (see manual).",
        "Ein anderer Mähroboter in der Nähe stört eventuell das Signal. Den Schleifensignal-Code ändern (siehe Anleitung).",
    ),
    18: (
        "Check that guide wire 1 is connected to the charging station and not broken.",
        "Prüfen, ob Leitdraht 1 an der Ladestation angeschlossen und nicht unterbrochen ist.",
    ),
    19: (
        "Check that guide wire 2 is connected to the charging station and not broken.",
        "Prüfen, ob Leitdraht 2 an der Ladestation angeschlossen und nicht unterbrochen ist.",
    ),
    20: _SENSOR,
    21: _SENSOR,
    22: _SENSOR,
    23: (
        "Check that the charging station has power and the mower sits correctly on the contacts.",
        "Prüfen, ob die Ladestation Strom hat und der Mäher richtig auf den Kontakten steht.",
    ),
    24: _SUPPORT,
    25: _SUPPORT,
    26: (
        "Usually temporary (trees, buildings, weather). If it happens often, check the mower's position in the app.",
        "Meist nur vorübergehend (Bäume, Gebäude, Wetter). Kommt es oft vor, die Position des Mähers in der App prüfen.",
    ),
    27: (
        "Problem with the built-in SIM card or mobile network. Restart the mower; if it persists, contact Greenworks support.",
        "Problem mit der eingebauten SIM-Karte oder dem Mobilfunknetz. Mäher neu starten; bleibt der Fehler, den Greenworks-Support kontaktieren.",
    ),
    28: _SUPPORT,
    29: _SUPPORT,
    30: _SUPPORT,
    31: (
        "The mower was reset. Check the settings and the schedule in the app and set them again if needed.",
        "Der Mäher wurde zurückgesetzt. Einstellungen und Mähplan in der App prüfen und bei Bedarf neu einstellen.",
    ),
    32: _WHEEL,
    33: _WHEEL_OVERLOAD,
    34: _WHEEL,
    35: _WHEEL,
    36: _WHEEL,
    37: _WHEEL_OVERLOAD,
    38: _WHEEL,
    39: _WHEEL,
    40: _BLADE,
    41: (
        "Usually the grass is too long or too wet. Mow it shorter once by hand or raise the cutting height, then try again.",
        "Meist ist das Gras zu hoch oder zu nass. Einmal von Hand kürzer mähen oder die Schnitthöhe erhöhen, dann erneut versuchen.",
    ),
    42: _BLADE,
    43: _BLADE,
    44: (
        "Carry the mower back inside the boundary wire and check that the wire is not broken.",
        "Mäher innerhalb des Begrenzungsdrahts zurücktragen und prüfen, ob der Draht unterbrochen ist.",
    ),
    45: (
        "Only use the original battery for this mower.",
        "Nur den Original-Akku für diesen Mäher verwenden.",
    ),
    46: (
        "Check that the battery sits firmly. If it persists, contact Greenworks support.",
        "Prüfen, ob der Akku fest sitzt. Bleibt der Fehler, den Greenworks-Support kontaktieren.",
    ),
    47: (
        "Carry the mower to the charging station and let it charge. If it happens often, check the way back to the station.",
        "Mäher zur Ladestation tragen und laden lassen. Passiert es öfter, den Rückweg zur Station prüfen.",
    ),
    48: (
        "Let the mower cool down in the shade. Avoid mowing in strong midday heat.",
        "Mäher im Schatten abkühlen lassen. Mähen bei starker Mittagshitze vermeiden.",
    ),
    49: (
        "Too cold for the battery. Wait until it gets warmer; in winter use the winter pause.",
        "Zu kalt für den Akku. Warten, bis es wärmer wird; im Winter die Winterpause nutzen.",
    ),
    50: _SUPPORT,
    51: _SUPPORT,
    52: _WHEEL,
    53: _STUCK,
    54: (
        "Remove anything blocking the charging station (grass, leaves, objects) and check the station stands level.",
        "Alles entfernen, was die Ladestation blockiert (Gras, Laub, Gegenstände), und prüfen, ob die Station gerade steht.",
    ),
    55: (
        "Free the mower from the charging station and check the station for objects and level ground.",
        "Mäher aus der Ladestation befreien und die Station auf Fremdkörper und geraden Stand prüfen.",
    ),
    56: (
        "The mower was switched off without the PIN. Switch it on again and enter the PIN.",
        "Der Mäher wurde ohne PIN ausgeschaltet. Wieder einschalten und PIN eingeben.",
    ),
    57: (
        "The mower was lifted. Check where it is and enter the PIN on the mower.",
        "Der Mäher wurde angehoben. Nachsehen, wo er ist, und die PIN am Mäher eingeben.",
    ),
    58: (
        "The mower left the geofence area. Check where it is (position in the app).",
        "Der Mäher hat den Geofence-Bereich verlassen. Nachsehen, wo er ist (Position in der App).",
    ),
    59: _LOOP,
    60: _LOOP,
    61: (
        "Check the power supply and socket of the charging station.",
        "Netzteil und Steckdose der Ladestation prüfen.",
    ),
    62: (
        "Another robotic mower nearby disturbs the signal. Change the loop signal code (see manual).",
        "Ein anderer Mähroboter in der Nähe stört das Signal. Den Schleifensignal-Code ändern (siehe Anleitung).",
    ),
    63: (
        "Information only, nothing to do.",
        "Nur eine Information, nichts zu tun.",
    ),
    64: (
        "Press STOP and then START on the mower.",
        "Am Mäher erst STOP und dann START drücken.",
    ),
    65: _SENSOR,
    66: _SUPPORT,
    67: (
        "Clean the charging contacts on the mower and the station and check the power supply.",
        "Ladekontakte an Mäher und Station reinigen und das Netzteil prüfen.",
    ),
    68: _SUPPORT,
    69: (
        "Open the app once so the mower's clock is set again; check date and time in the settings.",
        "Die App einmal öffnen, damit die Uhr des Mähers wieder gestellt wird; Datum und Uhrzeit in den Einstellungen prüfen.",
    ),
}
