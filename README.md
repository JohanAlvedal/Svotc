# SVOTC (Smart Virtual Outdoor Temperature Controller)

SVOTC is a minimal, drift-safe Home Assistant custom integration that generates a **virtual outdoor temperature** value.  
By gently adjusting a *virtual* outdoor temperature (instead of changing your heat pump setpoints directly), SVOTC can reduce heating during expensive hours and increase heating during cheap hours — while prioritizing indoor comfort and stability.

The main output is a single sensor:

- `sensor.svotc`  
  **State:** Virtual outdoor temperature (°C)  
  **Attributes:** Status, reason codes, offset, targets, and diagnostics

---

## What it does (current behavior)

SVOTC decides a **target offset** (in °C) and applies it to the real outdoor temperature:

- **Expensive electricity** → **Brake** heating by increasing the virtual outdoor temperature
- **Cheap electricity** → **Boost** heating by decreasing the virtual outdoor temperature
- **Neutral price** → no change (bypass), unless a cold-forecast rule requires boosting
- **Safety first:** if indoor temperature is too low, SVOTC boosts regardless of price

The output is always **rate-limited and clamped** to avoid sudden jumps and unstable behavior.

---

## Core controls (created by the integration)

SVOTC creates the following entities:

### Main output
- `sensor.svotc` — Virtual outdoor temperature (°C)

### User controls
- `number.svotc_brake` (0–5) — Brake aggressiveness  
- `number.svotc_heat` (0–5) — Heat/boost aggressiveness  
- `number.svotc_comfort` (°C) — Comfort target temperature  
- `number.svotc_vacation` (°C) — Vacation target temperature  
- `select.svotc_mode` — `Off`, `Smart`, `Vacation`

No Home Assistant helpers (`input_number`, `input_select`, etc.) are required.

---

## Aggressiveness mapping

### Brake mapping (`number.svotc_brake`)
| Level | Offset (°C) |
|------:|------------:|
| 0 | +0 |
| 1 | +3 |
| 2 | +5 |
| 3 | +7 |
| 4 | +9 |
| 5 | +10 |

### Heat/boost mapping (`number.svotc_heat`)
| Level | Offset (°C) |
|------:|------------:|
| 0 | 0 |
| 1 | -1 |
| 2 | -2 |
| 3 | -3 |
| 4 | -4 |
| 5 | -5 |

---

## Modes

### Off
- SVOTC runs in **bypass** mode:
  - virtual outdoor temp = real outdoor temp

### Smart
- Uses electricity price data when available.
- Uses weather forecast only for a single minimal override (see below).
- Always uses a safety anchor if indoor temperature is available.

### Vacation
- Uses `number.svotc_vacation` as the target temperature.
- Safety anchor is active if indoor temperature is available.

---

## Minimal forecast logic (v1)

SVOTC only uses forecast for one purpose: **avoid falling behind when colder weather is imminent**.

If all conditions below are true:

- `indoor_temp < dynamic_target + 0.2°C`
- `forecast_outdoor_min_next_6h < current_outdoor - 2.0°C`

Then SVOTC allows heat boosting even if the price is neutral, with:

- `reason_code = FORECAST_HEAT_NEED`
- `status = "Boosting (cold forecast ahead)"`

SVOTC does not implement warm-day / night-brake behavior in v1.

---

## Price classification (A-model)

SVOTC classifies prices into three states:

- `cheap` if price is at or below the **30th percentile (P30)**
- `expensive` if price is at or above the **70th percentile (P70)**
- `neutral` otherwise

Percentiles are computed over the available prices for the **remaining day**, including tomorrow if available (Tibber-like behavior).

---

## Drift-safe behavior (anti-jumps, fallbacks, restarts)

### Update interval
- SVOTC updates every **60 seconds**.

### Startup grace period
- After Home Assistant startup, SVOTC waits **60 seconds** before emitting warnings.
- During grace, it prefers holding or bypass behavior without log noise.

### Short glitches
- If critical inputs are temporarily missing, SVOTC **holds the last output** for up to **60 seconds**.

### Longer outages
- If missing inputs last longer than 60 seconds, SVOTC switches to **bypass** when possible:
  - virtual outdoor = real outdoor
- If real outdoor temperature is also unavailable, SVOTC continues to hold the last output and reports the issue via status and logs.

### Ramping (rate limiting)
- SVOTC never jumps directly to a new offset.
- It ramps toward the target offset smoothly over **20 minutes**.

### Clamps
- Virtual outdoor temperature is clamped to **-25°C .. +25°C**.

---

## Data availability matrix

SVOTC behaves predictably depending on which inputs are available:

1. **Price + Forecast available**  
   → Full Smart (price + minimal forecast override + safety)

2. **Price only**  
   → Smart (price only + safety)

3. **Forecast only**  
   → Bypass + safety

4. **Neither price nor forecast**  
   → Bypass (and safety if indoor temp exists)

---

## `sensor.svotc` attributes

The main `sensor.svotc` exposes useful diagnostics as attributes (keys in English), typically including:

- `status` — human-readable explanation
- `reason_code` — short reason code
- `offset_c` — current applied offset (°C)
- `mode` — Off/Smart/Vacation
- `dynamic_target_c` — currently active target temperature (°C)
- `indoor_temp_c` — current indoor temperature (°C) if available
- `outdoor_temp_c` — current outdoor temperature (°C) if available
- `price_state` — cheap/neutral/expensive/unknown
- `forecast_min_next_6h_c` — forecast min (°C) if available
- `startup_grace_active` — true/false

Exact attributes may expand slightly over time, but the core set is kept minimal.

---

## Notes

- SVOTC is designed to be **predictable, stable, and easy to understand**.
- It does not require any helpers.
- It can run without price and/or weather data and will safely fall back to bypass behavior while reporting degraded states.
- If you already have suffixed entity IDs (for example, `sensor.svotc_1234`), remove and re-add the integration to get the deterministic entity IDs.

---

**Disclaimer:** *Manipulating heating systems carries risks. Ensure your system has hardware-level safety limits and that you understand the thermal characteristics of your building before applying aggressive offsets.*

---
