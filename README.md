# Greenworks für Home Assistant

> [!IMPORTANT]
> **Diese Integration wurde von Claude (KI-Assistent von Anthropic) geschrieben.**
> Sie ist ein privates Testprojekt, wurde nur mit einem einzelnen Greenworks Optimow 10 ausprobiert und wird ohne Gewähr und ohne Support bereitgestellt. Nutzung auf eigene Verantwortung – vorher ein Backup anlegen.
>
> **This integration was written by Claude (AI assistant by Anthropic).** It is a private test project, only tried with a single Greenworks Optimow 10, and comes without warranty or support. Use at your own risk.

Custom Integration für Greenworks-Mähroboter (getestet mit dem **Optimow 10**) über die Greenworks-Cloud.

Weiterentwicklung von [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA) mit Erkenntnissen aus [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core) (MIT).

## Funktionen (v0.2.1)

- **Mäher** (`lawn_mower`): Status Mäht / Geparkt / Pausiert / Fährt zur Station / Fehler
- **Sensoren:** Status, Akku, nächster Start, letzter Fehler (Code und Zeitpunkt), Mähzeit, Laufzeit, Ladezeit, schwere Fehler, Signalqualität
- **Binärsensoren:** Online, Regensensor aktiv, Frostsensor aktiv
- **Position** (`device_tracker`): GPS-Position für die Karte, standardmäßig deaktiviert
- Steuerung (Start, Pause, Docken) ist noch nicht enthalten

## Wichtig: Du wirst öfter aus der Greenworks-App abgemeldet

**Kurz gesagt:** Home Assistant läuft zuverlässig weiter. Aber in der Greenworks-App musst du dich öfter neu anmelden, wenn du für beides dasselbe Konto nutzt.

**Warum?** Ein Greenworks-Konto kann anscheinend immer nur an **einer** Stelle gleichzeitig angemeldet sein.

1. Du meldest dich in der App an → die Anmeldung von Home Assistant wird ungültig.
2. Home Assistant merkt das spätestens nach einer Minute und meldet sich automatisch neu an. Davon bekommst du in Home Assistant nichts mit.
3. Dadurch wirst du in der App abgemeldet. Beim nächsten Öffnen der App musst du dich wieder anmelden.

**Was kann ich tun?**

Wenn dich das stört: Die Integration kurz ausschalten, solange du die App benutzt: *Einstellungen → Geräte & Dienste → Greenworks → ⋮ → Deaktivieren*. Danach wieder aktivieren.

> **English:** You will often be logged out of the Greenworks app if Home Assistant uses the same account. Home Assistant itself keeps working – it silently logs back in, which logs the app out. If that bothers you, disable the integration while using the app and re-enable it afterwards.

## Installation über HACS

1. HACS → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, Typ **Integration**, hinzufügen
3. **Greenworks** herunterladen, Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *Greenworks*
5. E-Mail und Passwort der Greenworks-App eingeben

## Versionen

- **0.2.1** – Bekannte Fehlercodes aus der App-Fehlerliste (13, 34, 47, 53, 59, 64) als mögliche Bedeutung am Sensor „Letzter Fehlercode“ (Zuordnung noch unbestätigt)
- **0.2.0** – Cloud-Anbindung neu geschrieben (tolerant gegenüber neuen/fehlenden Feldern, Winterpause ohne Absturz), ein Eintrag pro Konto für alle Mäher, neue Sensoren, deutsche Übersetzung, Diagnose-Download
