# Greenworks für Home Assistant

> [!IMPORTANT]
> **Diese Integration wurde von Claude (KI-Assistent von Anthropic) geschrieben.**
> Sie ist ein privates Testprojekt, wurde nur mit einem einzelnen Greenworks Optimow 10 ausprobiert und wird ohne Gewähr und ohne Support bereitgestellt. Nutzung auf eigene Verantwortung – vorher ein Backup anlegen.
>
> **This integration was written by Claude (AI assistant by Anthropic).** It is a private test project, only tried with a single Greenworks Optimow 10, and comes without warranty or support. Use at your own risk.

Custom Integration für Greenworks-Mähroboter (getestet mit dem **Optimow 10**) über die Greenworks-Cloud.

Weiterentwicklung von [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA) mit Erkenntnissen aus [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core) (MIT).

## Funktionen (v0.2.0)

- **Mäher** (`lawn_mower`): Status Mäht / Geparkt / Pausiert / Fährt zur Station / Fehler
- **Sensoren:** Status, Akku, nächster Start, letzter Fehler (Code und Zeitpunkt), Mähzeit, Laufzeit, Ladezeit, schwere Fehler, Signalqualität
- **Binärsensoren:** Online, Regensensor aktiv, Frostsensor aktiv
- **Position** (`device_tracker`): GPS-Position für die Karte, standardmäßig deaktiviert
- Steuerung (Start, Pause, Docken) ist noch nicht enthalten

## Wichtig: Abmeldung in der Greenworks-App

Die Greenworks-Cloud erlaubt anscheinend **nur eine aktive Anmeldung pro Konto**. Sobald Home Assistant sich anmeldet, wirst du in der Greenworks-App abgemeldet – und wenn du dich in der App wieder anmeldest, meldet sich Home Assistant kurz darauf erneut an. App und Home Assistant können sich so **regelmäßig gegenseitig abmelden**.

Empfehlung:

- Lege für Home Assistant ein **eigenes, zweites Greenworks-Konto** an und teile den Mäher in der App mit diesem Konto (falls deine App-Version das Teilen unterstützt).
- Alternativ die Integration kurz deaktivieren (Einstellungen → Geräte & Dienste → Greenworks → ⋮ → Deaktivieren), solange du die App benutzt.

> **Note (EN):** The Greenworks cloud seems to allow only one active login per account. Using the same account in Home Assistant and in the app may log you out of the app repeatedly. Use a separate account for Home Assistant if possible.

## Installation über HACS

1. HACS → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, Typ **Integration**, hinzufügen
3. **Greenworks** herunterladen, Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *Greenworks*
5. E-Mail und Passwort der Greenworks-App eingeben

## Versionen

- **0.2.0** – Cloud-Anbindung neu geschrieben (tolerant gegenüber neuen/fehlenden Feldern, Winterpause ohne Absturz), ein Eintrag pro Konto für alle Mäher, neue Sensoren, deutsche Übersetzung, Diagnose-Download
