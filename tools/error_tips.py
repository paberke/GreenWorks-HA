"""Tipps zu den Fehlercodes: von Claude (KI) geschrieben, KEIN offizieller Greenworks-Text.

Je Code: (Englisch, Deutsch). Wird von tools/error_list.py in ERRORS.md und
ERRORS.de.md geschrieben.
"""

_SUPPORT = (
    "Restart the mower. If the error comes back, contact Greenworks support.",
    "Starte den Mäher neu. Kommt der Fehler wieder, wende dich an den Greenworks-Support.",
)
_STUCK = (
    "Free the mower and check the spot (roots, holes, edges, toys). Fence off problem areas with the boundary wire if needed.",
    "Befreie den Mäher und schau dir die Stelle an: Liegen dort Wurzeln, Löcher, Kanten oder Spielzeug? Stellen, an denen er öfter hängen bleibt, kannst du mit dem Begrenzungsdraht aussparen.",
)
_LIFT = (
    "Check that nothing lifts the mower (bumps, branches, children, animals). If it happens on flat ground, contact Greenworks support.",
    "Schau nach, ob etwas den Mäher anhebt, zum Beispiel Bodenwellen, Äste, Kinder oder Tiere. Passiert es auch auf ebenem Boden, wende dich an den Greenworks-Support.",
)
_WHEEL = (
    "Switch off the mower and check the wheel for grass, mud or objects. Clean it and restart. If it persists, contact Greenworks support.",
    "Schalte den Mäher aus und sieh nach, ob sich Gras, Matsch oder etwas anderes am Rad verfangen hat. Mach es sauber und starte neu. Bleibt der Fehler, wende dich an den Greenworks-Support.",
)
_WHEEL_OVERLOAD = (
    "Usually too steep, too wet or too long grass. Clean the wheel, let the mower cool down and try again later.",
    "Meist ist es zu steil, zu nass oder das Gras zu hoch. Mach das Rad sauber, lass den Mäher abkühlen und versuch es später noch einmal.",
)
_BLADE = (
    "Switch off the mower (gloves!) and check the blade disc for grass, stones or other objects. If it persists, contact Greenworks support.",
    "Schalte den Mäher aus, zieh Handschuhe an und sieh nach, ob Gras, Steine oder etwas anderes in der Messerscheibe steckt. Bleibt der Fehler, wende dich an den Greenworks-Support.",
)
_LOOP = (
    "Check the charging station has power and its light is on, and that the boundary wire is connected and not broken.",
    "Prüfe, ob die Ladestation Strom hat und ihre Leuchte brennt und ob der Begrenzungsdraht angeschlossen und heil ist.",
)
_SENSOR = (
    "Possibly a sensor defect. Restart the mower; if it persists, contact Greenworks support.",
    "Vermutlich ist ein Sensor defekt. Starte den Mäher neu. Bleibt der Fehler, wende dich an den Greenworks-Support.",
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
        "Der Hang ist an dieser Stelle zu steil. Spar die Stelle mit dem Begrenzungsdraht aus oder verleg den Draht anders.",
    ),
    14: (
        "Turn the mower over carefully, check it for damage and restart it.",
        "Dreh den Mäher vorsichtig wieder um, prüf ihn auf Schäden und starte ihn neu.",
    ),
    15: (
        "Check the power supply of the charging station. If it persists, contact Greenworks support.",
        "Prüfe das Netzteil der Ladestation. Bleibt der Fehler, wende dich an den Greenworks-Support.",
    ),
    16: _LOOP,
    17: (
        "Another robotic mower nearby may disturb the signal. Change the loop signal code (see manual).",
        "Vielleicht stört ein anderer Mähroboter in der Nähe das Signal. Ändere den Schleifensignal-Code (steht in der Anleitung).",
    ),
    18: (
        "Check that guide wire 1 is connected to the charging station and not broken.",
        "Prüfe, ob Leitdraht 1 an der Ladestation angeschlossen und heil ist.",
    ),
    19: (
        "Check that guide wire 2 is connected to the charging station and not broken.",
        "Prüfe, ob Leitdraht 2 an der Ladestation angeschlossen und heil ist.",
    ),
    20: _SENSOR,
    21: _SENSOR,
    22: _SENSOR,
    23: (
        "Check that the charging station has power and the mower sits correctly on the contacts.",
        "Prüfe, ob die Ladestation Strom hat und der Mäher richtig auf den Kontakten steht.",
    ),
    24: _SUPPORT,
    25: _SUPPORT,
    26: (
        "Usually temporary (trees, buildings, weather). If it happens often, check the mower's position in the app.",
        "Das ist meist nur kurz (Bäume, Gebäude, Wetter). Kommt es oft vor, sieh in der App nach, wo der Mäher steht.",
    ),
    27: (
        "Problem with the built-in SIM card or mobile network. Restart the mower; if it persists, contact Greenworks support.",
        "Die eingebaute SIM-Karte oder das Mobilfunknetz macht Probleme. Starte den Mäher neu. Bleibt der Fehler, wende dich an den Greenworks-Support.",
    ),
    28: _SUPPORT,
    29: _SUPPORT,
    30: _SUPPORT,
    31: (
        "The mower was reset. Check the settings and the schedule in the app and set them again if needed.",
        "Der Mäher wurde zurückgesetzt. Sieh in der App nach, ob Einstellungen und Mähplan noch stimmen, und stell sie bei Bedarf neu ein.",
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
        "Meist ist das Gras zu hoch oder zu nass. Mäh einmal von Hand kürzer oder stell die Schnitthöhe höher und versuch es dann noch einmal.",
    ),
    42: _BLADE,
    43: _BLADE,
    44: (
        "Carry the mower back inside the boundary wire and check that the wire is not broken.",
        "Trag den Mäher zurück auf die Fläche innerhalb des Begrenzungsdrahts und prüfe, ob der Draht irgendwo unterbrochen ist.",
    ),
    45: (
        "Only use the original battery for this mower.",
        "Verwende nur den Original-Akku für diesen Mäher.",
    ),
    46: (
        "Check that the battery sits firmly. If it persists, contact Greenworks support.",
        "Prüfe, ob der Akku fest sitzt. Bleibt der Fehler, wende dich an den Greenworks-Support.",
    ),
    47: (
        "Carry the mower to the charging station and let it charge. If it happens often, check the way back to the station.",
        "Trag den Mäher zur Ladestation und lass ihn laden. Passiert das öfter, prüf den Weg zurück zur Station.",
    ),
    48: (
        "Let the mower cool down in the shade. Avoid mowing in strong midday heat.",
        "Lass den Mäher im Schatten abkühlen. Mäh besser nicht in der größten Mittagshitze.",
    ),
    49: (
        "Too cold for the battery. Wait until it gets warmer. In winter, store the mower indoors, dry and frost-free.",
        "Für den Akku ist es zu kalt. Warte, bis es wärmer wird. Im Winter gehört der Mäher trocken und frostfrei ins Haus.",
    ),
    50: _SUPPORT,
    51: _SUPPORT,
    52: _WHEEL,
    53: _STUCK,
    54: (
        "Remove anything blocking the charging station (grass, leaves, objects) and check the station stands level.",
        "Räum alles weg, was die Ladestation blockiert (Gras, Laub, Gegenstände), und prüfe, ob die Station gerade steht.",
    ),
    55: (
        "Free the mower from the charging station and check the station for objects and level ground.",
        "Hol den Mäher aus der Ladestation, sieh nach, ob dort etwas im Weg liegt, und prüfe, ob die Station gerade steht.",
    ),
    56: (
        "The mower was switched off without the PIN. Switch it on again and enter the PIN.",
        "Der Mäher wurde ohne PIN ausgeschaltet. Schalte ihn wieder ein und gib die PIN ein.",
    ),
    57: (
        "The mower was lifted. Check where it is and enter the PIN on the mower.",
        "Der Mäher wurde angehoben. Sieh nach, wo er ist, und gib am Mäher die PIN ein.",
    ),
    58: (
        "The mower left the geofence area. Check where it is (position in the app).",
        "Der Mäher hat den Geofence-Bereich verlassen. Sieh in der App unter Position nach, wo er ist.",
    ),
    59: _LOOP,
    60: _LOOP,
    61: (
        "Check the power supply and socket of the charging station.",
        "Prüfe Netzteil und Steckdose der Ladestation.",
    ),
    62: (
        "Another robotic mower nearby disturbs the signal. Change the loop signal code (see manual).",
        "Ein anderer Mähroboter in der Nähe stört das Signal. Ändere den Schleifensignal-Code (steht in der Anleitung).",
    ),
    63: (
        "Information only, nothing to do.",
        "Nur ein Hinweis, du musst nichts tun.",
    ),
    64: (
        "Press STOP and then START on the mower.",
        "Drück am Mäher erst STOP und dann START.",
    ),
    65: _SENSOR,
    66: _SUPPORT,
    67: (
        "Clean the charging contacts on the mower and the station and check the power supply.",
        "Mach die Ladekontakte an Mäher und Station sauber und prüfe das Netzteil.",
    ),
    68: _SUPPORT,
    69: (
        "Open the Schedule page in the app and confirm \"Incorrect time\" with OK. The mower then gets the correct time from your phone.",
        "Öffne in der App die Seite Zeitplan und bestätige „Fehlerhafte Uhrzeit“ mit OK. Dann bekommt der Mäher die richtige Uhrzeit vom Handy.",
    ),
}
