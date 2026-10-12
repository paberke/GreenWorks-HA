# Greenworks für Home Assistant

> [!WARNING]
> **Testphase – noch nicht fertig.**
> Diese Integration wurde von **Claude (KI-Assistent von Anthropic)** geschrieben. Sie ist ein privates Testprojekt und wurde bisher nur mit **einem einzigen Greenworks Optimow 10** ausprobiert. Es gibt **keine Gewähr und keinen Support**. Nutzung auf eigene Verantwortung – lege vorher ein Backup an.
>
> **Testing phase – not finished.** This integration was written by **Claude (AI assistant by Anthropic)**. It is a private test project, only tried with a single Greenworks Optimow 10. No warranty, no support. Use at your own risk and make a backup first.

Die Integration liest deinen Greenworks-Mähroboter über die Greenworks-Cloud aus und zeigt die Werte in Home Assistant an. **Steuern kann sie ihn noch nicht.**

Weiterentwicklung von [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA) mit Erkenntnissen aus [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core) (MIT). Vielen Dank an Boes24 für die Vorarbeit.

## Was funktioniert

Diese Werte wurden mit einem echten Optimow 10 in Home Assistant geprüft:

| Anzeige in Home Assistant | Was sie zeigt |
|---|---|
| **Mäher** | Zustand des Mähers, z. B. *Angedockt* |
| **Batterie** | Akkustand in % |
| **Status** | Genauer Zustand, z. B. *Geparkt (Benutzer)* |
| **Nächster Start** | Datum und Uhrzeit des nächsten geplanten Mähens |
| **Letzte Statusmeldung** | Wann der Mäher zuletzt Daten gemeldet hat |
| **Mähzeit gesamt** / **Laufzeit gesamt** / **Ladezeit gesamt** | Gesamtstunden seit Inbetriebnahme |
| **Schwere Fehler** | Anzahl schwerer Fehler laut Mäher |
| **Signalqualität** | Funkverbindung des Mähers |
| **Online** | Ob der Mäher mit der Cloud verbunden ist |
| **Regensensor aktiv** / **Frostsensor aktiv** | Ob diese Sensoren in der App eingeschaltet sind |

Außerdem:

- Einrichtung über die Oberfläche mit E-Mail und Passwort der Greenworks-App
- Bei falschem Passwort eine verständliche Meldung statt Absturz
- Wenn die Greenworks-Cloud kurz nicht erreichbar ist, versucht Home Assistant es automatisch später erneut
- Deutsch und Englisch

## Was noch nicht geht oder noch unsicher ist

- **Steuerung fehlt:** Starten, Pausieren und Zurück zur Station sind noch nicht möglich.
- **Zustände beim Mähen ungeprüft:** Bisher wurde der Mäher nur im angedockten Zustand beobachtet. Ob *Mäht*, *Pausiert*, *Fährt zur Station* usw. richtig angezeigt werden, ist noch nicht bestätigt.
- **„Zustand 9“ ist unbekannt:** Der Mäher meldet manchmal einen Zustand 9, dessen Bedeutung noch nicht klar ist. Er wird als *Zustand 9* angezeigt.
- **Fehlermeldungen unsicher:** **Letzter Fehlercode** und **Letzter Fehler** (Zeitpunkt) werden angezeigt. Die Nummer passte im Test aber **nicht** zur Fehlerliste in der App. Die Texte aus der App-Fehlerliste stehen deshalb nur als *mögliche Bedeutung* dabei.
- **GPS-Position ungeprüft:** Es gibt eine Position für die Karte. Sie ist standardmäßig **ausgeschaltet** und wurde noch nicht mit echten Daten geprüft.

## Wichtig: Du wirst öfter aus der Greenworks-App abgemeldet

**Kurz gesagt:** Home Assistant läuft zuverlässig weiter. Aber in der Greenworks-App musst du dich öfter neu anmelden, wenn du für beides dasselbe Konto nutzt.

**Warum?** Ein Greenworks-Konto kann anscheinend immer nur an **einer** Stelle gleichzeitig angemeldet sein.

1. Du meldest dich in der App an → die Anmeldung von Home Assistant wird ungültig.
2. Home Assistant merkt das spätestens nach einer Minute und meldet sich automatisch neu an. Davon bekommst du in Home Assistant nichts mit.
3. Dadurch wirst du in der App abgemeldet. Beim nächsten Öffnen der App musst du dich wieder anmelden.

**Was kann ich tun?** Wenn dich das stört: Die Integration kurz ausschalten, solange du die App benutzt: *Einstellungen → Geräte & Dienste → Greenworks → ⋮ → Deaktivieren*. Danach wieder aktivieren.

> **English:** You will often be logged out of the Greenworks app if Home Assistant uses the same account. Home Assistant itself keeps working – it silently logs back in, which logs the app out. If that bothers you, disable the integration while using the app and re-enable it afterwards.

## Installation über HACS

1. HACS → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, Typ **Integration**, hinzufügen
3. **Greenworks** herunterladen und Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *Greenworks*
5. E-Mail und Passwort der Greenworks-App eingeben

## Versionen

- **0.2.1** *(im Test)* – Texte aus der App-Fehlerliste als *mögliche Bedeutung* am Sensor **Letzter Fehlercode**
- **0.2.0** – Verbindung zur Greenworks-Cloud neu geschrieben: läuft wieder mit der aktuellen Cloud und auch in der Winterpause, alle Mäher eines Kontos in einem Eintrag, neue Sensoren, deutsche Übersetzung
