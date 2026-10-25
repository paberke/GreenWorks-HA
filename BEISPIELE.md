# Beispiele für Automationen und Vorlagen

[English](EXAMPLES.md) · **Deutsch** · [Zurück zur Readme](README.de.md)

Fertige Beispiele zum Kopieren. Ersetze überall **`rasenrobo`** durch den Namen deines Mähers und **`notify.mobile_app_dein_handy`** durch dein Handy. Die genauen Entity-IDs findest du unter *Einstellungen → Geräte & Dienste → Greenworks → dein Mäher*. Sie richten sich nach dem Gerätenamen und der Sprache von Home Assistant; die Beispiele hier nutzen die deutschen Namen.

**Automationen einfügen:** *Einstellungen → Automationen & Szenen → Automation erstellen → Neue Automation → ⋮ → In YAML bearbeiten*, Text einfügen, speichern.

**Vorlagen ausprobieren:** *Entwicklerwerkzeuge → Template*.

**Lieber mit einer KI bauen?** Fertige Prompts: [PROMPTS.de.md](PROMPTS.de.md).

**Inhalt:** [Benachrichtigung bei neuem Fehler](#benachrichtigung-bei-neuem-fehler) · [Messerwechsel fällig](#messerwechsel-fallig) · [Mäher hat ein Problem](#maher-hat-ein-problem) · [Winterpause nach Datum](#winterpause-nach-datum) · [Einwintern und Saisonstart](#einwintern-und-saisonstart) · [Zeitumstellung](#erinnerung-bei-der-zeitumstellung) · [Werte abfragen](#werte-abfragen)

## Benachrichtigung bei neuem Fehler

Schickt bei jedem neuen Fehler eine Nachricht, z. B. *„Zu starke Neigung (13)“*. Nutzt das Ereignis **Fehler**, das genau einmal pro neuem Fehler auslöst.

```yaml
alias: Rasenmäher – Fehler melden
description: Benachrichtigung bei jedem neuen Fehler des Mähers
triggers:
  - trigger: state
    entity_id: event.rasenrobo_fehler
    not_from:
      - unavailable
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.state not in ['unavailable', 'unknown'] }}"
actions:
  - action: notify.mobile_app_dein_handy
    data:
      title: Rasenmäher
      message: >-
        {{ state_attr(trigger.entity_id, 'text') }}
        (Fehler {{ state_attr(trigger.entity_id, 'code') }})
mode: queued
```

<a id="messerwechsel-fallig"></a>

## Messerwechsel fällig

Meldet sich einmal, sobald die eingestellte Grenze der Messer-Laufzeit erreicht ist (Standard 150 h).

```yaml
alias: Rasenmäher – Messerwechsel fällig
description: Erinnerung, wenn die Messer gewechselt werden sollten
triggers:
  - trigger: state
    entity_id: binary_sensor.rasenrobo_messerwechsel_fallig
    from: "off"
    to: "on"
actions:
  - action: notify.mobile_app_dein_handy
    data:
      title: Rasenmäher
      message: >-
        Messerwechsel fällig: {{ states('sensor.rasenrobo_messer_laufzeit') }} Stunden
        seit dem letzten Wechsel. Danach die Messerzeit in der App zurücksetzen.
mode: single
```

<a id="maher-hat-ein-problem"></a>

## Mäher hat ein Problem

Meldet sich, wenn **Problem** 10 Minuten lang ansteht (Fehler, Alarm oder offline – nicht in der Winterpause), und nennt den Grund.

```yaml
alias: Rasenmäher – Problem
description: Benachrichtigung, wenn der Mäher 10 Minuten lang ein Problem hat
triggers:
  - trigger: state
    entity_id: binary_sensor.rasenrobo_problem
    to: "on"
    for:
      minutes: 10
actions:
  - action: notify.mobile_app_dein_handy
    data:
      title: Rasenmäher
      message: "Problem: {{ state_attr('binary_sensor.rasenrobo_problem', 'reason') }}"
mode: single
```

## Winterpause nach Datum

Schaltet die **Winterpause** am 1. November ein und am 15. März aus. Am Mäher selbst ändert sich dadurch nichts.

```yaml
alias: Rasenmäher – Winterpause
description: Winterpause am 1.11. ein- und am 15.3. ausschalten
triggers:
  - trigger: time
    at: "00:05:00"
actions:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ now().month == 11 and now().day == 1 }}"
        sequence:
          - action: switch.turn_on
            target:
              entity_id: switch.rasenrobo_winterpause
      - conditions:
          - condition: template
            value_template: "{{ now().month == 3 and now().day == 15 }}"
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.rasenrobo_winterpause
mode: single
```

## Einwintern und Saisonstart

Eine Automation für Herbst und Frühjahr:

- **Erinnerung:** Ab 15. Oktober samstags um 10 Uhr, wenn in den nächsten 4 Tagen Frost (2 °C oder weniger) vorhergesagt ist – mit Akkustand und den Schritten zum Einwintern. Kommt jede Woche wieder, bis die Winterpause an ist.
- **Winterpause an:** wenn der Mäher zwischen 15. Oktober und Ende Februar 24 Stunden offline ist, also eingelagert wurde.
- **Winterpause aus:** sobald er wieder online ist – mit den Schritten zum Saisonstart.

`weather.forecast_home` durch deine Wetter-Entität ersetzen.

```yaml
alias: Rasenmäher – Einwintern und Saisonstart
description: Erinnerung zum Einwintern bei Frost, Winterpause automatisch ein und aus
triggers:
  - trigger: time
    at: "10:00:00"
    id: erinnerung
  - trigger: state
    entity_id: binary_sensor.rasenrobo_online
    to: "off"
    for:
      hours: 24
    id: eingelagert
  - trigger: state
    entity_id: binary_sensor.rasenrobo_online
    from: "off"
    to: "on"
    id: saisonstart
actions:
  - choose:
      - alias: Erinnerung zum Einwintern
        conditions:
          - condition: trigger
            id: erinnerung
          - condition: time
            weekday: sat
          - condition: template
            value_template: "{{ (now().month == 10 and now().day >= 15) or now().month in [11, 12] }}"
          - condition: state
            entity_id: switch.rasenrobo_winterpause
            state: "off"
        sequence:
          - action: weather.get_forecasts
            target:
              entity_id: weather.forecast_home
            data:
              type: daily
            response_variable: prognose
          - variables:
              tiefst: >-
                {{ (prognose['weather.forecast_home'].forecast[0:4]
                   | selectattr('templow', 'defined')
                   | map(attribute='templow') | list + [99]) | min }}
          - condition: template
            value_template: "{{ tiefst | float(99) <= 2 }}"
          - action: notify.mobile_app_dein_handy
            data:
              title: Rasenmäher einwintern
              message: >-
                Frost bis {{ tiefst }} °C vorhergesagt. Akku: {{ states('sensor.rasenrobo_batterie') }} %.
                1. Akku voll laden. 2. Mäher reinigen und trocken, frostfrei lagern.
                3. Ladestation und Netzteil reinholen, Drahtenden vor Feuchtigkeit schützen.
                Die Winterpause schaltet sich danach von selbst ein.
      - alias: Eingelagert – Winterpause an
        conditions:
          - condition: trigger
            id: eingelagert
          - condition: template
            value_template: "{{ (now().month == 10 and now().day >= 15) or now().month in [11, 12, 1, 2] }}"
          - condition: state
            entity_id: switch.rasenrobo_winterpause
            state: "off"
        sequence:
          - action: switch.turn_on
            target:
              entity_id: switch.rasenrobo_winterpause
          - action: notify.mobile_app_dein_handy
            data:
              title: Rasenmäher
              message: Seit 24 Stunden offline – Winterpause ist jetzt an.
      - alias: Saisonstart – Winterpause aus
        conditions:
          - condition: trigger
            id: saisonstart
          - condition: state
            entity_id: switch.rasenrobo_winterpause
            state: "on"
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.rasenrobo_winterpause
          - action: notify.mobile_app_dein_handy
            data:
              title: Rasenmäher ist zurück
              message: >-
                Winterpause ist aus. 1. In der Greenworks-App die Seite Zeitplan öffnen
                und bei „Fehlerhafte Uhrzeit“ OK drücken. 2. Ladekontakte an Mäher und
                Station auf Korrosion prüfen. 3. Messer prüfen.
mode: queued
```

## Erinnerung bei der Zeitumstellung

Der Mäher stellt seine Uhr nicht selbst auf Sommer- oder Winterzeit um (siehe [Readme](README.de.md#uhrzeit-nach-der-zeitumstellung)). Diese Automation erinnert dich am Tag der Zeitumstellung um 10 Uhr daran, die Uhr in der App zu stellen – nicht in der Winterpause. Sie erkennt die Zeitumstellung selbst, egal in welchem Land und an welchem Datum. In Ländern ohne Zeitumstellung meldet sie sich nie.

```yaml
alias: Rasenmäher – Uhr nach Zeitumstellung stellen
description: Erinnerung am Tag der Zeitumstellung, die Uhr des Mähers in der App zu stellen
triggers:
  - trigger: time
    at: "10:00:00"
conditions:
  - condition: template
    value_template: >-
      {{ now().utcoffset() != (now() - timedelta(days=1)).utcoffset() }}
  - condition: state
    entity_id: switch.rasenrobo_winterpause
    state: "off"
actions:
  - action: notify.mobile_app_dein_handy
    data:
      title: Rasenmäher
      message: >-
        Heute war Zeitumstellung. Bitte in der Greenworks-App die Seite
        Zeitplan öffnen und bei „Fehlerhafte Uhrzeit“ OK drücken.
mode: single
```

## Werte abfragen

Vorlagen für Nachrichten, Dashboards (z. B. Markdown-Karte) oder die Entwicklerwerkzeuge.

**Geräteinfo** – Seriennummer, Modell, Teilenummer, Software, Hardware:

```jinja
{% set geraet = device_id('lawn_mower.rasenrobo') %}
Seriennummer: {{ device_attr(geraet, 'serial_number') }}
Modell: {{ device_attr(geraet, 'model') }} ({{ device_attr(geraet, 'model_id') }})
Software: {{ device_attr(geraet, 'sw_version') }}
Hardware: {{ device_attr(geraet, 'hw_version') }}
```

**Stunden bis zum Messerwechsel:**

```jinja
Noch {{ state_attr('binary_sensor.rasenrobo_messerwechsel_fallig', 'remaining') }} Stunden bis zum Messerwechsel
```

**Statustext und Problem-Grund:**

```jinja
{{ states('sensor.rasenrobo_statustext') }}
{{ state_attr('binary_sensor.rasenrobo_problem', 'reason') or 'Kein Problem' }}
```

**Die letzten drei Einträge aus der Fehlerliste der App** (Gruppe *Fehler ausführlich*):

```jinja
{% for eintrag in (state_attr('sensor.rasenrobo_letzte_fehlermeldung', 'history') or [])[:3] %}
- {{ eintrag }}
{% endfor %}
```

**Nächster Start als „Mo 09:00“:**

```jinja
{{ as_timestamp(states('sensor.rasenrobo_nachster_start')) | timestamp_custom('%a %H:%M') }}
```
