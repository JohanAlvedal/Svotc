<!-- ============================================================
SVOTC – Stable Core Edition (2026-02)
Single-file README with stable, explicit anchors (SV + EN)
============================================================ -->

<a id="svotc-sv"></a>
# SVOTC – Stable Core Edition (2026-02)
**Smart Virtual Outdoor Temperature Control**

**Språk / Language:**  
- [Svenska](#svotc-sv)  
- [English](#svotc-en)

SVOTC styr din värmepump **indirekt** genom att skapa en *virtuell utomhustemperatur* som värmepumpen använder för sina värmekurvor.

Istället för att slå på/av pumpen eller aggressivt ändra börvärden (setpoints), justerar SVOTC en **offset (°C)** som läggs till den verkliga utomhustemperaturen:

- **Positiv offset** (+2°C) → ”varmare ute” → värmepumpen minskar framledningen (**prisbroms**)
- **Negativ offset** (−1°C) → ”kallare ute” → värmepumpen ökar framledningen (**komfortskydd**)

**Designmål**
- 🎯 Stabil (inget fladdrigt beteende vid prisspikar)
- 📊 Förklarbar (statuskoder visar *varför* beslut fattas)
- 🏗️ Lagerbaserad arkitektur: sensorer → stabilisering → planering → ramp-begränsat utförande

---

<a id="sv-snabbstart"></a>
## 🚀 Snabbstart

Om du bara vill att det ska fungera:

1. Installera SVOTC och starta om Home Assistant (Se [1) Krav](#sv-1-krav))
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

<a id="sv-innehallsforteckning"></a>
## 📋 Innehållsförteckning
1. [Krav](#sv-1-krav)
2. [Installation](#sv-2-installation)
3. [Första uppstarten](#sv-3-forsta-uppstarten)
4. [Entitetsmappning](#sv-4-entitetsmappning)
5. [Dashboards](#sv-5-dashboards)
6. [Felsökning](#sv-6-felsokning)
7. [Så fungerar det](#sv-7-sa-fungerar-det)
8. [Rekommenderade startvärden](#sv-8-rekommenderade-startvarden)
9. [Statuskoder (Reason codes)](#sv-9-statuskoder)
10. [FAQ](#sv-10-faq)
11. [Avancerat: Bromsfaser](#sv-11-avancerat)
12. [Licens / Disclaimer](#sv-12-licens)

---

<a id="sv-1-krav"></a>
## 1) Krav

Du behöver:
- ✅ Home Assistant (modern version rekommenderas)
- ✅ Inomhustemperatursensor
- ✅ Utomhustemperatursensor
- ✅ Elprissensor (Nordpool)som tillhandahåller:
  - `current_price`
  - `raw_today`
  - `raw_tomorrow`
Koden är anpassad till HACS varianten av Nordpool men med den bifogade paketfilen som finns i 

SVOTC läser prissensorn via **entitetsmappning** (`input_text`). Inga sensornamn är hårdkodade i logiken.

<a id="sv-2-installation"></a>
## 2) Installation

1. Placera `svotc.yaml` i mappen:
   ```text
   /config/packages/

2. Aktivera packages i din `configuration.yaml` (om ej redan aktivt):

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

3. Starta om Home Assistant.

4. Verifiera att hjälpare och sensorer skapats:

   * Inställningar → Enheter & tjänster → Hjälpare → sök på **SVOTC**.

---

<a id="sv-3-forsta-uppstarten"></a>

## 3) Första uppstarten (5-minuters setup)

1. Installera och starta om.
2. Gå till **Hjälpare → SVOTC**.
3. Ställ in entiteter för: Inne, Ute och Pris.
4. Sätt **Mode = Smart** *(eller **Simple** för en mer “bara-funka”-start)*.
5. Vänta ~2 minuter.
6. Kontrollera:

   * `binary_sensor.svotc_inputs_healthy` = on
   * `input_text.svotc_reason_code` får ett värde (inte `MISSING_INPUTS_FREEZE`).

---

<a id="sv-4-entitetsmappning"></a>

## 4) Entitetsmappning (Viktigast)

| Hjälpare                          | Betydelse                     |
| --------------------------------- | ----------------------------- |
| `input_text.svotc_entity_indoor`  | Inomhustemperatur             |
| `input_text.svotc_entity_outdoor` | Utomhustemperatur             |
| `input_text.svotc_entity_price`   | Prissensor                    |
| `input_text.svotc_notify_service` | (Valfritt) notifieringstjänst |

---

<a id="sv-5-dashboards"></a>

## 5) Dashboards

SVOTC fungerar utan dashboards, men ett UI gör det enklare att förstå vad som händer.

Rekommendation:

* Visa minst:

  * Requested offset
  * Applied offset
  * Virtuell utetemp
  * Reason code
  * Inputs healthy / price available

---

<a id="sv-6-felsokning"></a>

## 6) Felsökning

### Inget händer

Kontrollera:

* Mode ≠ Off
* `binary_sensor.svotc_inputs_healthy` = on
* Entitetsmappning korrekt (inne/ute/price)
* `input_text.svotc_reason_code` (varför systemet gör/inte gör något)

### Priset verkar “dött”

Kontrollera:

* `binary_sensor.svotc_price_available` = on
* Prissensorn exponerar nödvändiga attribut (`current_price`, `raw_today`, `raw_tomorrow`)

---

<a id="sv-7-sa-fungerar-det"></a>

## 7) Så fungerar det

### Lagerbaserad arkitektur

```text
Sensorer → Råpris → Dwell (tröghet) → Framåtblick → Bromsfas → Motor
```

SVOTC hoppar aldrig i värden. Alla ändringar är **hastighetsbegränsade** (rate limited) och tillståndsbaserade.
Det innebär att om logiken vill ändra temperaturen 2 grader, så sker det gradvis över t.ex. 20 minuter för att värmepumpen ska hänga med mjukt.

---

<a id="sv-8-rekommenderade-startvarden"></a>

## 8) Rekommenderade startvärden (Defaults)

<a id="sv-8-1-lage"></a>

### 8.1 Läge

* `svotc_mode = Smart`

<a id="sv-8-2-komfortskydd"></a>

### 8.2 Comfort guard

| Setting             | Value |
| ------------------- | ----: |
| Comfort temperature |  21.0 |
| Activate below      |   0.8 |
| Deactivate above    |   0.3 |
| Heat aggressiveness |     2 |

<a id="en-8-3-price-braking"></a>

### 8.3 Price braking

| Setting              | Value |
| -------------------- | ----: |
| Brake aggressiveness |     2 |
| Brake hold offset    |   6.0 |

<a id="en-8-4-dwell"></a>

### 8.4 Dwell (stability)

Recommended for **15-minute prices** (keep dwell < 15 minutes):

- cheap → neutral: **8 min**
- neutral → brake: **8 min**
- brake → neutral: **8 min**
- neutral → cheap: **8 min**

<a id="en-8-5-brake-phase-durations"></a>

### 8.5 Brake phase durations

- rampup: **20 min**
- hold: **15 min**
- rampdown: **25 min**

<a id="en-8-6-rate-limiting"></a>

### 8.6 Rate limiting

- `svotc_max_delta_per_step_c = 0.20 °C/min`

---

<a id="en-9-reason-codes"></a>

## 9) Statuskoder (Reason codes)

| Kod                     | Betydelse                                           |
| ----------------------- | --------------------------------------------------- |
| `OFF`                   | Systemet avstängt                                   |
| `PASS_THROUGH`          | Ingen kontroll, SVOTC observerar bara               |
| `MISSING_INPUTS_FREEZE` | Sensorvärden saknas, offset fryst på 0              |
| `COMFORT_GUARD`         | Komfortskydd aktivt (värmer extra)                  |
| `MCP_BLOCKS_BRAKE`      | Det är dyrt, men komfortskyddet stoppar prisbromsen |
| `PRICE_BRAKE`           | Prisbroms aktiv                                     |
| `NEUTRAL`               | Normal drift                                        |

---

<a id="sv-10-faq"></a>

## 10) FAQ

**Styr SVOTC värmepumpen direkt?**
Nej. Den levererar en virtuell utomhustemperatur. Du måste själv konfigurera din värmepumpsintegration (t.ex. Nibe, Mitsubishi, Daikin) att läsa detta värde istället för den fysiska utegivaren.

**Vad är skillnaden på Requested och Applied offset?**

* **Requested:** Vad logiken *vill* göra just nu.
* **Applied:** Det faktiska värdet som skickas till pumpen (efter att hastighetsbegränsningen gjort sitt).

---

<a id="sv-11-avancerat"></a>

## 11) Avancerat: Bromsfaser (Brake phase timing)

Logiken för prisbroms följer en kurva för att minimera slitage:

```text
idle → ramping_up → holding → ramping_down → idle
```

---

<a id="sv-12-licens"></a>

## 12) Licens / Disclaimer

Använd på egen risk. Kontrollera alltid din pumps manual för att säkerställa att extern styrning av utetemperatur är lämplig.

---

<a id="sv-credits"></a>

## Credits

SVOTC – Stable Core Edition (2026-02)
Designad för mjuk, förklarbar och prismedveten värmepumpsstyrning.

---

<br>

<a id="svotc-en"></a>

# SVOTC – Stable Core Edition (2026-02)

**Smart Virtual Outdoor Temperature Control**

**Language / Språk:**

* [English](#svotc-en)
* [Svenska](#svotc-sv)

SVOTC controls your heat pump **indirectly** by creating a *virtual outdoor temperature* that your heat pump can use for its heating curves.

Instead of toggling the pump on/off or aggressively changing setpoints, SVOTC adjusts an **offset (°C)** that is added to the real outdoor temperature:

* **Positive offset** (+2°C) → “warmer outside” → the heat pump reduces heating (**price brake**)
* **Negative offset** (−1°C) → “colder outside” → the heat pump increases heating (**comfort guard**)

**Design goals**

* 🎯 Stable (no flappy price-spike control)
* 📊 Explainable (reason codes show *why* decisions are made)
* 🏗️ Layered architecture: sensing → stabilization → planning → ramp-limited execution

---

<a id="en-quick-start"></a>

## 🚀 Quick start

If you just want it to work:

1. Install SVOTC and restart Home Assistant (See [1 Requirements](#en-1-requirements))
2. Set entity mapping:

   * Indoor temperature
   * Outdoor temperature
   * Price sensor
3. Set:

   * **Mode = Simple**
   * **Prioritize comfort = ON**
4. Done ✔️

SVOTC will now:

* Protect indoor comfort automatically
* Reduce heating when electricity is expensive
* Avoid sudden jumps or unstable behavior

You can switch to **Smart** mode later if you want more control.

---

<a id="en-toc"></a>

## 📋 Table of contents

1. [Requirements](#en-1-requirements)

   * [Price sensor compatibility (HACS vs Official Nordpool)](#en-price-sensor-compatibility)
2. [Installation](#en-2-installation)
3. [First run (5-minute setup)](#en-3-first-run)
4. [Entity mapping](#en-4-entity-mapping)
5. [Lovelace dashboards](#en-5-lovelace-dashboards)
6. [Troubleshooting](#en-6-troubleshooting)
7. [How it works](#en-7-how-it-works)
8. [Recommended starting values (defaults)](#en-8-recommended-starting-values)
9. [Reason codes](#en-9-reason-codes)
10. [FAQ](#en-10-faq)
11. [Advanced: Brake phase timing](#en-11-advanced-brake-phase-timing)
12. [License / Disclaimer](#en-12-license)

---

<a id="en-1-requirements"></a>

## 1) Requirements

You need:

* ✅ Home Assistant (modern version recommended)
* ✅ Indoor temperature sensor
* ✅ Outdoor temperature sensor
* ✅ Electricity price sensor (Nordpool/Tibber) providing:

  * `current_price`
  * `raw_today`
  * `raw_tomorrow`

SVOTC reads the price sensor via **entity mapping** (`input_text`).
No price sensor is hard-coded.

<a id="en-price-sensor-compatibility"></a>

### Price sensor compatibility (HACS vs Official Nordpool)

**HACS Nordpool**
Set `input_text.svotc_entity_price` to your Nordpool sensor (e.g. `sensor.nordpool_tibber`).

**Official Nordpool**
Requires an adapter package that exposes SVOTC-compatible attributes.

---

<a id="en-2-installation"></a>

## 2) Installation

1. Place `svotc.yaml` in:

```text
/config/packages/
```

2. Enable packages (if not already):

```yaml
homeassistant:
  packages: !include_dir_named packages
```

3. Restart Home Assistant

4. Verify helpers & sensors exist:
   Settings → Devices & Services → Helpers → search **SVOTC**

---

<a id="en-3-first-run"></a>

## 3) First run (5-minute setup)

1. Install and restart
2. Go to **Helpers → SVOTC**
3. Set:

   * Indoor temp entity
   * Outdoor temp entity
   * Price entity
4. Set **Mode = Smart** *(or **Simple** for a worry-free start)*
5. Wait ~2 minutes
6. Verify:

   * `binary_sensor.svotc_inputs_healthy` = on
   * `input_text.svotc_reason_code` ≠ `MISSING_INPUTS_FREEZE`

> 💡 Tip
> In **Smart** mode, keep **Prioritize comfort** enabled unless you explicitly accept colder indoor temperature.

---

<a id="en-4-entity-mapping"></a>

## 4) Entity mapping (most important)

| Helper                            | Meaning                 |
| --------------------------------- | ----------------------- |
| `input_text.svotc_entity_indoor`  | Indoor temperature      |
| `input_text.svotc_entity_outdoor` | Outdoor temperature     |
| `input_text.svotc_entity_price`   | Price sensor            |
| `input_text.svotc_notify_service` | Optional notify service |

---

<a id="en-5-lovelace-dashboards"></a>

## 5) Lovelace dashboards

SVOTC works without dashboards, but a UI helps.

A minimal dashboard example is included in the repo.

---

<a id="en-6-troubleshooting"></a>

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

<a id="en-7-how-it-works"></a>

## 7) How it works

### Layered architecture

```text
Sensing → Raw price → Dwell → Forward look → Brake phase → Engine
```

SVOTC never jumps values.
All changes are **rate limited** and **stateful**.

---

<a id="en-8-recommended-starting-values"></a>

## 8) Recommended starting values (defaults)

<a id="en-8-1-mode"></a>

### 8.1 Mode

* `svotc_mode = Smart`

<a id="en-8-2-comfort-guard"></a>

### 8.2 Comfort guard

| Setting             | Value |
| ------------------- | ----: |
| Comfort temperature |  21.0 |
| Activate below      |   0.8 |
| Deactivate above    |   0.4 |
| Heat aggressiveness |     2 |

<a id="en-8-3-price-braking"></a>

### 8.3 Price braking

| Setting              | Value |
| -------------------- | ----: |
| Brake aggressiveness |     2 |
| Brake hold offset    |   2.0 |

<a id="en-8-4-dwell"></a>

### 8.4 Dwell (stability)

Typical values:

* neutral → brake: 30 min
* brake → neutral: 15 min

<a id="en-8-5-brake-phase-durations"></a>

### 8.5 Brake phase durations

* rampup: 30 min
* hold: 60 min
* rampdown: 45 min

<a id="en-8-6-rate-limiting"></a>

### 8.6 Rate limiting

* `svotc_max_delta_per_step_c = 0.10 °C/min`

<a id="en-8-7-prioritize-comfort"></a>

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

<a id="en-simple-vs-smart"></a>

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

<a id="en-9-reason-codes"></a>

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

<a id="en-10-faq"></a>

## 10) FAQ

**Does SVOTC control the heat pump directly?**
No. It outputs a virtual outdoor temperature.

**Requested vs Applied offset?**
Requested = what logic wants
Applied = ramp-limited reality

---

<a id="en-11-advanced-brake-phase-timing"></a>

## 11) Advanced: Brake phase timing

```text
idle → ramping_up → holding → ramping_down → idle
```

---

<a id="en-12-license"></a>

## 12) License / Disclaimer

Use at your own risk.
Test carefully before relying on SVOTC for comfort or savings.

---

<a id="en-credits"></a>

## Credits

SVOTC – Stable Core Edition (2026-02)
Designed for smooth, explainable, price-aware heat pump control.

```
