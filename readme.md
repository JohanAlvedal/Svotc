[🇸🇪 Svenska](readme.md) | [🇬🇧 English](readme_e.md)

---

# 💥 Breaking Changes – SVOTC 3.0.0

> ⚠️ **ANVÄND PÅ EGEN RISK**
>
> SVOTC 3.0 Funktioner kan ändras utan föregående meddelande, buggar kan förekomma och konfigurationsdetaljer kan ändras i framtida releaser. Använd inte i produktion om du inte fullt ut förstår riskerna. **Du är själv ansvarig för eventuella konsekvenser som påverkar ditt värmesystem.**

---

## SVOTC 3.0.0 introducerar "breaking changes" från 2.x.x

Den största förändringen i SVOTC 3.0.0 är att systemet har **förenklats in i en ny Core v1-arkitektur**.

Detta är **inte en direkt uppgradering från 2.x.x**.

Flera tidigare delsystem har tagits bort eller slagits samman till en mindre och mer transparent kärna. Den gamla 2.x-strukturen och logiken bör inte återanvändas utan granskning.

---

## Vad har ändrats?

### Tidigare struktur (2.x.x)

```text
/config/packages/svotc/
├── 00_helpers.yaml
├── 10_sensors.yaml
├── 20_price_fsm.yaml
├── 22_engine.yaml
├── 30_learning.yaml
└── 40_notify.yaml
```

### Ny struktur (3.0.0 / Core v1)

```text
/config/packages/svotc/
├── 00_helpers.yaml  ← Användarkontroller och interna hjälptillstånd
├── 10_sensors.yaml  ← Temperaturer, prisgränser, pristillstånd, hälsa
├── 20_engine.yaml   ← Huvudsaklig kontroll-loop, begärd/applicerad offset, orsakskod
└── 30_notify.yaml   ← Valfri FAIL_SAFE-notifiering
```

> ✅ De tre första filerna krävs. `30_notify.yaml` är valfri men rekommenderad.

---

## Vad behöver du göra?

### 1. Ta bort gamla 2.x package-filer

Ta bort eller arkivera äldre filer såsom:

```text
20_price_fsm.yaml
22_engine.yaml
30_learning.yaml
40_notify.yaml
```

Om du migrerar från en äldre version med en enda fil, ta även bort eller arkivera:

```text
/config/packages/svotc.yaml
```

### Rensa gamla entiteter (rekommenderas)

Om du tidigare körde SVOTC 2.x.x kan vissa template-sensorer finnas kvar i Home Assistants entitetsregister.

Om dessa entiteter blir kvar kan Home Assistant skapa nya sensorer med namn som:

`sensor.svotc_virtual_outdoor_temperature_2`
`sensor.svotc_forward_price_state_2`

För att undvika detta, ta bort de gamla entiteterna innan du startar SVOTC 3.0.0.

**Steg:**

1. Gå till **Inställningar → Enheter och tjänster → Entiteter**
2. Sök efter `svotc`
3. Ta bort entiteter som tillhör den gamla 2.x-installationen
4. Starta om Home Assistant
5. Starta SVOTC 3.0.0

Detta säkerställer att de nya sensorerna behåller sina korrekta namn.

---

### 2. Skapa mappen

```text
/config/packages/svotc/
```

### 3. Kopiera in de nya Core v1-filerna

```text
00_helpers.yaml
10_sensors.yaml
20_engine.yaml
30_notify.yaml
```

### 4. Kontrollera `configuration.yaml`

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### 5. Starta om Home Assistant

---

### 6. Konfigurera käll-entiteter (source entities)

Efter omstart, ställ in dessa helpers:

* `input_text.svotc_source_indoor_temp`
* `input_text.svotc_source_outdoor_temp`
* `input_text.svotc_source_price`

**Exempel:**

```text
sensor.indoor_temperature
sensor.outdoor_temperature
sensor.nordpool_kwh_se3
```

---

### 7. Verifiera att systemet fungerar

Kontrollera:

* `binary_sensor.svotc_inputs_healthy` → **ON**
* `sensor.svotc_forward_price_state` → `neutral`, `cheap`, `prebrake`, `hold (bridge between brake blocks)` eller `brake`
* `input_text.svotc_reason_code` → t.ex. `NEUTRAL`
* `sensor.svotc_virtual_outdoor_temperature` → rimligt värde

---

## Större arkitektoniska förändringar i 3.0.0

### 1. Single-engine design

SVOTC 3.0.0 ersätter den äldre kontrollstrukturen med en **enda huvudmotor**.

Kärnan innehåller även en lättviktsbaserad PI-regulator för temperaturkontroll som används i Comfort-läge samt för komfort- och övertemperaturskydd.

Den centrala beslutsslingan körs kontinuerligt och ersätter tidigare delsystem såsom:

* Pris-FSM
* Bromsfaser
* Inlärningslogik

Detta gör systemet:

* Lättare att förstå
* Lättare att felsöka
* Lättare att underhålla
* Mer förutsägbart

---

### 2. Enklare filstruktur

SVOTC använder nu endast fyra kärnfiler, vilket minskar komplexitet och förenklar uppgraderingar.

---

### 3. Tydlig separation mellan requested och applied offset

* **Requested offset** — vad logiken vill göra
* **Applied offset** — vad som faktiskt skickas efter rate limiting

Detta minskar abrupta förändringar och skyddar hårdvaran.

---

### 4. Enklare och mer transparent prislogik

Forward price state:

* `cheap`
* `neutral`
* `prebrake`
* `hold` (bridge mellan brake-block)
* `brake`

---

### 5. Inbyggda skydd i kärnan

Motorn hanterar:

* Comfort guard
* Overtemperature brake
* Fail-safe

Alla utvärderas i en strikt prioritetsordning.

---

### Temperaturreglering med PI-kontroll

SVOTC använder en enkel **PI-regulator (Proportional + Integral)**.

Används i:

* Comfort-läge
* Comfort guard
* Overtemperature braking

Regulatorn:

* Reagerar direkt (P-del)
* Kompenserar över tid (I-del)
* Använder deadband för stabilitet

Derivative (D) används inte eftersom byggnader redan är tröga system.

PI arbetar tillsammans med ramp-begränsning för mjuka förändringar.

---

### 6. Enklare notifieringsmodell

Systemet kan skicka notifiering om `FAIL_SAFE` varar >5 minuter.

---

## Andra viktiga ändringar

* `20_price_fsm.yaml` borttagen
* `22_engine.yaml` ersatt
* `30_learning.yaml` borttagen
* `40_notify.yaml` ersatt

Driftlägen:

* `Off`
* `Smart`
* `Comfort`
* `PassThrough`

---

## Varför denna förändring?

Core v1 är designad för att vara:

* **Renare**
* **Säkrare**
* **Hårdvaruvänligare**
* **Lättare att felsöka**
* **Lättare att underhålla**

Målet är stabilitet, inte komplexitet.

---

### Designad för enkelhet

SVOTC 3.0.0 undviker medvetet avancerade inställningar.

Du behöver i praktiken bara:

* Innetemperatur
* Utetemperatur
* Elpris
* Komfortmål

Systemet hanterar resten automatiskt.

👉 **Fungerar direkt ur lådan**

---

## Rekommenderad migrering

1. Ta bort gamla filer
2. Installera Core v1
3. Sätt `PassThrough`
4. Verifiera inputs
5. Kontrollera sensors
6. Växla till `Smart`

---

## Påminnelse om Beta

SVOTC styr din värmepump indirekt.

Fel konfiguration kan påverka:

* Komfort
* Drift
* Effektivitet

Rekommendation:

* Testa i `PassThrough`
* Övervaka `reason_code`
* Ha fallback

---

**Version:** SVOTC 3.0.0 Beta
**Core:** Core v1
**Licens:** MIT
