# SVOTC – Stable Core Edition (2026-02)
**Smart Virtual Outdoor Temperature Control**

SVOTC controls your heat pump **indirectly** by creating a *virtual outdoor temperature* that your heat pump can use for its heating curves.

Instead of toggling the pump on/off or aggressively changing setpoints, SVOTC adjusts an **offset (°C)** that is added to the real outdoor temperature:

- **Positive offset** (+2°C) → “warmer outside” → the heat pump reduces heating (**price brake**)
- **Negative offset** (−1°C) → “colder outside” → the heat pump increases heating (**comfort guard**)

**Design goals**
- 🎯 Stable (no flappy price-spike control)
- 📊 Explainable (reason codes show *why* decisions are made)
- 🏗️ Layered architecture: sensing → stabilization → planning → ramp-limited execution

---

## 📋 Table of contents
1. [Requirements](#1-requirements)
   - [Price sensor compatibility (HACS vs Official Nordpool)](#price-sensor-compatibility-hacs-vs-official-nordpool)
2. [Installation](#2-installation)
3. [First run (5-minute setup)](#3-first-run-5-minute-setup)
4. [Entity mapping](#4-entity-mapping-most-important)
5. [Lovelace dashboards](#5-lovelace-dashboards)
   - [5.1 Requirements (HACS / custom cards)](#51-requirements-hacs--custom-cards)
   - [5.2 Import guide: how to add YAML dashboards](#52-import-guide-how-to-add-yaml-dashboards)
   - [5.3 Minimal dashboard (no custom cards)](#53-minimal-dashboard-no-custom-cards)
   - [5.4 Ready-made dashboards (copy/paste)](#54-ready-made-dashboards-copypaste)
6. [Troubleshooting](#6-troubleshooting)
7. [How it works](#7-how-it-works)
8. [Recommended starting values (defaults)](#8-recommended-starting-values-defaults)
9. [Reason codes](#9-reason-codes-what-do-they-mean)
10. [FAQ](#10-faq)
11. [Advanced: Brake phase timing](#11-advanced-brake-phase-timing)
12. [License / Disclaimer](#12-license--disclaimer)

---

## 1) Requirements
You need:
- ✅ Home Assistant (modern version recommended)
- ✅ Indoor temperature sensor (e.g. `sensor.inomhusmedel`)
- ✅ Outdoor temperature sensor (e.g. `sensor.temperatur_nu`)
- ✅ Electricity price sensor (Nordpool/Tibber) that provides:
  - `current_price`
  - `raw_today` (list of `{start, end, value}`)
  - `raw_tomorrow` (list of `{start, end, value}`)

> SVOTC reads the price sensor via **entity mapping** (`input_text`). No price sensor is hard-coded in this Stable Core version.

### Price sensor compatibility (HACS vs Official Nordpool)

SVOTC requires a price entity that exposes **SVOTC-compatible** attributes:
- `current_price`
- `raw_today` (list of `{start, end, value}`)
- `raw_tomorrow` (list of `{start, end, value}`)

> Note: `raw_tomorrow` may be empty until Nordpool publishes tomorrow’s prices (~13:00–14:00).

There are two common setups:

#### Option A — HACS Nordpool (simplest)
If you use the **HACS Nordpool integration**, SVOTC can usually use it directly.

✅ You only need the SVOTC package.  
➡️ Set `input_text.svotc_entity_price` to your HACS Nordpool price sensor  
(example: `sensor.nordpool_tibber`).

#### Option B — Official Nordpool integration (requires an adapter package)
If you use the **official Nordpool integration**, the attributes/structure do not match what SVOTC expects.

✅ In this case you typically use **two packages**:
1) `svotc.yaml` (SVOTC core)
2) `nordpool_svotc_adapter.yaml` (official Nordpool → SVOTC bridge)

➡️ Follow the adapter guide in `nordpool-official/README.md` (or wherever you placed the adapter docs), then set:

- `input_text.svotc_entity_price` = `sensor.nordpool_offical` *(the adapter sensor)*

> In short: **HACS Nordpool = SVOTC only**  
> **Official Nordpool = SVOTC + adapter package**

---

## 2) Installation

### Step 1: Add the YAML file
Place the file in your packages folder, for example:
```bash
/config/packages/svotc.yaml
````

### Step 2: Enable packages (if not already enabled)

In `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### Step 3: Restart Home Assistant

Settings → System → Restart

### Step 4: Verify it loaded

Settings → Devices & Services → **Helpers**
Search for **SVOTC**

You should see helpers (`input_*`) and sensors (`sensor.svotc_*`).

---

## 3) First run (5-minute setup)

⏱️ **Quick start**

1. Install using [Installation](#2-installation)
2. Restart Home Assistant
3. Go to **Helpers** and search for “SVOTC”
4. Fill in Entity mapping (next section):

   * Indoor → your indoor temp sensor
   * Outdoor → your outdoor temp sensor
   * Price → your price sensor
5. Set **Mode = Smart**
6. Wait 2 minutes
7. Check:

   * ✅ `binary_sensor.svotc_inputs_healthy` = **on**
   * ✅ `input_text.svotc_reason_code` does **not** show `MISSING_INPUTS_FREEZE`
   * ✅ `sensor.svotc_virtual_outdoor_temperature` looks reasonable

If something is off: see [Troubleshooting](#6-troubleshooting).

---

## 4) Entity mapping (most important)

These helpers tell SVOTC which of *your* entities to use. You **must** set them.

| Helper                                         | What                | Example                  |
| ---------------------------------------------- | ------------------- | ------------------------ |
| `input_text.svotc_entity_indoor`               | Indoor temp sensor  | `sensor.inomhusmedel`    |
| `input_text.svotc_entity_outdoor`              | Outdoor temp sensor | `sensor.temperatur_nu`   |
| `input_text.svotc_entity_price`                | Price sensor        | `sensor.nordpool_tibber` |
| `input_text.svotc_notify_service` *(optional)* | Notify service      | `notify.mobile_app_...`  |

### How to change (recommended)

1. Settings → Devices & Services → **Helpers**
2. Search: `svotc_entity`
3. Open each helper and enter your `entity_id`
4. Save

✅ Tip: Because mapping is stored in helpers, it survives YAML updates.

---

## 5) Lovelace dashboards

### 5.1 Requirements (HACS / custom cards)

Your “SVOTC Control” dashboard uses:

* `custom:mini-graph-card`

👉 Install **mini-graph-card** via HACS or those cards will break.

**Short install guide**

1. HACS → Frontend
2. Search “mini graph card”
3. Install
4. Restart Home Assistant (or reload frontend)
5. Confirm `type: custom:mini-graph-card` no longer shows errors

---

### 5.2 Import guide: how to add YAML dashboards

Two common approaches—pick the one that matches your Lovelace setup.

#### A) Storage mode dashboard (most common)

You normally build dashboards in the UI, but can paste YAML into a view.

1. Settings → Dashboards
2. Create a new dashboard (or open an existing one)
3. Create a new **View** tab, e.g. “SVOTC”
4. Top right: **⋮ → Edit dashboard**
5. Choose **Raw configuration editor**
6. Paste YAML (see [5.4](#54-ready-made-dashboards-copypaste))
7. Save

> Tip: If you already have a dashboard and only want a new SVOTC tab, paste only the **view** part (a block starting with `title:` / `type:` / `sections:`).

#### B) YAML mode (if you run `lovelace: yaml`)

If you keep dashboards as YAML files in your repo and want HA to load them.

Example structure:

```
lovelace/
  svotc_control.yaml
  svotc_debug.yaml
```

Concept:

* Create a new dashboard and point it to the YAML file
* Or merge these as “views” depending on your setup

> Exact steps depend on your current Lovelace configuration. The manual still works without this detail.

---

### 5.3 Minimal dashboard (no custom cards)

For a “must-work” view without mini-graph-card:

```yaml
title: SVOTC Minimal
type: sections
sections:
  - type: grid
    cards:
      - type: entities
        title: SVOTC – Setup & Control
        show_header_toggle: false
        state_color: true
        entities:
          - type: section
            label: Setup (one-time)
          - entity: input_text.svotc_entity_indoor
            name: "📍 Indoor temp entity"
          - entity: input_text.svotc_entity_outdoor
            name: "🌡️ Outdoor temp entity"
          - entity: input_text.svotc_entity_price
            name: "💰 Price entity"
          - entity: input_text.svotc_notify_service
            name: "🔔 Notify service (optional)"

          - type: divider
          - type: section
            label: Mode & target
          - entity: input_select.svotc_mode
            name: "Mode"
          - entity: input_number.svotc_comfort_temperature
            name: "Target temperature"

          - type: divider
          - type: section
            label: Status
          - entity: binary_sensor.svotc_inputs_healthy
            name: "✅ Temp inputs healthy?"
          - entity: binary_sensor.svotc_price_available
            name: "💰 Price available?"
          - entity: input_text.svotc_reason_code
            name: "🧠 Reason code"
          - entity: input_number.svotc_applied_offset_c
            name: "↕️ Applied offset (°C)"
          - entity: sensor.svotc_virtual_outdoor_temperature
            name: "🎯 Virtual outdoor temp (to heat pump)"
```

---

## 6) Troubleshooting

### 🔴 Nothing happens

Check in this order:

1. `input_select.svotc_mode` = **Smart**
2. `binary_sensor.svotc_inputs_healthy` = **on**
3. Entity mapping:

   * `input_text.svotc_entity_indoor`
   * `input_text.svotc_entity_outdoor`
   * `input_text.svotc_entity_price`
4. Read `input_text.svotc_reason_code`:

   * `OFF` → Mode = Off
   * `PASS_THROUGH` → Mode = PassThrough
   * `MISSING_INPUTS_FREEZE` → temp input missing/broken

### 🔴 Price looks “dead”

1. `binary_sensor.svotc_price_available` = **on**?
2. `sensor.svotc_current_price` shows a reasonable value?
3. Verify the price sensor attributes:

   * Developer Tools → States → your price sensor
   * must have `current_price`, `raw_today`, `raw_tomorrow`

> Official Nordpool users: SVOTC must point to the **adapter sensor** (`sensor.nordpool_offical`), not the original Nordpool entity.

4. If `sensor.svotc_p30` and `sensor.svotc_p80` are `none`:

   * SVOTC requires at least **20** prices from `raw_today + raw_tomorrow`
   * Common when tomorrow’s prices are not available yet
   * Fix: wait, or use **ComfortOnly** temporarily

---

## 7) How it works

### 🏗️ Layered architecture

SVOTC follows a **layered control** design:

```

1. SENSING (validated inputs)

   * sensor.svotc_src_indoor
   * sensor.svotc_src_outdoor
   * sensor.svotc_src_current_price

2. RAW PRICE STATE (instant, no memory)

   * sensor.svotc_raw_price_state

3. DWELL (raw → stable, anti-spikes)

   * automation: SVOTC Price dwell
   * output: input_text.svotc_last_price_state

4. FORWARD LOOK (prebrake_strength 0..1)

   * sensor.svotc_prebrake_strength

5. BRAKE PHASE (memory; avoids “restarting” each minute)

   * input_text.svotc_brake_phase
   * automation: SVOTC Brake phase controller

6. ENGINE (requested → ramp-limited applied)

   * automation: SVOTC Engine
   * outputs:

     * input_number.svotc_requested_offset_c
     * input_number.svotc_applied_offset_c
   * final output:

     * sensor.svotc_virtual_outdoor_temperature

```

### 🧮 Offset calculation (Engine)

The engine calculates a **requested offset**, then applies **rate limiting** to produce the final **applied offset**.

**Comfort term (negative = more heat)**  
When comfort guard is active:

- `comfort_term = -(heat_aggressiveness * 0.4)`
- Example: `heat_aggressiveness = 5` → `comfort_term = −2.0°C`

**Price term (positive = less heat)**  
In **Smart** mode, when comfort guard is **not** active:

- `price_term = brake_hold_offset * prebrake_strength`
- Example: `hold_offset = 2.0` and `strength = 1.0` → `price_term = +2.0°C`

**Requested offset**

- `requested = comfort_term + price_term`

**Applied offset (ramp-limited)**

- The change per step is limited by `svotc_max_delta_per_step_c`

**Virtual outdoor temperature**

- `virtual_outdoor = real_outdoor + applied`

---

## 8) Recommended starting values (defaults)

### 8.1 Mode
- `svotc_mode` = **Smart**

### 8.2 Comfort guard

| Parameter                                | Value | Meaning             |
| ---------------------------------------- | ----: | ------------------- |
| `svotc_comfort_temperature`              |  21.0 | Indoor target       |
| `svotc_comfort_guard_activate_below_c`   |   0.8 | Guard ON at 20.2°C  |
| `svotc_comfort_guard_deactivate_above_c` |   0.4 | Guard OFF at 20.6°C |
| `svotc_heat_aggressiveness`              |     2 | Boost ≈ −0.8°C      |

### 8.3 Price braking

| Parameter                    | Value | Meaning                |
| ---------------------------- | ----: | ---------------------- |
| `svotc_brake_aggressiveness` |     2 | Prebrake window 60 min |
| `svotc_brake_hold_offset_c`  |   2.0 | Max brake +2.0°C       |

Aggressiveness → window:

| Level | Window (min) |
| ----: | -----------: |
|     0 |            0 |
|     1 |           30 |
|     2 |           60 |
|     3 |           90 |
|     4 |          105 |
|     5 |          120 |

### 8.4 Dwell (stability)

Example:

| Transition      | Minutes |
| --------------- | ------: |
| neutral → brake |      30 |
| brake → neutral |      15 |
| neutral → cheap |      20 |
| cheap → neutral |      15 |

### 8.5 Brake phase durations

| Phase    | Minutes |
| -------- | ------: |
| rampup   |      30 |
| hold     |      60 |
| rampdown |      45 |

### 8.6 Rate limiting
- `svotc_max_delta_per_step_c` = **0.10 °C/min** (smooth)

---

## 9) Reason codes (what do they mean?)

| Code                    | Meaning                                     |
| ----------------------- | ------------------------------------------- |
| `INIT`                  | Initial state                               |
| `OFF`                   | Mode = Off                                  |
| `PASS_THROUGH`          | Mode = PassThrough                          |
| `COMFORT_ONLY`          | Comfort guard only                          |
| `MISSING_INPUTS_FREEZE` | Missing temp inputs → applied offset frozen |
| `COMFORT_GUARD`         | Comfort guard active (negative offset)      |
| `MCP_BLOCKS_BRAKE`      | Comfort overrides price brake               |
| `PRICE_BRAKE`           | Price brake active (positive offset)        |
| `NEUTRAL`               | Normal mode                                 |

---

## 10) FAQ

### Does SVOTC control the heat pump directly?
No. SVOTC produces `sensor.svotc_virtual_outdoor_temperature`, which you map into your heat pump integration/setup.

### Requested vs Applied offset?

| Type      | Description                                  |
| --------- | -------------------------------------------- |
| Requested | What the logic *wants*                       |
| Applied   | What is actually applied after ramp limiting |

---

## 11) Advanced: Brake phase timing

### 📊 Visual timeline

```

Time:     0 ─── 30 ───────── 90 ───── 135 ──→
Phase:  idle | ramping_up | holding | ramping_down | idle
Offset:  0 →→→→→ hold_offset →→ hold_offset →→→→→ 0

```

Parameters:
- rampup   = 30 min (0 → hold_offset)
- hold     = 60 min
- rampdown = 45 min (hold_offset → 0)

⚠️ This only runs while the stable price state remains `brake`.  
If price leaves `brake`, the phase is forced back to `idle`.

---

## 12) License / Disclaimer

⚠️ Use at your own risk.  
SVOTC influences heating indirectly through a virtual outdoor temperature. Test and verify behavior in your environment before relying on it.

### Safe-start recommendation

1. Start gentle:
   - `brake_hold_offset_c` = 1.0°C
   - `max_delta_per_step_c` = 0.10°C/min
   - Comfort guard: activate 0.8 / deactivate 0.4

2. Monitor the first week:
   - `sensor.svotc_virtual_outdoor_temperature`
   - `input_number.svotc_applied_offset_c`
   - `sensor.svotc_src_indoor`
   - `input_text.svotc_reason_code`

3. Increase aggressiveness step-by-step:
   - Week 2: hold_offset 2.0
   - Week 3: brake_aggressiveness 3
   - Later: fine-tune guard/ramp

---

## Credits

SVOTC – Stable Core Edition (2026-02)

Designed for:
- 🏠 Swedish houses with heat pumps
- ⚡ Nordpool/Tibber spot price control
- 🎚️ Smooth, predictable, explainable control
```
