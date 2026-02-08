# SVOTC – Stable Core Edition (2026-02)

**Smart Virtual Outdoor Temperature Control**

SVOTC styr din värmepump **indirekt** genom att skapa en *virtuell utetemperatur* som värmepumpen använder för sina kurvor.

I stället för att slå av/på pumpen eller ändra börvärden aggressivt, justerar SVOTC en **offset (°C)** som adderas till verklig utetemperatur:

- **Positiv offset** (+2°C) → "varmare ute" → värmepumpen drar ner värme (pris-broms)
- **Negativ offset** (−1°C) → "kallare ute" → värmepumpen drar upp värme (komfort-skydd)

**Designmål:**
- 🎯 Stabilt (ingen fladdrig prisspik-styrning)
- 📊 Förklarbart (reason codes visar varför beslut tas)
- 🏗️ Layered arkitektur: sensing → stabilisering → planering → ramp-limited execution

---

## 📋 Innehållsförteckning

1. [Krav](#1-krav)
2. [Installation](#2-installation)
3. [Första gången du kör SVOTC](#3-första-gången-du-kör-svotc-5-minuters-setup)
4. [Entity mapping](#4-entity-mapping-viktigast-att-ändra)
5. [Lovelace dashboard](#5-lovelace-dashboard)
6. [Felsökning](#6-felsökning)
7. [Hur systemet fungerar](#7-hur-systemet-fungerar)
8. [Rekommenderade startvärden](#8-rekommenderade-startvärden-defaults)
9. [Reason codes](#9-reason-codes-vad-betyder-de)
10. [FAQ](#10-faq)
11. [Avancerat: Brake phase timing](#11-avancerat-brake-phase-timing)
12. [License](#12-license--disclaimer)

---

## 1) Krav

Du behöver:
- ✅ **Home Assistant** (2024.1 eller senare rekommenderas)
- ✅ **Innetemperatur-sensor** (t.ex. `sensor.inomhusmedel`)
- ✅ **Utetemperatur-sensor** (t.ex. `sensor.temperatur_nu`)
- ✅ **Elpris-sensor** (Nordpool/Tibber HACS-stil) med attribut:
  - `current_price` (aktuellt pris)
  - `raw_today` (lista av `{start, end, value}`)
  - `raw_tomorrow` (lista av `{start, end, value}`)

> **Standard i koden:** `sensor.nordpool_tibber`

---

## 2) Installation

### Steg 1: Lägg till YAML-filen
```bash
# Lägg filen i packages-mappen
/config/packages/svotc.yaml


Steg 2: Aktivera packages
I configuration.yaml, lägg till (om inte redan aktiverat):

homeassistant:
  packages: !include_dir_named packages


Steg 3: Starta om Home Assistant
	∙	Gå till Inställningar → System → Starta om
	∙	Vänta ~1 minut
Steg 4: Verifiera installation
	∙	Gå till Inställningar → Enheter & tjänster → Hjälpare
	∙	Sök på “SVOTC”
	∙	Du ska se ~30 helpers (input_number, input_select, input_text etc.)

3) Första gången du kör SVOTC (5-minuters setup)
⏱️ Snabbstart
	1.	Installera (enligt steg 2 ovan)
	2.	Vänta 1 minut (automationer startar)
	3.	Öppna Hjälpare i Home Assistant
	4.	Sök på “SVOTC”
	5.	Sätt entity mapping (se nästa avsnitt):
	∙	Indoor → din innetemp-sensor
	∙	Outdoor → din utetemp-sensor
	∙	Price → din elpris-sensor
	6.	Sätt Mode = Smart
	7.	Vänta 2 minuter
	8.	Kontrollera:
	∙	✅ binary_sensor.svotc_inputs_healthy = ON
	∙	✅ input_text.svotc_reason_code visar INTE “MISSING_INPUTS”
	∙	✅ sensor.svotc_virtual_outdoor_temperature har ett rimligt värde
Om något är fel: Gå till avsnitt 6 (Felsökning)

4) Entity mapping (viktigast att ändra)
Dessa tre helpers pekar SVOTC till dina sensorer. Du MÅSTE ändra dem.



|Helper                           |Vad            |Standard                |Din sensor        |
|---------------------------------|---------------|------------------------|------------------|
|`input_text.svotc_entity_indoor` |Innetemp-sensor|`sensor.inomhusmedel`   |`sensor.DIN_INNE` |
|`input_text.svotc_entity_outdoor`|Utetemp-sensor |`sensor.temperatur_nu`  |`sensor.DIN_UTE`  |
|`input_text.svotc_entity_price`  |Elpris-sensor  |`sensor.nordpool_tibber`|`sensor.DITT_PRIS`|

Hur man ändrar (UI-metod, rekommenderas)
	1.	Gå till Hjälpare (Developer Tools → States)
	2.	Sök på svotc_entity
	3.	Klicka på varje helper
	4.	Skriv in din entity_id
	5.	Spara
✅ Tips: Använd UI-metoden så överlever inställningarna om du uppdaterar YAML senare.

5) Lovelace dashboard
5.1 Snabbkort (nybörjare)
För dig som bara vill sätta igång snabbt:

type: entities
title: SVOTC – Snabbkontroll
entities:
  # Setup (EN GÅNG)
  - entity: input_text.svotc_entity_indoor
    name: "📍 Innetemp-sensor"
  - entity: input_text.svotc_entity_outdoor
    name: "🌡️ Utetemp-sensor"
  - entity: input_text.svotc_entity_price
    name: "💰 Elpris-sensor"
  
  # Drift
  - type: section
    label: "Läge & komfort"
  - entity: input_select.svotc_mode
    name: "Mode"
  - entity: input_number.svotc_comfort_temperature
    name: "Target temp"
  
  # Status (läs av)
  - type: section
    label: "Status"
  - entity: binary_sensor.svotc_inputs_healthy
    name: "✅ System OK?"
  - entity: binary_sensor.svotc_price_available
    name: "💰 Pris tillgängligt?"
  - entity: input_text.svotc_reason_code
    name: "🔍 Vad gör den nu?"
  - entity: sensor.svotc_virtual_outdoor_temperature
    name: "🎯 Virtuell utetemp (till värmepump)"


5.2 Fullständigt kort (avancerade användare)

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
    name: "Current price"
  - entity: sensor.svotc_p30
    name: "P30 (billigt under)"
  - entity: sensor.svotc_p80
    name: "P80 (dyrt över)"
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


6) Felsökning
🔴 Det händer inget
Kolla i denna ordning:
	1.	✅ input_select.svotc_mode = Smart (inte Off/PassThrough)
	2.	✅ binary_sensor.svotc_inputs_healthy = ON
	3.	✅ Entity mapping pekar på rätt sensorer:
	∙	input_text.svotc_entity_indoor
	∙	input_text.svotc_entity_outdoor
	∙	input_text.svotc_entity_price
	4.	✅ input_text.svotc_reason_code för ledtråd:
	∙	OFF → Mode = Off
	∙	PASS_THROUGH → Mode = PassThrough
	∙	MISSING_INPUTS_FREEZE → Sensorer saknas (se nedan)
🔴 Priset verkar “dött”
Diagnos:
	1.	✅ binary_sensor.svotc_price_available = ON?
	2.	✅ sensor.svotc_current_price visar ett rimligt värde?
	3.	✅ Verifiera att din prissensor har attribut:

# Developer Tools → States → din prissensor
attributes:
  current_price: 1.234
  raw_today: [{start: ..., end: ..., value: ...}, ...]
  raw_tomorrow: [...]


	4.	✅ Om sensor.svotc_p30 och sensor.svotc_p80 är unknown/none:
	∙	SVOTC kräver minst 20 priser från raw_today + raw_tomorrow
	∙	Vanligt problem: kl 13-14 innan morgondagens priser publicerats
	∙	Lösning: Vänta tills data finns, eller använd ComfortOnly-mode

# I FREEZE-läge:
requested_offset: 0        # Nollställs
applied_offset: FROZEN     # Fryses på sista kända värde
reason_code: MISSING_INPUTS_FREEZE


Varför FREEZE är viktigt:
	∙	Förhindrar att värmepumpen hoppar vilt om sensorer tillfälligt tappas
	∙	Ingen vertikal “spike” i offset
	∙	Säkert läge tills sensorer återhämtar sig
Åtgärd:
	1.	Kontrollera sensorerna som mapping pekar på:
	∙	input_text.svotc_entity_indoor
	∙	input_text.svotc_entity_outdoor
	2.	Verifiera att de inte är unknown/unavailable:
	∙	Developer Tools → States → sök din sensor
	3.	Om sensorn är trasig: Byt sensor i entity mapping

7) Hur systemet fungerar
🏗️ Arkitektur (layers)
SVOTC är byggt enligt “layered control”-principen:

┌─────────────────────────────────────────────────────────────┐
│ 1. SENSING (validerade råinputs)                            │
│    sensor.svotc_src_indoor                                  │
│    sensor.svotc_src_outdoor                                 │
│    sensor.svotc_src_current_price                           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. RAW PRICE STATE (instant, ingen memory)                 │
│    sensor.svotc_raw_price_state                             │
│    → cheap / neutral / brake                                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. DWELL (raw → stable, förhindrar spikar)                 │
│    Automation: SVOTC Price dwell                            │
│    Output: input_text.svotc_last_price_state                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. FORWARD LOOK (prebrake_strength 0..1)                   │
│    sensor.svotc_prebrake_strength                           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 5. BRAKE PHASE (undvik att "starta om" varje minut)        │
│    input_text.svotc_brake_phase                             │
│    Automation: SVOTC Brake phase controller                 │
│    → idle / ramping_up / holding / ramping_down             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 6. ENGINE (requested → ramp-limited applied)                │
│    Automation: SVOTC Engine                                 │
│    Output: input_number.svotc_requested_offset_c            │
│            input_number.svotc_applied_offset_c              │
│    Slutresultat: sensor.svotc_virtual_outdoor_temperature   │
└─────────────────────────────────────────────────────────────┘


🧮 Offset-beräkning (Engine logic)

# Comfort term (negativ offset = mer värme)
if comfort_guard_active:
    comfort_term = -(heat_aggressiveness * 0.4)
    # heat=5 → -2.0°C boost
else:
    comfort_term = 0

# Price term (positiv offset = mindre värme)
if mode == Smart and not comfort_guard_active:
    price_term = brake_hold_offset * prebrake_strength
    # hold=2.0, strength=1.0 → +2.0°C bromsning
else:
    price_term = 0

# Requested offset
requested = comfort_term + price_term

# Applied offset (ramp-limited)
if abs(requested - prev_applied) > max_delta_per_step:
    applied = prev_applied + sign(delta) * max_delta_per_step
else:
    applied = requested

# Virtual outdoor temperature
virtual_outdoor = real_outdoor + applied


8) Rekommenderade startvärden (defaults)
8.1 Mode
	∙	input_select.svotc_mode: Smart
8.2 Comfort guard (skydd mot för kallt)



|Parameter                               |Värde   |Förklaring                    |
|----------------------------------------|--------|------------------------------|
|`svotc_comfort_temperature`             |**21.0**|Måltemperatur inomhus         |
|`svotc_comfort_guard_activate_below_c`  |**0.8** |Aktiveras vid <20.2°C         |
|`svotc_comfort_guard_deactivate_above_c`|**0.4** |Deaktiveras vid >20.6°C       |
|`svotc_heat_aggressiveness`             |**2**   |Boost ≈ −0.8°C när guard aktiv|

Hysteresis-förklaring:

Target: 21.0°C
├─────────────────────────────────────────────┤
     ↓ 20.2°C                ↓ 20.6°C
   ACTIVATE              DEACTIVATE
   (guard ON)            (guard OFF)

Hysteresis gap: 0.8 - 0.4 = 0.4°C
→ Förhindrar att guard slår av/på varje minut


Aktivering:
	∙	Slår PÅ när: innetemp < (target - activate_below)
	∙	Exempel: 21.0 - 0.8 = 20.2°C
Deaktivering:
	∙	Slår AV när: innetemp > (target - deactivate_above)
	∙	Exempel: 21.0 - 0.4 = 20.6°C
✅ Tips: För att undvika att det blir kallt, sänk activate_below till 0.6
8.3 Price braking (pris-broms)



|Parameter                   |Värde  |Förklaring             |
|----------------------------|-------|-----------------------|
|`svotc_brake_aggressiveness`|**2**  |Prebrake-fönster 60 min|
|`svotc_brake_hold_offset_c` |**2.0**|Max bromsning +2.0°C   |

Prebrake-fönster per aggressivitetsnivå:



|Level|Fönster|Användning                      |
|-----|-------|--------------------------------|
|**0**|0 min  |Ingen prebrake                  |
|**1**|30 min |Tidig varning                   |
|**2**|60 min |✅ **Balanserad (rekommenderad)**|
|**3**|90 min |Aggressiv                       |
|**4**|105 min|Mycket aggressiv                |
|**5**|120 min|Maximal                         |

Prebrake-styrka (linear ramp):

prebrake_strength = (window - minutes_to_brake) / window

Exempel (window=60):
- 60 min kvar → strength = 0.00 (ingen bromsning)
- 30 min kvar → strength = 0.50 (halv bromsning)
- 0 min kvar  → strength = 1.00 (full bromsning)


✅ Tips: För att spara mer, höj brake_hold_offset_c till 3.0
8.4 Dwell (stabilitet mot prisspikar)



|Transition       |Tid (min)|Förklaring                            |
|-----------------|---------|--------------------------------------|
|`neutral → brake`|**30**   |Kräver 30 min över P80 innan bromsning|
|`brake → neutral`|**15**   |Snabbare återhämtning                 |
|`neutral → cheap`|**20**   |Försiktig cheap-klassning             |
|`cheap → neutral`|**15**   |Måttlig övergång                      |

✅ Tips: Vill du ha snabbare reaktion? Sänk dwell. Vill du ha mer stabilitet? Höj dwell.
8.5 Brake phase durations



|Phase     |Tid (min)|Vad händer             |
|----------|---------|-----------------------|
|`rampup`  |**30**   |0 → hold_offset gradvis|
|`hold`    |**60**   |Håller hold_offset     |
|`rampdown`|**45**   |hold_offset → 0 gradvis|

Se avsnitt 11 för visuell timeline.
8.6 Rate limiting (mjukhet per minut)



|Parameter                   |Värde   |Förklaring           |
|----------------------------|--------|---------------------|
|`svotc_max_delta_per_step_c`|**0.10**|Max ±0.10°C per minut|

✅ Tips: Vill du ha snabbare respons? 0.20. Vill du ha supermjukt? 0.05.

9) Reason codes (vad betyder de?)
Visar varför SVOTC fattar sitt nuvarande beslut.



|Kod                    |Betydelse            |Vad händer                        |Offset                |
|-----------------------|---------------------|----------------------------------|----------------------|
|`INIT`                 |Initial state        |Systemet startar                  |0                     |
|`OFF`                  |Mode = Off           |Ingen styrning                    |0                     |
|`PASS_THROUGH`         |Mode = PassThrough   |Ingen offset, bara monitorering   |0                     |
|`COMFORT_ONLY`         |Mode = ComfortOnly   |Endast comfort guard, inget pris  |comfort_term          |
|`MISSING_INPUTS_FREEZE`|Sensorer saknas      |Offset **fryses** (ingen styrning)|FROZEN                |
|`COMFORT_GUARD`        |Innetemp för låg     |Boost-värme aktiv                 |comfort_term (negativ)|
|`MCP_BLOCKS_BRAKE`     |Guard blockerar broms|Komfort prioriteras över pris     |comfort_term (negativ)|
|`PRICE_BRAKE`          |Dyrt elpris          |Bromsning aktiv                   |price_term (positiv)  |
|`NEUTRAL`              |Normalläge           |Ingen justering behövs            |0                     |

🔍 Exempel på reason code-logik

if mode == 'Off':
    reason = 'OFF'
elif not inputs_healthy:
    reason = 'MISSING_INPUTS_FREEZE'  # FREEZE applied offset
elif mode == 'PassThrough':
    reason = 'PASS_THROUGH'
elif mode == 'ComfortOnly':
    reason = 'COMFORT_ONLY'
elif comfort_guard_active and prebrake_strength > 0:
    reason = 'MCP_BLOCKS_BRAKE'       # Comfort wins over price
elif comfort_guard_active:
    reason = 'COMFORT_GUARD'
elif prebrake_strength > 0:
    reason = 'PRICE_BRAKE'
else:
    reason = 'NEUTRAL'


10) FAQ
❓ Styr SVOTC direkt värmepumpen?
Nej. SVOTC skapar en virtuell utetemperatur (sensor.svotc_virtual_outdoor_temperature) som du sedan mappar in till din värmepump/integration.
Exempel:

# Din värmepump-integration
climate.heat_pump:
  outdoor_temperature: sensor.svotc_virtual_outdoor_temperature


❓ Vad är skillnaden på requested och applied offset?



|Typ          |Beskrivning                                                                |Exempel                   |
|-------------|---------------------------------------------------------------------------|--------------------------|
|**Requested**|Vad logiken “vill” (utan begränsningar)                                    |+2.0°C                    |
|**Applied**  |Vad som faktiskt appliceras efter ramp-begränsning (`max_delta_per_step_c`)|+1.8°C (om ramp 0.2°C/min)|

Exempel på ramp:

Tid:      0 min → 1 min → 2 min
Requested:  +2.0     +2.0     +2.0
Applied:     0.0     +0.2     +0.4  (ramp 0.2°C/min)


❓ Hur skyddas komforten?
Comfort guard med hysteresis:
	1.	Aktiveras när innetemp < (target − activate_below)
	2.	Blockerar prisbroms (reason = MCP_BLOCKS_BRAKE)
	3.	Ger boost via heat_aggressiveness:

comfort_term = -(heat_aggressiveness * 0.4)
# heat=5 → -2.0°C boost (värmepumpen "tror" det är kallare ute)


	4.	Deaktiveras när innetemp > (target − deactivate_above)

{% set prices = (today + tomorrow) | map(attribute='value') | select('number') | list %}
{% if prices | length >= 20 %}
  # Beräkna P30/P80
{% else %}
  {{ none }}  # Inte tillräckligt med data
{% endif %}


När kan detta bli problem:
	∙	⏰ Tidigt på morgonen (kl 13-14) innan morgondagens priser publicerats
	∙	🔌 Prisensor ger inte båda listorna (raw_today och raw_tomorrow)
	∙	❌ Prisensorfel (sensor unavailable)
Vad händer då:
	∙	sensor.svotc_p30 och sensor.svotc_p80 blir none
	∙	sensor.svotc_raw_price_state kan inte avgöra cheap/brake
	∙	Systemet faller tillbaka till neutral (säkert läge)
Lösning:
	∙	✅ Vänta tills data finns
	∙	✅ Använd ComfortOnly-mode temporärt
	∙	✅ Kontrollera att din prissensor levererar båda listorna
❓ Vad händer om sensorer försvinner?
FREEZE-läge (MISSING_INPUTS_FREEZE):

if not inputs_healthy and mode in ['Smart', 'ComfortOnly']:
    requested_offset = 0
    applied_offset = FROZEN  # Fryses på sista kända värde
    reason = 'MISSING_INPUTS_FREEZE'


Varför FREEZE är viktigt:
	∙	🛡️ Förhindrar vertikala “spikar” om sensorer tillfälligt tappas
	∙	🎯 Värmepumpen fortsätter med sista kända offset
	∙	⚠️ Ingen ny styrning tills sensorer återhämtar sig
Vilka sensorer kollas:

inputs_healthy = (
    sensor.svotc_src_indoor is available AND
    sensor.svotc_src_outdoor is available
)
# OBS: Pris kollas INTE här (price glitches ska inte stoppa styrning)


❓ Kan jag använda SVOTC utan prisstyrning?
Ja, Mode = ComfortOnly:
	∙	✅ Endast comfort guard
	∙	❌ Ingen prisbroms
	∙	✅ Fungerar även om prissensor saknas

11) Avancerat: Brake phase timing
📊 Visuell timeline

Tid:     0 min ────── 30 min ────── 90 min ──── 135 min ──→
Phase:  [idle]    | [ramping_up] | [holding] | [ramping_down] | [idle]
Offset:   0°C → → → → → 2.0°C → → → 2.0°C → → → → → 0°C

Parametrar:
├─ rampup   = 30 min (0 → 2.0°C gradvis)
├─ hold     = 60 min (håller 2.0°C)
└─ rampdown = 45 min (2.0°C → 0 gradvis)

Total tid: 30 + 60 + 45 = 135 minuter


⚠️ OBS: Detta sker endast om stable price state = brake hela tiden.Om priset går ner tidigare → phase återställs till idle.
🔄 State machine transitions

┌──────┐  price=brake  ┌────────────┐  elapsed≥rampup  ┌─────────┐
│ idle ├──────────────→│ ramping_up ├─────────────────→│ holding │
└──────┘               └────────────┘                  └────┬────┘
   ↑                                                         │
   │                                                         │ elapsed≥hold
   │  price≠brake                                            ↓
   │  (anywhere)      ┌──────────────┐  elapsed≥rampdown  ┌────────────┐
   └──────────────────┤ ramping_down │←────────────────────│  holding   │
                      └──────────────┘                     └────────────┘


🧮 Offset under varje phase

if phase == 'idle':
    brake_offset = 0

elif phase == 'ramping_up':
    progress = elapsed_min / rampup_duration
    brake_offset = hold_offset * progress
    # Exempel: 15 min / 30 min = 0.5 → offset = 2.0 * 0.5 = 1.0°C

elif phase == 'holding':
    brake_offset = hold_offset
    # Exempel: offset = 2.0°C

elif phase == 'ramping_down':
    progress = elapsed_min / rampdown_duration
    brake_offset = hold_offset * (1 - progress)
    # Exempel: 22.5 min / 45 min = 0.5 → offset = 2.0 * 0.5 = 1.0°C


⏱️ Exempel på realistisk timeline
Scenario: Pris går över P80 kl 17:00, under P80 kl 19:30

17:00  Price > P80 → stable state = 'brake' → phase = 'ramping_up'
       ├─ Offset: 0 → 2.0°C (30 min ramp)

17:30  Phase → 'holding'
       ├─ Offset: 2.0°C (håller)

18:30  Phase → 'ramping_down' (hold duration 60 min slut)
       ├─ Offset: 2.0 → 0°C (45 min ramp)

19:15  Phase → 'idle' (rampdown klar)
       ├─ Offset: 0°C

19:30  Price < P80 → stable state = 'neutral'
       ├─ Phase stannar i 'idle' (redan där)


12) License / Disclaimer
⚠️ Använd på egen risk.
Detta projekt styr värme indirekt via en virtuell utetemperatur.Testa och verifiera beteendet i din miljö innan du litar på det i skarpt läge.
📋 Rekommendation för säker start
	1.	Börja försiktigt:
	∙	Låg brake_hold_offset_c (1.0°C)
	∙	Låg max_delta_per_step_c (0.10°C/min)
	∙	Tydlig comfort guard (activate 0.8, deactivate 0.4)
	2.	Övervaka första veckan:
	∙	Följ grafer för:
	∙	sensor.svotc_virtual_outdoor_temperature
	∙	input_number.svotc_applied_offset_c
	∙	sensor.svotc_src_indoor
	∙	Kolla input_text.svotc_reason_code dagligen
	3.	Öka aggressivitet stegvis:
	∙	Efter 1 vecka: Höj brake_hold_offset_c till 2.0
	∙	Efter 2 veckor: Testa brake_aggressiveness = 3
	∙	Efter 1 månad: Finjustera comfort guard

🎯 Credits
SVOTC – Stable Core Edition (2026-02)
Designad för:
	∙	🏠 Svenska villor med värmepump
	∙	⚡ Nordpool/Tibber spotpris-styrning
	∙	🎚️ Mjuk, förutsägbar, och förklarbar kontroll
Arkitektur: Layered control med dwell, prebrake, och ramp-limiting.
Support: Se GitHub Issues eller Home Assistant Community

🚀 Lycka till med din SVOTC-installation!
