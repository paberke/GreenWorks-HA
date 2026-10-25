# Greenworks für Home Assistant

[![Release](https://img.shields.io/github/v/release/paberke/GreenWorks-HA)](https://github.com/paberke/GreenWorks-HA/releases)
[![Tests](https://github.com/paberke/GreenWorks-HA/actions/workflows/tests.yaml/badge.svg)](https://github.com/paberke/GreenWorks-HA/actions/workflows/tests.yaml)
[![HACS](https://github.com/paberke/GreenWorks-HA/actions/workflows/validate.yaml/badge.svg)](https://github.com/paberke/GreenWorks-HA/actions/workflows/validate.yaml)
[![Hassfest](https://github.com/paberke/GreenWorks-HA/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/paberke/GreenWorks-HA/actions/workflows/hassfest.yaml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
![Home Assistant 2025.1+](https://img.shields.io/badge/Home%20Assistant-2025.1%2B-blue.svg)

[🇬🇧 English version](README.md) · **Deutsch**

> [!WARNING]
> - Diese Integration wurde von **Claude (KI-Assistent von Anthropic)** zusammen mit [Patrick (paberke)](https://github.com/paberke) geschrieben. Sie ist ein privates Hobbyprojekt und **kein** offizielles Produkt von Greenworks.
> - Sie kann den Mäher **nur auslesen, nicht steuern** – kein Starten, Pausieren oder Zurückschicken.
> - Du wirst in der **Greenworks-App öfter abgemeldet**, wenn Home Assistant dasselbe Konto nutzt ([Details](#du-wirst-öfter-aus-der-greenworks-app-abgemeldet)).
> - **Keine Gewähr, kein Support.** Nutzung auf eigene Verantwortung – lege vorher ein Backup an.

Die Integration liest deinen Greenworks-Mähroboter über die Greenworks-Cloud aus und zeigt die Werte in Home Assistant an: Status, Batterie, nächster Start, Fehler im Klartext, Messer-Laufzeit, Mähplan und mehr. Starten, Parken und Einstellungen ändern geht weiterhin nur in der Greenworks-App.

**Inhalt:** [Getestete Mäher](#getestete-mäher) · [Installation](#installation) · [Was du bekommst](#was-du-bekommst) · [Fehlercodes](ERRORS.de.md) · [Beispiele](BEISPIELE.md) · [Einstellungen](#einstellungen-konfigurieren) · [Winterpause](#winterpause) · [Reparaturen](#hinweise-unter-reparaturen) · [Einschränkungen](#einschränkungen) · [Zeitumstellung](#uhrzeit-nach-der-zeitumstellung) · [Abmelden aus der App](#du-wirst-öfter-aus-der-greenworks-app-abgemeldet) · [Entfernen](#entfernen)

## Getestete Mäher

| Mäher | Getestet von |
|---|---|
| Greenworks **Optimow 10** | dem Entwickler, im täglichen Betrieb |
| Cramer **RM1000** und **RM1500** (mit der Greenworks-App) | von einem Nutzer gemeldet ([Kommentar](https://github.com/Boes24/GreenWorks-HA/issues/1)) |

Andere Greenworks-/Cramer-Mähroboter, die mit der Greenworks-App laufen, funktionieren wahrscheinlich auch. **Cramer-Flottenkonten** (`fleet.cramertools.com`) sind ein eigener Dienst und werden **nicht** unterstützt. Wenn du ein anderes Modell ausprobierst, [gib uns gern Bescheid](https://github.com/paberke/GreenWorks-HA/issues/new/choose).

## Installation

**Voraussetzung:** Home Assistant **2025.1 oder neuer**. Automatisch getestet mit 2025.2 und 2026.2.

**Ab Home Assistant 2026.11 (Marketplace)** – ab 2026.11 ist HACS als **Marketplace** in Home Assistant eingebaut:

1. Einstellungen → **Marketplace** → Menü (⋮) → **Benutzerdefinierte Repositories** (einmalig wirst du gebeten, GitHub zu verbinden)
2. URL `https://github.com/paberke/GreenWorks-HA`, Typ **Integration**, hinzufügen
3. **Greenworks** herunterladen und Home Assistant neu starten

**Ältere Versionen (HACS)**

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=paberke&repository=GreenWorks-HA&category=integration)

1. HACS → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, Typ **Integration**, hinzufügen
3. **Greenworks** herunterladen und Home Assistant neu starten

**Einrichten**

1. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *Greenworks*
2. E-Mail und Passwort der Greenworks-App eingeben
3. Auswählen, was du zusätzlich zu den Standard-Entitäten sehen möchtest (siehe unten). Das kannst du jederzeit unter **Konfigurieren** ändern.

## Was du bekommst

Die **Standard-Entitäten** werden immer angelegt. Alles andere ist in Gruppen eingeteilt, die du ein- und ausschalten kannst – beim Einrichten oder später unter **Konfigurieren**. Ausgeschaltete Entitäten werden nur *deaktiviert*, nicht gelöscht. Schaltest du sie wieder ein, haben sie dieselben Entity-IDs wie vorher.

| Standard | Was sie zeigt |
|---|---|
| **Mäher** | *Angedockt*, *Mäht*, *Fährt zurück* oder *Fehler*; *nicht verfügbar*, solange der Mäher offline ist |
| **Status** | Genauer Zustand mit den Bezeichnungen der App, z. B. *Nach Zeitplan geparkt*, *Lädt*, *Sucht Station*, *Schwerer Fehler*, *Offline* oder *Winterpause* |
| **Statustext** | Die Statuszeile der App, z. B. *Nach Zeitplan geparkt bis Mo. 09:00*, *Mäht bis 12:30* oder *Vom Benutzer geparkt bis auf Weiteres* – praktisch für Dashboards und Benachrichtigungen |
| **Batterie** | Akkustand in % |
| **Lädt** | An, solange der Mäher lädt |
| **Nächster Start** / **Mähende** | Wann der Mäher das nächste Mal losfährt / wann das aktuelle Mähfenster endet |
| **Online** | Ob der Mäher mit der Cloud verbunden ist |
| **Problem** | *Problem* oder *Kein Problem*. Das Attribut *Grund* sagt, warum, z. B. *Zu starke Neigung (Fehler 13)*, *Offline* oder *Winterpause* |
| **Fehler** (Ereignis) | Löst bei jedem neuen Fehler einmal aus, mit Code, Text und Uhrzeit – ideal für Automationen mit Benachrichtigung |
| **Winterpause** (Schalter) | Siehe [Winterpause](#winterpause) |
| **Messer-Laufzeit** | Mähstunden seit dem letzten Zurücksetzen der Messerzeit in der App (gleiche Rechnung wie die App) |
| **Messerwechsel fällig** | *Fällig*, sobald die Messer-Laufzeit die Grenze erreicht (Standard 150 h) |

<details>
<summary><b>Zusätzliche Gruppen</b> (zum Aufklappen antippen)</summary>

| Gruppe | Entitäten |
|---|---|
| **Fehler ausführlich** | Letzter Fehlercode, Letzter Fehler (Zeitpunkt), Letzte Fehlermeldung (Klartext, mit der Fehlerliste der App als Attribut), Schwere Fehler |
| **Statistik** | Mähzeit gesamt, Laufzeit gesamt, Ladezeit gesamt, Statistik-Stand, Letzte Statusmeldung |
| **Einstellungen aus der App** | Mähplan (z. B. *Mo–Fr 09:00–12:30*), Überfahrweite, Abstand beim Drahtfolgen, Startpunkte, Regenschutz, Frostschutz, **PIN-Schutz** und **Geofence** (Diebstahlschutz, wie in der App eingestellt) – nur Anzeige |
| **Diagnose** | Software (mit Mähwerk und Ladestation), Signalqualität |
| **Kalender** | Der Mähplan als Kalendertermine („Mähen“) |
| **Position** | Der Mäher auf der Karte (GPS) |

Bestehende Installationen von vor 0.3.0 behalten alle ihre Entitäten; nur der Kalender ist neu und ausgeschaltet.

Auf der Geräteseite stehen außerdem die Teilenummer des Mähers (*Modell-ID*) und die Hardware-Revision mit Produktionsmonat, z. B. *Rev. 1 (2019-02)*.

</details>

<details>
<summary><b>Zusatzinfos (Attribute)</b></summary>

Entität antippen → **⋮** → **Details** → **Attribute**. In Automationen und Vorlagen kommst du mit `state_attr()` an sie heran.

| Entität | Attribute |
|---|---|
| **Status** | *Letzter Zustand* – nur wenn der Mäher offline ist: der Zustand vor dem Ausfall |
| **Problem** | *Grund* |
| **Fehler** (Ereignis) | *Fehlercode*, *Text*, *Uhrzeit* |
| **Letzter Fehlercode** | *Bedeutung* – der Fehler als Klartext |
| **Letzte Fehlermeldung** | *Klartext*, *Verlauf* (Fehlerliste der App mit Datum), *Verlauf aktualisiert* |
| **Mähplan** | *Montag* bis *Sonntag* mit den Mähzeiten, *Aktualisiert* |
| **Software** | *Mähwerk*, *Ladestation*, *Vom Mäher gemeldet* (wann der Mäher seinen Softwarestand zuletzt selbst geschickt hat) |
| **Abstand beim Drahtfolgen** | *Leitdraht 1*, *Leitdraht 2*, *Aktualisiert* |
| **Startpunkte** | *Punkt 1* bis *Punkt 5* (Draht, Entfernung, Anteil der Starts), *Ladestation*, *Aktualisiert* |
| **Messerwechsel fällig** | *Grenze (h)*, *Verbleibend (h)* |
| **Mähzeit gesamt**, **Messer-Laufzeit** | *Davon gezählt*, *Letzte echte Statistik* (siehe [Einschränkungen](#einschränkungen)) |
| **Mäher** | *status*, *status_code*, *park_reason_code*, *sub_status_code* – Rohwerte für Automationen |

*Aktualisiert* zeigt, wann die App den Wert zuletzt aus dem Mäher gelesen hat.

</details>

### Fehlercodes

Alle 69 Fehlercodes mit Bedeutung und einem kurzen Tipp, was zu tun ist: **[ERRORS.de.md](ERRORS.de.md)**.

## Einstellungen (Konfigurieren)

Einstellungen → Geräte & Dienste → Greenworks → **Konfigurieren**:

| Einstellung | Standard | Bedeutung |
|---|---|---|
| Zusätzliche Entitäten | – | Welche zusätzlichen Gruppen angezeigt werden |
| Abfrage-Intervall | 60 s | Wie oft die Cloud gefragt wird (30–600 s) |
| Letzte Werte bei Aussetzern behalten | 5 min | Kurze Ausfälle der Cloud werden überbrückt (1–60 min) |
| Messerwechsel nach | 150 h | Grenze für *Messerwechsel fällig* (0 = aus). Greenworks nennt kein festes Intervall; allgemein empfohlen wird ein Wechsel alle 6–10 Wochen Mähbetrieb |
| Hinweis unter Reparaturen, wenn offline seit | 1 h | Siehe [Hinweise unter Reparaturen](#hinweise-unter-reparaturen) (0 = aus) |

## Winterpause

Im Winter ist der Mäher ausgeschaltet und damit offline. Ohne Winterpause kämen monatelang Offline-Hinweise, und **Problem** stünde dauerhaft auf *Problem*.

Schalte **Winterpause** ein (ein Schalter auf der Geräteseite des Mähers):

- kein Offline-Hinweis unter *Reparaturen*
- **Problem** zeigt *Kein Problem*, Grund *Winterpause*
- **Status** zeigt *Winterpause* statt *Offline*

Der Schalter ändert nur die Anzeige in Home Assistant – **am Mäher wird nichts verändert**. Tipp: Eine Automation kann ihn nach Datum ein- und ausschalten, z. B. am 1. November und am 15. März – [fertiges Beispiel](BEISPIELE.md#winterpause-nach-datum).

## Hinweise unter Reparaturen

Unter Einstellungen → System → **Reparaturen** erscheint ein Hinweis, wenn

- der Mäher länger als die eingestellte Zeit **offline** ist (Standard 1 Stunde, nicht in der Winterpause), oder
- die **Greenworks-Cloud** so lange nicht erreichbar ist.

Beide Hinweise verschwinden von selbst, sobald wieder alles läuft. Wird das Passwort nicht mehr angenommen, fragt Home Assistant wie gewohnt danach (*Neu authentifizieren*).

<details>
<summary><b>Beispiel für eine Dashboard-Karte</b></summary>

`rasenrobo` durch den Namen deines Mähers ersetzen. Die Entity-IDs richten sich nach dem Gerätenamen und der Sprache von Home Assistant.

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: lawn_mower.rasenrobo
  - type: grid
    columns: 2
    square: false
    cards:
      - type: tile
        entity: sensor.rasenrobo_status
      - type: tile
        entity: sensor.rasenrobo_batterie
      - type: tile
        entity: binary_sensor.rasenrobo_problem
      - type: tile
        entity: sensor.rasenrobo_nachster_start
```

</details>

## Einschränkungen

- **Keine Steuerung:** nur Auslesen. Starten, Parken oder Einstellungen ändern ist über Home Assistant nicht möglich und auch nicht geplant.
- **Statistik nur beim Öffnen der App aktuell:** Mäh-, Lauf- und Ladezeit schickt der Mäher nur, wenn in der App die Statistik geöffnet wird. Damit **Mähzeit gesamt** und **Messer-Laufzeit** trotzdem aktuell sind, zählt die Integration die Minuten selbst mit, in denen der Mäher *mäht*, und schlägt sie auf den letzten echten Wert auf (Attribut *Davon gezählt*). Kommt eine neue echte Statistik, gilt wieder diese.
- **Mähplan, Fehlerverlauf und Einstellungen sind nur so aktuell wie die App:** Die Cloud aktualisiert sie, wenn du in der App die jeweilige Seite öffnest (Attribut *Aktualisiert*).
- **Keine Anzeige für Software-Updates:** Ob es neue Mäher-Software gibt, zeigt nur die Greenworks-App (Seite *Software*). Ihr Update-Server beantwortet keine Anfragen von außerhalb der App.
- **Softwarestand kann von der App abweichen:** Der Sensor **Software** zeigt die Version, die der Mäher selbst regelmäßig meldet. Die App zeigt auf ihrer Seite *Software* teils einen **alten, gespeicherten Stand** (bei unserem Optimow 10 die 6.53 von 2022, obwohl er längst 6.65 hat). Wann der Mäher den Wert zuletzt geschickt hat, steht im Attribut *Vom Mäher gemeldet*.
- **Letzte Fehlermeldung kann von der Fehlerliste der App abweichen:** Home Assistant zeigt das zuletzt gemeldete Ereignis. Das ist manchmal eine kurze Warnung, die die App nicht auflistet.

## Uhrzeit nach der Zeitumstellung

Der Mäher hat eine eigene Uhr mit einer **festen Zeitzone**. Die Umstellung zwischen Sommer- und Winterzeit macht er **nicht selbst** – die Zeitzone stellt nur die Greenworks-App. Das betrifft nur Länder mit Sommerzeit (z. B. EU, Großbritannien, große Teile der USA, Kanadas und Australiens); die Termine sind je nach Land verschieden.

**Was dann passiert:** Nach der Zeitumstellung rechnet der Mäher seinen Mähplan noch in der alten Zeit. Nach der Umstellung auf Winterzeit fährt er dadurch **eine Stunde zu früh** los, nach der Umstellung auf Sommerzeit eine Stunde zu spät. Home Assistant zeigt das so an, wie der Mäher es meldet, z. B. *Nach Zeitplan geparkt bis Mo. 08:00* statt 09:00. Die Integration rechnet dabei richtig.

**So behebst du es:** Öffne in der Greenworks-App die Seite **Zeitplan**. Die App meldet dann *„Fehlerhafte Uhrzeit“* und fragt, ob sie die Zeit vom Handy übernehmen soll – mit **OK** bestätigen. Kurz danach zeigt auch Home Assistant wieder die richtige Zeit. Der Mäher muss dafür online sein.

Damit du es nicht vergisst: [Beispiel-Automation, die dich am Tag der Zeitumstellung erinnert](BEISPIELE.md#erinnerung-bei-der-zeitumstellung).

## Du wirst öfter aus der Greenworks-App abgemeldet

Ein Greenworks-Konto kann anscheinend immer nur an **einer** Stelle gleichzeitig angemeldet sein. Meldest du dich in der App an, wird die Anmeldung von Home Assistant ungültig. Home Assistant meldet sich innerhalb einer Minute still neu an – und dadurch wirst du in der App abgemeldet. Home Assistant selbst läuft dabei zuverlässig weiter.

Wenn dich das stört: Die Integration ausschalten, solange du die App benutzt (*Einstellungen → Geräte & Dienste → Greenworks → ⋮ → Deaktivieren*), und danach wieder einschalten. Der Greenworks-Support hat empfohlen, für Home Assistant ein **zweites Konto** zu nutzen und den Mäher damit zu teilen; das haben wir noch nicht ausprobiert.

## Entfernen

1. Einstellungen → Geräte & Dienste → Greenworks → **⋮** → **Löschen**
2. In HACS / Marketplace: Greenworks → **⋮** → **Entfernen**, danach Home Assistant neu starten

## Versionen

Was sich in welcher Version geändert hat: [Releases](https://github.com/paberke/GreenWorks-HA/releases).

## Mitwirkende

- **[Patrick (paberke)](https://github.com/paberke)** – Idee, Tests am echten Optimow 10, Entscheidungen zum Funktionsumfang, Kontakt mit Greenworks, Betreuung des Projekts
- **Claude (KI-Assistent von Anthropic)** – Programmierung, automatische Tests, Dokumentation

## Danksagung

Entstanden als Fork von [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA). Der Code wurde inzwischen vollständig neu geschrieben; die Adresse der Greenworks-Cloud und der Anmeldeweg stammen ursprünglich aus [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core). Danke an Boes24 für den Anstoß.
