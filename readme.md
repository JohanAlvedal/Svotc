# SVOTC – Stable Core Edition (2026-02)
**Smart Virtual Outdoor Temperature Control**

[English version / Engelsk version](README.md)

SVOTC styr din värmepump **indirekt** genom att skapa en *virtuell utomhustemperatur* som värmepumpen använder för sina värmekurvor.

Istället för att slå på/av pumpen eller aggressivt ändra börvärden (setpoints), justerar SVOTC en **offset (°C)** som läggs till den verkliga utomhustemperaturen:

- **Positiv offset** (+2°C) → ”varmare ute” → värmepumpen minskar framledningen (**prisbroms**)
- **Negativ offset** (−1°C) → ”kallare ute” → värmepumpen ökar framledningen (**komfortskydd**)

**Designmål**
- 🎯 Stabil (inget fladdrigt beteende vid prisspikar)
- 📊 Förklarbar (statuskoder visar *varför* beslut fattas)
- 🏗️ Lagerbaserad arkitektur: sensorer → stabilisering → planering → ramp-begränsat utförande

---

## 🚀 Snabbstart

Om du bara vill att det ska fungera:

1. Installera SVOTC och starta om Home Assistant (Se sektion 1: Krav)
2. Ställ in entitetsmappning i UI:
   - Inomhustemperatur
   - Utomhustemperatur
   - Prissensor
3. Ställ in:
   - **Mode = Simple**
   - **Prioritize comfort = PÅ**
4. Klart ✔️

SVOTC kommer nu att:
- Skydda inomhuskomforten automatiskt.
- Reducera uppvärmningen när elen är dyr.
- Undvika plötsliga hopp som kan störa värmepumpens interna logik.

Du kan byta till **Smart** mode senare om du vill ha mer finkornig kontroll.

---

## 📋 Innehållsförteckning
1. [Krav](#1-krav)
2. [Installation](#2-installation)
3. [Första uppstarten](#3-första-uppstarten)
4. [Entitetsmappning](#4-entitetsmappning)
5. [Dashboards](#5-dashboards)
6. [Felsökning](#6-felsökning)
7. [Så fungerar det](#7-så-fungerar-det)
8. [Rekommenderade startvärden](#8-rekommenderade-startvärden)
9. [Statuskoder (Reason codes)](#9-statuskoder)
10. [FAQ](#10-faq)
11. [Avancerat: Brake phase timing](#11-avancerat)
12. [Licens / Disclaimer](#12-licens)

---

## 1) Krav

Du behöver:
- ✅ Home Assistant (modern version rekommenderas)
- ✅ Inomhustemperatursensor
- ✅ Utomhustemperatursensor
- ✅ Elprissensor (Nordpool/Tibber) som tillhandahåller:
  - `current_price`
  - `raw_today`
  - `raw_tomorrow`

SVOTC läser prissensorn via **entitetsmappning** (`input_text`). Inga sensornamn är hårdkodade i logiken.

---

## 2) Installation

1. Placera `svotc.yaml` i mappen: `/config/packages/`
2. Aktivera packages i din `configuration.yaml` (om ej redan aktivt):
   ```yaml
   homeassistant:
     packages: !include_dir_named packages

```

3. Starta om Home Assistant.
4. Verifiera att hjälpare och sensorer skapats:
Inställningar → Enheter & tjänster → Hjälpare → sök på **SVOTC**.

---

## 3) Första uppstarten (5-minuters setup)

1. Installera och starta om.
2. Gå till **Hjälpare → SVOTC**.
3. Ställ in entiteter för: Inne, Ute och Pris.
4. Sätt **Mode = Smart**.
5. Vänta ~2 minuter.
6. Kontrollera:
* `binary_sensor.svotc_inputs_healthy` = on
* `input_text.svotc_reason_code` får ett värde (inte `MISSING_INPUTS_FREEZE`).



---

## 4) Entitetsmappning (Viktigast)

| Hjälpare | Betydelse |
| --- | --- |
| `input_text.svotc_entity_indoor` | Inomhustemperatur |
| `input_text.svotc_entity_outdoor` | Utomhustemperatur |
| `input_text.svotc_entity_price` | Prissensor |
| `input_text.svotc_notify_service` | (Valfritt) notifieringstjänst |

---

## 7) Så fungerar det

### Lagerbaserad arkitektur

```text
Sensorer → Råpris → Dwell (tröghet) → Framåtblick → Bromsfas → Motor

```

SVOTC hoppar aldrig i värden. Alla ändringar är **hastighetsbegränsade** (rate limited) och tillståndsbaserade. Detta innebär att om logiken vill ändra temperaturen 2 grader, så sker det gradvis över t.ex. 20 minuter för att värmepumpen ska hänga med mjukt.

---

## 8) Rekommenderade startvärden (Defaults)

### 8.1 Läge

* `svotc_mode = Smart`

### 8.2 Komfortskydd (Comfort guard)

| Inställning | Värde |
| --- | --- |
| Comfort temperature | 21.0 |
| Activate below (Δ) | 0.8 |
| Deactivate above (Δ) | 0.4 |
| Heat aggressiveness | 2 |

### 8.3 Prisbroms (Price braking)

| Inställning | Värde |
| --- | --- |
| Brake aggressiveness | 2 |
| Brake hold offset | 2.0 |

### 8.4 Dwell (Stabilitet/Tröghet)

Typiska värden för att undvika att systemet reagerar på korta prisfluktuationer:

* Neutral → Broms: 30 min
* Broms → Neutral: 15 min

### 8.5 Varaktighet för bromsfaser

* Ramp-up: 30 min
* Hold: 60 min
* Ramp-down: 45 min

### 8.6 Hastighetsbegränsning (Rate limiting)

* `svotc_max_delta_per_step_c = 0.10 °C/min`

---

## 9) Statuskoder (Reason codes)

| Kod | Betydelse |
| --- | --- |
| `OFF` | Systemet avstängt |
| `PASS_THROUGH` | Ingen kontroll, SVOTC observerar bara |
| `MISSING_INPUTS_FREEZE` | Sensorvärden saknas, offset fryst på 0 |
| `COMFORT_GUARD` | Komfortskydd aktivt (värmer extra) |
| `MCP_BLOCKS_BRAKE` | Det är dyrt, men komfortskyddet stoppar prisbromsen |
| `PRICE_BRAKE` | Prisbroms aktiv |
| `NEUTRAL` | Normal drift |

---

## 10) FAQ

**Styr SVOTC värmepumpen direkt?**
Nej. Den levererar en virtuell utomhustemperatur. Du måste själv konfigurera din värmepumpsintegration (t.ex. Nibe, Mitsubishi, Daikin) att läsa detta värde istället för den fysiska utegivaren.

**Vad är skillnaden på Requested och Applied offset?**

* **Requested:** Vad logiken *vill* göra just nu.
* **Applied:** Det faktiska värdet som skickas till pumpen (efter att hastighetsbegränsningen gjort sitt).

---

## 11) Avancerat: Bromsfaser (Brake phase timing)

Logiken för prisbroms följer en kurva för att minimera slitage:
`idle → ramping_up → holding → ramping_down → idle`

---

## 12) Licens / Disclaimer

Använd på egen risk. Kontrollera alltid din pumps manual för att säkerställa att extern styrning av utetemperatur är lämplig.

---

**Credits**
SVOTC – Stable Core Edition (2026-02)
Designad för mjuk, förklarbar och prismedveten värmepumpsstyrning.


```

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

## 🚀 Quick start

If you just want it to work:

1. Install SVOTC and restart Home Assistant (See 1 Requirements)
2. Set entity mapping:
   - Indoor temperature
   - Outdoor temperature
   - Price sensor
3. Set:
   - **Mode = Simple**
   - **Prioritize comfort = ON**
4. Done ✔️

SVOTC will now:
- Protect indoor comfort automatically
- Reduce heating when electricity is expensive
- Avoid sudden jumps or unstable behavior

You can switch to **Smart** mode later if you want more control.

---

## 📋 Table of contents
1. [Requirements](#1-requirements)
   - [Price sensor compatibility (HACS vs Official Nordpool)](#price-sensor-compatibility-hacs-vs-official-nordpool)
2. [Installation](#2-installation)
3. [First run (5-minute setup)](#3-first-run-5-minute-setup)
4. [Entity mapping](#4-entity-mapping-most-important)
5. [Lovelace dashboards](#5-lovelace-dashboards)
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
- ✅ Indoor temperature sensor
- ✅ Outdoor temperature sensor
- ✅ Electricity price sensor (Nordpool/Tibber) providing:
  - `current_price`
  - `raw_today`
  - `raw_tomorrow`

SVOTC reads the price sensor via **entity mapping** (`input_text`).  
No price sensor is hard-coded.

### Price sensor compatibility (HACS vs Official Nordpool)

**HACS Nordpool**  
Set `input_text.svotc_entity_price` to your Nordpool sensor (e.g. `sensor.nordpool_tibber`).

**Official Nordpool**  
Requires an adapter package that exposes SVOTC-compatible attributes.

---

## 2) Installation

1. Place `svotc.yaml` in:

```text
/config/packages/
````

2. Enable packages (if not already):

```yaml
homeassistant:
  packages: !include_dir_named packages
```

3. Restart Home Assistant

4. Verify helpers & sensors exist:
   Settings → Devices & Services → Helpers → search **SVOTC**

---

## 3) First run (5-minute setup)

1. Install and restart
2. Go to **Helpers → SVOTC**
3. Set:

   * Indoor temp entity
   * Outdoor temp entity
   * Price entity
4. Set **Mode = Smart**
5. Wait ~2 minutes
6. Verify:

   * `binary_sensor.svotc_inputs_healthy` = on
   * `input_text.svotc_reason_code` ≠ `MISSING_INPUTS_FREEZE`

> 💡 Tip
> For a worry-free start, you can use **Simple** mode.
> In **Smart** mode, keep **Prioritize comfort** enabled unless you explicitly accept colder indoor temperature.

---

## 4) Entity mapping (most important)

| Helper                            | Meaning                 |
| --------------------------------- | ----------------------- |
| `input_text.svotc_entity_indoor`  | Indoor temperature      |
| `input_text.svotc_entity_outdoor` | Outdoor temperature     |
| `input_text.svotc_entity_price`   | Price sensor            |
| `input_text.svotc_notify_service` | Optional notify service |

---

## 5) Lovelace dashboards

SVOTC works without dashboards, but a UI helps.

A minimal dashboard example is included in the repo.

---

## 6) Troubleshooting

### Nothing happens

Check:

* Mode ≠ Off
* Inputs healthy = on
* Entity mapping correct
* Check `input_text.svotc_reason_code`

### Price looks dead

Check:

* `binary_sensor.svotc_price_available` = on
* Price sensor exposes required attributes

---

## 7) How it works

### Layered architecture

```text
Sensing → Raw price → Dwell → Forward look → Brake phase → Engine
```

SVOTC never jumps values.
All changes are **rate limited** and **stateful**.

---

## 8) Recommended starting values (defaults)

### 8.1 Mode

* `svotc_mode = Smart`

### 8.2 Comfort guard

| Setting             | Value |
| ------------------- | ----: |
| Comfort temperature |  21.0 |
| Activate below      |   0.8 |
| Deactivate above    |   0.4 |
| Heat aggressiveness |     2 |

### 8.3 Price braking

| Setting              | Value |
| -------------------- | ----: |
| Brake aggressiveness |     2 |
| Brake hold offset    |   2.0 |

### 8.4 Dwell (stability)

Typical values:

* neutral → brake: 30 min
* brake → neutral: 15 min

### 8.5 Brake phase durations

* rampup: 30 min
* hold: 60 min
* rampdown: 45 min

### 8.6 Rate limiting

* `svotc_max_delta_per_step_c = 0.10 °C/min`

### 8.7 Comfort Guard (Prioritize comfort)

SVOTC includes a **Comfort Guard** that protects indoor comfort when temperature risks dropping too low.

Controlled by:

* `input_boolean.svotc_comfort_guard_enabled`
  UI: **Prioritize comfort (blocks price braking)**

When active:

* Heating is boosted (negative offset)
* Price braking is blocked

#### Mode behavior

* **Simple**
  Designed to “just work”. Comfort Guard should normally be **ON**.

* **Smart + Guard ON**
  Balanced: saves money but protects comfort.

* **Smart + Guard OFF**
  Maximum savings. Indoor temperature may drop significantly.

* **ComfortOnly**
  Only comfort logic, no price braking.

* **PassThrough / Off**
  Guard ignored.

---

## Simple vs Smart – which mode should I use?

| Mode              | Who is it for?   | Behavior                                        |
| ----------------- | ---------------- | ----------------------------------------------- |
| Simple            | Most users       | Automatic, comfort-first, Ngenic-style behavior |
| Smart             | Advanced users   | Full control over aggressiveness and limits     |
| Smart + Guard ON  | Normal daily use | Balanced savings with comfort protection        |
| Smart + Guard OFF | Testing / away   | Maximum savings, indoor temp may drop           |
| ComfortOnly       | Comfort testing  | No price control, comfort only                  |
| PassThrough       | Debug / monitor  | No control, SVOTC only observes                 |

---

## 9) Reason codes

| Code                  | Meaning                   |
| --------------------- | ------------------------- |
| OFF                   | Disabled                  |
| PASS_THROUGH          | No control                |
| COMFORT_ONLY          | Comfort only              |
| MISSING_INPUTS_FREEZE | Inputs missing            |
| COMFORT_GUARD         | Comfort protection active |
| MCP_BLOCKS_BRAKE      | Comfort overrides price   |
| PRICE_BRAKE           | Price braking             |
| NEUTRAL               | Normal                    |

---

## 10) FAQ

**Does SVOTC control the heat pump directly?**
No. It outputs a virtual outdoor temperature.

**Requested vs Applied offset?**
Requested = what logic wants
Applied = ramp-limited reality

---

## 11) Advanced: Brake phase timing

```text
idle → ramping_up → holding → ramping_down → idle
```

---

## 12) License / Disclaimer

Use at your own risk.
Test carefully before relying on SVOTC for comfort or savings.

---

## Credits

SVOTC – Stable Core Edition (2026-02)
Designed for smooth, explainable, price-aware heat pump control.
