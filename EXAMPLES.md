# Examples for automations and templates

**English** · [Deutsch](BEISPIELE.md) · [Back to the README](README.md)

Ready-to-copy examples. Replace **`rasenrobo`** with the name of your mower and **`notify.mobile_app_your_phone`** with your phone everywhere. You find the exact entity IDs under *Settings → Devices & services → Greenworks → your mower*. They depend on the device name and the language of Home Assistant; the examples here use the English names.

**Adding an automation:** *Settings → Automations & scenes → Create automation → Create new automation → ⋮ → Edit in YAML*, paste, save.

**Trying a template:** *Developer tools → Template*.

**Contents:** [Notification on a new error](#notification-on-a-new-error) · [Blade change due](#blade-change-due) · [Mower has a problem](#mower-has-a-problem) · [Winter pause by date](#winter-pause-by-date) · [Reading values](#reading-values)

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
