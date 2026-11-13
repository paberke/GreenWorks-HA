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
> - Sie **liest** den Mäher standardmäßig **nur aus**. Starten, Pause und Parken gibt es nur, wenn du unter *Konfigurieren* die [Steuerung](#steuerung) einschaltest. Zeitplan und Einstellungen ändert sie nie.
> - Du wirst in der **Greenworks-App öfter abgemeldet**, wenn Home Assistant dasselbe Konto nutzt ([Details](#abmelden-aus-der-app)).
> - **Keine Gewähr, kein Support.** Nutzung auf eigene Verantwortung – lege vorher ein Backup an.

Die Integration liest deinen Greenworks-Mähroboter über die Greenworks-Cloud aus und zeigt die Werte in Home Assistant an: Status, Batterie, nächster Start, Fehler im Klartext, Messer-Laufzeit, Mähplan und mehr. Auf Wunsch kann sie den Mäher auch starten, pausieren und parken – wie die Knöpfe in der App – und den Mähplan setzen (Testphase). Andere Einstellungen änderst du weiterhin in der Greenworks-App.

**Inhalt:** [Getestete Mäher](#getestete-maher) · [Installation](#installation) · [Was du bekommst](#was-du-bekommst) · [Einstellungen](#einstellungen-konfigurieren) · [Steuerung](#steuerung) · [Winterpause](#winterpause) · [Reparaturen](#hinweise-unter-reparaturen) · [Einschränkungen](#einschrankungen) · [Zeitumstellung](#uhrzeit-nach-der-zeitumstellung) · [Abmelden aus der App](#abmelden-aus-der-app) · [Geplant](#geplant) · [Entfernen](#entfernen)

**Zum Nachschlagen:** 📋 [Fehlercodes](ERRORS.de.md) · 🛠️ [Beispiele: Automationen und Dashboard](BEISPIELE.md) · 🤖 [KI-Prompts](PROMPTS.de.md)

<a id="getestete-maher"></a>

## Getestete Mäher

| Mäher | Lesen | Lesen und steuern | Getestet von |
|---|:---:|:---:|---|
| Greenworks **Optimow 10** | ✅ | ✅ (Testphase) | dem Entwickler, im täglichen Betrieb |
| Cramer **RM1000** und **RM1500** (mit der Greenworks-App) | ✅ | ✅ RM1000 mit [PIN](#pin) (Testphase), RM1500 nicht getestet | von Nutzern gemeldet ([Kommentar 1](https://github.com/Boes24/GreenWorks-HA/issues/1), [Kommentar 2](https://github.com/paberke/GreenWorks-HA/issues/1), [Test Steuerung](https://github.com/paberke/GreenWorks-HA/issues/1#issuecomment-6766979832)) |

Andere Greenworks-/Cramer-Mähroboter, die mit der Greenworks-App laufen, funktionieren wahrscheinlich auch. Die [Steuerung](#steuerung) ist in der **Testphase** und wurde bisher mit dem **Optimow 10** und dem **Cramer RM1000** getestet. **Cramer-Flottenkonten** (`fleet.cramertools.com`) sind ein eigener Dienst und werden **nicht** unterstützt. Wenn du ein anderes Modell ausprobierst, [gib uns gern Bescheid](https://github.com/paberke/GreenWorks-HA/issues/new/choose).

## Installation

**Voraussetzung:** Home Assistant **2025.1 oder neuer**. Automatisch getestet mit 2025.2, 2026.2 und 2026.10. Läuft live mit 2026.11.1 (Lesen).

**Ab Home Assistant 2026.11 (Marketplace)** – ab 2026.11 ist HACS als **Marketplace** in Home Assistant eingebaut:

1. Einstellungen → **Marketplace** → **Über Link hinzufügen** (eventuell wirst du einmalig gebeten, GitHub zu verbinden)
2. GitHub-Link `https://github.com/paberke/GreenWorks-HA` eintragen → **Hinzufügen**
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
| **Mähen ohne Unterbrechung** | *An* mit Attribut *Bis*, solange der Mäher ohne Zeitplan durchmäht ([Steuerung](#steuerung)) |
| **Messerwechsel fällig** | *Fällig*, sobald die Messer-Laufzeit die Grenze erreicht (Standard 150 h) |

<details>
<summary><b>Zusätzliche Gruppen</b> (zum Aufklappen antippen)</summary>

| Gruppe | Entitäten |
|---|---|
| **Fehler ausführlich** | Letzter Fehlercode, Letzter Fehler (Zeitpunkt), Letzte Fehlermeldung (Klartext, mit der Fehlerliste der App als Attribut), Schwere Fehler |
| **Statistik** | Mähzeit gesamt, Laufzeit gesamt, Ladezeit gesamt, Statistik-Stand, Letzte Statusmeldung |
| **Einstellungen aus der App** | Mähplan (z. B. *Mo–Fr 09:00–12:30*), Überfahrweite, Abstand beim Drahtfolgen, Startpunkte, Regenschutz, Frostschutz, **PIN-Schutz** und **Geofence** (Diebstahlschutz, wie in der App eingestellt) – nur Anzeige. *Geofence* zeigt, ob der Schutz **eingeschaltet** ist, nicht ob der Mäher den Bereich verlassen hat |
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
| **Mähzeit gesamt**, **Messer-Laufzeit** | *Davon gezählt*, *Letzte echte Statistik* (siehe [Einschränkungen](#einschrankungen)) |
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
| Steuerung | Nur lesen | *Lesen und steuern* schaltet [Starten, Pause, Parken und Mähplan](#steuerung) frei |
| PIN | leer | Nur nötig, wenn am Mäher der **PIN-Schutz** an ist und *Starten* abgelehnt wird. 4 Ziffern wie in der App. Siehe [PIN](#pin) |
| Abfrage-Intervall | 60 s | Wie oft die Cloud gefragt wird (30–600 s) |
| Letzte Werte bei Aussetzern behalten | 5 min | Kurze Ausfälle der Cloud werden überbrückt (1–60 min) |
| Messerwechsel nach | 150 h | Grenze für *Messerwechsel fällig* (0 = aus). Greenworks nennt kein festes Intervall; allgemein empfohlen wird ein Wechsel alle 6–10 Wochen Mähbetrieb |
| Hinweis unter Reparaturen, wenn offline seit | 1 h | Siehe [Hinweise unter Reparaturen](#hinweise-unter-reparaturen) (0 = aus) |

<a id="steuerung"></a>

## Steuerung (optional)

Standardmäßig liest die Integration nur. Stellst du unter **Konfigurieren** die **Steuerung** auf *Lesen und steuern*, kannst du den Mäher aus Home Assistant heraus bedienen – mit denselben Befehlen, die auch die Greenworks-App schickt:

Auf der Geräteseite gibt es dieselben Auswahlen wie in der App:

| Taste | Wie in der App |
|---|---|
| **Mähen starten / Zeitplan fortsetzen** | Play-Knopf |
| **Pause** | Pause-Knopf |
| **Parken bis auf Weiteres** / **für 2 Stunden** / **für den Rest des Tages** / **für eigene Zeit** | Dialog *Rasenmäher parken* |
| **Mähen ohne Unterbrechung: 2 Tage** / **1 Woche** / **eigene Zeit** / **aus** | ∞ auf der Seite *Zeitplan* |

- Die **eigene Zeit** stellst du in den Zahlenfeldern *Parken für eigene Zeit: Stunden* (1–24) und *Mähen ohne Unterbrechung: eigene Zeit, Tage* (1–24) ein, wie in der App. Sie stehen direkt unter ihrer Taste.
- **Gesperrt wie in der App:** Tasten, die im aktuellen Zustand nicht gehen, sind *nicht verfügbar*. Beispiel: Ist der Mäher *nach Zeitplan*, *durch Regen-* oder *Frostschutz* geparkt, geht nur *Parken bis auf Weiteres*. *Start* gibt es nur, wenn er pausiert oder vom Benutzer geparkt ist, *Pause* nur, wenn er unterwegs ist.
- **Start heißt „Zeitplan fortsetzen“:** Außerhalb des Mähfensters bleibt der Mäher in der Station und fährt erst zum nächsten Termin los. Ist der Akku noch nicht voll genug, lädt er erst weiter (Status *Lädt*), auch das entscheidet der Mäher selbst.
- Für Automationen gibt es die Aktionen `greenworks.park` (`hours` 1–24, ohne Angabe: bis auf Weiteres) und `greenworks.mow_continuously` (`days` 1–24, 0 = aus). Die Mäher-Entität hat außerdem die üblichen Knöpfe Start, Pause und Zur Station.
- Home Assistant wartet auf die **Bestätigung des Mähers**. Kommt keine (z. B. Mäher offline) oder lehnt er ab, erscheint eine Fehlermeldung.
- Nach einem Befehl kann es **bis zu etwa einer Minute** dauern, bis Status und Tasten in Home Assistant den neuen Stand zeigen. Die App ist manchmal schneller, weil sie die Antwort direkt bekommt.
- Die Tasten sind nur verfügbar, solange der Mäher **online** ist.
- Ist am Mäher der **PIN-Schutz** an, lehnt er *Starten* ohne PIN ab. Dann die PIN unter **Konfigurieren** eintragen, siehe [PIN](#pin).
- **Mähen ohne Unterbrechung: aus** während der Mäher gerade mäht: Er hört auf und fährt zur Station. Danach geht es nach Mähplan weiter.
- Zurück auf *Nur lesen* stellen schaltet alles wieder ab: die Tasten werden deaktiviert, die Verbindung für die Befehle wird beendet.
- Der Sensor **Mähen ohne Unterbrechung** (immer da, auch bei *Nur lesen*) zeigt, ob es gerade an ist und bis wann. Das ist wichtig, weil die App es nicht anzeigt, solange der Mäher *vom Benutzer geparkt* ist: Gibst du ihn dann frei, mäht er sofort durch.

<a id="maehplan-setzen"></a>

### Mähplan setzen (Testphase)

Mit der Aktion `greenworks.set_schedule` (*Mähplan setzen*) stellst du den Mähplan ein wie in der App auf der Seite *Zeitplan bearbeiten*. In *Entwicklerwerkzeuge → Aktionen* oder in einer Automation gibt es dafür eine Maske:

| Feld | Bedeutung |
|---|---|
| **Tage** | Welche Tage geändert werden. Die anderen Tage bleiben, wie sie sind |
| **Fenster 1 Beginn / Ende** | Erstes Zeitfenster, z. B. 14:00 bis 19:00 |
| **Fenster 2 Beginn / Ende** | Optionales zweites Zeitfenster |

```yaml
action: greenworks.set_schedule
target:
  entity_id: lawn_mower.mein_maeher
data:
  weekdays: [monday, thursday]
  start_1: "14:00"
  end_1: "19:00"
```

- **Ohne Zeiten** wird an den gewählten Tagen nicht gemäht.
- **Geprüft wie in der App:** Das Ende muss am selben Tag nach dem Beginn liegen (kein Fenster über Mitternacht), die beiden Fenster dürfen sich nicht überschneiden.
- **Abgesichert:** Vor dem Speichern liest Home Assistant den aktuellen Plan frisch vom Mäher und ändert nur die gewählten Tage. Klappt das Lesen nicht, wird nichts gesendet. Nach dem Speichern liest es den Plan noch einmal und meldet einen Fehler, wenn er nicht stimmt.
- **Gesperrt**, solange *Mähen ohne Unterbrechung* läuft (wie in der App).
- Sensor und Kalender *Mähplan* zeigen den neuen Plan nach spätestens etwa einer Minute.
- **Testphase:** getestet am Optimow 10 und am Cramer RM1000.

<a id="pin"></a>

### PIN

Ist am Mäher der **PIN-Schutz** an, fragt die App beim Starten nach der PIN. Home Assistant kann nicht nachfragen. Darum trägst du die PIN einmal unter **Konfigurieren** ein (4 Ziffern). Ohne PIN schickt die Integration den Start wie bisher.

- Die PIN bleibt in Home Assistant. In der heruntergeladenen Diagnose ist sie ausgeblendet.
- **Testphase:** am Cramer RM1000 mit PIN-Schutz bestätigt (Starten nach Pause und nach *Vom Benutzer geparkt*).

## Winterpause

Im Winter ist der Mäher ausgeschaltet und damit offline. Ohne Winterpause kämen monatelang Offline-Hinweise, und **Problem** stünde dauerhaft auf *Problem*.

Schalte **Winterpause** ein (ein Schalter auf der Geräteseite des Mähers):

- kein Offline-Hinweis unter *Reparaturen*
- **Problem** zeigt *Kein Problem*, Grund *Winterpause*
- **Status** zeigt *Winterpause* statt *Offline*

Der Schalter ändert nur die Anzeige in Home Assistant – **am Mäher wird nichts verändert**. Tipp: Eine Automation kann ihn nach Datum ein- und ausschalten, z. B. am 1. November und am 15. März – [fertiges Beispiel](BEISPIELE.md#winterpause-nach-datum). Oder automatisch, sobald der Mäher eingelagert ist, mit Erinnerung zum Einwintern: [Beispiel](BEISPIELE.md#einwintern-und-saisonstart).

**Einwintern:** Greenworks empfiehlt, den Akku vor der Winterlagerung **voll zu laden** und den Mäher **trocken und frostfrei** zu lagern – ein Dach über der Ladestation reicht nicht, Frost schadet dem Akku. Ladestation und Netzteil möglichst ebenfalls reinholen; die Drähte bleiben im Boden, ihre Enden vor Feuchtigkeit schützen. Im Frühjahr die Ladekontakte auf Korrosion prüfen und die [Uhrzeit](#uhrzeit-nach-der-zeitumstellung) in der App stellen.

## Hinweise unter Reparaturen

Unter Einstellungen → System → **Reparaturen** erscheint ein Hinweis, wenn

- der Mäher länger als die eingestellte Zeit **offline** ist (Standard 1 Stunde, nicht in der Winterpause), oder
- die **Greenworks-Cloud** so lange nicht erreichbar ist.

Beide Hinweise verschwinden von selbst, sobald wieder alles läuft. Wird das Passwort nicht mehr angenommen, fragt Home Assistant wie gewohnt danach (*Neu authentifizieren*).

**Dashboard:** [Beispiel für eine Dashboard-Karte](BEISPIELE.md#dashboard-karte)

<a id="einschrankungen"></a>

## Einschränkungen

- **Einstellungen nur in der App:** Die [Steuerung](#steuerung) kann starten, pausieren, parken und den [Mähplan setzen](#maehplan-setzen). Regensensor, Schnittbreite usw. ändert die Integration nicht.
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

<a id="abmelden-aus-der-app"></a>

## Du wirst öfter aus der Greenworks-App abgemeldet

Ein Greenworks-Konto kann anscheinend immer nur an **einer** Stelle gleichzeitig angemeldet sein. Meldest du dich in der App an, wird die Anmeldung von Home Assistant ungültig. Home Assistant meldet sich innerhalb einer Minute still neu an – und dadurch wirst du in der App abgemeldet. Home Assistant selbst läuft dabei zuverlässig weiter.

Wenn dich das stört: Die Integration ausschalten, solange du die App benutzt (*Einstellungen → Geräte & Dienste → Greenworks → ⋮ → Deaktivieren*), und danach wieder einschalten. Der Greenworks-Support hat empfohlen, für Home Assistant ein **zweites Konto** zu nutzen und den Mäher damit zu teilen; das haben wir noch nicht ausprobiert.

## Geplant

Was wir als Nächstes angehen wollen. **Ob und wann das klappt, ist noch nicht sicher.** Wir probieren es aus und testen alles erst am eigenen Mäher.

- Aufnahme in den HACS-Store bzw. den neuen **Marketplace** ab Home Assistant 2026.11
- **Uhrzeit** des Mähers nach der Zeitumstellung automatisch stellen
- **Konto wechseln**, ohne die Integration neu einzurichten

Ideen und Wünsche gern als [Issue](https://github.com/paberke/GreenWorks-HA/issues/new/choose).

## Entfernen

1. Einstellungen → Geräte & Dienste → Greenworks → **⋮** → **Löschen**
2. In HACS / Marketplace: Greenworks → **⋮** → **Entfernen**, danach Home Assistant neu starten

## Versionen

Was sich in welcher Version geändert hat: [Releases](https://github.com/paberke/GreenWorks-HA/releases).

## Mitwirkende

- **[Patrick (paberke)](https://github.com/paberke)** – Idee, Tests am echten Optimow 10, Entscheidungen zum Funktionsumfang, Kontakt mit Greenworks, Betreuung des Projekts
- **[Sander Allefs (sanderallefs)](https://github.com/sanderallefs)** – Tests mit einem Cramer RM1000 (PIN, Steuerung, Mähplan)
- **Claude (KI-Assistent von Anthropic)** – Programmierung, automatische Tests, Dokumentation

## Danksagung

Entstanden als Fork von [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA). Der Code wurde inzwischen vollständig neu geschrieben; die Adresse der Greenworks-Cloud und der Anmeldeweg stammen ursprünglich aus [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core). Danke an Boes24 für den Anstoß.
