# SVOTC MCP (Model Predictive Control) - Snabbguide

## Vad är MCP?

MCP (Model Predictive Control) är den prediktiva logiken som optimerar värmningen baserat på elpriset UTAN att bromsa huset. Den aktiveras automatiskt när priset är billigt (under P30).

## När är MCP aktivt?

### ✅ MCP aktiveras när:
1. **Pris är under P30** (cheap state)
2. **Systemet INTE braking** (phase != ramping_up/holding)
3. **Comfort guard INTE aktiv** (huset inte för kallt)

### Formel:
```yaml
mcp_active = (phase not in ['ramping_up','holding']) AND (not guard)

Om mcp_active OCH price_state == 'cheap':
  lägg till extra värmning = heat_aggr * 1.5
```

## Hur fungerar MCP i olika lägen?

### Smart Mode
- **MCP aktivt vid billiga priser:** Värmer extra (heat_aggr * 1.5)
- **Brake aktivt vid höga priser:** Minskar värme (brake_aggr * 2.0)
- **Normal drift:** Endast comfort control
- **Status visas som:** "MCP (predictive heating)" vid billiga priser

### Vacation Mode
- **Samma som Smart Mode** men med lägre måltemperatur
- MCP fungerar identiskt

### ComfortOnly Mode
- **MCP aktivt vid billiga priser:** Värmer extra (heat_aggr * 1.5) ✅
- **Brake aktivt vid höga priser:** NEJ - systemet bromsar aldrig ❌
- **Normal drift:** Endast comfort control
- **Status visas som:** "MCP (predictive heating)" vid billiga priser

Detta är den stora fördelen med ComfortOnly + MCP: Du får optimering vid billiga timmar utan att någonsin riskera att huset blir för kallt vid dyra timmar.

### PassThrough Mode
- MCP inaktivt
- Systemet gör ingenting

### Off Mode
- Allt avstängt

## Praktiska Exempel

### Scenario 1: Billig elpris kl 02:00
```
Pris: 0.45 SEK/kWh (under P30 = 0.60)
Phase: idle (inte braking)
Comfort guard: off (huset varmt nog)
Mode: ComfortOnly

→ MCP AKTIVT ✅
→ Extra värmning: heat_aggr * 1.5
→ Status: "MCP (predictive heating)"
```

### Scenario 2: Dyr elpris kl 18:00, ComfortOnly
```
Pris: 2.15 SEK/kWh (över P80 = 1.80)
Phase: idle (brake aktiveras EJ i ComfortOnly)
Comfort guard: off
Mode: ComfortOnly

→ MCP INAKTIVT (pris inte cheap)
→ Ingen braking (ComfortOnly tillåter inte)
→ Status: "Comfort only"
→ Systemet håller bara måltemperaturen
```

### Scenario 3: Dyr elpris kl 18:00, Smart Mode
```
Pris: 2.15 SEK/kWh (över P80)
Phase: ramping_up → holding (brake aktivt)
Comfort guard: off
Mode: Smart

→ MCP INAKTIVT (braking pågår)
→ Brake aktivt: minskar värme
→ Status: "Braking (high price)"
```

### Scenario 4: Billig pris men comfort guard aktiv
```
Pris: 0.45 SEK/kWh (cheap)
Phase: idle
Comfort guard: ON (huset för kallt)
Mode: Smart

→ MCP INAKTIVT ❌ (guard har företräde)
→ Status: "Comfort guard active"
→ Systemet värmer för att nå måltemp först
```

## Inställningar som påverkar MCP

### heat_aggressiveness (0-5)
- **0:** MCP inaktivt (ingen extra värmning)
- **1:** +3.75°C offset vid billiga priser
- **2:** +7.5°C offset
- **3:** +11.25°C offset (rekommenderat)
- **4:** +15°C offset
- **5:** +18.75°C offset (max)

Formel: `cheap_boost = heat_aggr * 1.5 * 2.5 = heat_aggr * 3.75`

### svotc_max_total_offset_c
Begränsar totala offseten (default 8°C), så även med heat_aggr=5 blir max offset 8°C.

## Övervaka MCP

### I Home Assistant

**Sensor att kolla:**
```yaml
sensor.svotc_status
# Visar "MCP (predictive heating)" när MCP är aktivt
```

**Automatisering för notis:**
```yaml
automation:
  - alias: "Notify when MCP active"
    trigger:
      - platform: state
        entity_id: input_text.svotc_reason_code
        to: "MCP"
    action:
      - service: notify.mobile_app
        data:
          message: "SVOTC: MCP aktivt - värmer extra vid billigt pris!"
```

**Lovelace kort:**
```yaml
type: entities
entities:
  - sensor.svotc_status
  - sensor.svotc_current_price
  - sensor.svotc_p30
  - input_number.svotc_requested_offset_c
  - input_number.svotc_applied_offset_c
  - input_text.svotc_brake_phase
```

## Troubleshooting

### Problem: MCP aktiveras aldrig
**Kontrollera:**
1. `heat_aggressiveness` är > 0
2. Pris faktiskt under P30 (kolla `sensor.svotc_p30`)
3. `input_text.svotc_last_price_state` = "cheap"
4. `input_text.svotc_brake_phase` != "ramping_up" eller "holding"
5. `binary_sensor.svotc_comfort_guard_active` = off

### Problem: MCP aktiveras för ofta
**Lösning:**
- Öka `svotc_price_dwell_minutes` till 45-60 min
- Minskar flapping runt P30-gränsen

### Problem: Huset blir för varmt med MCP
**Lösning:**
- Minska `heat_aggressiveness` från 5 till 3
- Minska `svotc_max_total_offset_c` från 8 till 6°C
- Öka `svotc_comfort_temperature` något (paradoxalt men minskar error-termen)

### Problem: MCP fungerar inte i ComfortOnly
**Kontrollera kod version:**
- Denna funktionalitet kräver den förbättrade versionen
- Kolla att reason_code-logiken innehåller:
  ```yaml
  {% elif mode == 'ComfortOnly' and price_state == 'cheap' %} MCP
  ```

## Optimala Inställningar

### För maximal ekonomisk besparing (Smart Mode):
```yaml
heat_aggressiveness: 4-5
brake_aggressiveness: 3-4
svotc_max_total_offset_c: 8
svotc_min_phase_duration_minutes: 30
```

### För komfort med lite optimering (ComfortOnly):
```yaml
heat_aggressiveness: 2-3
brake_aggressiveness: 0 (används ej)
svotc_max_total_offset_c: 6
```

### För balanserad drift (Smart Mode):
```yaml
heat_aggressiveness: 3
brake_aggressiveness: 3
svotc_max_total_offset_c: 7
svotc_min_phase_duration_minutes: 25
```

## Sammanfattning

**MCP = Smart uppvärmning vid billiga priser**

- ✅ Fungerar i Smart, Vacation OCH ComfortOnly
- ✅ Aktiveras automatiskt vid priser under P30
- ✅ Pausas vid braking eller comfort guard
- ✅ Synligt i status
- ✅ Justeras med heat_aggressiveness
- ✅ Begränsas av max_total_offset_c

**Viktigt:** MCP är inte samma som braking - det är den POSITIVA delen av prisoptimeringen (ladda värme när det är billigt), medan braking är den NEGATIVA delen (spara när det är dyrt).
