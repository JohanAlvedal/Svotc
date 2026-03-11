# 💥 Breaking Changes – SVOTC 2.0 (Beta)

> ⚠️ **BETA-MJUKVARA — ANVÄND PÅ EGEN RISK**
>
> SVOTC 2.0 är i aktivt beta-test. Funktioner kan förändras utan förvarning, buggar kan förekomma och konfigurationen kan bryta framtida uppgraderingar. Använd inte i produktionsmiljöer utan att förstå riskerna. **Du ansvarar själv för eventuella konsekvenser på ditt värmesystem.**

---

## Filstruktur är nu uppdelad i separata filer

Den enskilt största förändringen i 2.0 är att **hela konfigurationen är splittad från en stor `svotc.yaml` till flera mindre filer**, organiserade i en gemensam mapp. Detta är en **obligatorisk förändring** — den gamla enkelfilen fungerar inte med 2.0.

---

## Vad har ändrats?

### Tidigare struktur (1.x)
```
/config/packages/
└── svotc.yaml   ← en enda fil med all konfiguration
```

### Ny struktur (2.0)
```
/config/packages/svotc/
├── 00_helpers.yaml       ← Hjälpfunktioner och mallar
├── 10_sensors.yaml       ← Sensorkonfiguration och hälsokontroller
├── 20_price_fsm.yaml     ← Prislogik och tillståndsmaskin (P30/P80)
├── 22_engine.yaml        ← Core control loop och offset-logik
├── 30_learning.yaml      ← Självjusterande brake-efficiency
└── 40_notify             ← Notifikationer och diagnostik
```

---

## Vad behöver du göra?

### 1. Ta bort din gamla fil
```
/config/packages/svotc.yaml  ← radera eller arkivera denna
```

### 2. Skapa en ny mapp
```
/config/packages/svotc/
```

### 3. Kopiera in de nya filerna
Hämta alla filer från [`beta-testing/2.0`](https://github.com/JohanAlvedal/Svotc/tree/main/beta-testing/2.0) och lägg dem i den nya mappen.

### 4. Kontrollera din `configuration.yaml`
Har du redan detta är du klar — annars lägg till:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

> ✅ Alla sex filer måste finnas på plats. De är beroende av varandra.

### 5. Starta om Home Assistant

### 6. Verifiera att allt fungerar
Efter omstart, kontrollera:
- `binary_sensor.svotc_inputs_healthy` → ska vara **ON**
- `binary_sensor.svotc_price_available` → ska vara **ON**
- `input_text.svotc_reason_code` → ska visa `NEUTRAL` eller annan aktiv kod

---

## Övriga ändringar i 2.0

- **Buggfixar** från 1.x-serien
- `svotc_requested_offset_c` och `svotc_applied_offset_c` har utökat max från **10°C → 20°C**

---

## Varför denna förändring?

Den uppdelade strukturen gör det enklare att:
- **Felsöka** — varje modul (sensorer, prislogik, engine, learning) är isolerad
- **Uppdatera** — enskilda filer kan uppdateras utan att röra resten
- **Förstå** — namngivningen (00_, 10_, 20_...) speglar laddningsordningen och systemets flöde

---

## ⚠️ Påminnelse om beta-status

SVOTC styr din värmepump indirekt via en virtuell utomhustemperatur. Felaktig konfiguration kan påverka inomhuskomforten eller värmepumpens driftsekonomi. Systemet är designat för att vara stabilt, men:

- Testa alltid i **PassThrough-läge** innan du aktiverar Smart-läge
- Övervaka `input_text.svotc_reason_code` under de första dagarna
- Ha alltid en manuell fallback om något går fel

Rapportera buggar via [GitHub Issues](https://github.com/JohanAlvedal/Svotc/issues).

---

**Version:** 2.0 Beta (2026)  
**Licens:** MIT — fritt att använda och ändra, men utan garanti av något slag.

# SVOTC — Smart Virtual Outdoor Temperature Control

### Beta Edition (2026)

SVOTC är ett stabilt och förutseende styrsystem för värmepumpar i Home Assistant.
Det optimerar värmeproduktion genom att kombinera komfortskydd och prislogik, med mjuka övergångar och tydliga förklaringar (reason codes).

Systemet är byggt för att vara:

* ✅ **Stabilt** — inga oscillationer eller instabila tillstånd
* ✅ **Förutsägbart** — tydlig logik med full observability
* ✅ **Självkorrigerande** — via stabiliserande lager (dwell, hysteresis, ramp-limit)
* ✅ **Enkelt att felsöka** — omfattande diagnostik och reason codes
* ✅ **Autonomt** — kräver minimal inblandning efter setup

---

## 🆕 Vad som är nytt i 3.0.0 (beta-testing/3.0.0)

SVOTC 3.0.0 bygger på en enklare kärna med fyra paketfiler (`00_helpers`, `10_sensors`, `20_engine`, `30_notify`) istället för fler specialiserade delsystem.

Det innebär i praktiken:

* Färre rörliga delar och en tydligare prioriteringsordning i en enda motor-loop
* Stabilare och mindre aggressiv styrning mot hårdvara via begränsad ändringshastighet per minut
* Tydlig separation mellan **requested offset** (vad logiken vill göra) och **applied offset** (vad som faktiskt skickas efter rampning)
* Komfortskydd prioriteras över prisstyrning i Smart-läge
* Prislogiken är mer transparent med explicita tillstånd: `brake`, `hold`, `prebrake`, `cheap`, `neutral`
* Övertemperaturbroms ("over-brake") finns som separat skyddsspår när innetemperaturen blir för hög

---

## Funktioner

### Komfortstyrning

* Håller inomhustemperaturen nära ett mål
* Komfortskydd aktiveras när temperaturen sjunker för lågt
* Komfortskydd har högre prioritet än prisstyrning i Smart-läge
* Hysteresis via latchar förhindrar studsning mellan aktiv/inaktiv komfort- och övertemperaturbroms

### Prisoptimering

* Använder **P30/P80-percentiler från `raw_today`** för att avgöra billiga/dyra perioder (Ngenic-liknande dagsfokus)
* **Forward price state** använder tillstånden `brake`, `hold`, `prebrake`, `cheap`, `neutral`
* `prebrake` aktiveras när nästa kommande brake-block ligger inom 15 minuter
* `hold` håller kvar bromsläge mellan närliggande brake-block för att undvika onödiga växlingar
* P30/P80 beräknas fortsatt från `raw_today`; `raw_tomorrow` används endast för forward-look

### Modularitet

Alla delar är separerade för enkel förståelse och underhåll:

* **00_helpers.yaml** — användarinställningar och intern state
* **10_sensors.yaml** — normalisering av input, percentiler, forward price state och hälsokontroll
* **20_engine.yaml** — en enda kontroll-loop med tydlig prioritet och rampning
* **30_notify.yaml** — notifiering om fail-safe kvarstår i minst 5 minuter

### Stabilitet

* **Fail-safe** vid ohälsosamma inputs: requested offset tvingas mot 0
* **Rate-limiter** via `svotc_max_delta_per_step_c` begränsar hur snabbt applied offset får ändras
* **Hälsokontroller** för alla inputs
* Tydliga min/max-gränser för offsets och skyddsparametrar

---

## 📦 Installation

### 1. Skapa en ny fil i Home Assistant

Lägg filen i:

```
/config/packages/svotc.yaml
```

Eller valfri plats om du använder `packages:` i `configuration.yaml`.

### 2. Aktivera packages (om inte redan gjort)

I din `configuration.yaml`, lägg till:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### 3. Klistra in rätt paketfil, t.ex. **svotc_v1.1.3-beta.yaml**


### 4. Starta om Home Assistant

### 5. Gå till Inställningar → Enheter & tjänster → Helpers

Där hittar du alla SVOTC-kontroller.

### 6. Viktigt vid första start (`svotc_initialized`)

För kompatibilitet är `input_boolean.svotc_initialized` satt till `on` från början.
Gör så här för säker first-run-init:

1. Sätt `input_boolean.svotc_initialized` till **off**
2. Vänta 30–60 sekunder så init-automation hinner skriva standardvärden
3. Verifiera att helpers fått rimliga defaultvärden
4. Låt `svotc_initialized` gå tillbaka till **on** (automatiskt eller manuellt)

Tips: Lägg gärna detta som punkt i din installationschecklista så det inte missas.

---

## ⚡ Quick Start (5 minuter)

**Följ dessa steg för att komma igång snabbt:**

1. **Installera filen** enligt ovan
2. **Starta om** Home Assistant
3. **Konfigurera entiteter:**
   - Gå till **Developer Tools → States**
   - Hitta dina temperatur- och pris-entiteter
   - Ange dem i:
     - `input_text.svotc_entity_indoor` → din inomhussensor
     - `input_text.svotc_entity_outdoor` → din utomhussensor  
     - `input_text.svotc_entity_price` → din Nordpool-sensor
4. **Sätt mode till Smart:**
   - `input_select.svotc_mode` → `Smart`
5. **Vänta 2-3 minuter** för första körningen
6. **Verifiera att det fungerar:**
   - Kolla `input_text.svotc_reason_code`
   - Om `NEUTRAL` eller `PRICE_BRAKE` → allt är OK
   - Om `MISSING_INPUTS_FREEZE` → kontrollera entitetsmappning

**Troubleshooting:** Om inget händer efter 5 minuter, kolla:
- `binary_sensor.svotc_inputs_healthy` (ska vara ON)
- `binary_sensor.svotc_price_available` (ska vara ON)
- `input_text.svotc_reason_code` för diagnos

---

## 🛠 Konfiguration

### Obligatoriska entiteter

Du måste ange dessa tre entiteter:

| Typ | Input | Exempel | Format |
|-----|--------|----------|---------|
| Inomhustemperatur | `input_text.svotc_entity_indoor` | `sensor.indoor_temp` | Numeriskt värde i °C |
| Utomhustemperatur | `input_text.svotc_entity_outdoor` | `sensor.outdoor_temp` | Numeriskt värde i °C |
| Nordpool-entitet | `input_text.svotc_entity_price` | `sensor.nordpool_kwh_se3` | Nordpool-integration med state=`current_price` och attribut `raw_today` (gärna även `raw_tomorrow`) |

**OBS:** Nordpool-entiteten måste vara från **Nordpool-integrationen** eller kompatibel.

- **P30/P80 beräknas endast från `raw_today`** (dagens priser).
- `raw_tomorrow` används bara för forward-look/bridge-hold när morgondagens block finns tillgängliga.

### Rekommenderade inställningar

| Parameter | Värde | Förklaring |
|-----------|-------|------------|
| Mode | **Smart** | Full autonom styrning |
| Prebrake lead time | **30 min** | Grundfönster före dyrperiod |
| Bridge-hold window | **45–90 min** | Undvik dip mellan nära pris-toppar |
| Thermal mass factor | **1.0** | Normal villa, justera sedan |
| Comfort temperature | **21.0°C** | Ditt önskade mål |
| Comfort guard | **PÅ** | Alltid rekommenderat |
| Brake hold offset | **6.0°C** | Maximal offset under dyra perioder |
| Minimum brake price | **0.10 SEK/kWh** | Hindrar bromsning vid extremt låga/negativa priser |

### Finjustering efter ditt hus

**Lätt hus** (snabb värme/kyla, dålig isolering):
- Thermal mass factor: **0.6–0.8**
- Prebrake lead time: **15–30 min**
- Brake hold offset: **4–6°C**

**Normal villa:**
- Thermal mass factor: **1.0**
- Prebrake lead time: **30 min**
- Brake hold offset: **6°C**

**Tung villa** (bra isolering, långsam värme/kyla):
- Thermal mass factor: **1.3–1.8**
- Prebrake lead time: **40–60 min**
- Brake hold offset: **6–8°C**

---

## 🧪 Driftlägen

| Mode | Beskrivning | Användning |
|------|-------------|------------|
| **Smart** | Full autonom styrning med komfortprioritet, prisstyrning och skydd mot övertemperatur | **Rekommenderas för daglig drift** |
| **Comfort** | Fristående enkel temperaturreglering kring komfortmål, utan prislogik | När du vill fokusera enbart på innetemperatur |
| **PassThrough** | Ingen offset appliceras (requested = 0) men sensorer/diagnostik uppdateras | Testning och kalibrering |
| **Off** | Systemet tvingar offset mot 0 | Underhåll eller felsökning |

---

## 🔌 Koppla till värmepumpen

SVOTC styr **inte direkt** din värmepump. Istället skapar den en **virtuell utomhustemperatur** som du måste skicka till pumpen.

### Huvudutput

```
sensor.svotc_virtual_outdoor_temperature
```

Detta är den temperatur din värmepump ska använda istället för verklig utomhustemperatur.

---

### Kopplingsmetoder

SVOTC kan kopplas till din värmepump på flera sätt:

#### 1. Via Ohmigo Ohm-on WiFi Plus (Rekommenderat)

**[Ohmigo Ohm-on WiFi Plus](https://www.ohmigo.io/product-page/ohm-on-wifi-plus)** är en WiFi-adapter som gör det enkelt att integrera SVOTC med din värmepump.

**Fördelar:**
- ✅ **Plug & Play** — enkel installation
- ✅ **WiFi-baserad** — kommunicerar direkt med Home Assistant
- ✅ **Kompatibel med många värmepumpar**
- ✅ **Ingen molntjänst krävs** — fungerar lokalt

**Installation:**
1. Montera Ohm-on WiFi Plus enligt tillverkarens instruktioner
2. Anslut enheten till ditt WiFi-nätverk
3. Integrera med Home Assistant (via MQTT)
4. Skapa en automation som läser `sensor.svotc_virtual_outdoor_temperature`
5. Skicka värdet till värmepumpen via Ohmigo-enheten
---

## 📊 Viktiga sensorer

### Primära outputs

| Sensor | Funktion | Typiskt värde |
|--------|----------|---------------|
| `sensor.svotc_virtual_outdoor_temperature` | **Den temperatur som skickas till värmepumpen** | Outdoor temp ± offset |
| `input_number.svotc_applied_offset_c` | **Aktuell offset** (efter rate-limit) | -2 till +8°C |
| `input_text.svotc_reason_code` | **Förklaring till senaste beslut** | NEUTRAL, PRICE_BRAKE, etc. |

### Diagnostik

| Sensor | Funktion |
|--------|----------|
| `input_number.svotc_requested_offset_c` | Rå offset från engine (före rate-limit) |
| `binary_sensor.svotc_inputs_healthy` | ON = alla sensorer fungerar |
| `sensor.svotc_forward_price_state` | Prisrelaterat framåtblickande tillstånd (`brake`/`hold`/`prebrake`/`cheap`/`neutral`) |
| `sensor.svotc_price_p30_today` | Dagens P30-tröskel |
| `sensor.svotc_price_p80_today` | Dagens P80-tröskel |

### Reason codes

| Code | Betydelse |
|------|-----------|
| `NEUTRAL` | Normal drift, inget pågår |
| `PRICE_BRAKE` | Aktiv prisbromsning |
| `PRICE_PREBRAKE` | Förbromsning innan nästa dyra block |
| `PRICE_HOLD` | Håller kvar broms mellan närliggande dyra block |
| `PRICE_CHEAP` | Billigperiod, negativ boost om cheap boost är aktiverad |
| `COMFORT_GUARD` | Komfortskydd aktivt |
| `OVERTEMP_BRAKE` | Övertemperaturskydd aktivt |
| `FAIL_SAFE` | Inputs ohälsosamma, requested sätts till 0 och applied rampas mot 0 |
| `PASS_THROUGH` | PassThrough mode aktiv |
| `COMFORT_HEAT` | Comfort-mode begär negativ offset (mer värme) |
| `COMFORT_BRAKE` | Comfort-mode begär positiv offset (broms) |
| `COMFORT_IDLE` | Comfort-mode utan behov av korrigering |
| `COMFORT_SENSOR_MISSING` | Comfort-mode saknar giltig innetemperatur |
| `OFF` | Systemet avstängt |

---

## 📈 Rekommenderad Dashboard

SVOTC levereras med **färdiga kort** som du kan kopiera in i din dashboard.

### Metod 1: Lägg till i befintlig dashboard (Enklast)

Detta är det **rekommenderade sättet** - lägg till SVOTC-kort i din befintliga dashboard.

#### Steg 1: Öppna din dashboard i edit-läge

1. Gå till din **Hemskärm** (eller valfri dashboard)
2. Klicka på **pennikonen** (Edit Dashboard) uppe till höger

#### Steg 2: Lägg till ett nytt kort

1. Klicka på **"+ ADD CARD"** där du vill ha kortet
2. Scrolla ner i kortlistan
3. Klicka på **"MANUAL"** längst ner (eller välj ett befintligt kort först)
4. Du ser nu en kod-editor med YAML

#### Steg 3: Klistra in kortets YAML

1. **Radera** det som står i editorn
2. Öppna filen **`SVOTC_Cards.yaml`** från repot
3. **Kopiera** det kort du vill ha (t.ex. "Kontrollpanel")
4. **Klistra in** i editorn
5. Klicka **"SAVE"**

#### Steg 4: Upprepa för fler kort

Lägg till fler kort genom att upprepa steg 2-3 för varje kort du vill ha.

**Klart!** Dina SVOTC-kort är nu tillagda. 🎉

---

### Metod 2: Skapa en dedikerad SVOTC-dashboard (Sections)

Om du vill ha en **egen dashboard för SVOTC** med Sections-layout:

#### Steg 1: Skapa en ny dashboard

1. Gå till **Settings → Dashboards**
2. Klicka på **"+ ADD DASHBOARD"** (nere till höger)
3. Välj **"New dashboard"**
4. Namn: **"SVOTC Control"**
5. Typ: Välj **"Sections (experimental)"** om tillgänglig, annars standard
6. Klicka **"CREATE"**

#### Steg 2: Lägg till en Section

1. På den nya dashboarden, klicka **"EDIT DASHBOARD"**
2. Klicka **"+ ADD SECTION"**
3. Välj **"Grid"**

#### Steg 3: Lägg till kort i sectionen

1. I den nya grid-sectionen, klicka **"+ ADD CARD"**
2. Scrolla ner och välj **"MANUAL"** (eller sök efter korttyp)
3. I YAML-editorn som öppnas:
   - **Radera** befintligt innehåll
   - **Klistra in** ett kort från `SVOTC_Cards.yaml`
   - Klicka **"SAVE"**
4. Upprepa för varje kort du vill ha

#### Steg 4: Lägg till badges (valfritt)

1. I edit-läge, klicka på **"MANAGE BADGES"** (om tillgängligt)
2. Lägg till relevanta entiteter som badges:
   - `sensor.svotc_virtual_outdoor_temperature`
   - `input_text.svotc_reason_code`
   - `binary_sensor.svotc_inputs_healthy`

**Klart!** Du har nu en dedikerad SVOTC-dashboard. 🎉

---

### Tillgängliga kort i SVOTC_Card1.yaml / SVOTC_Card2.yaml

#### 🎛️ Kontrollpanel (`entities`)
**Innehåll:**
- Driftsläge (Smart/Simple/ComfortOnly/etc.)
- Komfortinställningar (mål, guard-trösklar)
- Prisoptimering (brake/heat aggressiveness)
- Thermal mass factor
- Comfort guard on/off

**Användning:** Primära kontroller för daglig användning.

---

#### 📊 Offset-graf (`mini-graph-card`) ⭐ Rekommenderad
**Innehåll:**
- Requested offset (orange)
- Applied offset (röd)
- 24h historik

**Användning:** Se hur systemet justerar offset över tid.

---

#### 🌡️ Temperaturgraf (`mini-graph-card`)
**Innehåll:**
- Outdoor verklig (blå)
- Virtual outdoor → VP (lila)
- 24h historik

**Användning:** Se skillnaden mellan verklig och virtuell utetemperatur.

---

#### 💵 Prisgraf (`mini-graph-card`)
**Innehåll:**
- Nordpool-pris
- 24h historik

**Användning:** Övervaka elpriset och förstå när systemet bromsar.

---

#### 🔬 Diagnostik (`entities`)
**Innehåll:**
- Systemhälsa (sensors OK, price available)
- Timing (minuter till nästa brake, prebrake window)
- Prisstatus (raw → pending → stable)
- Brake phase

**Användning:** Felsökning och förståelse av systemets interna tillstånd.

---

#### 📋 System Status (`markdown`) ⭐ Kraftfull
**Innehåll:**
- Live systemöversikt med dynamiska beräkningar
- Temperaturstatus med offset-detaljer
- Prisstyrning med prebrake-indikator
- Komfortskydd med trösklar
- Bromsfas med progress
- Expanderbara diagnostikdetaljer
- Strategi-förklaring

**Användning:** En enda överblick över ALLT systemet gör.

**OBS:** Detta kort kräver mycket utrymme - rekommenderas i egen sektion.

---

#### 🎯 Snabbstatus (`horizontal-stack` med entities)
**Innehåll:**
- SVOTC Mode + System OK (rad 1)
- Comfort Guard + Reason Code (rad 2)

**Användning:** Kompakt statusöversikt.

---

### Beroenden (custom cards)

Graferna använder **mini-graph-card** från HACS:

#### Installera mini-graph-card (Rekommenderat):

1. Öppna **HACS** → **Frontend**
2. Sök efter **"mini-graph-card"**
3. Klicka **"Download"**
4. Starta om Home Assistant

**Alternativ utan custom cards:**
- Skippa grafkorten
- Eller ersätt med standard `history-graph`:
  ```yaml
  type: history-graph
  entities:
    - entity: input_number.svotc_applied_offset_c
  hours_to_show: 24
  ```

---

### Rekommenderad layout

För bästa översikt, använd denna ordning:

**Sektion 1 (Grid):**
1. 🎯 Snabbstatus (överst för snabb överblick)
2. 🎛️ Kontrollpanel (primära inställningar)
3. 📊 Offset-graf (viktigaste grafen)
4. 🌡️ Temperaturgraf
5. 💵 Prisgraf

**Sektion 2 (Grid, valfri):**
1. 📋 System Status (markdown) - hel bredd
2. 🔬 Diagnostik (för nördarna)

---

### Snabbtips

#### Redigera ett befintligt kort:
1. Håll nere på kortet (mobil) eller klicka tre prickar (desktop)
2. Välj **"Edit"**
3. Klicka **"SHOW CODE EDITOR"** (nere till höger)
4. Gör dina ändringar
5. Spara

#### Ta bort delar du inte behöver:
Öppna kortet i YAML-läge och ta bort rader. Exempel:
```yaml
entities:
  - entity: input_number.svotc_comfort_temperature
  # - entity: input_number.svotc_prebrake_lead_time_min  ← Ta bort denna rad om du inte vill ändra den
```

---

## 🧠 Lärande

SVOTC kan (i learning-varianten) använda en enkel **självjustering** som anpassar bromsningen över tid baserat på hur ofta komfortskyddet behöver ingripa.

### Hur det fungerar

1. Varje gång **komfortskyddet aktiveras** räknas en “komfortavvikelse”.
2. Vid **midnatt varje natt** analyseras senaste 24 timmarna med en finstegad kurva:

   * **>5 avvikelser** → systemet har varit för aggressivt → **minska brake-efficiency med 0.05**
   * **3–5 avvikelser** → något för aggressivt → **minska brake-efficiency med 0.02**
   * **0 avvikelser** → systemet kan bromsa mer → **öka brake-efficiency med 0.03**
   * **1 avvikelse** → nära balans men kan bromsa lite mer → **öka brake-efficiency med 0.01**
   * **2 avvikelser** → balans → **behåll nuvarande värde**
3. Räknaren nollställs.
4. Nästa dag används den uppdaterade effektiviteten i prisbromsningen.

Värdet klampas alltid till intervallet **0.5–1.5**.

### Konvergens

Systemet brukar stabilisera sig efter några dygn till någon vecka, men tiden varierar beroende på husets tröghet, väder, värmepumpens kurva och elprisernas mönster.

---

### Manuell överridning

Du kan alltid manuellt justera:
```
input_number.svotc_learned_brake_efficiency
```

Normalintervall: **0.5–1.5**
- 0.5 = mycket försiktig (liten offset)
- 1.0 = normal (rekommenderad start)
- 1.5 = aggressiv (stor offset)

---

## 🔔 Notifieringar

Systemet skickar automatiska notiser vid:

| Event | Trigger | Delay |
|-------|---------|-------|
| 🔴 Saknade inputs | `binary_sensor.svotc_inputs_healthy` = OFF | 3 minuter |
| 🔴 Saknade prisdata | `binary_sensor.svotc_price_available` = OFF | 3 minuter |
| 🟡 Comfort guard avstängt | `input_boolean.svotc_comfort_guard_enabled` = OFF | 5 minuter |
| 🟢 Återhämtning | Båda sensors = ON | 2 minuter |

### Konfigurera notifieringstjänst

Ange vilken notify-service som ska användas:

```
input_text.svotc_notify_service
```

**Exempel:**
- `notify.mobile_app_johan` (HA Companion App)
- `notify.telegram` (Telegram)
- `notify.pushover` (Pushover)
- `notify.notify` (default, alla notifieringstjänster)

### Exempelmeddelanden

**Vid problem:**
```
SVOTC: Missing data

Inputs eller prisdata saknas sedan minst 3 minuter.

Missing mappings: price mapping
Sources:
  indoor=21.3
  outdoor=5.2
  price=unknown
```

**Vid återhämtning:**
```
SVOTC: OK again

Inputs + price data är stabila igen.
```

---

---

## ❓ FAQ (Vanliga frågor)

### Installation & Konfiguration

**Q: Varför rör sig inte offset?**  
**A:** Kolla `input_text.svotc_reason_code`. Troligen:
- `MISSING_INPUTS_FREEZE` → saknar sensorer, kontrollera entitetsmappning
- `PRICE_DATA_WARMUP_FREEZE` → väntar på tillräcklig prisdata (främst `raw_today`) innan prislogik släpps
- `OFF` → systemet är avstängt, sätt mode till Smart

**Q: Hur vet jag att det fungerar?**  
**A:** Efter 2-3 minuter bör du se:
1. `binary_sensor.svotc_inputs_healthy` = ON
2. `binary_sensor.svotc_price_available` = ON
3. `input_text.svotc_reason_code` = NEUTRAL (eller annan aktiv kod)
4. `input_number.svotc_applied_offset_c` ändras gradvis

**Q: Vilken Nordpool-integration behöver jag?**  
**A:** Den officiella **Nordpool-integrationen** från HACS eller core. Sensorn måste ha attributen:
- `current_price`
- `raw_today` (lista med prisblock för idag)
- `raw_tomorrow` (valfritt men rekommenderat för bättre forward-look/bridge-hold)

**Tips:** Om du använder den officiella Nordpool-integrationen, kan du använda paketfilen från [Nordpool-official](https://github.com/custom-components/nordpool) för enklare konfiguration.

**Q: Vilken hårdvara behöver jag för att koppla SVOTC till min värmepump?**  
**A:** Det beror på din värmepump:
- **Rekommenderat:** [Ohmigo Ohm-on WiFi Plus](https://www.ohmigo.io/product-page/ohm-on-wifi-plus) — fungerar med de flesta värmepumpar och ger fullständig lokal kontroll
- **Annat:** Kontrollera om din pumpintegration stöder temperaturoffset eller värmekurva

### Prestanda & Tuning

**Q: Systemet är för aggressivt / för försiktigt**  
**A:** Justera i denna ordning:
1. `input_number.svotc_prebrake_lead_time_min` → hur tidigt prebrake ska börja
2. `input_number.svotc_thermal_mass_factor` (0.5-2.0) → anpassa till husets tröghet
3. `input_number.svotc_brake_hold_offset_c` (0-20) → max offset under dyra perioder
4. `input_number.svotc_bridge_hold_window_min` → minska/öka brohållning mellan toppar
5. Vänta 3-5 dagar om learning/autotune är aktiv innan ny större justering

**Q: Kan jag inaktivera learning?**  
**A:** Ja, ta bort automationen `SVOTC Learning: reset daily counter`. Då behåller systemet alltid det manuella värdet i `svotc_learned_brake_efficiency`.

### Tekniska frågor

**Q: Hur fungerar freeze-logiken?**  
**A:** När prisdata saknas:
1. **Comfort guard fortsätter fungera** (säkerhet först)
2. **Price logic frysas** på senast kända värde
3. **Offset ändras inte** (rate-limiter håller nuvarande värde)
4. **Notifikation skickas** efter 3 minuter
5. När data återkommer → systemet fortsätter normalt

**Q: Vad händer om Nordpool går ner?**  
**A:** 
1. Systemet detekterar saknad prisdata inom 1 minut
2. Övergår till freeze-mode (behåller senaste offset)
3. Comfort guard fortsätter fungera
4. Du får en notis efter 3 minuter
5. När Nordpool är uppe igen återgår allt till normalt

### Support & Community

**Q: Kan jag bidra?**  
**A:** Absolut! Pull requests välkomnas för:
- Buggfixar
- Dokumentationsförbättringar
- Översättningar

---

## 📝 Licens

**MIT License** — fritt att använda, ändra och dela.

```
Copyright (c) 2026 Johan Ä

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
---

## 📚 Ytterligare resurser

### Hårdvara för värmepumpstyrning

- [Ohmigo Ohm-on WiFi Plus](https://www.ohmigo.io/product-page/ohm-on-wifi-plus) — WiFi-adapter för värmepumpar


### Video tutorials

- *Coming soon: Installation guide*
- *Coming soon: Advanced tuning*
- *Coming soon: Integration examples*

---

**Version:** (2026-02-25)  
**Senast uppdaterad:** 2026-02-25
**Licens:** MIT
