# Greenworks für Home Assistant

**Deutsch** · [English version below](#english)

> [!WARNING]
> **Testphase – noch nicht fertig.**
> - Diese Integration wurde von **Claude (KI-Assistent von Anthropic)** geschrieben. Sie ist ein privates Testprojekt.
> - Sie kann den Mäher **nur auslesen, nicht steuern** (kein Starten, Pausieren oder Zurückschicken).
> - Bisher nur mit **einem einzigen Greenworks Optimow 10** ausprobiert.
> - Du wirst in der **Greenworks-App öfter abgemeldet**, wenn Home Assistant dasselbe Konto nutzt (siehe unten).
> - **Keine Gewähr, kein Support.** Nutzung auf eigene Verantwortung – lege vorher ein Backup an.
>
> **Testing phase – not finished.** Written by **Claude (AI assistant by Anthropic)**, private test project. **Read-only** – it cannot control the mower. Only tried with a single Optimow 10. Using the same account will often log you out of the Greenworks app. No warranty, no support. Use at your own risk and make a backup first.

Die Integration liest deinen Greenworks-Mähroboter über die Greenworks-Cloud aus und zeigt die Werte in Home Assistant an. **Sie kann den Mäher nicht steuern** – Starten, Parken und Zurückschicken gehen weiterhin nur über die Greenworks-App.

## Installation über HACS

**Voraussetzung:** Home Assistant **2025.1 oder neuer**. Automatisch getestet mit 2024.12, 2025.1, 2025.2 und 2026.2, im echten Betrieb mit 2026.10.

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=paberke&repository=GreenWorks-HA&category=integration)

Mit dem Button oben wird das Repository direkt in HACS geöffnet. Oder von Hand:

1. HACS → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, Typ **Integration**, hinzufügen
3. **Greenworks** herunterladen und Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *Greenworks*
5. E-Mail und Passwort der Greenworks-App eingeben

## Was funktioniert

Diese Werte wurden mit einem echten Optimow 10 in Home Assistant geprüft:

| Anzeige in Home Assistant | Was sie zeigt |
|---|---|
| **Mäher** ⓘ | Zustand des Mähers: *Angedockt*, *Mäht*, *Fährt zurück* oder *Fehler*. Ist der Mäher offline, steht hier *nicht verfügbar* |
| **Batterie** | Akkustand in %, sinkt beim Mähen live mit |
| **Status** ⓘ | Genauer Zustand mit den Bezeichnungen der App, z. B. *Nach Zeitplan geparkt*, *Lädt*, *Mäht*, *Sucht Station*, *Schwerer Fehler*. Ist der Mäher offline: *Offline* |
| **Nächster Start** | Wann der Mäher das nächste Mal losfährt. Nach dem Mähfenster der nächste Termin laut Zeitplan; beim Zwischenladen eine **Schätzung** des Mähers, wann er weitermacht. Während er mäht: leer |
| **Mähende** | Während er mäht: Ende des aktuellen Mähfensters. Sonst leer |
| **Letzte Statusmeldung** | Wann der Mäher zuletzt Daten gemeldet hat |
| **Mähzeit gesamt** / **Laufzeit gesamt** / **Ladezeit gesamt** | Gesamtstunden seit Inbetriebnahme (siehe Hinweis unten) |
| **Messer-Laufzeit** | Mähstunden seit dem letzten Zurücksetzen der Messerzeit in der App – gleiche Rechnung wie die App |
| **Mähplan** ⓘ | Wochenplan als Kurzform, z. B. *Mo–Fr 09:00–12:30*; die Zeiten je Tag als Attribute |
| **Fehlerverlauf** | Attribut *Verlauf* an **Letzte Fehlermeldung**: die Meldungen aus der Fehlerliste der App mit Datum und Klartext |
| **Software** ⓘ | Softwarestand des Mähers, dazu Mähwerk und Ladestation als Attribute (Diagnose) |
| **Überfahrweite** ⓘ, **Abstand beim Drahtfolgen** ⓘ, **Startpunkte** ⓘ | Die Einstellungen aus der App als reine Anzeige (Diagnose). Ändern geht weiterhin nur in der App |
| **Letzte Fehlermeldung** ⓘ | Letzter vom Mäher gemeldeter Fehler als Klartext, z. B. *Steckengeblieben* (alle 69 Fehlercodes der App). Das Attribut *Klartext* enthält den Text auch für Benachrichtigungen |
| **Letzter Fehlercode** ⓘ / **Letzter Fehler** | Nummer und Zeitpunkt des letzten Fehlers |
| **Schwere Fehler** | Anzahl schwerwiegender Fehler laut Mäher (siehe Hinweis unten) |
| **Statistik-Stand** | Wann der Mäher die Statistik-Werte zuletzt geschickt hat |
| **Signalqualität** | Funkverbindung des Mähers |
| **Online** | Ob der Mäher mit der Cloud verbunden ist |
| **Regenschutz** / **Frostschutz** | Ob diese Funktionen im „Wetterwächter“ der App eingeschaltet sind (nicht, ob es gerade regnet) |
| **Position** | GPS-Position für die Karte, wandert beim Mähen mit (standardmäßig ausgeschaltet, unter den Entitäten des Geräts aktivierbar) |

ⓘ = hat Zusatzinfos, siehe [Zusatzinfos (Attribute)](#zusatzinfos-attribute).

### Zusatzinfos (Attribute)

Einige Anzeigen haben weitere Angaben. So findest du sie: Anzeige antippen → oben rechts **⋮** → **Details**, dort unter **Attribute**. In Automationen und Vorlagen kommst du mit `state_attr()` an sie heran.

| Anzeige | Attribute |
|---|---|
| **Status** | *Letzter Zustand* – nur wenn der Mäher offline ist: der Zustand vor dem Ausfall |
| **Letzter Fehlercode** | *Bedeutung* – der Fehler als Klartext |
| **Letzte Fehlermeldung** | *Klartext* (für Benachrichtigungen), *Verlauf* (Fehlerliste der App mit Datum), *Verlauf aktualisiert* |
| **Mähplan** | *Montag* bis *Sonntag* mit den Mähzeiten, *Aktualisiert* |
| **Software** | *Mähwerk*, *Ladestation* |
| **Abstand beim Drahtfolgen** | *Leitdraht 1*, *Leitdraht 2*, *Aktualisiert* |
| **Startpunkte** | *Punkt 1* bis *Punkt 5* (Draht, Entfernung, Anteil der Starts), *Ladestation* (Anteil der Starts direkt an der Station), *Aktualisiert* |
| **Überfahrweite** | *Aktualisiert* |
| **Mäher** | *status* (genauer Zustand), *status_code*, *park_reason_code*, *sub_status_code* – die Rohwerte des Mähers, praktisch für Automationen |

*Aktualisiert* zeigt, wann die App den Wert zuletzt aus dem Mäher gelesen hat.

Außerdem:

- Einrichtung über die Oberfläche mit E-Mail und Passwort der Greenworks-App
- Bei falschem Passwort eine verständliche Meldung statt Absturz. Lehnt die Cloud die Anmeldung aus einem anderen Grund ab, versucht Home Assistant es später erneut, statt nach einem neuen Passwort zu fragen
- Die Werte werden jede Minute aktualisiert
- Wenn die Greenworks-Cloud kurz nicht erreichbar ist, bleiben die letzten Werte stehen und Home Assistant versucht es jede Minute erneut. Erst nach etwa 5 Minuten ohne Verbindung wird alles als *nicht verfügbar* angezeigt
- Meldet der Mäher nach seiner letzten Statusmeldung einen Fehler, zeigen **Status** und **Mäher** den Zustand aus der Fehlermeldung (z. B. *Fehler* statt *Sucht Station*)
- Deutsch und Englisch – Home Assistant wählt automatisch die eingestellte Sprache, auch für die Fehlertexte

## Was (noch) nicht geht

- **Keine Steuerung:** Die Integration liest nur aus. Starten, Parken oder Zurückschicken ist über Home Assistant **nicht** möglich und auch nicht geplant – das bleibt der Greenworks-App vorbehalten.
- **Nur mit einem Mäher getestet:** Alles wurde mit einem einzigen Optimow 10 geprüft. Bei anderen Modellen oder mehreren Mähern im Konto kann es Abweichungen geben.
- **Statistik nur beim Öffnen der App aktuell:** Mähzeit, Laufzeit, Ladezeit und schwere Fehler schickt der Mäher nur, wenn in der Greenworks-App die Statistik abgefragt wird. Wie alt die Werte sind, zeigt der Sensor **Statistik-Stand**.
- **Mähplan, Fehlerverlauf und Einstellungen sind nur so aktuell wie die App:** Die Cloud aktualisiert sie nur, wenn du in der App die jeweilige Seite öffnest. Wann das zuletzt war, steht im Attribut *Aktualisiert* bzw. *Verlauf aktualisiert*.
- **Fehlermeldung kann von der App-Fehlerliste abweichen:** Nummern und Texte sind dieselben wie in der App. Home Assistant zeigt aber das **zuletzt gemeldete Ereignis**; das war im Test nicht immer das, was in der App-Fehlerliste steht (vermutlich kurze Warnungen, die die App nicht auflistet). Die deutschen Texte sind teils eigene Übersetzungen.

## Wichtig: Du wirst öfter aus der Greenworks-App abgemeldet

**Kurz gesagt:** Home Assistant läuft zuverlässig weiter. Aber in der Greenworks-App musst du dich öfter neu anmelden, wenn du für beides dasselbe Konto nutzt.

**Warum?** Ein Greenworks-Konto kann anscheinend immer nur an **einer** Stelle gleichzeitig angemeldet sein.

1. Du meldest dich in der App an → die Anmeldung von Home Assistant wird ungültig.
2. Home Assistant merkt das spätestens nach einer Minute und meldet sich automatisch neu an. Davon bekommst du in Home Assistant nichts mit.
3. Dadurch wirst du in der App abgemeldet. Beim nächsten Öffnen der App musst du dich wieder anmelden.

**Was kann ich tun?** Wenn dich das stört: Die Integration kurz ausschalten, solange du die App benutzt: *Einstellungen → Geräte & Dienste → Greenworks → ⋮ → Deaktivieren*. Danach wieder aktivieren.

> **English:** You will often be logged out of the Greenworks app if Home Assistant uses the same account. Home Assistant itself keeps working – it silently logs back in, which logs the app out. If that bothers you, disable the integration while using the app and re-enable it afterwards.

## Versionen

- **0.2.11** – Läuft wieder mit älteren Home-Assistant-Versionen ab 2025.1 (vorher startete die Integration auf 2025.1 und 2025.2 nicht)
- **0.2.10** *(im Test)* – Ist der Mäher offline, zeigt **Status** *Offline* (mit Attribut *Letzter Zustand*) und **Mäher** *nicht verfügbar*
- **0.2.9** *(im Test)* – Status zeigt bei einem neueren Fehler den Zustand aus der Fehlermeldung (z. B. *Fehler* statt *Sucht Station*); kurze Verbindungsaussetzer (bis ca. 5 Minuten) werden überbrückt, statt alles auf *nicht verfügbar* zu setzen
- **0.2.8** – Neue Sensoren **Messer-Laufzeit**, **Mähplan** und **Software**, Einstellungen (**Überfahrweite**, **Abstand beim Drahtfolgen**, **Startpunkte**) als Anzeige, Fehlerverlauf als Attribut an **Letzte Fehlermeldung**; Diagnosedaten verbergen jetzt auch Seriennummer und SIM-Kartennummer
- **0.2.7** – Neues Attribut *Klartext* an **Letzte Fehlermeldung**: der Fehlertext in der Sprache von Home Assistant, z. B. für Push-Benachrichtigungen
- **0.2.6** – Status nutzt die vollständigen Bezeichnungen der App, inkl. Park-Grund (z. B. *Nach Zeitplan geparkt*, *Vom Regenschutz geparkt*); der frühere *Zustand 9* heißt jetzt *Schwerer Fehler*
- **0.2.5** – Alle **69 Fehlercodes** der App als Klartext: neuer Sensor **Letzte Fehlermeldung**, Attribut *Bedeutung* am **Letzten Fehlercode**
- **0.2.4** – Fehlertexte (*Mögliche Bedeutung*, *Hinweis*) erscheinen jetzt in der Sprache von Home Assistant (Deutsch/Englisch); README auch auf Englisch
- **0.2.3** – Neuer Sensor **Mähende**, **Nächster Start** zeigt beim Mähen nichts Irreführendes mehr; neuer Sensor **Statistik-Stand**; **Regenschutz**/**Frostschutz** heißen wie in der App; Zustand 2 heißt jetzt *Geparkt*
- **0.2.2** – Anmeldung robuster: nur ein echtes falsches Passwort führt zur Passwort-Abfrage, Token wird nie kürzer als 10 Minuten genutzt, unplausible GPS-Werte werden ignoriert
- **0.2.1** – Texte aus der App-Fehlerliste als *mögliche Bedeutung* am Sensor **Letzter Fehlercode**
- **0.2.0** – Verbindung zur Greenworks-Cloud neu geschrieben: läuft wieder mit der aktuellen Cloud und auch in der Winterpause, alle Mäher eines Kontos in einem Eintrag, neue Sensoren, deutsche Übersetzung

## Danksagung

Entstanden als Fork von [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA). Der Code wurde inzwischen vollständig neu geschrieben; die Adresse der Greenworks-Cloud und der Anmeldeweg stammen ursprünglich aus [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core). Danke an Boes24 für den Anstoß.

---

<a id="english"></a>

# Greenworks for Home Assistant (English)

> [!WARNING]
> **Testing phase – not finished.**
> - This integration was written by **Claude (AI assistant by Anthropic)**. It is a private test project.
> - It can only **read** the mower, **not control** it (no start, pause or return to station).
> - So far only tried with **a single Greenworks Optimow 10**.
> - You will often be **logged out of the Greenworks app** if Home Assistant uses the same account (see below).
> - **No warranty, no support.** Use at your own risk – make a backup first.

The integration reads your Greenworks robotic mower via the Greenworks cloud and shows the values in Home Assistant. **It cannot control the mower** – starting, parking and sending it home still only work through the Greenworks app.

## Installation via HACS

**Requirement:** Home Assistant **2025.1 or newer**. Automatically tested with 2024.12, 2025.1, 2025.2 and 2026.2, in real use with 2026.10.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=paberke&repository=GreenWorks-HA&category=integration)

The button above opens the repository directly in HACS. Or manually:

1. HACS → menu (⋮) → **Custom repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, type **Integration**, add
3. Download **Greenworks** and restart Home Assistant
4. Settings → Devices & services → **Add integration** → *Greenworks*
5. Enter the email and password of the Greenworks app

## What works

Checked with a real Optimow 10 in Home Assistant:

| Entity | What it shows |
|---|---|
| **Mower** ⓘ | Mower state: *Docked*, *Mowing*, *Returning* or *Error*. While the mower is offline it shows *unavailable* |
| **Battery** | Battery level in %, drops live while mowing |
| **Status** ⓘ | Detailed state with the app's wording, e.g. *Parked by schedule*, *Charging*, *Mowing*, *Searching station*, *Fatal error*. While the mower is offline: *Offline* |
| **Next start** | When the mower will start next. After the mowing window: the next scheduled start; while recharging in between: the mower's **estimate** of when it continues. While mowing: empty |
| **Mowing end** | While mowing: end of the current mowing window. Otherwise empty |
| **Last status report** | When the mower last reported data |
| **Total cutting time** / **Total running time** / **Total charging time** | Total hours since first use (see note below) |
| **Blade time** | Mowing hours since the blade time was last reset in the app – same calculation as the app |
| **Mowing schedule** ⓘ | Weekly schedule in short form, e.g. *Mon–Fri 09:00–12:30*; times per day as attributes |
| **Error history** | *History* attribute on **Last error message**: the entries of the app's error list with date and text |
| **Software** ⓘ | Mower software version, plus cutting unit and charging station as attributes (diagnostic) |
| **Drive past wire distance** ⓘ, **Follow wire distance** ⓘ, **Starting points** ⓘ | The app settings, display only (diagnostic). Changing them still only works in the app |
| **Last error message** ⓘ | Last error reported by the mower as plain text, e.g. *Mower is stuck* (all 69 error codes of the app). The *Text* attribute holds the text for use in notifications |
| **Last error code** ⓘ / **Last error** | Number and time of the last error |
| **Fatal errors** | Number of fatal errors reported by the mower (see note below) |
| **Statistics as of** | When the mower last sent the statistics values |
| **Signal quality** | Radio connection of the mower |
| **Online** | Whether the mower is connected to the cloud |
| **Rain protection** / **Frost protection** | Whether these options are enabled in the app's "weather guard" (not whether it is raining right now) |
| **Position** | GPS position for the map, moves while mowing (disabled by default, can be enabled under the device's entities) |

ⓘ = has extra details, see [Extra details (attributes)](#extra-details-attributes).

### Extra details (attributes)

Some entities carry more details. To see them: tap the entity → **⋮** at the top right → **Details**, under **Attributes**. In automations and templates use `state_attr()`.

| Entity | Attributes |
|---|---|
| **Status** | *Last state* – only while the mower is offline: the state before it went offline |
| **Last error code** | *Meaning* – the error as plain text |
| **Last error message** | *Text* (for notifications), *History* (the app's error list with dates), *History updated* |
| **Mowing schedule** | *Monday* to *Sunday* with the mowing times, *Updated* |
| **Software** | *Cutting unit*, *Charging station* |
| **Follow wire distance** | *Guide wire 1*, *Guide wire 2*, *Updated* |
| **Starting points** | *Point 1* to *Point 5* (wire, distance, share of starts), *Charging station* (share of starts at the station), *Updated* |
| **Drive past wire distance** | *Updated* |
| **Mower** | *status* (detailed state), *status_code*, *park_reason_code*, *sub_status_code* – the mower's raw values, handy for automations |

*Updated* shows when the app last read the value from the mower.

Also:

- Setup via the UI with the email and password of the Greenworks app
- A clear message for a wrong password instead of a crash. If the cloud rejects the login for another reason, Home Assistant retries later instead of asking for a new password
- Values are updated every minute
- If the Greenworks cloud is briefly unreachable, the last values are kept and Home Assistant retries every minute. Only after about 5 minutes without a connection are the entities shown as *unavailable*
- If the mower reports an error after its last status message, **Status** and **Mower** show the state from the error message (e.g. *Error* instead of *Searching station*)
- English and German – Home Assistant automatically uses your language, including the error texts

## What does not work

- **No control:** the integration is read-only. Starting, parking or sending the mower home is **not** possible from Home Assistant and not planned – that stays with the Greenworks app.
- **Tested with one mower only:** everything was checked with a single Optimow 10. Other models or several mowers per account may behave differently.
- **Statistics only update when the app asks for them:** cutting time, running time, charging time and fatal errors are only sent by the mower when the statistics are opened in the Greenworks app. The **Statistics as of** sensor shows how old they are.
- **Mowing schedule, error history and settings are only as current as the app:** the cloud only updates them when you open the respective page in the app. The *Updated* / *History updated* attributes show when that was.
- **Error message may differ from the app's error list:** codes and texts are the same as in the app. However, Home Assistant shows the **most recently reported event**, which in testing was not always what the app's error list shows (probably short warnings the app does not list). Some German texts are our own translations.

## Important: you will often be logged out of the Greenworks app

**In short:** Home Assistant keeps working reliably. But you will often have to log in to the Greenworks app again if both use the same account.

**Why?** A Greenworks account apparently can only be logged in at **one** place at a time.

1. You log in to the app → Home Assistant's login becomes invalid.
2. Home Assistant notices this within a minute and logs back in automatically. You won't notice anything in Home Assistant.
3. This logs you out of the app. The next time you open the app, you have to log in again.

**What can I do?** If it bothers you: disable the integration while you use the app – *Settings → Devices & services → Greenworks → ⋮ → Disable*. Enable it again afterwards.

The version history is in the German section above ("Versionen").

## Credits

Started as a fork of [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA). The code has since been completely rewritten; the Greenworks cloud address and login flow originally come from [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core). Thanks to Boes24 for the starting point.
