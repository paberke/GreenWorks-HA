# Prompts für KI-Assistenten

[English](PROMPTS.md) · **Deutsch** · [Zurück zur Readme](README.de.md) · [Beispiele](BEISPIELE.md)

Du lässt dir Automationen lieber von einer KI bauen (z. B. Claude, ChatGPT oder Assist in Home Assistant)? Hier sind fertige Prompts zum Kopieren.

> [!NOTE]
> Geschrieben von Claude (KI), nicht von Greenworks. Die KI kann sich irren – prüfe den Vorschlag, bevor du ihn speicherst.

**So geht's:** Kopiere zuerst den **Kontext-Block** in den Chat, danach einen der Prompts darunter.

- **KI mit Zugriff auf Home Assistant** (z. B. Assist oder eine KI mit Home-Assistant-Anbindung): Kontext-Block einfach so einfügen. Die KI sucht deinen Mäher und dein Handy selbst und lässt sie dich bestätigen.
- **KI ohne Zugriff** (z. B. ChatGPT oder Claude im Browser): Ersetze im Kontext-Block `rasenrobo` durch den Namen deines Mähers. Die genauen Entity-IDs findest du unter *Einstellungen → Geräte & Dienste → Greenworks → dein Mäher*. Nach deinem Handy fragt die KI dann selbst.

**Inhalt:** [Kontext-Block](#kontext-block) · [Fehler melden](#fehler-melden) · [Wochenübersicht](#wochenubersicht) · [Einwintern und Saisonstart](#einwintern-und-saisonstart) · [Zeitumstellung](#zeitumstellung) · [Messerwechsel](#messerwechsel) · [Dashboard-Karte](#dashboard-karte) · [Automation prüfen](#automation-prufen) · [Datenschutz](#datenschutz)

## Kontext-Block

```text
Ich nutze in Home Assistant die Integration "Greenworks" (HACS, github.com/paberke/GreenWorks-HA)
für meinen Greenworks-Mähroboter. Wichtig:
- Die Integration kann NUR LESEN. Es gibt keine Befehle zum Starten, Parken oder Einstellen.
  Schlage keine Aktionen am Mäher vor, nur Benachrichtigungen, Helfer und Anzeigen.
- Hast du Zugriff auf mein Home Assistant: Suche die Entitäten der Integration "greenworks" und
  meinen notify-Dienst fürs Handy selbst und lass sie mich bestätigen, bevor du baust.
  Sonst: Frag mich nach meinem notify-Dienst. Beispiel für die Entitäten (Mäher "rasenrobo",
  Home Assistant auf Deutsch; bei mir können die Namen anders sein):
  lawn_mower.rasenrobo (Attribute: status, status_code, park_reason_code, sub_status_code)
  sensor.rasenrobo_status (Werte u. a.: mowing, charging, parked_by_schedule, parked_by_user,
    parked_by_rain_guard, parked_by_frost_guard, searching_station, error, fatal_error, alarm,
    offline, winter_pause)
  sensor.rasenrobo_statustext (Text wie in der App, z. B. "Nach Zeitplan geparkt bis Mo. 09:00")
  sensor.rasenrobo_batterie (%), binary_sensor.rasenrobo_ladt, binary_sensor.rasenrobo_online
  sensor.rasenrobo_nachster_start, sensor.rasenrobo_mahende (Zeitstempel)
  binary_sensor.rasenrobo_problem (Attribut reason)
  event.rasenrobo_fehler (löst bei jedem neuen Fehler einmal aus; Attribute code, text, time)
  sensor.rasenrobo_messer_laufzeit (h), binary_sensor.rasenrobo_messerwechsel_fallig
    (Attribute limit, remaining)
  switch.rasenrobo_winterpause (ändert nur die Anzeige in Home Assistant, nichts am Mäher)
  Optional, wenn eingeschaltet: sensor.rasenrobo_letzte_fehlermeldung, sensor.rasenrobo_mahplan,
    calendar.rasenrobo_mahplan, device_tracker.rasenrobo_position
- Der Mäher stellt Sommer-/Winterzeit nicht selbst um; das passiert nur in der Greenworks-App.
Schreibe vollständiges YAML für den UI-Editor (Automation → In YAML bearbeiten), nutze
entity_id statt device_id und nichts in configuration.yaml.
```

## Fehler melden

```text
Erstelle eine Automation, die mir bei jedem neuen Fehler des Mähers eine Nachricht aufs Handy
schickt, mit Fehlertext und Code. Nutze dafür das Fehler-Ereignis des Mähers.
```

<a id="wochenubersicht"></a>

## Wochenübersicht

```text
Sammle jeden Fehler des Mähers in einer To-do-Liste und schicke mir sonntags um 18 Uhr eine
Übersicht der Woche aufs Handy. Danach soll die Liste geleert werden.
Sag mir, welche To-do-Liste ich vorher als Helfer anlegen muss.
```

## Einwintern und Saisonstart

```text
Erinnere mich ab Mitte Oktober samstags, den Mäher einzuwintern, wenn Frost vorhergesagt ist
(nimm meine Wetter-Entität). Schalte die Winterpause ein, wenn der Mäher im Winter
24 Stunden offline ist, und wieder aus, sobald er online ist – mit einer Nachricht, dass ich
in der App die Uhrzeit bestätigen und die Ladekontakte prüfen soll.
```

## Zeitumstellung

```text
Erinnere mich am Tag der Zeitumstellung, die Uhr des Mähers in der Greenworks-App zu stellen
(Seite Zeitplan, Meldung "Fehlerhafte Uhrzeit" mit OK bestätigen). Nicht in der Winterpause.
Die Automation soll die Zeitumstellung selbst erkennen, ohne feste Daten.
```

## Messerwechsel

```text
Schick mir eine Nachricht aufs Handy, sobald "Messerwechsel fällig" auf an geht,
mit der aktuellen Messer-Laufzeit. Und eine zweite Nachricht, wenn nur noch 10 Stunden übrig
sind (Attribut remaining).
```

## Dashboard-Karte

```text
Baue mir eine Dashboard-Karte für den Mäher mit Statustext, Batterie, nächstem Start, Problem
(mit Grund) und Messer-Laufzeit. Nur Standard-Karten von Home Assistant.
```

<a id="automation-prufen"></a>

## Automation prüfen

```text
Meine Automation für den Mäher löst nicht aus. Hier ist das YAML: [YAML einfügen].
Prüfe Entity-IDs, Zustände und Bedingungen anhand des Kontext-Blocks und sag mir, was falsch ist.
```

## Datenschutz

- Gib einer KI **keine** Seriennummer, SIM-Nummer (ICCID), Position oder E-Mail-Adresse.
- Die Diagnosedaten der Integration schwärzen das meiste, prüfe sie trotzdem vor dem Einfügen.
