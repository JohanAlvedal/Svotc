# SVOTC (Smart Virtual Outdoor Temperature Controller)

SVOTC is a minimal, drift-safe Home Assistant custom integration that generates a **virtual outdoor temperature** value.  
By gently adjusting a *virtual* outdoor temperature (instead of changing your heat pump setpoints directly), SVOTC can reduce heating during expensive hours and increase heating during cheap hours — while prioritizing indoor comfort and stability.

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
