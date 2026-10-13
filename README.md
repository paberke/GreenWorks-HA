# Greenworks für Home Assistant

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
| **Mäher** | Zustand des Mähers: *Angedockt* oder *Mäht* (beides geprüft) |
| **Batterie** | Akkustand in %, sinkt beim Mähen live mit |
| **Status** | Genauer Zustand: *Geparkt (Benutzer)*, *Lädt* oder *Mäht* (geprüft) |
| **Nächster Start** | Datum und Uhrzeit des nächsten geplanten Mähens (stimmt, solange der Mäher in der Station steht – siehe unten) |
| **Letzte Statusmeldung** | Wann der Mäher zuletzt Daten gemeldet hat |
| **Mähzeit gesamt** / **Laufzeit gesamt** / **Ladezeit gesamt** | Gesamtstunden seit Inbetriebnahme |
| **Schwere Fehler** | Anzahl schwerer Fehler laut Mäher |
| **Signalqualität** | Funkverbindung des Mähers |
| **Online** | Ob der Mäher mit der Cloud verbunden ist |
| **Regensensor aktiv** / **Frostsensor aktiv** | Ob diese Sensoren in der App eingeschaltet sind |
| **Position** | GPS-Position für die Karte, wandert beim Mähen mit (standardmäßig ausgeschaltet, unter den Entitäten des Geräts aktivierbar) |

Außerdem:

- Einrichtung über die Oberfläche mit E-Mail und Passwort der Greenworks-App
- Bei falschem Passwort eine verständliche Meldung statt Absturz. Lehnt die Cloud die Anmeldung aus einem anderen Grund ab, versucht Home Assistant es später erneut, statt nach einem neuen Passwort zu fragen
- Die Werte werden jede Minute aktualisiert
- Wenn die Greenworks-Cloud kurz nicht erreichbar ist, versucht Home Assistant es automatisch später erneut
- Deutsch und Englisch

## Was noch nicht geht oder noch unsicher ist

- **Steuerung fehlt:** Starten, Pausieren und Zurück zur Station sind noch nicht möglich.
- **Noch nicht alle Zustände geprüft:** *Angedockt*, *Lädt* und *Mäht* werden richtig angezeigt. *Verlässt Station*, *Fährt zur Station*, *Pausiert* und *Fehler* wurden noch nicht beobachtet.
- **„Nächster Start“ beim Mähen irreführend:** Während der Mäher mäht, liefert die Cloud in diesem Feld das **Ende** des Mähfensters statt des nächsten Starts. Das wird in einer der nächsten Versionen angepasst.
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

- **0.2.2** – Anmeldung robuster: nur ein echtes falsches Passwort führt zur Passwort-Abfrage, Token wird nie kürzer als 10 Minuten genutzt, unplausible GPS-Werte werden ignoriert
- **0.2.1** – Texte aus der App-Fehlerliste als *mögliche Bedeutung* am Sensor **Letzter Fehlercode**
- **0.2.0** – Verbindung zur Greenworks-Cloud neu geschrieben: läuft wieder mit der aktuellen Cloud und auch in der Winterpause, alle Mäher eines Kontos in einem Eintrag, neue Sensoren, deutsche Übersetzung
