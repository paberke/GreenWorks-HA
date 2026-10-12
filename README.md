# Greenworks für Home Assistant

Custom Integration für Greenworks-Mähroboter (getestet mit dem **Optimow 10**) über die Greenworks-Cloud.

Weiterentwicklung von [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA) mit Erkenntnissen aus [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core) (MIT).

## Funktionen (v0.2.0)

- **Mäher** (`lawn_mower`): Status Mäht / Geparkt / Pausiert / Fährt zur Station / Fehler
- **Sensoren:** Status, Akku, nächster Start, letzter Fehler (Code und Zeitpunkt), Mähzeit, Laufzeit, Ladezeit, schwere Fehler, Signalqualität
- **Binärsensoren:** Online, Regensensor aktiv, Frostsensor aktiv
- **Position** (`device_tracker`): GPS-Position für die Karte, standardmäßig deaktiviert
- Steuerung (Start, Pause, Docken) ist noch nicht enthalten

## Installation über HACS

1. HACS → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, Typ **Integration**, hinzufügen
3. **Greenworks** herunterladen, Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *Greenworks*
5. E-Mail und Passwort der Greenworks-App eingeben

## Versionen

- **0.2.0** – Cloud-Anbindung neu geschrieben (tolerant gegenüber neuen/fehlenden Feldern, Winterpause ohne Absturz), ein Eintrag pro Konto für alle Mäher, neue Sensoren, deutsche Übersetzung, Diagnose-Download
