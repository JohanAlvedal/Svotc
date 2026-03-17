[🇸🇪 Svenska](readme_sv.md) | [🇬🇧 English](readme.md)

---

# 💥 Breaking Changes – SVOTC 3.0.0

> ⚠️ **BETA SOFTWARE — USE AT YOUR OWN RISK**
>
> SVOTC 3.0.0 is in active beta testing. Features may change without notice, bugs may occur, and configuration details may change in future releases. Do not use in production unless you fully understand the risks. **You are responsible for any consequences affecting your heating system.**

---

## SVOTC 3.0.0 introduces breaking changes from 2.x.x

The biggest change in SVOTC 3.0.0 is that the system has been **simplified into a new Core v1 architecture**.

This is **not a drop-in upgrade from 2.x.x**.

Several earlier subsystems have been removed or merged into a smaller and more transparent core. The old 2.x structure and logic should not be reused without review.

---

## What changed?

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
├── 00_helpers.yaml   ← User controls and internal helper state
├── 10_sensors.yaml   ← Temperatures, price thresholds, price state, health
├── 20_engine.yaml    ← Main control loop, requested/applied offset, reason code
└── 30_notify.yaml    ← Optional FAIL_SAFE notification
```

> ✅ All four files are required. They depend on each other.

---

## What do you need to do?

### 1. Remove old 2.x package files

Remove or archive older files such as:

```text
20_price_fsm.yaml
22_engine.yaml
30_learning.yaml
40_notify.yaml
```

If you are migrating from an older single-file version, also remove or archive:

```text
/config/packages/svotc.yaml
```
### Clean up old entities (recommended)

If you previously ran SVOTC 2.x.x, some template sensors may still exist in the Home Assistant entity registry.

If these entities remain, Home Assistant may create new sensors with names such as:

sensor.svotc_virtual_outdoor_temperature_2  
sensor.svotc_forward_price_state_2  

To avoid this, remove the old entities before starting SVOTC 3.0.0.

Steps:

1. Go to **Settings → Devices & Services → Entities**
2. Search for `svotc`
3. Remove entities that belong to the old 2.x installation
4. Restart Home Assistant
5. Start SVOTC 3.0.0

This ensures the new sensors keep their correct names.
### 2. Create the folder

```text
/config/packages/svotc/
```

### 3. Copy in the new Core v1 files

Copy these files into the folder:

```text
00_helpers.yaml
10_sensors.yaml
20_engine.yaml
30_notify.yaml
```

### 4. Check `configuration.yaml`

If you do not already use Home Assistant packages, add:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### 5. Restart Home Assistant

### 6. Reconfigure your source entities

After restart, set these helpers to match your system:

* `input_text.svotc_source_indoor_temp`
* `input_text.svotc_source_outdoor_temp`
* `input_text.svotc_source_price`

Example:

```text
sensor.indoor_temperature
sensor.outdoor_temperature
sensor.nordpool_kwh_se3
```

### 7. Verify that the new core is working

After restart, check:

* `binary_sensor.svotc_inputs_healthy` → should be **ON**
* `sensor.svotc_forward_price_state` → should show `neutral`, `cheap`, `prebrake`, `hold`, or `brake`
* `input_text.svotc_reason_code` → should show `NEUTRAL` or another active reason
* `sensor.svotc_virtual_outdoor_temperature` → should resolve correctly

---

## Major architectural changes in 3.0.0

### 1. Single-engine design

SVOTC 3.0.0 replaces the older multi-layer control structure with a **single main engine**.
The core also includes a lightweight PI-based temperature regulator used for Comfort mode and temperature protection.

Instead of relying on separate subsystems for:

* price FSM
* brake phases
* learning logic

the new core runs one central decision loop every minute.

This makes the system:

* easier to understand
* easier to debug
* easier to maintain
* more predictable in day-to-day operation

---

### 2. Simpler file layout

SVOTC now uses only four core files.

This reduces complexity and makes upgrades easier.

---

### 3. Clear separation between requested and applied offset

SVOTC 3.0.0 clearly separates:

* **requested offset** — what the logic wants to do
* **applied offset** — what is actually sent after rate limiting

This reduces abrupt behavior and makes the system gentler on heat pump hardware.

---

### 4. Simpler and more transparent price logic

Price logic is now easier to inspect and reason about.

The forward price state is expressed directly as:

* `cheap`
* `neutral`
* `prebrake`
* `hold`
* `brake`

This replaces more complicated older flow structures.

---

### 5. Comfort and overtemperature protection are built directly into the core

The engine now handles:

* Comfort protection when indoor temperature is too low
* Overtemperature braking when indoor temperature is too high
* Fail-safe behavior when inputs are missing

These protections are evaluated in a strict priority order.

---

### Temperature control using PI regulation

SVOTC 3.0.0 introduces a lightweight **PI regulator (Proportional + Integral)** for temperature control.

This regulator is used in:

* **Comfort mode**
* **Comfort guard** during Smart mode
* **Overtemperature braking**

The regulator calculates an offset based on the difference between the current indoor temperature and the configured comfort target.

The proportional term reacts immediately to the temperature error, while the integral term gradually compensates for persistent deviations over time.

A small deadband around the target temperature prevents constant adjustments caused by tiny sensor fluctuations.

The PI controller works together with SVOTC’s ramp limiting between **requested offset** and **applied offset**, ensuring that changes happen gradually and remain gentle on the heat pump's behavior.

A derivative term (D) is intentionally not used. Buildings already behave as slow thermal systems and PI control provides stable regulation without unnecessary complexity.

These protections are evaluated in a strict priority order.

---

### 6. Simpler notification model

The new core includes an optional notification if the system remains in `FAIL_SAFE` for at least 5 minutes.

This is intentionally simpler than earlier notify/diagnostic layers.

---

## Other important changes in 3.0.0

* `20_price_fsm.yaml` is no longer used
* `22_engine.yaml` has been replaced by `20_engine.yaml`
* `30_learning.yaml` is no longer part of the core
* `40_notify.yaml` has been replaced by a smaller `30_notify.yaml`
* operating modes are now focused on:

  * `Off`
  * `Smart`
  * `Comfort`
  * `PassThrough`

---

## Why this change?

The new Core v1 structure is designed to make SVOTC:

* **cleaner** — fewer moving parts
* **safer** — less aggressive offset behavior
* **more hardware-friendly** — smoother output changes
* **easier to troubleshoot** — clearer logic and fewer internal layers
* **easier to maintain** — simpler architecture for future releases

The goal of 3.0.0 is not to add more complexity.

The goal is to make the core behavior more stable, readable, and reliable.

---
### Designed for simplicity

SVOTC 3.0.0 intentionally avoids large numbers of advanced tuning parameters.

Earlier versions exposed many internal controls and experimental features.  
While powerful, this also made the system harder to configure, harder to debug, and easier to misconfigure.

The new Core v1 focuses on **simple and predictable behaviour**.

Most users only need to configure:

* indoor temperature source
* outdoor temperature source
* electricity price source
* comfort temperature

The core logic then handles:

* price response
* braking behaviour
* comfort protection
* overtemperature protection

automatically.

This means that **SVOTC requires very little manual tuning** in normal use.

The design goal is that the system should work well **out of the box**, without requiring users to understand the internal control logic.

---

## Recommended migration approach

When upgrading from 2.x.x:

1. Remove old files
2. Install the new 3.0.0 Core v1 files
3. Set mode to `PassThrough` first
4. Verify all source mappings
5. Confirm `binary_sensor.svotc_inputs_healthy` is ON
6. Confirm `sensor.svotc_virtual_outdoor_temperature` behaves correctly
7. Switch to `Smart` only after verification

---

## Beta reminder

SVOTC controls your heat pump indirectly through a virtual outdoor temperature.

Even though the new core is simpler and more stable, incorrect configuration can still affect:

* indoor comfort
* heat pump cycling behavior
* overall system efficiency

Always:

* test in **PassThrough** first
* monitor `input_text.svotc_reason_code`
* keep a manual fallback available during first deployment

Report bugs through GitHub Issues.

---

**Version:** SVOTC 3.0.0 Beta
**Core:** Core v1
**License:** MIT
