# Nordpool Adapter för SVOTC

## 🎯 Vad är detta?

En enkel adapter som gör den **officiella Nordpool-integrationen** kompatibel med SVOTC.

SVOTC behöver specifika attribut som `current_price`, `raw_today`, och `raw_tomorrow`. Den officiella Nordpool-integrationen har inte dessa attribut direkt, så denna fil skapar en ny sensor som har dem.

---

## ✅ Förutsättningar

Du måste ha **Nordpool-integrationen** installerad och fungerande i Home Assistant.

**Verifiera:**
1. Gå till **Inställningar → Enheter & tjänster**
2. Sök efter "Nordpool"
3. Kontrollera att du har priser som uppdateras

---

## 📥 Installation (3 steg)

### Steg 1: Hitta ditt config_entry ID

**Enklaste sättet:**
1. Gå till **Developer Tools → States**
2. Sök efter din Nordpool-sensor (t.ex. `sensor.nordpool`)
3. Klicka på sensorn
4. Kopiera **config_entry** från attributen

**Alternativt via URL:**
```
Inställningar → Enheter & tjänster → Nordpool → Klicka på integration
URL:en innehåller config_entry: 
.../config/integrations/integration/01KGFMFDG6SDFKHQFKK5QKCJ5T
                                    ^^^^^^^^^^^^^^^^^^^^^^^^
                                    Kopiera denna del
```

### Steg 2: Anpassa filen

Öppna `nordpool_svotc_adapter.yaml` och ändra på **TVÅ STÄLLEN**:

⚠️ **VIKTIGT: Du måste ändra `config_entry` på BÅDA ställena i filen!**
```yaml
# FÖRSTA STÄLLET (rad ~20):
action:
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← ÄNDRA TILL DIN
      date: "{{ now().date() }}"
      areas: SE3  # ← ÄNDRA TILL DITT OMRÅDE
      currency: SEK
    response_variable: today_price

# ANDRA STÄLLET (rad ~27):
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← ÄNDRA TILL DIN (igen!)
      date: "{{ now().date() + timedelta(days=1) }}"
      areas: SE3  # ← ÄNDRA TILL DITT OMRÅDE (igen!)
      currency: SEK
    response_variable: tomorrow_price
```

**Sammanfattning av ändringar:**

| Vad | Var | Exempel |
|-----|-----|---------|
| `config_entry` | **Båda ställen** | `01KGFMFDG6SDFKHQFKK5QKCJ5T` → DIN |
| `areas` | **Båda ställen** | `SE3` → Ditt område |

**Elområden:**
- **SE1** - Norra Sverige (Luleå)
- **SE2** - Norra Mellansverige (Sundsvall)  
- **SE3** - Södra Mellansverige (Stockholm)
- **SE4** - Södra Sverige (Malmö)

**💡 Tips:** Använd Sök & Ersätt (Ctrl+F) i din editor:
```
Sök efter:    01KGFMFDG6SDFKHQFKK5QKCJ5T
Ersätt med:   DIN_CONFIG_ENTRY_HÄR
Ersätt alla:  2 träffar ska ersättas
```

### Steg 3: Installera filen
```bash
# Lägg filen här:
/config/packages/nordpool_svotc_adapter.yaml

# Starta om Home Assistant
```

---

## ⚙️ Konfiguration

Efter omstart finns två nya helpers:

| Helper | Beskrivning | Exempel |
|--------|-------------|---------|
| `Tibber påslag (öre/kWh)` | Påslag från din elleverantör | 4.0 öre/kWh |
| `Moms (%)` | Moms (standard 25%) | 25% |

**Sätt dessa i UI:**
1. Gå till **Inställningar → Enheter & tjänster → Hjälpare**
2. Sök "Tibber påslag"
3. Ange ditt påslag (vanligt är 3-5 öre/kWh)
4. Sök "Moms"
5. Ange 25%

---

## 🔗 Koppla till SVOTC

Den nya sensorn heter: `sensor.nordpool_offical`

**I SVOTC entity mapping:**
1. Öppna **Hjälpare**
2. Sök: `svotc_entity_price`
3. Sätt värde till: `sensor.nordpool_offical`

**Eller via YAML:**
```yaml
input_text:
  svotc_entity_price:
    initial: "sensor.nordpool_offical"
```

---

## 📊 Vad sensorn innehåller

`sensor.nordpool_offical` har följande attribut (som SVOTC kräver):

| Attribut | Beskrivning |
|----------|-------------|
| `current_price` | Aktuellt pris inkl. påslag + moms |
| `raw_today` | Lista med priser för idag: `[{start, end, value}, ...]` |
| `raw_tomorrow` | Lista med priser för imorgon (tom före kl 13) |
| `min` | Lägsta pris idag |
| `max` | Högsta pris idag |
| `today` | Array med 24 priser |
| `tomorrow` | Array med 24 priser (tom före kl 13) |

---

## 🧮 Prisberäkning
```python
# Exempel:
Nordpool spotpris = 0.50 SEK/kWh
Tibber påslag     = 4.0 öre/kWh (= 0.04 SEK/kWh)
Moms              = 25%

# Beräkning:
Pris med påslag = 0.50 + 0.04 = 0.54 SEK/kWh
Slutpris        = 0.54 × 1.25 = 0.675 SEK/kWh
```

---

## ⏱️ Uppdatering

Sensorn uppdateras automatiskt:
- ✅ Var 10:e minut (backup)
- ✅ När du ändrar påslag eller moms (omedelbart)
- ✅ Vid Home Assistant start

---

## ❓ Felsökning

### Sensorn blir "unavailable"

**Kontrollera i denna ordning:**

1. ✅ **Nordpool-integrationen fungerar**
```
   Inställningar → Enheter & tjänster → Nordpool
   Kontrollera att den är aktiverad
```

2. ✅ **config_entry är rätt på BÅDA ställen**
```yaml
   # Öppna filen och sök efter "config_entry"
   # Du ska hitta 2 rader med samma ID
```

3. ✅ **areas är rätt (SE1/SE2/SE3/SE4) på BÅDA ställen**

4. ✅ **Testa manuellt:**
```yaml
   # Developer Tools → Services
   service: nordpool.get_prices_for_date
   data:
     config_entry: DIN_CONFIG_ENTRY_HÄR
     date: "{{ now().date() }}"
     areas: SE3
     currency: SEK
   
   # Om detta ger fel → problem med Nordpool-integration eller fel config_entry
   # Om detta fungerar → problem i adapter-filen
```

### Priserna stämmer inte

**Kontrollera:**
1. ✅ `Tibber påslag` är rätt (öre/kWh, inte SEK/kWh!)
2. ✅ `Moms` är 25% (inte 0.25)

**Jämför:**
```
Nordpool spotpris × 1000 = öre/kWh
Din sensor.nordpool_offical = spotpris + påslag, sedan × 1.25
```

### Morgondagens priser saknas

**Detta är normalt före kl 13-14.**

Nordpool publicerar morgondagens priser ca kl 13:00 varje dag.

Kontrollera attribut:
```yaml
# Developer Tools → States → sensor.nordpool_offical
attributes:
  tomorrow_valid: false  # ← false före kl 13
  raw_tomorrow: []       # ← tom lista före kl 13
```

### Sensorn skapas inte alls

**Checklista:**
1. ✅ Filen ligger i `/config/packages/`
2. ✅ Packages är aktiverat i `configuration.yaml`:
```yaml
   homeassistant:
     packages: !include_dir_named packages
```
3. ✅ Home Assistant har startats om
4. ✅ Kontrollera loggen för fel:
```
   Inställningar → System → Loggar
   Sök efter: "nordpool_offical" eller "template"
```

---

## 🔍 Verifiera att det fungerar

### Test 1: Sensor finns och uppdateras
```yaml
# Developer Tools → States
# Sök: sensor.nordpool_offical
# Ska visa aktuellt pris i SEK/kWh
```

### Test 2: Attribut finns
```yaml
# Developer Tools → States → sensor.nordpool_offical
# Klicka på sensorn och verifiera:
attributes:
  current_price: 0.675  # ← Ett pris
  raw_today: [{start: ..., end: ..., value: ...}, ...]  # ← 24 poster
  raw_tomorrow: [...]  # ← 24 poster (eller [] före kl 13)
  min: 0.450
  max: 0.890
```

### Test 3: SVOTC använder sensorn
```yaml
# Developer Tools → States
# Sök: sensor.svotc_src_current_price
# Ska visa samma pris som sensor.nordpool_offical
```

---

## 📋 Snabb checklista

Före installation:
- [ ] Nordpool-integration installerad och fungerar
- [ ] Hittat mitt config_entry ID
- [ ] Vet vilket elområde jag är i (SE1/SE2/SE3/SE4)

Vid installation:
- [ ] Ändrat `config_entry` på **FÖRSTA stället** (idag)
- [ ] Ändrat `config_entry` på **ANDRA stället** (imorgon)
- [ ] Ändrat `areas` på **FÖRSTA stället** (idag)
- [ ] Ändrat `areas` på **ANDRA stället** (imorgon)
- [ ] Lagt filen i `/config/packages/`
- [ ] Startat om Home Assistant

Efter installation:
- [ ] `sensor.nordpool_offical` finns i States
- [ ] Sensorn visar ett pris (inte "unavailable")
- [ ] Attribut `current_price` finns och har ett värde
- [ ] Attribut `raw_today` har 24 poster
- [ ] Satt Tibber påslag (t.ex. 4.0 öre/kWh)
- [ ] Satt Moms (25%)
- [ ] Kopplat till SVOTC via `svotc_entity_price`

---

## ✅ Klart!

Nu har du:
- ✅ `sensor.nordpool_offical` med SVOTC-kompatibla attribut
- ✅ Påslag och moms inkluderat i priserna
- ✅ Automatisk uppdatering var 10:e minut

**Nästa steg:** Konfigurera SVOTC (se SVOTC README)

---

## 📝 Vanliga frågor

### Kan jag använda denna med Tibber också?

Nej, denna adapter är **endast för Nordpool Official Integration**.

Om du har Tibber använder du Tibber HACS-integrationen direkt:
```yaml
input_text:
  svotc_entity_price:
    initial: "sensor.electricity_price_skarholmen"  # Din Tibber-sensor
```

### Vad händer om Nordpool-integrationen slutar fungera?

Sensorn blir `unavailable`. SVOTC går då in i `MISSING_INPUTS` eller fortsätter i `ComfortOnly`-läge (beroende på konfiguration).

### Måste jag ändra något när priset uppdateras?

Nej, allt är automatiskt. Morgondagens priser läses in automatiskt när de publicerats (ca kl 13).

### Kan jag ha flera elområden?

Ja, men du måste skapa en sensor per område. Kopiera hela `sensor`-blocket och byt `unique_id`, `name`, och `areas`.

### Varför två gånger samma config_entry?

Filen hämtar priser för **två dagar**:
- **Första anropet** (`today_price`) hämtar idag
- **Andra anropet** (`tomorrow_price`) hämtar imorgon

Båda måste använda samma `config_entry` och `areas`.

---

**💡 Tips:** Lägg till denna sensor i din Lovelace-dashboard för att övervaka priserna visuellt!
