# SVOTC - Snabbguide för hårdkodade värden och tuning

Detta dokument listar ALLA hårdkodade värden i SVOTC som du kan vilja justera.
Varje värde är märkt med `TUNING:` i YAML-filen.

---

## 📍 Hur hittar jag dessa i koden?

Sök efter `TUNING:` i YAML-filen så hittar du alla ställen där du kan justera.

---

## 🌡️ TEMPERATURVALIDERING

### Indoor temperature (Inomhus)
**Plats:** `sensor.svotc_src_indoor`
```yaml
# Nuvarande: 10-35°C
{% if val >= 10 and val <= 35 %}
```

**När justera:**
- Fjällstuga / vinterbostad: `5-30°C`
- Varmt klimat: `15-40°C`
- Normal bostad Sverige: `10-35°C` ✅

---

### Outdoor temperature (Utomhus)
**Plats:** `sensor.svotc_src_outdoor`
```yaml
# Nuvarande: -40 till +45°C
{% if val >= -40 and val <= 45 %}
```

**När justera:**
- Norra Sverige: `-50 till +35°C`
- Södra Europa: `-10 till +50°C`
- Mellansverige: `-40 till +45°C` ✅

---

### Electricity price (Elpris)
**Plats:** `sensor.svotc_src_current_price`
```yaml
# Nuvarande: 0-10 SEK/kWh
{% if p >= 0 and p <= 10 %}
```

**När justera:**
- Extrema pristoppar 2022-2023: `0-20 SEK/kWh`
- Normal marknad: `0-10 SEK/kWh` ✅
- Mycket stabila priser: `0-5 SEK/kWh`

---

## 📊 PERCENTILER OCH PRISSTATUS

### Minimum data requirement
**Plats:** `sensor.svotc_p30/p70/p80`
```yaml
# Nuvarande: Minst 20 timmar
{% if prices | length >= 20 %}
```

**När justera:**
- Kräv fullständig data: `>= 24`
- Mer tolerant: `>= 10` ⚠️ (mindre exakt)
- Standard (rekommenderat): `>= 20` ✅

---

### Percentile thresholds
**Plats:** `sensor.svotc_p30/p70/p80`
```yaml
# Nuvarande:
# P30 = 0.30 (30:e percentilen = billigt)
# P80 = 0.80 (80:e percentilen = dyrt)
{% set pct = 0.30 if 'P30' in this.name else ... 0.80 %}
```

**När justera:**
- Striktare "billigt": `0.25` (endast 25% billigaste timmar)
- Striktare "dyrt": `0.85` (endast 15% dyraste timmar)
- Mer generöst "billigt": `0.35`
- Standard: `P30=0.30, P80=0.80` ✅

---

### Price state determination
**Plats:** `sensor.svotc_raw_price_state`
```yaml
# Nuvarande: > P80 = brake, < P30 = cheap
{% if p > p80 %} brake
{% elif p < p30 %} cheap
```

**När justera:**
- Mer känsligt system: Använd `P70` istället för `P80`
- Mindre känsligt: Använd `P90` istället för `P80`
- Standard: `P80` ✅

---

## 🔧 COMFORT GUARD & MCP

### MCP Deadband (när börja värma)
**Plats:** `SVOTC Engine` automation
```yaml
# Nuvarande: 0.4°C
deadband: 0.4
is_heating_comfort: "{{ err > deadband }}"
```

**När justera:**
- Mer tolerans: `0.6°C` (börja värma senare)
- Snabbare reaktion: `0.2°C` (börja värma tidigare)
- Standard: `0.4°C` ✅

---

### Comfort offset multiplier
**Plats:** `SVOTC Engine` automation
```yaml
# Nuvarande: error × -1.0
{% set comfort = (err * -1.0) if err|abs > deadband else 0 %}
```

**När justera:**
- Mildare reglering: `-0.8`
- Aggressivare reglering: `-1.2`
- Standard: `-1.0` ✅

---

### Comfort offset clamp
**Plats:** `SVOTC Engine` automation
```yaml
# Nuvarande: aggressiveness × 2
{% set comfort_clamped = comfort | clamp(-(heat_aggr*2), (brake_aggr*2)) %}
```

**När justera:**
- Mildare gränser: `× 1.5`
- Hårdare gränser: `× 2.5`
- Standard: `× 2.0` ✅

---

## 🛑 BRAKE & OFFSET LIMITS

### Virtual outdoor temp clamp
**Plats:** `sensor.svotc_virtual_outdoor_temperature`
```yaml
# Nuvarande: -30 till +30°C
{{ (out + off) | clamp(-30, 30) }}
```

**När justera:**
- Extra försiktig: `±25°C`
- Pump klarar mer: `±35°C`
- Standard (säkert för de flesta): `±30°C` ✅

---

### Total offset clamp
**Plats:** `SVOTC Engine` automation
```yaml
# Nuvarande: ±8°C
{{ (comfort_clamped + price) | clamp(-8, 8) }}
```

**När justera:**
- Extra försiktighet: `±6°C`
- Pump klarar mer: `±10°C`
- Standard (säkert): `±8°C` ✅

---

### Brake hold multiplier
**Plats:** `SVOTC Brake phase manager`
```yaml
# Nuvarande: aggressiveness × 2.0
data: { value: "{{ (states('input_number.svotc_brake_aggressiveness')|float * 2.0) }}" }
```

**När justera:**
- Mildare broms: `× 1.5`
- Hårdare broms: `× 2.5`
- Standard: `× 2.0` ✅

---

## ⏱️ TIMING & DELAYS

### Time pattern frequencies
**Platser:** Flera automations

```yaml
# Price dwell automation
minutes: "/1"    # Kontrollera varje minut

# Brake phase manager
minutes: "/1"    # Kontrollera varje minut

# Engine
minutes: "/1"    # Körs varje minut
```

**När justera:**
- Spara CPU-kraft: `/5` (var 5:e minut) ⚠️ grövre timing
- Maximal precision: `/1` (varje minut) ✅
- Lätt optimering: `/2` (varannan minut)

---

### Peak search lookback
**Plats:** `sensor.svotc_next_peak_price`
```yaml
# Nuvarande: 1 timme bakåt (-3600 sekunder)
{% if ts >= (now_ts - 3600) and ts <= end_ts %}
```

**När justera:**
- Längre historik: `-7200` (2 timmar bakåt)
- Bara framåt: `0`
- Standard: `-3600` (1 timme) ✅

---

### Peak search horizon
**Plats:** `sensor.svotc_next_peak_price`
```yaml
# Nuvarande: prebrake_window + 30 min, max 180 min
{% set horizon_m = (window + 30) | clamp(15, 180) %}
```

**När justera:**
- Längre framförhållning: `+ 60` min, max `240`
- Kortare horisont: `+ 15` min, max `120`
- Standard: `+ 30` min, max `180` ✅

---

### Peak matching tolerance
**Plats:** `sensor.svotc_minutes_to_next_peak`
```yaml
# Nuvarande: 0.01 SEK/kWh
{% if (v - peak)|abs < 0.01 %}
```

**När justera:**
- Mer generös: `0.05` (hittar fler peaks)
- Striktare: `0.005` (endast exakta peaks)
- Standard: `0.01` ✅

---

### Prebrake window mapping
**Plats:** `sensor.svotc_prebrake_window_min`
```yaml
# Nuvarande mapping:
# 0 → 0 min
# 1 → 15 min
# 2 → 30 min
# 3 → 45 min
# 4 → 60 min
# 5 → 75 min
{% set mapper = {0:0, 1:15, 2:30, 3:45, 4:60, 5:75} %}
```

**När justera:**
- Längre prebrake: `{0:0, 1:20, 2:40, 3:60, 4:80, 5:100}`
- Kortare prebrake: `{0:0, 1:10, 2:20, 3:30, 4:40, 5:50}`
- Standard: ovan ✅

---

### Fail-safe activation delay
**Plats:** `SVOTC Fail-safe handler`
```yaml
# Nuvarande: 5 minuter
- delay:
    minutes: 5
```

**När justera:**
- Mer tolerans mot avbrott: `10` minuter
- Snabbare säkerhetsreaktion: `3` minuter
- Standard: `5` minuter ✅

---

### Fail-safe recovery delay
**Plats:** `SVOTC Fail-safe handler`
```yaml
# Nuvarande: 3 minuter
- delay:
    minutes: 3
```

**När justera:**
- Mer stabil återställning: `5` minuter
- Snabbare återgång: `2` minuter
- Standard: `3` minuter ✅

---

### Missing input alert delay
**Plats:** `SVOTC Notify: missing inputs`
```yaml
# Nuvarande: 3 minuter för varning
for:
  minutes: 3

# 2 minuter för recovered
for:
  minutes: 2
```

**När justera:**
- Undvik spam: `5` min för varning, `5` min för recovered
- Snabbare varningar: `1` min för varning, `1` min för recovered
- Standard: `3` min / `2` min ✅

---

## 📈 OFFSET TRACKING

### Offset significance threshold
**Plats:** `SVOTC Track daily offset hours`
```yaml
# Nuvarande: |offset| > 0.5°C räknas som "stor"
- conditions: "{{ applied | abs > 0.5 }}"
```

**När justera:**
- Räkna bara större offset: `1.0`
- Räkna alla offset: `0.3`
- Standard: `0.5` ✅

---

## 🎛️ SAMMANFATTNING - REKOMMENDERADE STARTVÄRDEN

### För KONSERVATIVT system (försiktigt):
```yaml
# Temperatur
Indoor range: 12-33°C
Outdoor range: -35 till +40°C
Virtual temp clamp: ±25°C
Total offset clamp: ±6°C

# MCP
Deadband: 0.6°C
Comfort multiplier: -0.8

# Percentiler
P30: 0.25 (striktare billigt)
P80: 0.85 (striktare dyrt)
Min data: 24 timmar

# Timing
All frequencies: /2 eller /5
Fail-safe delay: 10 min
Recovery delay: 5 min
```

### För AGGRESSIVT system (max prestanda):
```yaml
# Temperatur
Indoor range: 10-35°C
Outdoor range: -40 till +45°C
Virtual temp clamp: ±35°C
Total offset clamp: ±10°C

# MCP
Deadband: 0.2°C
Comfort multiplier: -1.2

# Percentiler
P30: 0.35 (generösare billigt)
P80: 0.75 (generösare dyrt)
Min data: 15 timmar

# Timing
All frequencies: /1
Fail-safe delay: 3 min
Recovery delay: 2 min
```

### För BALANSERAT system (rekommenderat START):
```yaml
# Temperatur
Indoor range: 10-35°C ✅
Outdoor range: -40 till +45°C ✅
Virtual temp clamp: ±30°C ✅
Total offset clamp: ±8°C ✅

# MCP
Deadband: 0.4°C ✅
Comfort multiplier: -1.0 ✅

# Percentiler
P30: 0.30 ✅
P80: 0.80 ✅
Min data: 20 timmar ✅

# Timing
All frequencies: /1 ✅
Fail-safe delay: 5 min ✅
Recovery delay: 3 min ✅
```

---

## 🔍 FELSÖKNINGSGUIDE

### Systemet reagerar FÖR LÅNGSAMT på prisändringar
→ Minska dwell-tider (neutral→cheap: 10→5 min)
→ Öka percentil-tolerans (P30: 0.30→0.35)
→ Öka prebrake window

### Systemet OSCILLERAR / FLAXAR
→ Öka hysteres (activate: 0.8→1.0, deactivate: 0.4→0.3)
→ Öka dwell-tider
→ Öka MCP deadband (0.4→0.6)
→ Minska max_delta_per_step (0.5→0.3)

### Värmepumpen STÄNGER AV sig (säkerhetsbrytare)
→ Minska total offset clamp (±8→±6)
→ Minska brake multiplier (2.0→1.5)
→ Minska virtual temp clamp (±30→±25)
→ Öka brake ramp durations (30→45 min)

### För KALLT i huset under pristoppar
→ Sänk comfort guard activate threshold (0.8→0.6)
→ Öka comfort multiplier (-1.0→-1.2)
→ Minska brake aggressiveness (UI-slider)

### För VARMT i huset under låga priser
→ Minska heat aggressiveness (UI-slider)
→ Öka MCP deadband (0.4→0.6)

---

## 📝 LOGG ÖVER DINA ÄNDRINGAR

Använd denna sektion för att dokumentera dina justeringar:

```
DATUM       PARAMETER                    FRÅN → TILL    RESULTAT
----------  ---------------------------  -------------  ----------------
2024-xx-xx  MCP Deadband                 0.4 → 0.6      Mindre oscillation
2024-xx-xx  Total offset clamp           ±8 → ±6        Säkrare drift
```

---

## ⚠️ VIKTIGT ATT KOMMA IHÅG

1. **Ändra EN parameter åt gången** och testa i minst 24h
2. **Dokumentera alla ändringar** (använd tabellen ovan)
3. **Börja konservativt** och justera gradvis
4. **Övervaka grafer** i History under första veckan
5. **Håll backup** av fungerande konfiguration

---

## 🎯 SNABBVÄG TILL PERFEKT TUNING

### Vecka 1: Stabilitet
1. Kör med standardvärden
2. Observera oscillation → justera hysteres
3. Kolla fail-safe-aktiveringar → justera sensorgränser

### Vecka 2: Optimera timing
1. Justera dwell-tider baserat på ditt elpris-mönster
2. Justera brake phase durations
3. Kalibrera prebrake window

### Vecka 3: Fine-tuning prestanda
1. Justera percentiler om för ofta/sällan i brake
2. Optimera comfort multiplier
3. Justera aggressiveness-multiplikatorer

### Vecka 4: Polish
1. Sätt recorder purge_keep_days till önskat värde
2. Skapa perfekta Lovelace-dashboards
3. Njut av optimalt system! 🎉
