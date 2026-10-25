# Examples for automations and templates

**English** · [Deutsch](BEISPIELE.md) · [Back to the README](README.md)

Ready-to-copy examples. Replace **`rasenrobo`** with the name of your mower and **`notify.mobile_app_your_phone`** with your phone everywhere. You find the exact entity IDs under *Settings → Devices & services → Greenworks → your mower*. They depend on the device name and the language of Home Assistant; the examples here use the English names.

**Adding an automation:** *Settings → Automations & scenes → Create automation → Create new automation → ⋮ → Edit in YAML*, paste, save.

**Trying a template:** *Developer tools → Template*.

**Rather build it with an AI?** Ready-made prompts: [PROMPTS.md](PROMPTS.md).

**Contents:** [Notification on a new error](#notification-on-a-new-error) · [Blade change due](#blade-change-due) · [Mower has a problem](#mower-has-a-problem) · [Winter pause by date](#winter-pause-by-date) · [Winterising and start of season](#winterising-and-start-of-season) · [Clock change](#reminder-when-the-clocks-change) · [Dashboard card](#dashboard-card) · [Reading values](#reading-values)

## Notification on a new error

Sends a message for every new error, e.g. *"Too high inclination (13)"*. Uses the **Error** event, which fires exactly once per new error.

```yaml
alias: Mower – report errors
description: Notification for every new error of the mower
triggers:
  - trigger: state
    entity_id: event.rasenrobo_error
    not_from:
      - unavailable
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.state not in ['unavailable', 'unknown'] }}"
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: Mower
      message: >-
        {{ state_attr(trigger.entity_id, 'text') }}
        (error {{ state_attr(trigger.entity_id, 'code') }})
mode: queued
```

## Blade change due

Fires once when the blade time reaches the configured limit (default 150 h).

```yaml
alias: Mower – blade change due
description: Reminder when the blades should be changed
triggers:
  - trigger: state
    entity_id: binary_sensor.rasenrobo_blade_change_due
    from: "off"
    to: "on"
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: Mower
      message: >-
        Blade change due: {{ states('sensor.rasenrobo_blade_time') }} hours
        since the last change. Reset the blade time in the app afterwards.
mode: single
```

## Mower has a problem

Fires when **Problem** has been on for 10 minutes (error, alarm or offline – not during the winter pause) and tells you the reason.

```yaml
alias: Mower – problem
description: Notification when the mower has had a problem for 10 minutes
triggers:
  - trigger: state
    entity_id: binary_sensor.rasenrobo_problem
    to: "on"
    for:
      minutes: 10
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: Mower
      message: "Problem: {{ state_attr('binary_sensor.rasenrobo_problem', 'reason') }}"
mode: single
```

## Winter pause by date

Switches the **Winter pause** on on 1 November and off on 15 March. Nothing is changed on the mower itself.

```yaml
alias: Mower – winter pause
description: Winter pause on on 1 Nov and off on 15 Mar
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
              entity_id: switch.rasenrobo_winter_pause
      - conditions:
          - condition: template
            value_template: "{{ now().month == 3 and now().day == 15 }}"
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.rasenrobo_winter_pause
mode: single
```

## Winterising and start of season

One automation for autumn and spring:

- **Reminder:** from 15 October on Saturdays at 10:00, if frost (2 °C or less) is forecast for the next 4 days – with the battery level and the steps to winterise. Repeats every week until the winter pause is on.
- **Winter pause on:** when the mower has been offline for 24 hours between 15 October and the end of February, i.e. it has been stored.
- **Winter pause off:** as soon as it is back online – with the steps for the start of the season.

Replace `weather.forecast_home` with your weather entity.

```yaml
alias: Mower – winterising and start of season
description: Reminder to winterise on frost, winter pause on and off automatically
triggers:
  - trigger: time
    at: "10:00:00"
    id: reminder
  - trigger: state
    entity_id: binary_sensor.rasenrobo_online
    to: "off"
    for:
      hours: 24
    id: stored
  - trigger: state
    entity_id: binary_sensor.rasenrobo_online
    from: "off"
    to: "on"
    id: season_start
actions:
  - choose:
      - alias: Reminder to winterise
        conditions:
          - condition: trigger
            id: reminder
          - condition: time
            weekday: sat
          - condition: template
            value_template: "{{ (now().month == 10 and now().day >= 15) or now().month in [11, 12] }}"
          - condition: state
            entity_id: switch.rasenrobo_winter_pause
            state: "off"
        sequence:
          - action: weather.get_forecasts
            target:
              entity_id: weather.forecast_home
            data:
              type: daily
            response_variable: forecast
          - variables:
              lowest: >-
                {{ (forecast['weather.forecast_home'].forecast[0:4]
                   | selectattr('templow', 'defined')
                   | map(attribute='templow') | list + [99]) | min }}
          - condition: template
            value_template: "{{ lowest | float(99) <= 2 }}"
          - action: notify.mobile_app_your_phone
            data:
              title: Winterise the mower
              message: >-
                Frost down to {{ lowest }} °C forecast. Battery: {{ states('sensor.rasenrobo_battery') }} %.
                1. Fully charge the battery. 2. Clean the mower and store it dry and frost-free.
                3. Bring in the charging station and power supply, protect the wire ends against moisture.
                The winter pause will then switch on by itself.
      - alias: Stored – winter pause on
        conditions:
          - condition: trigger
            id: stored
          - condition: template
            value_template: "{{ (now().month == 10 and now().day >= 15) or now().month in [11, 12, 1, 2] }}"
          - condition: state
            entity_id: switch.rasenrobo_winter_pause
            state: "off"
        sequence:
          - action: switch.turn_on
            target:
              entity_id: switch.rasenrobo_winter_pause
          - action: notify.mobile_app_your_phone
            data:
              title: Lawn mower
              message: Offline for 24 hours – the winter pause is now on.
      - alias: Start of season – winter pause off
        conditions:
          - condition: trigger
            id: season_start
          - condition: state
            entity_id: switch.rasenrobo_winter_pause
            state: "on"
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.rasenrobo_winter_pause
          - action: notify.mobile_app_your_phone
            data:
              title: The mower is back
              message: >-
                Winter pause is off. 1. Open the Schedule page in the Greenworks app and
                confirm "Incorrect time" with OK. 2. Check the charging contacts on mower
                and station for corrosion. 3. Check the blades.
mode: queued
```

## Reminder when the clocks change

The mower does not switch its clock to summer or winter time by itself (see [README](README.md#clock-after-daylight-saving-time-changes)). This automation reminds you at 10:00 on the day the clocks change to set the time in the app – not during the winter pause. It detects the change by itself, whatever your country and date. In countries without daylight saving time it never fires.

```yaml
alias: Mower – set clock after time change
description: Reminder on the day the clocks change to set the mower's time in the app
triggers:
  - trigger: time
    at: "10:00:00"
conditions:
  - condition: template
    value_template: >-
      {{ now().utcoffset() != (now() - timedelta(days=1)).utcoffset() }}
  - condition: state
    entity_id: switch.rasenrobo_winter_pause
    state: "off"
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: Lawn mower
      message: >-
        The clocks changed today. Please open the Schedule page in the
        Greenworks app and confirm "Incorrect time" with OK.
mode: single
```

## Dashboard card

An overview card with mower, status text, status, battery, problem and next start. Uses only standard Home Assistant cards. Adding it: *Dashboard → Edit → Add card → Manual*.

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: lawn_mower.rasenrobo
  - type: markdown
    content: "{{ states('sensor.rasenrobo_status_text') }}"
  - type: grid
    columns: 2
    square: false
    cards:
      - type: tile
        entity: sensor.rasenrobo_status
      - type: tile
        entity: sensor.rasenrobo_battery
      - type: tile
        entity: binary_sensor.rasenrobo_problem
      - type: tile
        entity: sensor.rasenrobo_next_start
```

## Reading values

Templates for messages, dashboards (e.g. a Markdown card) or the developer tools.

**Device info** – serial number, model, part number, software, hardware:

```jinja
{% set device = device_id('lawn_mower.rasenrobo') %}
Serial number: {{ device_attr(device, 'serial_number') }}
Model: {{ device_attr(device, 'model') }} ({{ device_attr(device, 'model_id') }})
Software: {{ device_attr(device, 'sw_version') }}
Hardware: {{ device_attr(device, 'hw_version') }}
```

**Hours until the blade change:**

```jinja
{{ state_attr('binary_sensor.rasenrobo_blade_change_due', 'remaining') }} hours until the blade change
```

**Status text and problem reason:**

```jinja
{{ states('sensor.rasenrobo_status_text') }}
{{ state_attr('binary_sensor.rasenrobo_problem', 'reason') or 'No problem' }}
```

**The last three entries of the app's error list** (group *Detailed errors*):

```jinja
{% for entry in (state_attr('sensor.rasenrobo_last_error_message', 'history') or [])[:3] %}
- {{ entry }}
{% endfor %}
```

**Next start as "Mon 09:00":**

```jinja
{{ as_timestamp(states('sensor.rasenrobo_next_start')) | timestamp_custom('%a %H:%M') }}
```
