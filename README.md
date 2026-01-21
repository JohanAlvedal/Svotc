---

# Smart Virtual Outdoor Temperature Control (SVOTC) for Home Assistant

This project provides an advanced Home Assistant framework to optimize hydronic heating systems (Heat Pumps/Boilers) by manipulating the outdoor temperature sensor. By injecting a **Virtual Outdoor Temperature**, we influence the appliance's heating curve based on electricity prices (Nordpool), weather forecasts (SMHI/YR), and building physics—without internal software modifications.

## 🚀 Key Modules & Logic

### 1. The "Smart Lie" (Price & Forecast Optimization)

The core of the system is the ability to shift the perceived outdoor temperature to force the boiler to react to energy costs.

* **Braking (High Price):** The system reports a **higher** temperature to the boiler, reducing or stopping heat production.
* **Buffering (Low Price):** The system reports a **lower** temperature, forcing the boiler to store thermal energy in the building's mass.

#### Aggression Scaling (User Defined 0–5)

| Mode | Level | Offset (Celsius) | Effect |
| --- | --- | --- | --- |
| **Bypass** | 0 | 0°C | Real temperature is reported. |
| **Brake** | 1 | +3°C | Subtle energy saving. |
| **Brake** | 5 | +10°C | Aggressive shutdown during price spikes. |
| **Buffer** | 1 | -1°C | Gentle pre-heating. |
| **Buffer** | 5 | -5°C | Maximum thermal charging (limited to prevent overheating). |

### 2. Spring/Autumn Mode (Predictive Night Brake)

Designed to prevent unnecessary heating during cold nights followed by warm days.

* **Logic:** Scans the next 12–18 hours for the maximum forecasted temperature.
* **Threshold:** If the daytime high is predicted to exceed your **"Summer Threshold"** (e.g., 15°C), the system forces a "Night Brake" regardless of the current outdoor temperature.
* **Result:** The house utilizes its thermal mass overnight, and "free" solar energy restores the temperature the next morning.

### 3. Smart Vacation Mode

A fully automated absence strategy that balances savings with building safety.

* **Target:** Maintains a set indoor temperature (typically 16–18°C).
* **Indoor Anchor:** If the actual indoor temperature drops below 16.5°C, the system overrides all brakes and "gases" the heating until the safety limit is reached.
* **Maintenance:** Automatically lowers the virtual temperature to match the real temperature for 30 minutes daily to exercise circulation pumps and prevent seized valves.
* **Predictive Return:** Uses a **Thermal Inertia Calculation** (e.g., 12 hours) to start the reheating process before your arrival. It identifies the cheapest Nordpool hours within that window to "Power-boost" the home back to 20°C.

### 4. Domestic Hot Water (DHW) Logic

Includes an `input_boolean` toggle to allow the system to manipulate the virtual temperature high enough to block or force DHW production during extreme price fluctuations.

## 📋 Prerequisites (Home Assistant Helpers)

| Name | Type | Description |
| --- | --- | --- |
| `input_number.brake_aggression` | Slider (0-5) | 5 = +10°C offset |
| `input_number.buffer_aggression` | Slider (0-5) | 5 = -5°C offset |
| `input_select.heating_strategy` | Dropdown | Bypass, Smart, Vacation, Comfort |
| `input_datetime.vacation_start/end` | Date | Timeline for absence |
| `input_boolean.dhw_control` | Toggle | Enable/Disable Hot Water logic |

## 🧠 Background Ph.D. Logic

To ensure a user-friendly experience, the system operates with several background safeguards:

1. **Ramping:** To protect the compressor, temperature changes are never instantaneous; they are ramped over 20 minutes.
2. **Model Predictive Control:** The system treats the house as a "thermal battery" ().
3. **PID Adjustment:** A slow-moving PID loop finetunes the offsets to ensure that the "Smart Mode" doesn't drift too far from the desired comfort level.

---

**Disclaimer:** *Manipulating heating systems carries risks. Ensure your system has hardware-level safety limits and that you understand the thermal characteristics of your building before applying aggressive offsets.*

---
