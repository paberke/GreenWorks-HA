# Greenworks for Home Assistant

**English** · [🇩🇪 Deutsche Version](README.de.md)

> [!WARNING]
> - This integration was written by **Claude (AI assistant by Anthropic)** together with [Patrick (paberke)](https://github.com/paberke). It is a private hobby project, **not** an official Greenworks product.
> - It can only **read** the mower, **not control** it – no start, pause or return to station.
> - You will often be **logged out of the Greenworks app** if Home Assistant uses the same account ([details](#you-will-often-be-logged-out-of-the-greenworks-app)).
> - **No warranty, no support.** Use at your own risk and make a backup first.

The integration reads your Greenworks robotic mower via the Greenworks cloud and shows the values in Home Assistant: status, battery, next start, errors in plain text, blade runtime, mowing schedule and more. Starting, parking and changing settings still only work in the Greenworks app.

## Tested mowers

| Mower | Tested by |
|---|---|
| Greenworks **Optimow 10** | the developer, daily use |
| Cramer **RM1000** and **RM1500** (with the Greenworks app) | reported by users |

Other Greenworks/Cramer robotic mowers that use the Greenworks app will probably work too. **Cramer fleet accounts** (`fleet.cramertools.com`) are a separate service and are **not** supported. If you try another model, please [tell us](https://github.com/paberke/GreenWorks-HA/issues/new/choose).

## Installation

**Requirement:** Home Assistant **2025.1 or newer**. Automatically tested with 2025.2 and 2026.2.

**Home Assistant 2026.11 and newer (Marketplace)** – from 2026.11 HACS is built into Home Assistant as **Marketplace**:

1. Settings → **Marketplace** → menu (⋮) → **Custom repositories** (you will be asked to link GitHub once)
2. URL `https://github.com/paberke/GreenWorks-HA`, type **Integration**, add
3. Download **Greenworks** and restart Home Assistant

**Older versions (HACS)**

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=paberke&repository=GreenWorks-HA&category=integration)

1. HACS → menu (⋮) → **Custom repositories**
2. URL `https://github.com/paberke/GreenWorks-HA`, type **Integration**, add
3. Download **Greenworks** and restart Home Assistant

**Set up**

1. Settings → Devices & services → **Add integration** → *Greenworks*
2. Enter the email and password of the Greenworks app
3. Choose what you want to see in addition to the standard entities (see below). You can change this at any time under **Configure**.

## What you get

The **standard entities** are always created. Everything else is grouped and can be switched on and off – when installing or later under **Configure**. Switched-off entities are only *disabled*, not deleted, so their entity IDs stay the same when you switch them on again.

| Standard | What it shows |
|---|---|
| **Mower** | *Docked*, *Mowing*, *Returning* or *Error*; *unavailable* while the mower is offline |
| **Status** | Detailed state with the app's wording, e.g. *Parked by schedule*, *Charging*, *Searching station*, *Fatal error*, *Offline* or *Winter pause* |
| **Battery** | Battery level in % |
| **Charging** | On while the mower is charging |
| **Next start** / **Mowing end** | When the mower starts next / when the current mowing window ends |
| **Online** | Whether the mower is connected to the cloud |
| **Problem** | *Problem* or *OK*. The attribute *Reason* says why, e.g. *Too high inclination (error 13)*, *Offline* or *Winter pause* |
| **Error** (event) | Fires once for every new error, with code, text and time – ideal for notifications ([blueprint](#notification-on-errors)) |
| **Winter pause** (switch) | See [Winter pause](#winter-pause) |
| **Blade time** | Mowing hours since the blade time was last reset in the app (same as the app) |
| **Blade change due** | *Due* when the blade time reaches the limit (default 150 h) |

<details>
<summary><b>Optional groups</b> (click to open)</summary>

| Group | Entities |
|---|---|
| **Detailed errors** | Last error code, Last error (time), Last error message (plain text, with the app's error history as attribute), Fatal errors |
| **Statistics** | Total cutting time, Total running time, Total charging time, Statistics as of, Last status report |
| **Settings from the app** | Mowing schedule (e.g. *Mon–Fri 09:00–12:30*), Drive past wire distance, Follow wire distance, Starting points, Rain protection, Frost protection – display only |
| **Diagnostics** | Software (with cutting unit and charging station), Signal quality, Mower software update |
| **Calendar** | The mowing schedule as calendar events ("Mowing") |
| **Position** | The mower on the map (GPS) |

Existing installations from before 0.3.0 keep all their entities; only the calendar is new and switched off.

</details>

<details>
<summary><b>Extra details (attributes)</b></summary>

Tap an entity → **⋮** → **Details** → **Attributes**. In automations and templates use `state_attr()`.

| Entity | Attributes |
|---|---|
| **Status** | *Last state* – only while the mower is offline: the state before it went offline |
| **Problem** | *Reason* |
| **Error** (event) | *Error code*, *Text*, *Time* |
| **Last error code** | *Meaning* – the error as plain text |
| **Last error message** | *Text*, *History* (the app's error list with dates), *History updated* |
| **Mowing schedule** | *Monday* to *Sunday* with the mowing times, *Updated* |
| **Software** | *Cutting unit*, *Charging station*, *Reported by the mower* (when the mower last sent its software version itself) |
| **Follow wire distance** | *Guide wire 1*, *Guide wire 2*, *Updated* |
| **Starting points** | *Point 1* to *Point 5* (wire, distance, share of starts), *Charging station*, *Updated* |
| **Blade change due** | *Limit (h)*, *Remaining (h)* |
| **Total cutting time**, **Blade time** | *Counted since last statistics*, *Last real statistics* (see [limitations](#limitations)) |
| **Mower** | *status*, *status_code*, *park_reason_code*, *sub_status_code* – raw values for automations |

*Updated* shows when the app last read the value from the mower.

</details>

### Error codes

All 69 error codes with their meaning and a short tip what to do: **[ERRORS.md](ERRORS.md)**.

## Settings (Configure)

Settings → Devices & services → Greenworks → **Configure**:

| Setting | Default | Meaning |
|---|---|---|
| Additional entities | – | Which optional groups are shown |
| Update interval | 60 s | How often the cloud is asked (30–600 s) |
| Keep last values during drops | 5 min | Short cloud outages are bridged (1–60 min) |
| Blade change after | 150 h | Limit for *Blade change due* (0 = off). Greenworks gives no fixed interval; a common recommendation is every 6–10 weeks of mowing |
| Repair notice when offline for | 1 h | See [Notices under Repairs](#notices-under-repairs) (0 = off) |

## Winter pause

In winter the mower is switched off and therefore offline. Without the winter pause you would get offline notices for months and **Problem** would always show *Problem*.

Switch on **Winter pause** (a switch on the mower's device page):

- no offline notice under *Repairs*
- **Problem** shows *OK*, reason *Winter pause*
- **Status** shows *Winter pause* instead of *Offline*

The switch only changes what Home Assistant shows – **nothing is changed on the mower**. Tip: an automation can switch it on and off by date, e.g. on 1 November and 15 March.

## Notices under Repairs

Under Settings → System → **Repairs** a notice appears when

- the mower has been **offline** for longer than the set time (default 1 hour, not during the winter pause), or
- the **Greenworks cloud** has not been reachable for that long.

Both notices disappear by themselves as soon as everything works again. If the password is no longer accepted, Home Assistant asks for it again as usual (*Re-authenticate*).

## Notification on errors

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fpaberke%2FGreenWorks-HA%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fgreenworks%2Ferror_notification.yaml)

The blueprint sends a push notification to your phone (Home Assistant app) for every new error of the mower, e.g. *"Too high inclination (13)"*. Import it with the button, then create an automation from it: choose the **Error** event of your mower and your phone.

## Mower software update

*Experimental.* In the **Diagnostics** group, the integration asks the Greenworks update server once a day – the same question the app asks on its *Software* page. If there is new software, Settings shows *Mower software: update available*. **Install it with the Greenworks app**; Home Assistant has no install button. If the update server does not answer, there is simply no update entity.

<details>
<summary><b>Example dashboard card</b></summary>

Replace `rasenrobo` with the name of your mower (the entity IDs follow the name of the device and your language).

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
        entity: sensor.rasenrobo_battery
      - type: tile
        entity: binary_sensor.rasenrobo_problem
      - type: tile
        entity: sensor.rasenrobo_next_start
```

</details>

## Limitations

- **No control:** read-only. Starting, parking or changing settings is not possible from Home Assistant and not planned.
- **Statistics only update when the app asks for them:** the mower sends cutting, running and charging time only when the statistics are opened in the app. To keep **Total cutting time** and **Blade time** current anyway, the integration counts the minutes in which the mower is *mowing* and adds them to the last real value (attribute *Counted since last statistics*). When new real statistics arrive, they take over again.
- **Schedule, error history and settings are only as current as the app:** the cloud updates them when you open the respective page in the app (attribute *Updated*).
- **Software version may differ from the app:** the **Software** sensor shows the version the mower reports itself regularly. The app's *Software* page sometimes shows an **old, stored value** (on our Optimow 10 version 6.53 from 2022, although it has long been running 6.65). The attribute *Reported by the mower* shows when the mower last sent it.
- **Last error message may differ from the app's error list:** Home Assistant shows the most recently reported event, which is sometimes a short warning the app does not list.

## You will often be logged out of the Greenworks app

A Greenworks account can apparently only be logged in at **one** place at a time. When you log in to the app, Home Assistant's login becomes invalid; Home Assistant silently logs back in within a minute – and that logs the app out. Home Assistant itself keeps working.

If that bothers you, disable the integration while you use the app (*Settings → Devices & services → Greenworks → ⋮ → Disable*) and enable it again afterwards. Greenworks support suggested using a **second account** for Home Assistant and sharing the mower with it; we have not tested this yet.

## Removal

1. Settings → Devices & services → Greenworks → **⋮** → **Delete**
2. In HACS / Marketplace: Greenworks → **⋮** → **Remove**, then restart Home Assistant

## Versions

What changed in each version: [Releases](https://github.com/paberke/GreenWorks-HA/releases).

## Contributors

- **[Patrick (paberke)](https://github.com/paberke)** – idea, testing with a real Optimow 10, feature decisions, contact with Greenworks, project maintenance
- **Claude (AI assistant by Anthropic)** – programming, automated tests, documentation

## Credits

Started as a fork of [Boes24/GreenWorks-HA](https://github.com/Boes24/GreenWorks-HA). The code has since been completely rewritten; the Greenworks cloud address and login flow originally come from [Boes24/GreenWorks-Core](https://github.com/Boes24/GreenWorks-Core). Thanks to Boes24 for the starting point.
