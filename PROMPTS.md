# Prompts for AI assistants

**English** · [Deutsch](PROMPTS.de.md) · [Back to the README](README.md) · [Examples](EXAMPLES.md)

You'd rather have an AI build your automations (e.g. Claude, ChatGPT or Assist in Home Assistant)? Here are ready-to-copy prompts.

> [!NOTE]
> Written by Claude (AI), not by Greenworks. The AI can be wrong – check its suggestion before you save it.

**How to use:** first paste the **context block** into the chat and replace `rasenrobo` with the name of your mower. Then one of the prompts below. You find the exact entity IDs under *Settings → Devices & services → Greenworks → your mower*.

**Contents:** [Context block](#context-block) · [Error notification](#error-notification) · [Weekly summary](#weekly-summary) · [Winterising and start of season](#winterising-and-start-of-season) · [Clock change](#clock-change) · [Blade change](#blade-change) · [Dashboard card](#dashboard-card) · [Check an automation](#check-an-automation) · [Privacy](#privacy)

## Context block

```text
I use the Home Assistant integration "Greenworks" (HACS, github.com/paberke/GreenWorks-HA)
for my Greenworks robotic mower. Important:
- The integration is READ-ONLY. There are no commands to start, park or change settings.
  Don't suggest actions on the mower, only notifications, helpers and displays.
- My mower is called "rasenrobo", Home Assistant is in English. Entities (use only these):
  lawn_mower.rasenrobo (attributes: status, status_code, park_reason_code, sub_status_code)
  sensor.rasenrobo_status (values include: mowing, charging, parked_by_schedule, parked_by_user,
    parked_by_rain_guard, parked_by_frost_guard, searching_station, error, fatal_error, alarm,
    offline, winter_pause)
  sensor.rasenrobo_status_text (text as in the app, e.g. "Parked by schedule until Mon 09:00")
  sensor.rasenrobo_battery (%), binary_sensor.rasenrobo_charging, binary_sensor.rasenrobo_online
  sensor.rasenrobo_next_start, sensor.rasenrobo_mowing_end (timestamps)
  binary_sensor.rasenrobo_problem (attribute reason)
  event.rasenrobo_error (fires once per new error; attributes code, text, time)
  sensor.rasenrobo_blade_time (h), binary_sensor.rasenrobo_blade_change_due
    (attributes limit, remaining)
  switch.rasenrobo_winter_pause (only changes what Home Assistant shows, nothing on the mower)
  Optional, if enabled: sensor.rasenrobo_last_error_message, sensor.rasenrobo_mowing_schedule,
    calendar.rasenrobo_mowing_schedule, device_tracker.rasenrobo_position
- The mower does not switch between summer and winter time by itself; only the Greenworks app does.
Write complete YAML for the UI editor (automation → Edit in YAML), use entity_id instead of
device_id and nothing in configuration.yaml.
```

## Error notification

```text
Create an automation that sends me a message to notify.mobile_app_MY_PHONE for every new
error of the mower, with error text and code. Use the event event.rasenrobo_error.
```

## Weekly summary

```text
Collect every error of the mower in a to-do list and send me a summary of the week on Sundays
at 18:00 to notify.mobile_app_MY_PHONE. Then clear the list. Tell me which to-do list helper
I have to create first.
```

## Winterising and start of season

```text
From mid-October, remind me on Saturdays to winterise the mower if frost is forecast
(weather entity: weather.MY_WEATHER). Switch on the winter pause when the mower has been
offline for 24 hours in winter, and off again as soon as it is online – with a message to
confirm the time in the app and check the charging contacts.
```

## Clock change

```text
Remind me on the day the clocks change to set the mower's clock in the Greenworks app
(Schedule page, confirm "Incorrect time" with OK). Not during the winter pause.
The automation should detect the change by itself, without fixed dates.
```

## Blade change

```text
Send me a message as soon as binary_sensor.rasenrobo_blade_change_due turns on, with the
current blade time. And a second message when only 10 hours are left (attribute remaining).
```

## Dashboard card

```text
Build me a dashboard card for the mower with status text, battery, next start, problem
(with reason) and blade time. Only standard Home Assistant cards.
```

## Check an automation

```text
My automation for the mower does not trigger. Here is the YAML: [paste YAML].
Check entity IDs, states and conditions against the context block and tell me what is wrong.
```

## Privacy

- Do **not** give an AI your serial number, SIM number (ICCID), position or e-mail address.
- The integration's diagnostics redact most of it; still check them before pasting.
