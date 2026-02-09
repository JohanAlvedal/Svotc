````markdown
# SVOTC – Stable Core Edition (2026-02)
**Smart Virtual Outdoor Temperature Control**

SVOTC styr din värmepump **indirekt** genom att skapa en *virtuell utetemperatur* som värmepumpen kan använda i sina kurvor.

I stället för att slå av/på pumpen eller ändra börvärden aggressivt, justerar SVOTC en **offset (°C)** som adderas till verklig utetemperatur:

- **Positiv offset** (+2°C) → "varmare ute" → värmepumpen drar ner värme (**pris-broms**)
- **Negativ offset** (−1°C) → "kallare ute" → värmepumpen drar upp värme (**komfort-skydd**)

**Designmål**
- 🎯 Stabilt (ingen fladdrig prisspik-styrning)
- 📊 Förklarbart (reason codes visar varför beslut tas)
- 🏗️ Layered arkitektur: sensing → stabilisering → planering → ramp-limited execution

---

## 📋 Innehållsförteckning
1. [Krav](#1-krav)
2. [Installation](#2-installation)
3. [Första gången du kör SVOTC](#3-första-gången-du-kör-svotc-5-minuters-setup)
4. [Entity mapping](#4-entity-mapping-viktigast-att-ändra)
5. [Lovelace dashboards](#5-lovelace-dashboards)
   - [5.1 Krav (HACS / custom cards)](#51-krav-hacs--custom-cards)
   - [5.2 Importguide: så lägger du in YAML-dashboards](#52-importguide-så-lägger-du-in-yaml-dashboards)
   - [5.3 Minimal dashboard (utan custom cards)](#53-minimal-dashboard-utan-custom-cards)
   - [5.4 Färdiga dashboards (copy/paste)](#54-färdiga-dashboards-copypaste)
7. [Felsökning](#6-felsökning)
8. [Hur systemet fungerar](#7-hur-systemet-fungerar)
9. [Rekommenderade startvärden](#8-rekommenderade-startvärden-defaults)
10. [Reason codes](#9-reason-codes-vad-betyder-de)
11. [FAQ](#10-faq)
12. [Avancerat: Brake phase timing](#11-avancerat-brake-phase-timing)
13. [License](#12-license--disclaimer)

---

## 1) Krav
Du behöver:
- ✅ Home Assistant (modern version rekommenderas)
- ✅ Innetemperatur-sensor (t.ex. `sensor.inomhusmedel`)
- ✅ Utetemperatur-sensor (t.ex. `sensor.temperatur_nu`)
- ✅ Elpris-sensor (Nordpool/Tibber) med attribut:
  - `current_price`
  - `raw_today` (lista av `{start, end, value}`)
  - `raw_tomorrow` (lista av `{start, end, value}`)

> SVOTC läser prissensorn via **entity mapping** (input_text). Ingen hårdkodad prissensor används i denna Stable Core-version.

---

## 2) Installation

### Steg 1: Lägg till YAML-filen
Lägg filen i din packages-mapp, t.ex:
```bash
/config/packages/svotc.yaml
````

### Steg 2: Aktivera packages (om du inte redan har)

I `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### Steg 3: Starta om Home Assistant

* Inställningar → System → Starta om

### Steg 4: Verifiera att allt laddat

* Inställningar → Enheter & tjänster → **Hjälpare**
* Sök på **SVOTC**
* Du ska se hjälpare (`input_*`) och nya sensorer (`sensor.svotc_*`)

---

## 3) Första gången du kör SVOTC (5-minuters setup)

⏱️ **Snabbstart**

1. Installera enligt [Installation](#2-installation)
2. Starta om Home Assistant
3. Gå till **Hjälpare** och sök på “SVOTC”
4. Fyll i Entity mapping (se nästa avsnitt):

   * Indoor → din innetemp-sensor
   * Outdoor → din utetemp-sensor
   * Price → din elpris-sensor
5. Sätt **Mode = Smart**
6. Vänta 2 minuter
7. Kontrollera:

   * ✅ `binary_sensor.svotc_inputs_healthy` = **on**
   * ✅ `input_text.svotc_reason_code` visar **inte** `MISSING_INPUTS_FREEZE`
   * ✅ `sensor.svotc_virtual_outdoor_temperature` visar ett rimligt värde

Om något är fel: se [Felsökning](#6-felsökning)

---

## 4) Entity mapping (viktigast att ändra)

Dessa helpers pekar SVOTC till dina sensorer. Du **måste** sätta dem.

| Helper                                       | Vad             | Exempel                         |
| -------------------------------------------- | --------------- | ------------------------------- |
| `input_text.svotc_entity_indoor`             | Innetemp-sensor | `sensor.inomhusmedel`           |
| `input_text.svotc_entity_outdoor`            | Utetemp-sensor  | `sensor.temperatur_nu`          |
| `input_text.svotc_entity_price`              | Elpris-sensor   | `sensor.nordpool_tibber`        |
| `input_text.svotc_notify_service` *(valfri)* | notify-service  | `notify.mobile_app_iphone13pro` |

### Så ändrar du (rekommenderat sätt)

1. Inställningar → Enheter & tjänster → **Hjälpare**
2. Sök: `svotc_entity`
3. Öppna respektive helper och skriv in `entity_id`
4. Spara

✅ Tips: Eftersom mapping ligger i helpers överlever det uppdateringar av YAML-filen.

---

## 5) Lovelace dashboards

### 5.1 Krav (HACS / custom cards)

Dina “Styrsystem”-kort använder:

* `custom:mini-graph-card`

👉 Installera **mini-graph-card** via HACS, annars blir de korten trasiga.

**Installationsguide (kort)**

1. HACS → Frontend
2. Sök “mini graph card”
3. Installera
4. Starta om Home Assistant (eller ladda om frontend)
5. Kontrollera att ett `type: custom:mini-graph-card` inte visar fel längre

---

### 5.2 Importguide: så lägger du in YAML-dashboards

Det finns två vanliga sätt. Välj den som passar hur din HA kör Lovelace.

#### A) Dashboard i “Storage mode” (vanligast)

Detta är när du normalt bygger dashboards via UI, men kan klistra in YAML i en vy.

**Så gör du:**

1. Inställningar → Dashboards
2. Skapa ny dashboard (eller öppna befintlig)
3. Skapa ny **View** (flik) t.ex. “SVOTC”
4. Uppe till höger: **⋮ → Redigera dashboard**
5. Välj **Raw configuration editor**
6. Klistra in YAML (se [5.4](#54-färdiga-dashboards-copypaste))
7. Spara

> Tips: Om du redan har en dashboard och bara vill lägga till SVOTC som en ny vy,
> klistra bara in *view*-delen (en “title/type/sections…”).

#### B) Dashboard i YAML-mode (om du kör lovelace: yaml)

Om du har en YAML-dashboardfil (t.ex. i repo) och vill peka HA mot den.

**Exempelstruktur i repo**

```
lovelace/
  svotc_styrsystem.yaml
  svotc_debug.yaml
```

**Konceptet:**

* du skapar en ny dashboard och anger YAML-filen som källa
* alternativt lägger du in som “views” beroende på din setup

> Exakt var detta ställs in skiljer lite beroende på HA-version och hur du redan kör Lovelace.
> Om du vill: skriv om du kör storage eller yaml idag, så kan du få en super-exakt steglista för just din variant.
> (Manualen funkar ändå utan den detaljen.)

---

### 5.3 Minimal dashboard (utan custom cards)

För nybörjare som vill ha en “måste-funka”-vy utan mini-graph-card:

```yaml
title: SVOTC Minimal
type: sections
sections:
  - type: grid
    cards:
      - type: entities
        title: SVOTC – Setup & Drift
        show_header_toggle: false
        state_color: true
        entities:
          - type: section
            label: Setup (en gång)
          - entity: input_text.svotc_entity_indoor
            name: "📍 Innetemp-sensor"
          - entity: input_text.svotc_entity_outdoor
            name: "🌡️ Utetemp-sensor"
          - entity: input_text.svotc_entity_price
            name: "💰 Elpris-sensor"
          - entity: input_text.svotc_notify_service
            name: "🔔 Notify service (valfri)"

          - type: divider
          - type: section
            label: Läge & mål
          - entity: input_select.svotc_mode
            name: "Mode"
          - entity: input_number.svotc_comfort_temperature
            name: "Måltemperatur"

          - type: divider
          - type: section
            label: Status
          - entity: binary_sensor.svotc_inputs_healthy
            name: "✅ Temperatursensorer OK?"
          - entity: binary_sensor.svotc_price_available
            name: "💰 Pris tillgängligt?"
          - entity: input_text.svotc_reason_code
            name: "🧠 Reason code"
          - entity: input_number.svotc_applied_offset_c
            name: "↕️ Applied offset (°C)"
          - entity: sensor.svotc_virtual_outdoor_temperature
            name: "🎯 Virtuell utetemp (→ VP)"
```

---

### 5.4 Färdiga dashboards (copy/paste)

Här är dina två dashboards. De är redo att klistra in som **views** i Lovelace.

> **Obs:** “SVOTC Styrsystem” använder `custom:mini-graph-card` → installera via HACS (se 5.1).

#### 5.4.1 SVOTC Styrsystem (view)

```yaml
title: SVOTC Styrsystem
icon: ""
badges: []
cards: []
type: sections
sections:
  - type: grid
    cards:
      - type: entities
        title: 🎛️ SVOTC Kontroller
        state_color: true
        show_header_toggle: false
        entities:
          - entity: input_select.svotc_mode
            name: Driftsläge
            icon: mdi:toggle-switch
          - type: divider
          - type: section
            label: Komfortinställningar
          - entity: input_number.svotc_comfort_temperature
            name: Måltemperatur
            icon: mdi:target
          - entity: input_number.svotc_comfort_guard_activate_below_c
            name: Skydd vid (under mål)
            icon: mdi:shield-alert
          - entity: input_number.svotc_comfort_guard_deactivate_above_c
            name: Skydd vid (över mål)
            icon: mdi:shield-check
          - type: divider
          - type: section
            label: Prisoptimering
          - entity: input_number.svotc_brake_aggressiveness
            name: Broms (0-5)
            icon: mdi:speedometer-slow
          - entity: input_number.svotc_heat_aggressiveness
            name: Värme (0-5)
            icon: mdi:fire
          - entity: input_number.svotc_brake_hold_offset_c
            name: Max bromsoffset (°C)
            icon: mdi:thermometer-minus
      - type: horizontal-stack
        cards:
          - type: entity
            entity: input_select.svotc_mode
            name: SVOTC Läge
            icon: mdi:power
          - type: entity
            entity: binary_sensor.svotc_inputs_healthy
            name: System OK
            icon: mdi:heart-pulse
      - type: horizontal-stack
        cards:
          - type: entity
            entity: binary_sensor.svotc_comfort_guard_active
            name: Komfortskydd
            icon: mdi:shield-home
          - type: entity
            entity: input_text.svotc_reason_code
            name: Strategi
            icon: mdi:brain
      - type: custom:mini-graph-card
        name: 📈 Offset-utveckling (24h)
        hours_to_show: 24
        points_per_hour: 4
        line_width: 3
        font_size: 75
        animate: true
        show:
          labels: true
          legend: true
          icon: false
        entities:
          - entity: input_number.svotc_requested_offset_c
            name: Begärd offset
            color: "#f39c12"
            show_state: true
          - entity: input_number.svotc_applied_offset_c
            name: Tillämpad offset
            color: "#e67e22"
            show_state: true
      - type: custom:mini-graph-card
        name: 🌡️ Temperaturöversikt (24h)
        hours_to_show: 24
        points_per_hour: 4
        line_width: 2
        font_size: 75
        animate: true
        show:
          labels: true
          legend: true
          icon: false
        entities:
          - entity: sensor.svotc_src_indoor
            name: Inomhus
            color: "#e74c3c"
            show_state: true
          - entity: sensor.svotc_src_outdoor
            name: Utomhus (verklig)
            color: "#3498db"
            show_state: true
          - entity: sensor.svotc_virtual_outdoor_temperature
            name: Virtuell ute (→VP)
            color: "#9b59b6"
            show_state: true
          - entity: sensor.svotc_dynamic_target_temperature
            name: Måltemperatur
            color: "#2ecc71"
            show_line: true
            show_points: false
            show_state: true
            line_width: 1
      - type: entities
        title: 🔬 Diagnostik
        state_color: true
        show_header_toggle: false
        entities:
          - type: section
            label: Systemhälsa
          - entity: binary_sensor.svotc_inputs_healthy
            name: Temperatursensorer OK
            icon: mdi:thermometer-check
          - entity: binary_sensor.svotc_price_available
            name: Prisdata tillgänglig
            icon: mdi:cash-check
          - type: divider
          - type: section
            label: Timing
          - entity: sensor.svotc_minutes_to_next_brake_start
            name: Minuter till nästa dyr period
            icon: mdi:timer-outline
          - entity: sensor.svotc_prebrake_window_min
            name: Förbromsfönster (min)
            icon: mdi:window-open
          - type: divider
          - type: section
            label: Prisstatus (flöde)
          - entity: sensor.svotc_raw_price_state
            name: Råprisstatus (direkt)
            icon: mdi:flash
          - entity: input_text.svotc_pending_price_state
            name: Pending status (väntar)
            icon: mdi:timer-sand
          - entity: input_text.svotc_last_price_state
            name: Stabil status (aktiv)
            icon: mdi:lock-check
          - type: divider
          - type: section
            label: Tidsstämplar
          - entity: input_datetime.svotc_last_price_state_changed
            name: Pending sedan
            icon: mdi:clock-start
          - entity: input_datetime.svotc_brake_phase_changed
            name: Bromsfas startade
            icon: mdi:clock-start
      - type: markdown
        title: 📋 System Status
        content: >
          ### SVOTC Statusöversikt

          **Driftsläge:** `{{ states('input_select.svotc_mode') }}`
          **Aktuell Strategi:** `{{ states('input_text.svotc_reason_code') }}`

          ---

          #### Temperaturer
          - 🏠 Inne: **{{ states('sensor.svotc_src_indoor') }}°C** (mål: {{ states('sensor.svotc_dynamic_target_temperature') }}°C)
          - 🌡️ Ute (verklig): **{{ states('sensor.svotc_src_outdoor') }}°C**
          - 🎯 Ute (virtuell → VP): **{{ states('sensor.svotc_virtual_outdoor_temperature') }}°C**
          - 📊 Offset tillämpad: **{{ states('input_number.svotc_applied_offset_c') }}°C**

          ---

          #### Prisstatus
          - 💵 Pris nu: **{{ states('sensor.svotc_current_price') }} SEK/kWh**
          - 📉 P30 (billig): **{{ states('sensor.svotc_p30') }} SEK/kWh**
          - 📈 P80 (dyr): **{{ states('sensor.svotc_p80') }} SEK/kWh**
          - 🚦 Status: **{{ states('input_text.svotc_last_price_state') }}**
          - ⏱️ Nästa dyr period om: **{{ states('sensor.svotc_minutes_to_next_brake_start') }} min**

          ---

          #### Kontrollstatus
          - 🛡️ Komfortskydd: **{% if is_state('binary_sensor.svotc_comfort_guard_active', 'on') %}🟢 AKTIVT{% else %}⚪ Inaktivt{% endif %}**
          - 🔄 Bromsfas: **{{ states('input_text.svotc_brake_phase') }}**
          - 💪 Förbromsstyrka: **{{ (states('sensor.svotc_prebrake_strength') | float * 100) | round(0) }}%**

          ---

          #### Systemhälsa
          - ✅ Sensorer: **{% if is_state('binary_sensor.svotc_inputs_healthy','on') %}OK{% else %}⚠️ PROBLEM{% endif %}**
          - 💰 Prisdata: **{% if is_state('binary_sensor.svotc_price_available','on') %}OK{% else %}⚠️ SAKNAS{% endif %}**

          ---

          *Senast uppdaterad: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}*
  - type: grid
    cards:
      - type: entities
        title: 📊 Aktuell Status
        state_color: true
        show_header_toggle: false
        entities:
          - type: section
            label: Temperaturer
          - entity: sensor.svotc_src_indoor
            name: Inomhus
            icon: mdi:home-thermometer
          - entity: sensor.svotc_dynamic_target_temperature
            name: Måltemperatur
            icon: mdi:target
          - entity: sensor.svotc_src_outdoor
            name: Utomhus (verklig)
            icon: mdi:thermometer
          - entity: sensor.svotc_virtual_outdoor_temperature
            name: Utomhus (virtuell → VP)
            icon: mdi:thermometer-chevron-up
            secondary_info: last-changed
          - type: divider
          - type: section
            label: Prisstyrning
          - entity: sensor.svotc_current_price
            name: Elpris nu
            icon: mdi:currency-usd
          - entity: sensor.svotc_p30
            name: P30 (billig under)
            icon: mdi:arrow-down-bold-circle
          - entity: sensor.svotc_p80
            name: P80 (dyr över)
            icon: mdi:arrow-up-bold-circle
          - entity: input_text.svotc_last_price_state
            name: Prisstatus (stabil)
            icon: mdi:state-machine
          - entity: input_text.svotc_brake_phase
            name: Bromsfas
            icon: mdi:timeline-clock
          - type: divider
          - type: section
            label: Offset & Kontroll
          - entity: input_number.svotc_requested_offset_c
            name: Begärd offset
            icon: mdi:delta
          - entity: input_number.svotc_applied_offset_c
            name: Tillämpad offset
            icon: mdi:slope-uphill
          - entity: sensor.svotc_prebrake_strength
            name: Förbromsstyrka (0-1)
            icon: mdi:speedometer
      - type: entities
        title: 🔧 Entitetskonfiguration
        state_color: true
        show_header_toggle: false
        entities:
          - entity: input_text.svotc_entity_indoor
            name: Inomhustemperatur-sensor
            icon: mdi:home-thermometer-outline
          - entity: input_text.svotc_entity_outdoor
            name: Utomhustemperatur-sensor
            icon: mdi:thermometer
          - entity: input_text.svotc_entity_price
            name: Prisentitet (Nordpool)
            icon: mdi:currency-usd
          - entity: input_text.svotc_notify_service
      - type: entities
        title: ⚙️ Avancerade Inställningar
        state_color: true
        show_header_toggle: false
        entities:
          - type: section
            label: Dwell Times (Pristösklar)
          - entity: input_number.svotc_price_dwell_cheap_to_neutral_min
            name: Billig → Neutral (min)
            icon: mdi:arrow-right-bold
          - entity: input_number.svotc_price_dwell_neutral_to_brake_min
            name: Neutral → Broms (min)
            icon: mdi:arrow-right-bold
          - entity: input_number.svotc_price_dwell_brake_to_neutral_min
            name: Broms → Neutral (min)
            icon: mdi:arrow-left-bold
          - entity: input_number.svotc_price_dwell_neutral_to_cheap_min
            name: Neutral → Billig (min)
            icon: mdi:arrow-left-bold
          - type: divider
          - type: section
            label: Bromsfaser (Duration)
          - entity: input_number.svotc_brake_rampup_duration_min
            name: Ramp-up tid (min)
            icon: mdi:slope-uphill
          - entity: input_number.svotc_brake_hold_duration_min
            name: Hold tid (min)
            icon: mdi:minus-circle
          - entity: input_number.svotc_brake_rampdown_duration_min
            name: Ramp-down tid (min)
            icon: mdi:slope-downhill
          - type: divider
          - type: section
            label: Rate Limiting
          - entity: input_number.svotc_max_delta_per_step_c
            name: Max förändring per minut (°C)
            icon: mdi:speedometer
max_columns: 4
```

#### 5.4.2 SVOTC Debug (view)

```yaml
title: SVOTC Debug
type: sections
cards: []
sections:
  - type: grid
    cards:
      - type: entities
        title: 🚦 Systemstatus
        show_header_toggle: false
        entities:
          - entity: input_select.svotc_mode
            name: Driftsläge
          - entity: binary_sensor.svotc_inputs_healthy
            name: Sensorer OK
          - entity: binary_sensor.svotc_price_available
            name: Prisdata OK
          - entity: binary_sensor.svotc_comfort_guard_active
            name: Komfortskydd
          - entity: input_text.svotc_reason_code
            name: Reason code
      - type: entities
        title: 🌡️ Temperaturer
        show_header_toggle: false
        entities:
          - entity: sensor.svotc_src_indoor
            name: Inomhus (källa)
            secondary_info: last-changed
          - entity: sensor.svotc_dynamic_target_temperature
            name: Måltemperatur
            secondary_info: last-changed
          - entity: sensor.svotc_src_outdoor
            name: Utomhus (källa)
            secondary_info: last-changed
          - entity: sensor.svotc_virtual_outdoor_temperature
            name: Virtuell ute (→VP)
            secondary_info: last-changed
          - entity: input_number.svotc_requested_offset_c
            name: Requested offset (°C)
            secondary_info: last-changed
          - entity: input_number.svotc_applied_offset_c
            name: Applied offset (°C)
            secondary_info: last-changed
      - type: entities
        title: 💰 Pris & percentiler
        show_header_toggle: false
        entities:
          - entity: sensor.svotc_src_current_price
            name: Råpris (källa)
            secondary_info: last-changed
          - entity: sensor.svotc_current_price
            name: Current price
            secondary_info: last-changed
          - entity: sensor.svotc_p30
            name: P30 (billig)
            secondary_info: last-changed
          - entity: sensor.svotc_p80
            name: P80 (dyr)
            secondary_info: last-changed
      - type: entities
        title: 🔧 Entity mapping
        show_header_toggle: false
        entities:
          - entity: input_text.svotc_entity_indoor
            name: Indoor sensor entity
          - entity: input_text.svotc_entity_outdoor
            name: Outdoor sensor entity
          - entity: input_text.svotc_entity_price
            name: Price sensor entity
      - type: history-graph
        title: 📊 Temperaturhistorik (8h)
        hours_to_show: 8
        entities:
          - entity: sensor.svotc_src_indoor
            name: Inne
          - entity: sensor.svotc_src_outdoor
            name: Ute (verklig)
          - entity: sensor.svotc_virtual_outdoor_temperature
            name: Virtuell ute
          - entity: sensor.svotc_dynamic_target_temperature
            name: Måltemp
      - type: history-graph
        title: 📈 Offset-historik (8h)
        hours_to_show: 8
        entities:
          - entity: input_number.svotc_requested_offset_c
            name: Requested
          - entity: input_number.svotc_applied_offset_c
            name: Applied
  - type: grid
    cards:
      - type: entities
        title: 🔄 Price state machine
        show_header_toggle: false
        entities:
          - entity: sensor.svotc_raw_price_state
            name: Raw state
          - entity: input_text.svotc_pending_price_state
            name: Pending state
          - entity: input_text.svotc_last_price_state
            name: Stable state
          - entity: input_datetime.svotc_last_price_state_changed
            name: Pending sedan
      - type: entities
        title: 🛑 Brake phase & look-ahead
        show_header_toggle: false
        entities:
          - entity: input_text.svotc_brake_phase
            name: Bromsfas
          - entity: input_datetime.svotc_brake_phase_changed
            name: Fas startade
          - entity: sensor.svotc_minutes_to_next_brake_start
            name: Min till dyr period
          - entity: sensor.svotc_prebrake_window_min
            name: Prebrake window (min)
          - entity: sensor.svotc_prebrake_strength
            name: Prebrake strength
      - type: entities
        title: 🛡️ / ⏱️ / ⚡ Tuning
        show_header_toggle: false
        entities:
          - entity: input_number.svotc_comfort_guard_activate_below_c
            name: Guard activate Δ (°C)
          - entity: input_number.svotc_comfort_guard_deactivate_above_c
            name: Guard deactivate Δ (°C)
          - type: divider
          - entity: input_number.svotc_price_dwell_cheap_to_neutral_min
            name: Dwell Cheap → Neutral (min)
          - entity: input_number.svotc_price_dwell_neutral_to_brake_min
            name: Dwell Neutral → Brake (min)
          - entity: input_number.svotc_price_dwell_brake_to_neutral_min
            name: Dwell Brake → Neutral (min)
          - entity: input_number.svotc_price_dwell_neutral_to_cheap_min
            name: Dwell Neutral → Cheap (min)
          - type: divider
          - entity: input_number.svotc_brake_rampup_duration_min
            name: Brake ramp-up (min)
          - entity: input_number.svotc_brake_hold_duration_min
            name: Brake hold (min)
          - entity: input_number.svotc_brake_rampdown_duration_min
            name: Brake ramp-down (min)
          - type: divider
          - entity: input_number.svotc_max_delta_per_step_c
            name: Max Δ per min (°C)
          - entity: input_number.svotc_brake_hold_offset_c
            name: Brake hold offset (°C)
          - entity: input_number.svotc_heat_aggressiveness
            name: Heat aggressiveness
          - entity: input_number.svotc_brake_aggressiveness
            name: Brake aggressiveness
      - type: history-graph
        title: 💰 Prishistorik (24h)
        hours_to_show: 24
        entities:
          - entity: sensor.svotc_current_price
            name: Pris
          - entity: sensor.svotc_p30
            name: P30
          - entity: sensor.svotc_p80
            name: P80
```

---

## 6) Felsökning

### 🔴 Det händer inget

Kontrollera i denna ordning:

1. `input_select.svotc_mode` = **Smart**
2. `binary_sensor.svotc_inputs_healthy` = **on**
3. Entity mapping:

   * `input_text.svotc_entity_indoor`
   * `input_text.svotc_entity_outdoor`
   * `input_text.svotc_entity_price`
4. Läs `input_text.svotc_reason_code`:

   * `OFF` → Mode = Off
   * `PASS_THROUGH` → Mode = PassThrough
   * `MISSING_INPUTS_FREEZE` → temp-sensor saknas/är trasig

### 🔴 Priset verkar “dött”

1. `binary_sensor.svotc_price_available` = **on**?

2. `sensor.svotc_current_price` visar rimligt värde?

3. Verifiera attribut på prissensorn:

   * Developer Tools → States → din prissensor
   * ska ha `current_price`, `raw_today`, `raw_tomorrow`

4. Om `sensor.svotc_p30` och `sensor.svotc_p80` är `none`:

   * SVOTC kräver minst **20** priser från `raw_today + raw_tomorrow`
   * vanligt när morgondagens priser inte är publicerade än
   * lösning: vänta, eller kör **ComfortOnly** temporärt

---

## 7) Hur systemet fungerar

### 🏗️ Arkitektur (layers)

SVOTC är byggt enligt “layered control”:

```
1) SENSING (validerade inputs)
   - sensor.svotc_src_indoor
   - sensor.svotc_src_outdoor
   - sensor.svotc_src_current_price

2) RAW PRICE STATE (instant, ingen memory)
   - sensor.svotc_raw_price_state

3) DWELL (raw → stable, anti-spikar)
   - automation: SVOTC Price dwell
   - output: input_text.svotc_last_price_state

4) FORWARD LOOK (prebrake_strength 0..1)
   - sensor.svotc_prebrake_strength

5) BRAKE PHASE (minne; undvik “starta om”)
   - input_text.svotc_brake_phase
   - automation: SVOTC Brake phase controller

6) ENGINE (requested → ramp-limited applied)
   - automation: SVOTC Engine
   - output:
     - input_number.svotc_requested_offset_c
     - input_number.svotc_applied_offset_c
   - slutresultat:
     - sensor.svotc_virtual_outdoor_temperature
```

### 🧮 Offset-beräkning (Engine)

**Comfort term (negativ = mer värme)**

* om comfort guard aktiv:

  * `comfort_term = -(heat_aggressiveness * 0.4)`
  * heat=5 → −2.0°C

**Price term (positiv = mindre värme)**

* i Smart och om comfort guard inte aktiv:

  * `price_term = brake_hold_offset * prebrake_strength`
  * hold=2.0 och strength=1.0 → +2.0°C

**Requested**

* `requested = comfort_term + price_term`

**Applied (ramp-limited)**

* begränsas av `svotc_max_delta_per_step_c`

**Virtuell utetemp**

* `virtual_outdoor = real_outdoor + applied`

---

## 8) Rekommenderade startvärden (defaults)

### 8.1 Mode

* `svotc_mode` = **Smart**

### 8.2 Comfort guard

| Parameter                                | Värde | Förklaring           |
| ---------------------------------------- | ----: | -------------------- |
| `svotc_comfort_temperature`              |  21.0 | Måltemperatur        |
| `svotc_comfort_guard_activate_below_c`   |   0.8 | Guard ON vid 20.2°C  |
| `svotc_comfort_guard_deactivate_above_c` |   0.4 | Guard OFF vid 20.6°C |
| `svotc_heat_aggressiveness`              |     2 | Boost ≈ −0.8°C       |

### 8.3 Price braking

| Parameter                    | Värde | Förklaring              |
| ---------------------------- | ----: | ----------------------- |
| `svotc_brake_aggressiveness` |     2 | prebrake-fönster 60 min |
| `svotc_brake_hold_offset_c`  |   2.0 | max broms +2.0°C        |

Aggressiveness → fönster:

| Level | Fönster |
| ----: | ------: |
|     0 |       0 |
|     1 |      30 |
|     2 |      60 |
|     3 |      90 |
|     4 |     105 |
|     5 |     120 |

### 8.4 Dwell (stabilitet)

Exempel:

| Transition      | Tid (min) |
| --------------- | --------: |
| neutral → brake |        30 |
| brake → neutral |        15 |
| neutral → cheap |        20 |
| cheap → neutral |        15 |

### 8.5 Brake phase durations

| Phase    | Tid (min) |
| -------- | --------: |
| rampup   |        30 |
| hold     |        60 |
| rampdown |        45 |

### 8.6 Rate limiting

* `svotc_max_delta_per_step_c` = **0.10** °C/min (mjukt)

---

## 9) Reason codes (vad betyder de?)

| Kod                   | Betydelse                            |
| --------------------- | ------------------------------------ |
| INIT                  | Startläge                            |
| OFF                   | Mode = Off                           |
| PASS_THROUGH          | Mode = PassThrough                   |
| COMFORT_ONLY          | Endast komfortskydd                  |
| MISSING_INPUTS_FREEZE | Temp-input saknas → applied fryser   |
| COMFORT_GUARD         | Komfortskydd värmer (negativ offset) |
| MCP_BLOCKS_BRAKE      | Guard blockerar prisbroms            |
| PRICE_BRAKE           | Prisbroms aktiv (positiv offset)     |
| NEUTRAL               | Normalläge                           |

---

## 10) FAQ

### Styr SVOTC direkt värmepumpen?

Nej. SVOTC skapar `sensor.svotc_virtual_outdoor_temperature` som du mappar in i din integration/metod för att påverka värmepumpen.

### Requested vs Applied?

| Typ       | Beskrivning                                   |
| --------- | --------------------------------------------- |
| Requested | Vad logiken vill ha                           |
| Applied   | Vad som faktiskt gäller efter rampbegränsning |

---

## 11) Avancerat: Brake phase timing

### 📊 Visuell timeline

```
Tid:     0 ─── 30 ───────── 90 ───── 135 ──→
Phase:  idle | ramping_up | holding | ramping_down | idle
Offset:  0 →→→→→ hold_offset →→ hold_offset →→→→→ 0
```

Parametrar:

* rampup   = 30 min (0 → hold_offset)
* hold     = 60 min
* rampdown = 45 min (hold_offset → 0)

⚠️ Om stable price state slutar vara `brake` så tvingas phase till `idle`.

---

## 12) License / Disclaimer

⚠️ Använd på egen risk.
SVOTC påverkar värme indirekt via virtuell utetemperatur. Testa och verifiera beteendet i din miljö innan du litar på det i skarpt läge.

**Rekommendation för säker start**

1. Börja försiktigt:

   * `brake_hold_offset_c` = 1.0°C
   * `max_delta_per_step_c` = 0.10°C/min
   * comfort guard: activate 0.8 / deactivate 0.4
2. Övervaka första veckan:

   * `sensor.svotc_virtual_outdoor_temperature`
   * `input_number.svotc_applied_offset_c`
   * `sensor.svotc_src_indoor`
   * `input_text.svotc_reason_code`
3. Öka aggressivitet stegvis:

   * vecka 2: hold_offset 2.0
   * vecka 3: brake_aggressiveness 3
   * därefter: finjustera guard/ramp


---

## 12) License / Disclaimer

⚠️ Använd på egen risk.
SVOTC påverkar värme indirekt via virtuell utetemperatur. Testa och verifiera beteendet i din miljö innan du litar på det i skarpt läge.

---

## Credits

SVOTC – Stable Core Edition (2026-02)
Designad för:

* 🏠 Svenska villor med värmepump
* ⚡ Nordpool/Tibber spotpris-styrning
* 🎚️ Mjuk, förutsägbar och förklarbar kontroll
