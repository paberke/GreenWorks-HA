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

Die Integration liest deinen Greenworks-Mähroboter über die Greenworks-Cloud aus und zeigt die Werte in Home Assistant an. **Steuern kann sie ihn noch nicht.**

Weiterentwicklung von [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA) mit Erkenntnissen aus [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core) (MIT). Vielen Dank an Boes24 für die Vorarbeit.

## Was funktioniert

Diese Werte wurden mit einem echten Optimow 10 in Home Assistant geprüft:

| Anzeige in Home Assistant | Was sie zeigt |
|---|---|
| **Mäher** | Zustand des Mähers: *Angedockt*, *Mäht* oder *Fährt zurück* (geprüft) |
| **Batterie** | Akkustand in %, sinkt beim Mähen live mit |
| **Status** | Genauer Zustand: *Geparkt*, *Lädt*, *Mäht* oder *Sucht Station* (geprüft) |
| **Nächster Start** | Wann der Mäher das nächste Mal losfährt. Nach dem Mähfenster der nächste Termin laut Zeitplan; beim Zwischenladen eine **Schätzung** des Mähers, wann er weitermacht. Während er mäht: leer |
| **Mähende** | Während er mäht: Ende des aktuellen Mähfensters. Sonst leer |
| **Letzte Statusmeldung** | Wann der Mäher zuletzt Daten gemeldet hat |
| **Mähzeit gesamt** / **Laufzeit gesamt** / **Ladezeit gesamt** | Gesamtstunden seit Inbetriebnahme (siehe Hinweis unten) |
| **Schwere Fehler** | Anzahl schwerwiegender Fehler laut Mäher (siehe Hinweis unten) |
| **Statistik-Stand** | Wann der Mäher die Statistik-Werte zuletzt geschickt hat |
| **Signalqualität** | Funkverbindung des Mähers |
| **Online** | Ob der Mäher mit der Cloud verbunden ist |
| **Regenschutz** / **Frostschutz** | Ob diese Funktionen im „Wetterwächter“ der App eingeschaltet sind (nicht, ob es gerade regnet) |
| **Position** | GPS-Position für die Karte, wandert beim Mähen mit (standardmäßig ausgeschaltet, unter den Entitäten des Geräts aktivierbar) |

Außerdem:

- Einrichtung über die Oberfläche mit E-Mail und Passwort der Greenworks-App
- Bei falschem Passwort eine verständliche Meldung statt Absturz. Lehnt die Cloud die Anmeldung aus einem anderen Grund ab, versucht Home Assistant es später erneut, statt nach einem neuen Passwort zu fragen
- Die Werte werden jede Minute aktualisiert
- Wenn die Greenworks-Cloud kurz nicht erreichbar ist, versucht Home Assistant es automatisch später erneut
- Deutsch und Englisch – Home Assistant wählt automatisch die eingestellte Sprache, auch für die Fehlertexte

## Was noch nicht geht oder noch unsicher ist

- **Steuerung fehlt:** Starten, Pausieren und Zurück zur Station sind noch nicht möglich.
- **Noch nicht alle Zustände geprüft:** *Verlässt Station*, *Pausiert* und *Fehler* wurden noch nicht beobachtet.
- **Statistik nur beim Öffnen der App aktuell:** Mähzeit, Laufzeit, Ladezeit und schwere Fehler schickt der Mäher nur, wenn in der Greenworks-App die Statistik abgefragt wird. Wie alt die Werte sind, zeigt der Sensor **Statistik-Stand**.
- **„Zustand 9“ ist unbekannt:** Der Mäher meldet manchmal einen Zustand 9, dessen Bedeutung noch nicht klar ist. Er wird als *Zustand 9* angezeigt.
- **Fehlermeldungen unsicher:** **Letzter Fehlercode** und **Letzter Fehler** (Zeitpunkt) werden angezeigt. Die Nummer passte im Test aber **nicht** zur Fehlerliste in der App. Die Texte aus der App-Fehlerliste stehen deshalb nur als *mögliche Bedeutung* dabei.

## Wichtig: Du wirst öfter aus der Greenworks-App abgemeldet

**Kurz gesagt:** Home Assistant läuft zuverlässig weiter. Aber in der Greenworks-App musst du dich öfter neu anmelden, wenn du für beides dasselbe Konto nutzt.

**Warum?** Ein Greenworks-Konto kann anscheinend immer nur an **einer** Stelle gleichzeitig angemeldet sein.

1. Du meldest dich in der App an → die Anmeldung von Home Assistant wird ungültig.
2. Home Assistant merkt das spätestens nach einer Minute und meldet sich automatisch neu an. Davon bekommst du in Home Assistant nichts mit.
3. Dadurch wirst du in der App abgemeldet. Beim nächsten Öffnen der App musst du dich wieder anmelden.

**Was kann ich tun?** Wenn dich das stört: Die Integration kurz ausschalten, solange du die App benutzt: *Einstellungen → Geräte & Dienste → Greenworks → ⋮ → Deaktivieren*. Danach wieder aktivieren.

> **English:** You will often be logged out of the Greenworks app if Home Assistant uses the same account. Home Assistant itself keeps working – it silently logs back in, which logs the app out. If that bothers you, disable the integration while using the app and re-enable it afterwards.

## Installation über HACS

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=paberke&repository=GreenWorks-HA&category=integration)

Mit dem Button oben wird das Repository direkt in HACS geöffnet. Oder von Hand:

1. HACS → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, Typ **Integration**, hinzufügen
3. **Greenworks** herunterladen und Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *Greenworks*
5. E-Mail und Passwort der Greenworks-App eingeben

## Versionen

- **0.2.4** – Fehlertexte (*Mögliche Bedeutung*, *Hinweis*) erscheinen jetzt in der Sprache von Home Assistant (Deutsch/Englisch); README auch auf Englisch
- **0.2.3** – Neuer Sensor **Mähende**, **Nächster Start** zeigt beim Mähen nichts Irreführendes mehr; neuer Sensor **Statistik-Stand**; **Regenschutz**/**Frostschutz** heißen wie in der App; Zustand 2 heißt jetzt *Geparkt*
- **0.2.2** – Anmeldung robuster: nur ein echtes falsches Passwort führt zur Passwort-Abfrage, Token wird nie kürzer als 10 Minuten genutzt, unplausible GPS-Werte werden ignoriert
- **0.2.1** – Texte aus der App-Fehlerliste als *mögliche Bedeutung* am Sensor **Letzter Fehlercode**
- **0.2.0** – Verbindung zur Greenworks-Cloud neu geschrieben: läuft wieder mit der aktuellen Cloud und auch in der Winterpause, alle Mäher eines Kontos in einem Eintrag, neue Sensoren, deutsche Übersetzung

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

The integration reads your Greenworks robotic mower via the Greenworks cloud and shows the values in Home Assistant. **It cannot control the mower yet.**

Based on [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA) with findings from [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core) (MIT). Many thanks to Boes24 for the groundwork.

## What works

Checked with a real Optimow 10 in Home Assistant:

| Entity | What it shows |
|---|---|
| **Mower** | Mower state: *Docked*, *Mowing* or *Returning* (checked) |
| **Battery** | Battery level in %, drops live while mowing |
| **Status** | Detailed state: *Parked*, *Charging*, *Mowing* or *Searching station* (checked) |
| **Next start** | When the mower will start next. After the mowing window: the next scheduled start; while recharging in between: the mower's **estimate** of when it continues. While mowing: empty |
| **Mowing end** | While mowing: end of the current mowing window. Otherwise empty |
| **Last status report** | When the mower last reported data |
| **Total cutting time** / **Total running time** / **Total charging time** | Total hours since first use (see note below) |
| **Fatal errors** | Number of fatal errors reported by the mower (see note below) |
| **Statistics as of** | When the mower last sent the statistics values |
| **Signal quality** | Radio connection of the mower |
| **Online** | Whether the mower is connected to the cloud |
| **Rain protection** / **Frost protection** | Whether these options are enabled in the app's "weather guard" (not whether it is raining right now) |
| **Position** | GPS position for the map, moves while mowing (disabled by default, can be enabled under the device's entities) |

Also:

- Setup via the UI with the email and password of the Greenworks app
- A clear message for a wrong password instead of a crash. If the cloud rejects the login for another reason, Home Assistant retries later instead of asking for a new password
- Values are updated every minute
- If the Greenworks cloud is briefly unreachable, Home Assistant automatically retries later
- English and German – Home Assistant automatically uses your language, including the error texts

## Not working yet / uncertain

- **No control:** start, pause and return to station are not possible yet.
- **Not all states checked:** *Leaving station*, *Paused* and *Error* have not been observed yet.
- **Statistics only update when the app asks for them:** cutting time, running time, charging time and fatal errors are only sent by the mower when the statistics are opened in the Greenworks app. The **Statistics as of** sensor shows how old they are.
- **"State 9" is unknown:** the mower sometimes reports a state 9 whose meaning is not clear yet. It is shown as *State 9*.
- **Error messages uncertain:** **Last error code** and **Last error** (time) are shown. In testing, however, the number did **not** match the error list in the app. Texts from the app's error list are therefore only shown as *possible meaning*.

## Important: you will often be logged out of the Greenworks app

**In short:** Home Assistant keeps working reliably. But you will often have to log in to the Greenworks app again if both use the same account.

**Why?** A Greenworks account apparently can only be logged in at **one** place at a time.

1. You log in to the app → Home Assistant's login becomes invalid.
2. Home Assistant notices this within a minute and logs back in automatically. You won't notice anything in Home Assistant.
3. This logs you out of the app. The next time you open the app, you have to log in again.

**What can I do?** If it bothers you: disable the integration while you use the app – *Settings → Devices & services → Greenworks → ⋮ → Disable*. Enable it again afterwards.

## Installation via HACS

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=paberke&repository=GreenWorks-HA&category=integration)

The button above opens the repository directly in HACS. Or manually:

1. HACS → menu (⋮) → **Custom repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, type **Integration**, add
3. Download **Greenworks** and restart Home Assistant
4. Settings → Devices & services → **Add integration** → *Greenworks*
5. Enter the email and password of the Greenworks app

The version history is in the German section above ("Versionen").
