# SVOTC — Smart Virtual Outdoor Temperature Controller

> ⚠️ **BREAKING CHANGES NOTICE**
>
> SVOTC **3.0.0 introduces breaking changes compared to SVOTC 2.x.x**.
> The architecture and file structure have been simplified and several subsystems were removed.
>
> If you are upgrading from **2.x.x**, read the **Breaking Changes** section below before installing.

---

# SVOTC

SVOTC is a Home Assistant control system that optimizes heat pump operation by dynamically adjusting a **virtual outdoor temperature** based on electricity prices and indoor comfort.

Instead of controlling the heat pump directly, SVOTC influences the heat pump's regulation curve by modifying the outdoor temperature value the pump reads.

This allows **price‑aware heating without modifying the heat pump itself**.

---

# Features

• Price‑aware heating using Nordpool electricity prices
• Comfort protection that always prioritizes indoor temperature
• Stable control with ramp limiting
• Automatic pre‑braking before expensive electricity periods
• Cheap‑price heating boost
• Fail‑safe protection if sensor data is missing
• Transparent logic with clear reason codes

---

# How SVOTC Works

SVOTC modifies the outdoor temperature used by the heat pump.

virtual_outdoor_temperature = outdoor_temperature + offset

Example

Real outdoor temperature: 5°C
SVOTC offset: +6°C
Heat pump believes it is: 11°C

The heat pump therefore reduces heating output during expensive electricity periods.

---

# Installation

Create the directory:

/config/packages/svotc/

Place the following files inside:

00_helpers.yaml
10_sensors.yaml
20_engine.yaml
30_notify.yaml

Ensure your configuration.yaml contains:

homeassistant:
packages: !include_dir_named packages

Restart Home Assistant.

---

# Configuration

Define the source entities used by SVOTC.

input_text.svotc_source_indoor_temp
input_text.svotc_source_outdoor_temp
input_text.svotc_source_price

Example configuration:

sensor.indoor_temperature
sensor.outdoor_temperature
sensor.nordpool_kwh_se3

---

# System Architecture

SVOTC uses a simple modular architecture.

Helpers
↓
Sensors
↓
Engine
↓
Notifications

Files:

00_helpers.yaml — user configuration and internal state helpers
10_sensors.yaml — sensor normalization and price analysis
20_engine.yaml — main decision engine
30_notify.yaml — critical system notifications

The **engine runs once per minute** and calculates:

requested_offset
applied_offset
reason_code

---

# Safety Mechanisms

SVOTC includes multiple safeguards to ensure stable system behavior.

Comfort guard
Protects indoor temperature if it drops below the target.

Overtemperature brake
Reduces heating if the house becomes too warm.

Rate limiting
Prevents sudden offset jumps that could stress the heat pump.

Fail‑safe mode
If sensor inputs are invalid the system ramps offset back to zero.

---

# Operating Modes

Smart
Full autonomous control using both price and comfort logic.

Comfort
Temperature regulation only, price logic disabled.

PassThrough
No offset is applied. Useful for testing.

Off
SVOTC disabled.

---

# Monitoring

Useful diagnostic entities:

sensor.svotc_virtual_outdoor_temperature
input_number.svotc_requested_offset_c
input_number.svotc_applied_offset_c
input_text.svotc_reason_code
sensor.svotc_forward_price_state

---

# Breaking Changes (3.0.0)

SVOTC 3.0 introduces a simplified architecture.

Key changes from SVOTC 2.x.x:

• Single engine design
• Simplified package structure
• Removal of legacy price FSM system
• Removal of learning subsystem from the core
• New requested vs applied offset model
• Offset rate limiting to protect heat pump hardware

These changes make the system:

• easier to maintain
• easier to debug
• more predictable
• less aggressive toward heat pump hardware

---

# License

MIT License

Copyright (c) 2026 Johan Ä
