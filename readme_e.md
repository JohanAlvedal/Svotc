[🇸🇪 Svenska](readme_sv.md) | [🇬🇧 English](readme_e.md)

---

# 💥 Breaking Changes – SVOTC 3.0.0

> ⚠️ **USE AT YOUR OWN RISK**
>
> SVOTC 3.0.0 is under active beta testing. Features may change without prior notice, bugs may occur, and configuration details may change in future releases. Do not use in production unless you fully understand the risks. **You are responsible for any consequences affecting your heating system.**

---

## SVOTC 3.0.0 introduces breaking changes from 2.x.x

The biggest change in SVOTC 3.0.0 is that the system has been **simplified into a new Core v1 architecture**.

This is **not a drop-in upgrade from 2.x.x**.

Several previous subsystems have been removed or merged into a smaller and more transparent core. The old 2.x structure and logic should not be reused without review.

---

## What has changed?

### Previous structure (2.x.x)

```text
/config/packages/svotc/
├── 00_helpers.yaml
├── 10_sensors.yaml
├── 20_price_fsm.yaml
├── 22_engine.yaml
├── 30_learning.yaml
└── 40_notify.yaml
```

### New structure (3.0.0 / Core v1)

```text
/config/packages/svotc/
├── 00_helpers.yaml  ← User controls and internal helper states
├── 10_sensors.yaml  ← Temperatures, price thresholds, price states, health
├── 20_engine.yaml   ← Main control loop, requested/applied offset, reason code
└── 30_notify.yaml   ← Optional FAIL_SAFE notification
```

> ✅ The first three files are required. `30_notify.yaml` is optional but recommended.

---

## What do you need to do?

### 1. Remove old 2.x package files

Remove or archive old files such as:

```text
20_price_fsm.yaml
22_engine.yaml
30_learning.yaml
40_notify.yaml
```

If you previously used a single-file setup, also remove:

```text
/config/packages/svotc.yaml
```

---

### Clean up old entities (recommended)

If you previously ran SVOTC 2.x.x, some template sensors may still exist in Home Assistant’s entity registry.

If left behind, Home Assistant may create duplicate entities like:

`sensor.svotc_virtual_outdoor_temperature_2`
`sensor.svotc_forward_price_state_2`

To avoid this, remove old entities before starting SVOTC 3.0.0.

**Steps:**

1. Go to **Settings → Devices & Services → Entities**
2. Search for `svotc`
3. Remove entities belonging to the old 2.x setup
4. Restart Home Assistant
5. Start SVOTC 3.0.0

This ensures correct naming for new sensors.

---

### 2. Create the folder

```text
/config/packages/svotc/
```

---

### 3. Copy the new Core v1 files

```text
00_helpers.yaml
10_sensors.yaml
20_engine.yaml
30_notify.yaml
```

---

### 4. Check `configuration.yaml`

```yaml
homeassistant:
  packages: !include_dir_named packages
```

---

### 5. Restart Home Assistant

---

### 6. Configure source entities

Set these helpers after restart:

* `input_text.svotc_source_indoor_temp`
* `input_text.svotc_source_outdoor_temp`
* `input_text.svotc_source_price`

**Example:**

```text
sensor.indoor_temperature
sensor.outdoor_temperature
sensor.nordpool_kwh_se3
```

---

### 7. Verify system operation

Check:

* `binary_sensor.svotc_inputs_healthy` → **ON**
* `sensor.svotc_forward_price_state` → `neutral`, `cheap`, `prebrake`, `hold (bridge between brake blocks)`, or `brake`
* `input_text.svotc_reason_code` → e.g. `NEUTRAL`
* `sensor.svotc_virtual_outdoor_temperature` → reasonable value

---

## Major architectural changes in 3.0.0

### 1. Single-engine design

SVOTC 3.0.0 replaces the previous layered control system with a **single core engine**.

The core includes a lightweight PI controller for temperature regulation used in:

* Comfort mode
* Comfort guard
* Overtemperature protection

A central decision loop replaces:

* Price FSM
* Brake phases
* Learning logic

This makes the system:

* Easier to understand
* Easier to debug
* Easier to maintain
* More predictable

---

### 2. Simplified file structure

Only four core files are used, reducing complexity and improving upgrade clarity.

---

### 3. Clear separation of requested vs applied offset

* **Requested offset** — what the logic wants
* **Applied offset** — what is actually sent after rate limiting

This prevents abrupt changes and protects hardware.

---

### 4. Transparent price logic

Forward price state:

* `cheap`
* `neutral`
* `prebrake`
* `hold` (bridge between brake blocks)
* `brake`

---

### 5. Built-in protection mechanisms

The engine handles:

* Comfort guard
* Overtemperature brake
* Fail-safe

All evaluated in strict priority order.

---

### Temperature control with PI regulation

SVOTC uses a simple **PI controller (Proportional + Integral)**.

Used in:

* Comfort mode
* Comfort guard
* Overtemperature braking

The controller:

* Reacts instantly (P term)
* Corrects over time (I term)
* Uses a deadband for stability

Derivative (D) is not used since buildings are inherently slow systems.

PI works together with ramp limiting to ensure smooth behavior.

---

### 6. Simplified notification model

A notification can be triggered if the system remains in `FAIL_SAFE` for more than 5 minutes.

---

## Other important changes

* `20_price_fsm.yaml` removed
* `22_engine.yaml` replaced
* `30_learning.yaml` removed
* `40_notify.yaml` replaced

Operating modes:

* `Off`
* `Smart`
* `Comfort`
* `PassThrough`

---

## Why this change?

Core v1 is designed to be:

* **Cleaner**
* **Safer**
* **More hardware-friendly**
* **Easier to debug**
* **Easier to maintain**

The goal is stability — not added complexity.

---

### Designed for simplicity

SVOTC 3.0.0 intentionally avoids exposing too many advanced parameters.

In most cases, you only need to configure:

* Indoor temperature
* Outdoor temperature
* Electricity price
* Comfort target

The system handles:

* Price response
* Brake behavior
* Comfort protection
* Overtemperature protection

👉 **Works out of the box**

---

## Recommended migration approach

1. Remove old files
2. Install Core v1
3. Set mode to `PassThrough`
4. Verify inputs
5. Check sensors
6. Switch to `Smart`

---

## Beta reminder

SVOTC controls your heat pump indirectly.

Misconfiguration may affect:

* Comfort
* Operation
* Efficiency

Recommendations:

* Test in `PassThrough`
* Monitor `reason_code`
* Keep a fallback ready

---

**Version:** SVOTC 3.0.0 Beta
**Core:** Core v1
**License:** MIT
