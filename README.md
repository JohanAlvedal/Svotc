# SVOTC – Stable Core Edition (2026-02)

SVOTC (Smart Virtual Outdoor Temperature Control) styr värmepumpen **indirekt** genom att skapa en *virtuell utetemperatur*.

I stället för att slå av/på pumpen eller ändra börvärden aggressivt, justerar SVOTC en **offset (°C)** som adderas till verklig utetemperatur:

- **Positiv offset** → “varmare ute” → värmepumpen drar ner (pris-broms)
- **Negativ offset** → “kallare ute” → värmepumpen drar upp (komfort-skydd)

Designmål:
- Stabilt (ingen fladdrig prisspik-styrning)
- Förklarbart (reason codes)
- Layered arkitektur: sensing → stabilisering → planering → ramp-limited execution

---

## 1) Krav

Du behöver:
- Home Assistant
- En innetemperatur-sensor (t.ex. `sensor.inomhusmedel`)
- En utetemperatur-sensor (t.ex. `sensor.temperatur_nu`)
- Elpris-sensor (Nordpool/Tibber HACS-stil) som har attribut:
  - `current_price`
  - `raw_today` (lista av `{start,end,value}`)
  - `raw_tomorrow` (lista av `{start,end,value}`)

> Standard i koden är `sensor.nordpool_tibber`.

---

## 2) Installation (kort)

1. Lägg YAML-filen i t.ex. `packages/svotc.yaml`
2. Aktivera packages i `configuration.yaml` (om du inte redan gjort det)
3. Starta om Home Assistant
4. Gå till **Inställningar → Enheter & tjänster → Hjälpare** och verifiera att SVOTC-helpers skapats

---

## 3) Viktigast att ändra: Entity mapping (peka på dina sensorer)

Dessa tre helpers är “mappningen” – de gör att du slipper ändra koden på massa ställen:

- `input_text.svotc_entity_indoor`  → din innetemp-sensor
- `input_text.svotc_entity_outdoor` → din utetemp-sensor
- `input_text.svotc_entity_price`   → din elpris-sensor

Exempel:
- Indoor: `sensor.inomhusmedel`
- Outdoor: `sensor.temperatur_nu`
- Price:  `sensor.nordpool_tibber`

> Tips: Ändra dem i UI (Hjälpare), så överlever det om du uppdaterar YAML senare.

---

## 4) Lovelace – “Setup & Control” kort (det här är kortet du ändrar)

Detta kort är gjort för att vara UI-vänligt.
Det visar:
- vad du ska ändra (mapping)
- driftläge
- viktiga reglage
- diagnoser + utdata (requested/applied, virtual outdoor temp)

### 4.1 Entities-kort (rekommenderas)

Kopiera detta till en Lovelace dashboard (YAML-läge för kortet):

```yaml
type: entities
title: SVOTC – Setup & Control
show_header_toggle: false
entities:
  - type: section
    label: "1) Entity mapping (ÄNDRA HÄR)"
  - entity: input_text.svotc_entity_indoor
    name: "Indoor temp entity"
  - entity: input_text.svotc_entity_outdoor
    name: "Outdoor temp entity"
  - entity: input_text.svotc_entity_price
    name: "Price entity"

  - type: section
    label: "2) Mode"
  - entity: input_select.svotc_mode
    name: "Mode (Off/Smart/PassThrough/ComfortOnly)"

  - type: section
    label: "3) Comfort guard (skydd mot för kallt)"
  - entity: input_number.svotc_comfort_temperature
    name: "Target temp"
  - entity: input_number.svotc_comfort_guard_activate_below_c
    name: "Activate below (°C under target)"
  - entity: input_number.svotc_comfort_guard_deactivate_above_c
    name: "Deactivate above (°C under target)"
  - entity: input_number.svotc_heat_aggressiveness
    name: "Heat aggressiveness (boost)"

  - type: section
    label: "4) Price braking"
  - entity: input_number.svotc_brake_aggressiveness
    name: "Brake aggressiveness (look-ahead)"
  - entity: input_number.svotc_brake_hold_offset_c
    name: "Brake hold offset (°C)"

  - type: section
    label: "5) Stability & rate limit"
  - entity: input_number.svotc_max_delta_per_step_c
    name: "Max delta per minute (°C/min)"

  - type: section
    label: "6) Diagnostics"
  - entity: sensor.svotc_src_indoor
    name: "Indoor (validated)"
  - entity: sensor.svotc_src_outdoor
    name: "Outdoor (validated)"
  - entity: sensor.svotc_current_price
    name: "Current price (mirror)"
  - entity: sensor.svotc_p30
    name: "P30"
  - entity: sensor.svotc_p80
    name: "P80"
  - entity: sensor.svotc_raw_price_state
    name: "Raw price state (instant)"
  - entity: input_text.svotc_last_price_state
    name: "Stable price state (dwell)"
  - entity: sensor.svotc_prebrake_strength
    name: "Prebrake strength (0..1)"
  - entity: input_text.svotc_brake_phase
    name: "Brake phase"
  - entity: binary_sensor.svotc_comfort_guard_active
    name: "Comfort guard active"
  - entity: binary_sensor.svotc_inputs_healthy
    name: "Inputs healthy"
  - entity: binary_sensor.svotc_price_available
    name: "Price available"
  - entity: input_text.svotc_reason_code
    name: "Reason code"

  - type: section
    label: "7) Outputs"
  - entity: input_number.svotc_requested_offset_c
    name: "Requested offset (engine)"
  - entity: input_number.svotc_applied_offset_c
    name: "Applied offset (ramp-limited)"
  - entity: sensor.svotc_virtual_outdoor_temperature
    name: "Virtual outdoor temperature"
## 6) Felsökning (snabbt)

### Det händer inget
- Kontrollera `input_select.svotc_mode` = `Smart`
- Kontrollera `binary_sensor.svotc_inputs_healthy` = `on`
- Kontrollera att mapping-helpers pekar på rätt entities:
  - `input_text.svotc_entity_indoor`
  - `input_text.svotc_entity_outdoor`
  - `input_text.svotc_entity_price`
- Kontrollera `input_text.svotc_reason_code` för ledtråd (t.ex. `OFF`, `PASS_THROUGH`, `MISSING_INPUTS_FREEZE`)

### Priset verkar “dött”
- Kontrollera `binary_sensor.svotc_price_available` = `on`
- Kontrollera `sensor.svotc_current_price` visar ett rimligt värde
- Verifiera att din prissensor verkligen har attribut:
  - `current_price`
  - `raw_today`
  - `raw_tomorrow`
- Om `sensor.svotc_p30` och `sensor.svotc_p80` är `unknown/none`:
  - då saknas ofta tillräckligt många priser (SVOTC kräver ca 20 datapunkter för percentiler)
  - vänta tills data för dagen (och ev. morgondagen) finns

### Det blir för kallt
- Sänk `input_number.svotc_comfort_guard_activate_below_c` (guard slår till tidigare)
  - Ex: från `1.0` → `0.6`
- Öka `input_number.svotc_heat_aggressiveness` (mer boost när guard är aktiv)
- Minska `input_number.svotc_brake_hold_offset_c` om bromsningen är för aggressiv
- Kolla att `binary_sensor.svotc_comfort_guard_active` faktiskt blir `on` när det är kallt

### Det blir “hackigt” / offset hoppar för snabbt
- Sänk `input_number.svotc_max_delta_per_step_c` (mjukare ramp)
  - Ex: `0.20` → `0.10`
- Kontrollera att du inte har andra automationer som också skriver till samma styrvariabler

### Jag ser “MISSING_INPUTS_FREEZE”
- SVOTC har tappat innetemp eller utetemp.
- Åtgärd:
  - Kontrollera sensorerna som `input_text.svotc_entity_indoor` och `input_text.svotc_entity_outdoor` pekar på
  - Kontrollera att de inte blir `unknown/unavailable`
- I detta läge:
  - `requested_offset` sätts till 0
  - `applied_offset` **fryses** (för att undvika vertikala hopp)

---

## 7) License / Disclaimer

Använd på egen risk. Detta projekt styr värme **indirekt** via en virtuell utetemperatur.
Testa och verifiera beteendet i din miljö innan du litar på det i skarpt läge.

Rekommendation:
- Börja med försiktiga inställningar:
  - låg `Brake hold offset`
  - låg `Max delta per minute`
  - tydlig comfort guard (rimliga activate/deactivate)
- Öka aggressivitet stegvis och följ grafer/diagnostik.

---

## 8) Credits / Arkitektur (kort)

SVOTC är byggt enligt “layered control”-principen:

1. **Sensing (validerade råinputs)**  
   `sensor.svotc_src_indoor`, `sensor.svotc_src_outdoor`, `sensor.svotc_src_current_price`

2. **Raw price state (instant, ingen memory)**  
   `sensor.svotc_raw_price_state`

3. **Dwell (raw → stable, förhindrar spikar)**  
   Automation: `SVOTC Price dwell`  
   Output: `input_text.svotc_last_price_state`

4. **Forward look (prebrake_strength 0..1)**  
   `sensor.svotc_prebrake_strength`

5. **Brake phase memory (undvik att “starta om” varje minut)**  
   `input_text.svotc_brake_phase` + automation `SVOTC Brake phase controller`

6. **Engine (requested → ramp-limited applied)**  
   Automation: `SVOTC Engine`  
   Output: `input_number.svotc_requested_offset_c`, `input_number.svotc_applied_offset_c`  
   Slutresultat: `sensor.svotc_virtual_outdoor_temperature`

---

## 9) FAQ (kort)

### Styr SVOTC direkt värmepumpen?
Nej. SVOTC skapar en virtuell utetemperatur (`sensor.svotc_virtual_outdoor_temperature`) som du sedan mappar in till din värmepump / integration.

### Vad är skillnaden på requested och applied offset?
- **Requested** = vad logiken “vill” (utan begränsningar)
- **Applied** = vad som faktiskt appliceras efter ramp-begränsning (`max_delta_per_step_c`)

### Hur skyddas komforten?
Comfort guard:
- aktiveras när innetemp hamnar under target med en viss marginal
- blockar prisbroms
- kan ge “boost” (negativ offset) via `heat_aggressiveness`

### Varför kräver percentilerna (P30/P80) “många” datapunkter?
För att undvika att thresholds blir fel när prislistan är ofullständig.
När `P30`/`P80` är `none` blir raw price state ofta mer “neutral” och SVOTC blir försiktigare.

---

## 10) Rekommenderade startvärden (defaults)

Det här är en trygg “kom igång”-profil som brukar ge stabilt beteende utan att ta i för hårt.

### 10.1 Mode
- `input_select.svotc_mode`: **Smart**

### 10.2 Comfort guard (skydd mot att det blir kallt)
- `input_number.svotc_comfort_temperature`: **21.0**
- `input_number.svotc_comfort_guard_activate_below_c`: **0.8**
- `input_number.svotc_comfort_guard_deactivate_above_c`: **0.4**
- `input_number.svotc_heat_aggressiveness`: **2**
  - Ger boost ≈ `-(2 * 0.4) = -0.8°C` offset när guard är aktiv

> Om du ofta känner att det blir för kallt: sänk `activate_below` (t.ex. 0.6) eller höj `heat_aggressiveness` (t.ex. 3).

### 10.3 Price braking (pris-broms)
- `input_number.svotc_brake_aggressiveness`: **2**
  - Ger prebrake-fönster ca **60 min** (enligt din mapping)
- `input_number.svotc_brake_hold_offset_c`: **2.0**
  - Max bromsning ≈ +2.0°C (värmepumpen “tror” att det är varmare ute)

> Om du vill spara mer på dyra timmar: höj `brake_hold_offset_c` till 3.0 eller `brake_aggressiveness` till 3.  
> Om du märker komfortdippar: sänk `brake_hold_offset_c` eller öka comfort guard/heat.

### 10.4 Dwell (stabilitet mot prisspikar)
För att undvika att enstaka spikar triggar bromsning, använd dwell:

- `input_number.svotc_price_dwell_neutral_to_brake_min`: **30**
- `input_number.svotc_price_dwell_brake_to_neutral_min`: **15**
- `input_number.svotc_price_dwell_neutral_to_cheap_min`: **20**
- `input_number.svotc_price_dwell_cheap_to_neutral_min`: **15**

> Vill du ha snabbare reaktion: sänk dwell.  
> Vill du ha ännu stabilare och mindre “fladder”: höj dwell.

### 10.5 Brake phase durations (hur bromsning “formas”)
- `input_number.svotc_brake_rampup_duration_min`: **30**
- `input_number.svotc_brake_hold_duration_min`: **60**
- `input_number.svotc_brake_rampdown_duration_min`: **45**

> Tips: Längre ramp-up/ramp-down ger mjukare beteende men mindre “snärt”.

### 10.6 Rate limiting (mjukhet per minut)
- `input_number.svotc_max_delta_per_step_c`: **0.10**

> Om du vill ha snabbare respons: 0.20  
> Om du vill ha supermjukt: 0.05

---

## 11) “30-sekunders check” efter installation

1. Sätt entity mapping:
   - `input_text.svotc_entity_indoor`
   - `input_text.svotc_entity_outdoor`
   - `input_text.svotc_entity_price`
2. Sätt `svotc_mode = Smart`
3. Kontrollera:
   - `binary_sensor.svotc_inputs_healthy` = **on**
   - `binary_sensor.svotc_price_available` = **on**
4. Kolla att dessa rör sig rimligt:
   - `sensor.svotc_current_price`
   - `sensor.svotc_p30` / `sensor.svotc_p80` (kan vara `none` om prislistan är ofullständig)
   - `sensor.svotc_virtual_outdoor_temperature`
   - `input_text.svotc_reason_code`

---

