# SVOTC + Nordpool Price Sensors

> Den här versionen är anpassad till paketet med sensorerna:
>
> * `sensor.elpris_spot_avgifter`
> * `sensor.elpris_svotc`
> * `sensor.elpris_chart`
> * `sensor.elpriskoefficient`
> * `sensor.nordpool_price_band`

---

## 🎯 Vad är detta?

Ett Nordpool-baserat paket för Home Assistant som ger dig:

1. **SVOTC-kompatibel prissensor** (`sensor.elpris_svotc`)
2. **Pris inklusive elhandelpåslag/elcertifikat/moms** (`sensor.elpris_spot_avgifter`)
3. **Prisfeed för grafer** (`sensor.elpris_chart`)
4. **Elpriskoefficient** (dynamisk relativ prisnivå)
5. **Prisband** (5 zoner: `very_cheap` → `very_expensive`)

Perfekt för SVOTC och egna prisstyrda automationer.

---

## ✅ Förkrav

Du måste ha **Nordpool-integrationen** installerad och fungerande i Home Assistant.

### Verifiera:

1. Gå till **Inställningar → Enheter och tjänster**
2. Sök efter **Nordpool**
3. Kontrollera att priser uppdateras

---

## 📥 Installation (3 steg)

## Steg 1: Hitta ditt `config_entry`-ID

### Enklaste sättet:

1. Gå till **Utvecklarverktyg → Tillstånd**
2. Sök efter din Nordpool-sensor (t.ex. `sensor.nordpool`)
3. Klicka på sensorn
4. Kopiera **`config_entry`** från attributen

### Alternativ via URL:

```text
Inställningar → Enheter och tjänster → Nordpool → Klicka på integrationen
URL:en innehåller config_entry:
.../config/integrations/integration/01KHAXM5D239V0B77VNTCDJ3RG
                                    ^^^^^^^^^^^^^^^^^^^^^^^^
                                    Kopiera denna del
```

---

## Steg 2: Anpassa YAML-filen

Öppna paketfilen och ändra dessa värden:

### ⚠️ Viktigt: Ändra `config_entry` på BÅDA ställena

Du har två anrop till `nordpool.get_prices_for_date`:

* ett för **idag**
* ett för **imorgon**

Byt ut `config_entry` i båda.

### ⚠️ Viktigt: Ändra `areas` på BÅDA ställena

Exemplet använder `SE3`. Byt till din elområdekod om du inte bor i SE3.

### Exempel (detta ska ändras)

```yaml
config_entry: 01KHAXM5D239V0B77VNTCDJ3RG  # ← byt till ditt ID
areas: SE3                                # ← byt till ditt område (SE1/SE2/SE3/SE4)
```

### Sammanfattning av ändringar

| Vad            | Var                       | Exempel               |
| -------------- | ------------------------- | --------------------- |
| `config_entry` | **Båda Nordpool-anropen** | `01KHAX...` → ditt ID |
| `areas`        | **Båda Nordpool-anropen** | `SE3` → ditt område   |

### Svenska elområden

* **SE1** – Norra Sverige (Luleå)
* **SE2** – Norra Mellansverige (Sundsvall)
* **SE3** – Södra Mellansverige (Stockholm)
* **SE4** – Södra Sverige (Malmö)

💡 Tips: använd **Sök och ersätt** i editorn:

```text
Sök:      01KHAXM5D239V0B77VNTCDJ3RG
Ersätt:   DITT_CONFIG_ENTRY_HÄR
```

---

## Steg 3: Installera paketfilen

Lägg filen här:

```bash
/config/packages/svotc_nordpool_price.yaml
```

Starta sedan om Home Assistant.

---

## ⚙️ Konfiguration – ställ in dina elhandelsvärden

Efter omstart skapas tre `input_number`-helpers som du ska fylla i.

### Elhandel (input_number)

| Helper                            | Beskrivning         | Typiskt värde |
| --------------------------------- | ------------------- | ------------- |
| `Elhandel påslag (SEK/kWh)`       | Elhandlarens påslag | 0.035–0.050   |
| `Elhandel elcertifikat (SEK/kWh)` | Elcertifikat        | 0.005–0.015   |
| `Elhandel moms (%)`               | Moms på elhandel    | 25            |

### Så här ställer du in dem:

1. Gå till **Inställningar → Enheter och tjänster → Hjälpare**
2. Sök efter:

   * `Elhandel påslag`
   * `Elhandel elcertifikat`
   * `Elhandel moms`
3. Fyll i värden från ditt avtal

### Exempel (svensk elhandel)

```text
Elhandel påslag:       0.040 SEK/kWh
Elhandel elcertifikat: 0.010 SEK/kWh
Elhandel moms:         25 %
```

> Obs: Den här YAML-versionen räknar **elhandel** (spot + påslag + elcertifikat + moms).
> Den inkluderar **inte nätavgift/energiskatt** i totalen.

---

## 🔗 Koppla till SVOTC

Huvudsensorn för SVOTC är:

```text
sensor.elpris_svotc
```

### I SVOTC entity mapping

1. Öppna **Hjälpare**
2. Sök: `svotc_entity_price`
3. Sätt värde till:

```text
sensor.elpris_svotc
```

### Alternativ via YAML

```yaml
input_text:
  svotc_entity_price:
    initial: "sensor.elpris_svotc"
```

---

## 📊 Vilka sensorer skapas?

## 1) Prissensorer

### `sensor.elpris_spot_avgifter`

Pris inklusive:

* Spotpris (Nordpool)
* Elhandelspåslag
* Elcertifikat
* Elhandel moms

**Attribut:**

* `min` – dagens lägsta pris (inkl avgifter)
* `max` – dagens högsta pris (inkl avgifter)
* `raw_today` – dagens 24 timpriser (SVOTC-format)
* `raw_tomorrow` – morgondagens timpriser när de publiceras

---

### `sensor.elpris_svotc` ⭐

SVOTC-kompatibel prisfeed (samma prislogik som ovan) med SVOTC-vänliga attribut.

**Attribut:**

* `raw_today`
* `raw_tomorrow`
* `unit: kWh`
* `currency: SEK`
* `country: Sweden`
* `region: SE3` (ändra i YAML om annat område)

Den här använder du i SVOTC.

---

### `sensor.elpris_chart`

En separat sensor för historik/grafer.

* Hämtar state från `sensor.elpris_svotc`
* Bra om du vill logga en lättare sensor i Recorder

---

## 2) Analyssensorer

### `sensor.elpriskoefficient`

Dynamisk prisnivå relativt dagens prisintervall.

* **< 1.0** = billigt
* **> 1.0** = dyrt

Bra för automationer, t.ex.:

* Kör tvättmaskin när koefficient < 0.8
* Stoppa last när koefficient > 1.2

---

### `sensor.nordpool_price_band`

Priszon i 5 nivåer med hysteresis (mindre fladder):

* `very_cheap`
* `cheap`
* `normal`
* `expensive`
* `very_expensive`

Bra för enklare logik i automationer (utan att behöva jämföra exakta tal).

---

## 🧮 Prisberäkning (i denna YAML-version)

Den här versionen räknar:

```python
spotpris + elhandelspåslag + elcertifikat
→ därefter elhandel moms
```

### Exempel

```python
Spotpris             = 0.50 SEK/kWh
+ Elhandel påslag    = 0.04 SEK/kWh
+ Elcertifikat       = 0.01 SEK/kWh
= 0.55 SEK/kWh

Moms 25%:
0.55 * 1.25 = 0.6875 SEK/kWh
```

**Resultat:** `0.688 SEK/kWh` (avrundat)

---

## ⏱️ Uppdateringar

Sensorn uppdateras automatiskt:

* ✅ Var 10:e minut
* ✅ Vid omstart av Home Assistant
* ✅ När du ändrar någon `input_number`-helper
* ✅ Morgondagens priser dyker upp runt ca **13:00 CET**

---

## ❓ Felsökning

## Sensor blir `unavailable`

Kontrollera i denna ordning:

1. ✅ **Nordpool-integrationen fungerar**
2. ✅ **`config_entry` är rätt i båda anropen**
3. ✅ **`areas` är rätt i båda anropen**
4. ✅ **Testa tjänsten manuellt**

### Testa manuellt i Utvecklarverktyg → Tjänster

```yaml
service: nordpool.get_prices_for_date
data:
  config_entry: DITT_CONFIG_ENTRY_HÄR
  date: "{{ now().date() }}"
  areas: SE3
  currency: SEK
```

---

## Priserna verkar fel

Kontrollera:

1. ✅ Alla värden är i **SEK/kWh** (inte öre/kWh)
2. ✅ Moms är i **procent** (25, inte 0.25)
3. ✅ Du har fyllt i rätt helpers

### Verifiering

Öppna:

* `sensor.elpris_spot_avgifter`
* kontrollera attributen `min`, `max`, `raw_today`

---

## Morgondagens priser saknas

Detta är normalt före ungefär **13:00 CET**.

Nordpool publicerar normalt morgondagens priser runt den tiden.

---

## Prisband verkar “fastna”

Det är normalt att sensorn har hysteresis (2 %) för att undvika fladdrande mellan nivåer.

Vänta till nästa uppdatering (10 min) och kontrollera:

* `sensor.elpris_spot_avgifter` uppdateras
* `min`/`max` finns
* aktuellt pris ändras

---

## 🔍 Verifiera att allt fungerar

## Test 1: Alla sensorer finns

Sök i **Utvecklarverktyg → Tillstånd** efter:

```text
sensor.elpris_spot_avgifter
sensor.elpris_svotc
sensor.elpris_chart
sensor.elpriskoefficient
sensor.nordpool_price_band
```

---

## Test 2: SVOTC-sensorn har rätt attribut

Öppna `sensor.elpris_svotc` och kontrollera:

* `state` = ett numeriskt pris i SEK/kWh
* `raw_today` = lista med 24 poster
* `raw_tomorrow` = lista med 24 poster (efter ~13:00)
* `currency = SEK`
* `region = SE3` (eller ditt område)

---

## Test 3: SVOTC läser rätt pris

Sök efter:

```text
sensor.svotc_src_current_price
```

Det värdet ska matcha `sensor.elpris_svotc`.

---

## Test 4: Analyssensorer fungerar

Kontrollera:

* `sensor.elpriskoefficient` → typiskt ca `0.5–2.0`
* `sensor.nordpool_price_band` → ett av:

  * `very_cheap`
  * `cheap`
  * `normal`
  * `expensive`
  * `very_expensive`

---

## 📋 Snabb checklista

### Före installation

* [ ] Nordpool fungerar
* [ ] Jag har mitt `config_entry`
* [ ] Jag vet mitt elområde (SE1/SE2/SE3/SE4)

### Under installation

* [ ] Jag ändrade `config_entry` i **båda** Nordpool-anropen
* [ ] Jag ändrade `areas` i **båda** Nordpool-anropen
* [ ] Jag la filen i `/config/packages/`
* [ ] Jag startade om Home Assistant

### Efter installation

* [ ] Jag ser alla sensorer
* [ ] Jag har fyllt i elhandel-helpers
* [ ] `sensor.elpris_svotc` har `raw_today`
* [ ] SVOTC använder `sensor.elpris_svotc`
* [ ] Koefficient och prisband uppdateras

---

## ✅ Klart!

Nu har du:

* ✅ Nordpool-pris med elhandelspåslag/elcertifikat/moms
* ✅ SVOTC-kompatibel prisfeed
* ✅ Grafsensor för historik
* ✅ Dynamisk elpriskoefficient
* ✅ 5-zons prisband för automationer

---

## 📝 FAQ

### Vad är skillnaden mellan `sensor.elpris_spot_avgifter` och `sensor.elpris_svotc`?

De räknar i praktiken samma pris, men:

* `sensor.elpris_spot_avgifter` = “vanlig” prissensor med `min/max`
* `sensor.elpris_svotc` = SVOTC-feed med rätt attribut (`raw_today`, `raw_tomorrow`, m.m.)

---

### Ingår nätavgift och energiskatt i den här versionen?

Nej, inte i YAML:en du skickade.

Den här versionen räknar endast:

* spot
* elhandelpåslag
* elcertifikat
* elhandel moms

Om du vill kan jag också göra en **v2** av YAML:en som lägger till:

* nätöverföring
* energiskatt
* nätmoms
  …så du får ett “riktigt totalpris” igen.

---

### Varför finns `sensor.elpris_chart`?

För att du ska kunna logga en lättare sensor i Recorder och ändå ge SVOTC sin egen sensor med `raw_today/raw_tomorrow`.

---

### Vad är Recorder-tipset i slutet till för?

Det minskar databasbelastning.

Du kan exkludera `sensor.elpris_svotc` från Recorder (den har stora attribut), men ändå logga `sensor.elpris_chart` för historik/grafer.

---
