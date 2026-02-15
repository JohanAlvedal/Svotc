# SVOTC Bonus - Nordpool Prissensorer

> 🇬🇧 **English:** For instructions in English, see [README.md](./README.md).

---

## 🎯 Vad är detta?

Ett omfattande Nordpool-prispaket som ger dig:

1. **SVOTC-kompatibel prissensor** med alla avgifter inkluderade
2. **Priskoefficient** (dynamisk relativ prisnivå)
3. **Priszoner** (5 zoner: very_cheap → very_expensive)
4. **Hjälpsensorer** (pris OK, toppdetektion)

Perfekt för avancerade automationer och SVOTC-integration.

---

## ✅ Förutsättningar

Du måste ha **Nordpool-integrationen** installerad och fungerande i Home Assistant.

**Kontrollera:**
1. Gå till **Inställningar → Enheter & tjänster**
2. Sök efter "Nordpool"
3. Bekräfta att priserna uppdateras

---

## 📥 Installation (3 steg)

### Steg 1: Hitta ditt `config_entry` ID

**Enklaste metoden:**
1. Gå till **Utvecklarverktyg → Tillstånd**
2. Sök efter din Nordpool-sensor (t.ex. `sensor.nordpool`)
3. Klicka på sensorn
4. Kopiera **config_entry** från attributen

**Alternativ via URL:**
```
Inställningar → Enheter & tjänster → Nordpool → Klicka på integrationen
URL:en innehåller config_entry:
.../config/integrations/integration/01KGFMFDG6SDFKHQFKK5QKCJ5T
                                    ^^^^^^^^^^^^^^^^^^^^^^^^
                                    Kopiera denna del
```

---

### Steg 2: Anpassa filen

Öppna `svotc_bonus_nordpool_sensors.yaml` och ändra på **TVÅ STÄLLEN**:

⚠️ **VIKTIGT: Du måste ändra `config_entry` på BÅDA ställena i filen!**

```yaml
# FÖRSTA STÄLLET (runt rad 94):
action:
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← ÄNDRA TILL DITT
      date: "{{ now().date() }}"
      areas: SE3  # ← ÄNDRA TILL DITT ELOMRÅDE
      currency: SEK
    response_variable: today_price

# ANDRA STÄLLET (runt rad 102):
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← ÄNDRA TILL DITT (igen!)
      date: "{{ (now() + timedelta(days=1)).date() }}"
      areas: SE3  # ← ÄNDRA TILL DITT ELOMRÅDE (igen!)
      currency: SEK
    response_variable: tomorrow_price
```

**Sammanfattning av ändringar:**

| Vad            | Var             | Exempel                              |
| -------------- | --------------- | ------------------------------------ |
| `config_entry` | **Båda ställen** | `01KGFMFDG6SDFKHQFKK5QKCJ5T` → DITT |
| `areas`        | **Båda ställen** | `SE3` → Ditt område                   |

**Elområden (Sverige):**
* **SE1** – Norra Sverige (Luleå)
* **SE2** – Norra Mellansverige (Sundsvall)
* **SE3** – Södra Mellansverige (Stockholm)
* **SE4** – Södra Sverige (Malmö)

**💡 Tips:** Använd Sök & Ersätt (Ctrl+F) i din editor:
```
Sök:        01KGFMFDG6SDFKHQFKK5QKCJ5T
Ersätt:     DITT_CONFIG_ENTRY_HÄR
Ersätt alla: 2 träffar bör ersättas
```

---

### Steg 3: Installera filen

```bash
# Placera filen här:
/config/packages/svotc_bonus_nordpool_sensors.yaml

# Starta om Home Assistant
```

---

## ⚙️ Konfiguration - Ange dina avtalsvillkor

Efter omstart, konfigurera ditt elavtal i hjälparna:

### Elhandel
| Hjälpare                                     | Beskrivning              | Typiskt värde |
| -------------------------------------------- | ------------------------ | ------------- |
| `Elhandel påslag (SEK/kWh)`                  | Leverantörspåslag        | 0.035-0.050   |
| `Elhandel elcertifikat (SEK/kWh)`            | Elcertifikat             | 0.005-0.015   |
| `Elhandel moms (%)`                          | Moms på elhandel         | 25            |
| `Elhandel månadsavgift (SEK/månad)` (oanvänd)| Månadsavgift (bara info) | 0-50          |

### Nät
| Hjälpare                           | Beskrivning             | Typiskt värde |
| ---------------------------------- | ----------------------- | ------------- |
| `Nät elöverföring (SEK/kWh)`       | Nätavgift               | 0.30-0.50     |
| `Nät energiskatt (SEK/kWh)`        | Energiskatt             | 0.42          |
| `Nät moms (%)`                     | Moms på nät             | 25            |

**Ange dessa värden i gränssnittet:**
1. Gå till **Inställningar → Enheter & tjänster → Hjälpare**
2. Sök efter varje hjälpare
3. Ange dina värden från ditt avtal

**Exempel svenskt avtal (2026):**
```
Elhandel påslag:         0.040 SEK/kWh  (4.0 öre/kWh)
Elhandel elcertifikat:   0.010 SEK/kWh  (1.0 öre/kWh)
Elhandel moms:           25%
Nät elöverföring:        0.45 SEK/kWh
Nät energiskatt:         0.42 SEK/kWh
Nät moms:                25%
```

---

## 🔗 Koppla till SVOTC

Huvudprissensorn är: `sensor.elpris_total_inkl_avgifter_moms`

**I SVOTC entity mapping:**
1. Öppna **Hjälpare**
2. Sök: `svotc_entity_price`
3. Sätt värde till: `sensor.elpris_total_inkl_avgifter_moms`

**Eller via YAML:**
```yaml
input_text:
  svotc_entity_price:
    initial: "sensor.elpris_total_inkl_avgifter_moms"
```

---

## 📊 Vilka sensorer skapas

### 1. Prissensorer

#### `sensor.elpris_spot_exkl_moms`
Rent spotpris (inga avgifter, ingen moms)
- Användbart för jämförelser och grafer

#### `sensor.elpris_total_inkl_avgifter_moms` ⭐
**Totalpris inklusive ALLA avgifter** (använd denna för SVOTC!)
- Spotpris + elhandelspåslag + certifikat + nätavgifter + energiskatt + moms
- **SVOTC-kompatibla attribut:**
  - `current_price` - Nuvarande totalpris
  - `raw_today` - Lista med 24 timpriser (start/end/value)
  - `raw_tomorrow` - Lista med morgondagens priser (tom före ~13:00)
  - `min` / `max` - Lägsta/högsta pris idag
  - Alla dina avtalsdetaljer som attribut

### 2. Analyssensorer

#### `sensor.elpriskoefficient`
Dynamisk prisnivå relativt dagens spann
- **< 1.0** = Billigt (under tröskelvärde)
- **> 1.0** = Dyrt (över tröskelvärde)
- Använder smart formel som anpassar sig efter både min/max-nivåer
- Perfekt för automationer: "kör bara när koefficient < 0.8"

#### `sensor.nordpool_price_band`
5 priszoner med hysteres (förhindrar fladdring)
- `very_cheap` (0-15% av dagligt spann)
- `cheap` (15-35%)
- `normal` (35-65%)
- `expensive` (65-85%)
- `very_expensive` (85-100%)
- Inkluderar 2% hysteres för stabila övergångar

### 3. Hjälpsensorer (Binära)

#### `binary_sensor.elpris_ok`
Sant när priset är billigt OCH temperaturen är mild
- Koefficient < 1.0 OCH utetemp < 3°C
- Användbart för villkorlig uppvärmning/laddning

#### `binary_sensor.kort_peak_nu`
Sant under korta pristoppar
- Koefficient >= 1.0
- Användbart för att pausa icke-kritiska laster

---

## 🧮 Exempel på prisberäkning

```python
# Exempel spotpris från Nordpool
Spotpris                = 0.50 SEK/kWh

# Ditt elhandelsavtal
+ Elhandel påslag       = 0.04 SEK/kWh
+ Elcertifikat          = 0.01 SEK/kWh
= Delsumma elhandel     = 0.55 SEK/kWh
× Elhandel moms (25%)   = 0.6875 SEK/kWh

# Ditt nätavtal
Nätavgift               = 0.45 SEK/kWh
+ Energiskatt           = 0.42 SEK/kWh
= Delsumma nät          = 0.87 SEK/kWh
× Nät moms (25%)        = 1.0875 SEK/kWh

# Slutligt totalpris
Elhandel (med moms)     = 0.6875 SEK/kWh
+ Nät (med moms)        = 1.0875 SEK/kWh
= TOTALT                = 1.775 SEK/kWh  ← Detta ser SVOTC
```

---

## ⏱️ Uppdateringar

Alla sensorer uppdateras automatiskt:
* ✅ Var 10:e minut (backup)
* ✅ När du ändrar någon avtalsparameter (omedelbart)
* ✅ Vid Home Assistant-omstart
* ✅ Morgondagens priser dyker upp ~13:00 varje dag

---

## ❓ Felsökning

### Sensorn blir `unavailable`

Kontrollera i denna ordning:

1. ✅ **Nordpool-integrationen fungerar**
   ```
   Inställningar → Enheter & tjänster → Nordpool
   Bekräfta att den är laddad och uppdaterar
   ```

2. ✅ **`config_entry` är korrekt på BÅDA ställena**
   ```yaml
   # Sök i filen efter "config_entry"
   # Bör hitta 2 identiska ID:n
   ```

3. ✅ **`areas` är korrekt (SE1/SE2/SE3/SE4) på BÅDA ställena**

4. ✅ **Testa manuellt:**
   ```yaml
   # Utvecklarverktyg → Tjänster
   service: nordpool.get_prices_for_date
   data:
     config_entry: DITT_CONFIG_ENTRY_HÄR
     date: "{{ now().date() }}"
     areas: SE3
     currency: SEK
   ```

### Priserna verkar felaktiga

Kontrollera:
1. ✅ Alla avtalsvärden är i **SEK/kWh** (inte öre/kWh)
2. ✅ Moms-procent är heltal (25, inte 0.25)
3. ✅ Jämför med din faktiska elräkning

**Prisverifiering:**
```
Öppna sensor.elpris_total_inkl_avgifter_moms attribut
Kolla: elhandel_paslag, nat_overforing, etc.
Verifiera att dessa stämmer med ditt avtal
```

### Morgondagens priser saknas

**Detta är normalt före ~13:00.**

Nordpool publicerar morgondagens priser runt 13:00 CET varje dag.

Kontrollera:
```yaml
# Utvecklarverktyg → Tillstånd → sensor.elpris_total_inkl_avgifter_moms
attributes:
  tomorrow_valid: false  # ← normalt före ~13:00
  raw_tomorrow: []       # ← tom före priserna publiceras
```

### Priskoefficienten alltid 0

Kontrollera:
```yaml
# Utvecklarverktyg → Tillstånd
sensor.elpris_total_inkl_avgifter_moms
  attributes:
    min: [bör ha värde]
    max: [bör ha värde]

# Om min/max saknas → kolla avtalsinställningar
```

### Priszonen fastnar i ett läge

Sensorn har 2% hysteres by design för att förhindra fladdring.

Vänta 10 minuter på nästa uppdatering, eller kontrollera:
```yaml
# Utvecklarverktyg → Tillstånd → sensor.nordpool_price_band
attributes:
  normalized_0_1: [bör vara mellan 0.0 och 1.0]
  current_price: [bör uppdatera]
```

---

## 🔍 Verifiera att det fungerar

### Test 1: Alla sensorer finns
```yaml
# Utvecklarverktyg → Tillstånd
# Sök och verifiera att dessa finns:
sensor.elpris_spot_exkl_moms
sensor.elpris_total_inkl_avgifter_moms  ← Huvudsensor
sensor.elpriskoefficient
sensor.nordpool_price_band
binary_sensor.elpris_ok
binary_sensor.kort_peak_nu
```

### Test 2: Huvudsensorn har korrekta attribut
```yaml
# Utvecklarverktyg → Tillstånd → sensor.elpris_total_inkl_avgifter_moms
# Verifiera:
state: [nummer i SEK/kWh]
attributes:
  current_price: [samma som state]
  raw_today: [{start: ..., end: ..., value: ...}, ...]  # 24 poster
  raw_tomorrow: [...]  # 24 poster efter ~13:00
  min: [nummer]
  max: [nummer]
  elhandel_paslag: [ditt värde]
  nat_overforing: [ditt värde]
```

### Test 3: SVOTC-integration fungerar
```yaml
# Utvecklarverktyg → Tillstånd
# Sök: sensor.svotc_src_current_price
# Bör matcha sensor.elpris_total_inkl_avgifter_moms
```

### Test 4: Analyssensorer fungerar
```yaml
# Kolla koefficient
sensor.elpriskoefficient: [nummer, typiskt 0.5-2.0]

# Kolla priszon
sensor.nordpool_price_band: [en av: very_cheap, cheap, normal, expensive, very_expensive]
```

---

## 📋 Snabb checklista

Före installation:
* [ ] Nordpool-integration installerad och fungerar
* [ ] Hittat mitt `config_entry` ID
* [ ] Vet mitt elområde (SE1/SE2/SE3/SE4)
* [ ] Har mina avtalsvillkor redo

Under installation:
* [ ] Ändrat `config_entry` på **BÅDA** ställena
* [ ] Ändrat `areas` på **BÅDA** ställena
* [ ] Placerat fil i `/config/packages/`
* [ ] Startat om Home Assistant

Efter installation:
* [ ] Alla sensorer finns och visar värden
* [ ] Konfigurerat alla avtalshjälpare (elhandel + nät)
* [ ] Verifierat att totalpriset stämmer
* [ ] Kopplat till SVOTC via `svotc_entity_price`
* [ ] Priskoefficient och zoner fungerar

---

## ✅ Klart!

Nu har du:
* ✅ Komplett prisberäkning med alla avgifter
* ✅ SVOTC-kompatibel prissensor
* ✅ Smart priskoefficient för automationer
* ✅ 5-zons prissystem
* ✅ Hjälpsensorer för avancerad styrning
* ✅ Automatiska uppdateringar

**Nästa steg:** Konfigurera SVOTC och skapa prisbaserade automationer!

---

## 📝 Vanliga frågor

### Vad är skillnaden mellan detta och den enkla adaptern?

**Enkel adapter:**
- Bara gör Nordpool kompatibel med SVOTC
- Basic påslag + moms

**Detta bonuspaket:**
- Komplett avgiftsberäkning (elhandel + nät + skatter)
- Priskoefficient (smart relativ prissättning)
- Priszoner (5 zoner)
- Hjälpsensorer
- Redo för avancerade automationer

### Kan jag använda detta utan SVOTC?

Ja! Sensorerna fungerar fristående och är perfekta för alla prisbaserade automationer.

### Tänk om jag har en annan avtalstyp?

Justera input_number-värdena:
- Fast pris? Sätt påslag till ditt fasta pris minus spot
- Andra nätavgifter? Uppdatera nat_eloverforing och nat_energiskatt
- Andra momszoner? Justera moms-procentsatserna

### Varför är elhandel och nät separerade?

Svenska avtal har typiskt:
- **Elhandel:** Spot + påslag, med 25% moms
- **Nät:** Överföring + skatt, med 25% moms

Denna separation möjliggör korrekt beräkning per svensk marknadsstruktur.

### Kan jag lägga till fler avgifter?

Ja, redigera template-beräkningarna. Sök efter:
```yaml
{% set elhandel = (spot + el_paslag + el_cert) * el_moms %}
{% set nat = (nat_overf + nat_skatt) * nat_moms %}
```

Lägg till dina avgifter i lämplig sektion.

---

## 🆚 Jämförelse med Tibber-integration

| Funktion               | SVOTC Bonus (Nordpool) | Tibber HACS       |
| ---------------------- | ---------------------- | ----------------- |
| SVOTC-kompatibel       | ✅ Ja                  | ✅ Ja             |
| Anpassade avgifter     | ✅ Full kontroll       | ⚠️ Begränsad      |
| Priskoefficient        | ✅ Inkluderad          | ❌ Nej            |
| Priszoner (5 zoner)    | ✅ Inkluderad          | ❌ Nej            |
| Kräver prenumeration   | ❌ Nej (gratis Nordpool)| ⚠️ Tibber-konto  |
| Realtidspriser         | ⚠️ Endast timme        | ✅ Ja             |

**Använd Nordpool + detta paket om:**
- Du vill ha full kontroll över avgiftsberäkning
- Du behöver priskoefficient/zoner
- Du inte har/vill ha Tibber-prenumeration

**Använd Tibber HACS om:**
- Du har Tibber som leverantör
- Du vill ha realtidspriser
- Du föredrar enklare installation

---

## 🎓 Avancerade tips

### Kombinera koefficient och priszon
```yaml
automation:
  - alias: "Optimerad laddning"
    trigger:
      - platform: state
        entity_id: sensor.nordpool_price_band
        to: 'cheap'
    condition:
      - condition: numeric_state
        entity_id: sensor.elpriskoefficient
        below: 0.8
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.elbilsladdare
```

### Använd temperaturkompensation
```yaml
automation:
  - alias: "Dynamisk uppvärmning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.elpriskoefficient
        below: 0.7
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.vardagsrum
        data:
          temperature: >
            {% set outdoor = states('sensor.temperatur_ute') | float %}
            {% if outdoor < -10 %}
              22
            {% elif outdoor < 0 %}
              21
            {% else %}
              20
            {% endif %}
```

### Skapa prisvarningar
```yaml
automation:
  - alias: "Varning vid höga priser"
    trigger:
      - platform: state
        entity_id: sensor.nordpool_price_band
        to: 'very_expensive'
    action:
      - service: notify.mobile_app
        data:
          message: "Högt elpris nu ({{ states('sensor.elpriskoefficient') }}x). Överväg att sänka förbrukningen."
```

---
