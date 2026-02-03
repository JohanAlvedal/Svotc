# SVOTC - Förbättringar och förändringar

## Sammanfattning av alla 6 förbättringarna

---

## 1. ✅ Brake phase manager triggas nu regelbundet

### Problem i original:
```yaml
- alias: "SVOTC Brake phase manager"
  trigger:
    - platform: state  # Bara vid tillståndsändringar!
```

### Lösning:
```yaml
- alias: "SVOTC Brake phase manager (improved)"
  trigger:
    - platform: time_pattern
      minutes: "/1"      # ← NU KONTROLLERAS VARJE MINUT
    - platform: state
      entity_id:
        - input_text.svotc_last_price_state
        # ...
```

**Resultat**: Systemet kan nu automatiskt gå mellan faser även om inga externa state-changes händer.

---

## 2. ✅ Komplett state machine för brake phases

### Nya komponenter:

#### A) Input numbers för tidstyrning:
```yaml
svotc_brake_rampup_duration_min: 30      # Hur länge ramping_up pågår
svotc_brake_hold_duration_min: 60        # Hur länge holding pågår
svotc_brake_rampdown_duration_min: 45    # Hur länge ramping_down pågår
```

#### B) Progress-sensor:
```yaml
- name: "SVOTC Brake phase progress"
  state: >
    {% set phase = states('input_text.svotc_brake_phase') %}
    {% set changed = states('input_datetime.svotc_brake_phase_changed') %}
    {% set elapsed = (now() - changed) / 60 %}
    {% set duration = ... %}  # Hämta från input_number beroende på fas
    {{ (elapsed / duration * 100) | clamp(0, 100) }}
```

#### C) State machine logik i automation:
```yaml
- choose:
    # idle → ramping_up (när brake behövs)
    - conditions: "{{ want_brake and phase == 'idle' }}"
      sequence: [växla till ramping_up]
    
    # ramping_up → holding (efter 100% progress)
    - conditions: "{{ phase == 'ramping_up' and progress >= 100 }}"
      sequence: [växla till holding]
    
    # holding → ramping_down (efter X min ELLER om brake inte längre behövs)
    - conditions: "{{ phase == 'holding' and (progress >= 100 or not want_brake) }}"
      sequence: [växla till ramping_down]
    
    # ramping_down → idle (efter 100% progress)
    - conditions: "{{ phase == 'ramping_down' and progress >= 100 }}"
      sequence: [växla till idle]
    
    # Avbrott: ramping_up → ramping_down (om brake inte längre behövs)
    - conditions: "{{ phase == 'ramping_up' and not want_brake }}"
      sequence: [hoppa direkt till ramping_down]
```

#### D) Gradvis offset i Engine:
```yaml
brake_multiplier: >
  {% if phase == 'ramping_up' %}
    {{ (progress / 100) | clamp(0, 1) }}      # 0% → 100% under ramp-up
  {% elif phase == 'holding' %}
    1.0                                        # Full kraft
  {% elif phase == 'ramping_down' %}
    {{ (1 - progress / 100) | clamp(0, 1) }}  # 100% → 0% under ramp-down
  {% else %}
    0
  {% endif %}

brake_with_prebrake = brake_base * (brake_multiplier + prebrake)
```

**Resultat**: 
- Mjuka övergångar istället för abrupt på/av
- Förutsägbar timing
- Visuell feedback via progress-sensor

---

## 3. ✅ Hysteres i comfort guard

### Problem i original:
```yaml
# Samma tröskel för av och på → oscillation!
{{ indoor < (target - db) }}
```

**Exempel:**
- Target = 21°C, deadband = 0.8°C
- Vid 20.2°C: Guard PÅ
- Vid 20.21°C: Guard AV (!!!)
- Systemet flaxar mellan på/av

### Lösning:
```yaml
input_number:
  svotc_comfort_guard_activate_below_c:
    initial: 0.8      # Aktivera när temp < target - 0.8
  
  svotc_comfort_guard_deactivate_above_c:
    initial: 0.4      # Deaktivera när temp > target - 0.4

# I binary_sensor:
- name: "SVOTC Comfort guard active"
  state: >
    {% set current = is_state('binary_sensor.svotc_comfort_guard_active','on') %}
    {% if current %}
      # Guard är på: kräv att temp stiger till target-0.4 för att släppa
      {{ indoor < (target - deactivate_above) }}
    {% else %}
      # Guard är av: kräv att temp sjunker till target-0.8 för att aktivera
      {{ indoor < (target - activate_below) }}
    {% endif %}
```

**Exempel med nya värden:**
- Target = 21°C
- Aktivera vid: < 20.2°C (21 - 0.8)
- Deaktivera vid: > 20.6°C (21 - 0.4)
- **Hysteres-zon: 20.2°C → 20.6°C** = 0.4°C margin

**Resultat**: Inga oscillationer, stabilt beteende.

---

## 4. ✅ Validering av extrema sensorvärden + fail-safe

### A) Validering i källsensorer:

#### Indoor temp:
```yaml
- name: "SVOTC Src Indoor"
  state: >
    {% set val = states(ent) | float(none) %}
    # VALIDERING: Rimliga inomhusvärden 10-35°C
    {% if val is number and val >= 10 and val <= 35 %}
      {{ val | round(2) }}
    {% else %}
      {{ this.state if this.state | is_number else none }}  # Behåll förra värdet
    {% endif %}
```

#### Outdoor temp:
```yaml
state: >
  {% set val = states(ent) | float(none) %}
  # VALIDERING: Rimliga utomhusvärden -40 till +45°C
  {% if val is number and val >= -40 and val <= 45 %}
    {{ val | round(2) }}
  {% else %}
    {{ this.state if this.state | is_number else none }}
  {% endif %}
```

#### Price:
```yaml
state: >
  {% set p = state_attr(ent, 'current_price') %}
  # VALIDERING: Rimliga elpriser 0-10 SEK/kWh
  {% if p is number and p >= 0 and p <= 10 %}
    {{ p | round(3) }}
  {% else %}
    {{ this.state | float(0) }}
  {% endif %}
```

### B) Health monitoring:
```yaml
- name: "SVOTC All sensors healthy"
  state: >
    {{ is_state('binary_sensor.svotc_price_available','on')
       and (states('sensor.svotc_src_indoor') | is_number)
       and (states('sensor.svotc_src_outdoor') | is_number) }}
```

### C) Fail-safe automation:
```yaml
- alias: "SVOTC Fail-safe handler"
  trigger:
    - platform: time_pattern
      minutes: "/1"
  action:
    - choose:
        # Om sensorer saknas > 5 min → aktivera fail-safe
        - conditions: "{{ not all_ok and not fail_safe_active }}"
          sequence:
            - delay: { minutes: 5 }
            - service: input_boolean.turn_on
              target: { entity_id: input_boolean.svotc_fail_safe_active }
            - service: input_number.set_value
              data: { value: 0 }  # ← NOLLSTÄLL OFFSET
            - [skicka notifikation]
        
        # Om allt OK > 3 min → avaktivera fail-safe
        - conditions: "{{ all_ok and fail_safe_active }}"
          sequence:
            - delay: { minutes: 3 }
            - service: input_boolean.turn_off
              target: { entity_id: input_boolean.svotc_fail_safe_active }
```

### D) Engine respekterar fail-safe:
```yaml
req: >
  {% if fail_safe or indoor is not number or mode in ['Off', 'PassThrough'] %}
    0  # ← SÄKERT LÄGE
  {% else %}
    [normal beräkning]
  {% endif %}
```

**Resultat**: 
- Felaktiga sensorvärden ignoreras
- Systemet går i säkert läge vid långvariga fel
- Automatisk återställning när allt fungerar

---

## 5. ✅ Separata dwell-tider per övergång

### Problem i original:
```yaml
dwell: 30 minuter  # Samma för ALLA övergångar
```

**Nackdel:** 
- cheap → neutral: 30 min kan vara för långt (du missar billig el)
- neutral → brake: 30 min kan vara för kort (onödig aktivering)

### Lösning:
```yaml
input_number:
  svotc_price_dwell_cheap_to_neutral_min: 20
  svotc_price_dwell_neutral_to_brake_min: 30
  svotc_price_dwell_brake_to_neutral_min: 15
  svotc_price_dwell_neutral_to_cheap_min: 10
```

### Dynamisk dwell i automation:
```yaml
dwell: >
  {% set stable = states('input_text.svotc_last_price_state') %}
  {% set raw = states('sensor.svotc_raw_price_state') %}
  
  {% if stable == 'cheap' and raw == 'neutral' %}
    {{ states('input_number.svotc_price_dwell_cheap_to_neutral_min') | int(20) }}
  
  {% elif stable == 'neutral' and raw == 'brake' %}
    {{ states('input_number.svotc_price_dwell_neutral_to_brake_min') | int(30) }}
  
  {% elif stable == 'brake' and raw == 'neutral' %}
    {{ states('input_number.svotc_price_dwell_brake_to_neutral_min') | int(15) }}
  
  {% elif stable == 'neutral' and raw == 'cheap' %}
    {{ states('input_number.svotc_price_dwell_neutral_to_cheap_min') | int(10) }}
  
  {% else %}
    20
  {% endif %}
```

**Förslag på värden:**

| Övergång | Dwell | Motivering |
|----------|-------|-----------|
| cheap → neutral | 20 min | Medellång - inte brått att sluta värma extra |
| neutral → brake | **30 min** | Långsam - undvik felaktivering av dyra bromsar |
| brake → neutral | 15 min | Snabb - börja värma igen när priset sjunker |
| neutral → cheap | **10 min** | Snabbast - börja värma extra snabbt vid låga priser |

**Resultat**: Optimal respons för varje situation.

---

## 6. ✅ Logging och historik

### A) Konfigurerbar notifier:
```yaml
input_text:
  svotc_notifier:
    name: "SVOTC Notifier service"
    initial: "notify.notify"  # ← Användaren kan ändra till sin notifier

# I automation:
- service: "{{ notifier }}"
  data:
    title: "SVOTC: Saknar input"
    message: "Saknar: {{ missing_list }}"
```

### B) Spåra offset-användning per dag:
```yaml
input_number:
  svotc_total_offset_hours_today: 0-24 timmar
  svotc_max_offset_hours_per_day: 18 (standard)

input_datetime:
  svotc_offset_hours_reset: senaste reset

# Automation:
- alias: "SVOTC Track daily offset hours"
  trigger:
    - platform: time_pattern
      minutes: "/1"
  action:
    # Reset vid midnatt
    # Räkna upp om |offset| > 0.5°C
```

**Användning:**
- Se hur många timmar per dag systemet använder stor offset
- Sätt max-gräns för att skydda värmepumpen
- Analysera effektivitet över tid

### C) Recorder configuration:
```yaml
recorder:
  include:
    entities:
      - sensor.svotc_src_indoor
      - sensor.svotc_src_outdoor
      - sensor.svotc_src_current_price
      - input_number.svotc_requested_offset_c
      - input_number.svotc_applied_offset_c
      - input_text.svotc_reason_code
      - input_text.svotc_brake_phase
      - sensor.svotc_brake_phase_progress
      - binary_sensor.svotc_comfort_guard_active
      - input_number.svotc_total_offset_hours_today
      - binary_sensor.svotc_all_sensors_healthy
      - input_boolean.svotc_fail_safe_active
```

**Användning i Lovelace:**
```yaml
type: history-graph
entities:
  - entity: sensor.svotc_current_price
    name: Elpris
  - entity: input_number.svotc_applied_offset_c
    name: Applied offset
  - entity: sensor.svotc_src_indoor
    name: Inomhustemp
  - entity: input_text.svotc_brake_phase
    name: Fas
hours_to_show: 24
```

**Resultat**: 
- Full historik för analys
- Grafisk visualisering av systemets beteende
- Felsökning blir enkel

---

## Sammanfattning av alla förbättringar

| # | Förbättring | Nyckelfunktion |
|---|-------------|----------------|
| 1 | Time pattern trigger | Brake phase manager körs varje minut |
| 2 | State machine | Automatisk fasövergång med progress (ramping_up → holding → ramping_down → idle) |
| 3 | Hysteres | Comfort guard: olika trösklar för på (0.8°C) och av (0.4°C) |
| 4 | Validering + fail-safe | Felaktiga värden ignoreras, offset nollställs vid långvariga fel |
| 5 | Separata dwell-tider | cheap→neutral: 20 min, neutral→brake: 30 min, brake→neutral: 15 min, neutral→cheap: 10 min |
| 6 | Logging | Recorder för historik, konfigurerbar notifier, spåra offset-timmar per dag |

---

## Installation och migration

### 1. Backup:
```bash
# Kopiera din gamla config
cp packages/svotc.yaml packages/svotc_backup.yaml
```

### 2. Ersätt fil:
```bash
# Kopiera nya filen
cp svotc_improved.yaml packages/svotc.yaml
```

### 3. Check config:
```bash
# I Home Assistant Developer Tools → YAML
# Klicka "Check Configuration"
```

### 4. Restart:
```bash
# Starta om Home Assistant
```

### 5. Kalibrera nya parametrar:

#### Hysteres (börja här):
- `svotc_comfort_guard_activate_below_c`: 0.8°C
- `svotc_comfort_guard_deactivate_above_c`: 0.4°C

#### Brake timers:
- `svotc_brake_rampup_duration_min`: 30 min
- `svotc_brake_hold_duration_min`: 60 min
- `svotc_brake_rampdown_duration_min`: 45 min

#### Dwell-tider (optimera efter behov):
- cheap→neutral: 20 min
- neutral→brake: 30 min
- brake→neutral: 15 min
- neutral→cheap: 10 min

### 6. Övervaka i 24h:
- Kolla grafer i history
- Se att state machine fungerar
- Verifiera att comfort guard inte flaxar

---

## Felsökning

### Problem: "Brake phase fastnar i ramping_up"
**Lösning**: Kontrollera att `input_datetime.svotc_brake_phase_changed` är satt. Om inte, trigga manuellt:
```yaml
service: input_datetime.set_datetime
target: { entity_id: input_datetime.svotc_brake_phase_changed }
data: { datetime: "{{ now().strftime('%Y-%m-%d %H:%M:%S') }}" }
```

### Problem: "Comfort guard flaxar fortfarande"
**Lösning**: Öka hysteres-skillnaden:
- Activate: 1.0°C (istället för 0.8)
- Deactivate: 0.3°C (istället för 0.4)

### Problem: "Fail-safe aktiveras hela tiden"
**Lösning**: Kontrollera sensorernas värden:
```yaml
# Developer Tools → Template
{{ states('sensor.svotc_src_indoor') }}  # Ska vara 10-35
{{ states('sensor.svotc_src_outdoor') }} # Ska vara -40 till 45
{{ state_attr('sensor.nordpool_tibber', 'current_price') }} # Ska vara 0-10
```

---

## Nya Lovelace-kort (rekommenderade)

### Översiktskort:
```yaml
type: entities
title: SVOTC Status
entities:
  - entity: sensor.svotc_status
  - entity: input_text.svotc_brake_phase
    name: Fas
  - entity: sensor.svotc_brake_phase_progress
    name: Progress
  - entity: input_number.svotc_applied_offset_c
    name: Offset
  - entity: binary_sensor.svotc_comfort_guard_active
    name: Comfort guard
  - entity: input_boolean.svotc_fail_safe_active
    name: Fail-safe
```

### Graf för analys:
```yaml
type: history-graph
title: SVOTC 24h
entities:
  - entity: sensor.svotc_current_price
  - entity: input_number.svotc_applied_offset_c
  - entity: sensor.svotc_src_indoor
  - entity: sensor.svotc_virtual_outdoor_temperature
hours_to_show: 24
```

### Inställningar:
```yaml
type: entities
title: SVOTC Tuning
entities:
  - entity: input_select.svotc_mode
  - entity: input_number.svotc_brake_aggressiveness
  - entity: input_number.svotc_heat_aggressiveness
  - entity: input_number.svotc_comfort_temperature
  - type: divider
  - entity: input_number.svotc_comfort_guard_activate_below_c
  - entity: input_number.svotc_comfort_guard_deactivate_above_c
  - type: divider
  - entity: input_number.svotc_brake_rampup_duration_min
  - entity: input_number.svotc_brake_hold_duration_min
  - entity: input_number.svotc_brake_rampdown_duration_min
```

---

## Slutsats

Den nya versionen är:
- ✅ Mer stabil (hysteres, validering)
- ✅ Mer förutsägbar (state machine, timers)
- ✅ Mer säker (fail-safe, clamp)
- ✅ Mer flexibel (separata dwell-tider)
- ✅ Mer transparent (logging, progress)

**Rekommendation**: Testa i 1 vecka och justera parametrar baserat på ditt hus och dina priser.
