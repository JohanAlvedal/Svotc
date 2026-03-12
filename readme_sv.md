[🇸🇪 Svenska](readme_sv.md) | [🇬🇧 English](readme.md)

---
# 💥 Breaking Changes – SVOTC 3.0.0 (Beta)

> ⚠️ **BETA-MJUKVARA — ANVÄND PÅ EGEN RISK**
> 
> SVOTC 3.0.0 genomgår aktiv betatestning. Funktioner kan ändras utan förvarning, buggar kan förekomma och konfigurationsdetaljer kan ändras i framtida releaser. Använd inte i produktion om du inte fullt ut förstår riskerna. **Du är själv ansvarig för eventuella konsekvenser som påverkar ditt värmesystem.**

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

> ✅ Alla fyra filer krävs. De är beroende av varandra.

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

### 2. Skapa mappen

```text
/config/packages/svotc/

```

### 3. Kopiera in de nya Core v1-filerna

Kopiera in dessa filer i mappen:

```text
00_helpers.yaml
10_sensors.yaml
20_engine.yaml
30_notify.yaml

```

### 4. Kontrollera `configuration.yaml`

Om du inte redan använder Home Assistant packages, lägg till:

```yaml
homeassistant:
  packages: !include_dir_named packages

```

### 5. Starta om Home Assistant

### 6. Konfigurera om dina käll-entiteter (source entities)

Efter omstart, ställ in dessa helpers för att matcha ditt system:

* `input_text.svotc_source_indoor_temp`
* `input_text.svotc_source_outdoor_temp`
* `input_text.svotc_source_price`

**Exempel:**

```text
sensor.indoor_temperature
sensor.outdoor_temperature
sensor.nordpool_kwh_se3

```

### 7. Verifiera att den nya kärnan (core) fungerar

Efter omstart, kontrollera:

* `binary_sensor.svotc_inputs_healthy` → bör vara **ON**
* `sensor.svotc_forward_price_state` → bör visa `neutral`, `cheap`, `prebrake`, `hold`, eller `brake`
* `input_text.svotc_reason_code` → bör visa `NEUTRAL` eller en annan aktiv orsak
* `sensor.svotc_virtual_outdoor_temperature` → bör lösa ut korrekt

---

## Större arkitektoniska förändringar i 3.0.0

### 1. Single-engine design

SVOTC 3.0.0 ersätter den äldre kontrollstrukturen i flera lager med en **enda huvudmotor**.

Kärnan innehåller även en lättviktsbaserad PI-regulator för temperaturkontroll som används i Comfort-läge samt för komfort- och övertemperaturskydd.

Istället för att förlita sig på separata delsystem för:

* Pris-FSM (Finite State Machine)
* Bromsfaser (brake phases)
* Inlärningslogik (learning logic)

...så kör den nya kärnan en central beslutsslinga varje minut.

Detta gör systemet:

* Lättare att förstå
* Lättare att felsöka
* Lättare att underhålla
* Mer förutsägbart i den dagliga driften

---

### 2. Enklare filstruktur

SVOTC använder nu endast fyra kärnfiler.

Detta minskar komplexiteten och gör uppgraderingar enklare.

---

### 3. Tydlig separation mellan begärd och applicerad offset

SVOTC 3.0.0 separerar tydligt:

* **Requested offset** (begärd) — vad logiken vill göra
* **Applied offset** (applicerad) — vad som faktiskt skickas efter hastighetsbegränsning (rate limiting)

Detta minskar abrupta beteenden och gör systemet skonsammare mot värmepumpens hårdvara.

---

### 4. Enklare och mer transparent prislogik

Prislogiken är nu lättare att inspektera och förstå.

Det framåtblickande pristillståndet (forward price state) uttrycks direkt som:

* `cheap`
* `neutral`
* `prebrake`
* `hold`
* `brake`

Detta ersätter äldre och mer komplicerade flödesstrukturer.

---

### 5. Komfort- och övertemperaturskydd är inbyggda direkt i kärnan

Motorn hanterar nu:

* Komfortskydd (comfort guard) när innetemperaturen är för låg
* Övertemperaturbroms när innetemperaturen är för hög
* Fail-safe-beteende när indata saknas

Dessa skydd utvärderas i en strikt prioritetsordning.

---

### Temperaturreglering med PI-kontroll

SVOTC 3.0.0 använder en enkel **PI-regulator (Proportional + Integral)** för temperaturkontroll.

Denna regulator används i:

* **Comfort-läge**
* **Comfort guard** i Smart-läge
* **Overtemperature braking**

Regulatorn beräknar ett offset baserat på temperaturfelet mellan aktuell innetemperatur och komfortmålet.

Den proportionella delen reagerar direkt på temperaturfelet, medan den integrerande delen gradvis kompenserar för kvarstående avvikelser över tid.

En liten deadband används runt måltemperaturen för att undvika att små sensorvariationer orsakar konstant reglering.

PI-regulatorn arbetar tillsammans med SVOTC:s ramp-begränsning mellan **requested offset** och **applied offset**, vilket gör att förändringar sker gradvis och mer skonsamt mot värmepumpens drift.

Derivative-del (D) används inte eftersom byggnader redan är långsamma termiska system och PI-reglering ger tillräckligt stabil kontroll i praktiken.

Dessa skydd utvärderas i en strikt prioritetsordning.

---

### 6. Enklare notifieringsmodell

Den nya kärnan inkluderar en valfri notifiering om systemet förblir i `FAIL_SAFE` i minst 5 minuter.

Detta är avsiktligt enklare än tidigare notifierings- och diagnostiklager.

---

## Andra viktiga ändringar i 3.0.0

* `20_price_fsm.yaml` används inte längre
* `22_engine.yaml` har ersatts av `20_engine.yaml`
* `30_learning.yaml` är inte längre en del av kärnan
* `40_notify.yaml` har ersatts av en mindre `30_notify.yaml`
* Driftlägen (operating modes) är nu fokuserade på:
* `Off`
* `Smart`
* `Comfort`
* `PassThrough`



---

## Varför denna förändring?

Den nya Core v1-strukturen är designad för att göra SVOTC:

* **Renare** — färre rörliga delar
* **Säkrare** — mindre aggressivt offset-beteende
* **Hårdvaruvänligare** — mjukare förändringar i utdata
* **Lättare att felsöka** — tydligare logik och färre interna lager
* **Lättare att underhålla** — enklare arkitektur för framtida releaser

Målet med 3.0.0 är inte att lägga till mer komplexitet.

Målet är att göra kärnans beteende mer stabilt, läsbart och pålitligt.

---

### Designad för enkelhet

SVOTC 3.0.0 undviker avsiktligt ett stort antal avancerade inställningsparametrar.

Tidigare versioner exponerade många interna kontroller och experimentella funktioner. Även om det var kraftfullt, gjorde det också systemet svårare att konfigurera, svårare att felsöka och lättare att konfigurera fel.

Den nya Core v1 fokuserar på ett **enkelt och förutsägbart beteende**.

De flesta användare behöver bara konfigurera:

* Källa för innetemperatur
* Källa för utetemperatur
* Källa för elpris
* Komforttemperatur

Kärnlogiken hanterar sedan:

* Prisrespons
* Bromsbeteende
* Komfortskydd
* Övertemperaturskydd

...automatiskt.

Detta innebär att **SVOTC kräver väldigt lite manuell justering** vid normal användning.

Designmålet är att systemet ska fungera väl **direkt ur lådan**, utan att användaren behöver förstå den interna kontrollogiken.

---

## Rekommenderad metod för migrering

När du uppgraderar från 2.x.x:

1. Ta bort gamla filer
2. Installera de nya 3.0.0 Core v1-filerna
3. Ställ in läget till `PassThrough` först
4. Verifiera alla källmappningar (source mappings)
5. Bekräfta att `binary_sensor.svotc_inputs_healthy` är ON
6. Bekräfta att `sensor.svotc_virtual_outdoor_temperature` beter sig korrekt
7. Växla till `Smart` först efter verifiering

---

## Påminnelse om Beta

SVOTC styr din värmepump indirekt via en virtuell utetemperatur.

Även om den nya kärnan är enklare och stabilare, kan felaktig konfiguration fortfarande påverka:

* Innekomfort
* Värmepumpens cyklingsbeteende
* Den totala systemeffektiviteten

Gör alltid följande:

* Testa i **PassThrough** först
* Övervaka `input_text.svotc_reason_code`
* Ha en manuell fallback (reservplan) tillgänglig under första driftsättningen

Rapportera buggar via GitHub Issues.

---

**Version:** SVOTC 3.0.0 Beta

**Core:** Core v1

**Licens:** MIT
