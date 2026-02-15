# Nordpool-paket för SVOTC

## 🎯 Vad är detta?

Ett enkelt paket som gör den **officiella Nordpool-integrationen** kompatibel med SVOTC.

SVOTC förväntar sig specifika attribut som `current_price`, `raw_today` och `raw_tomorrow`. Den officiella Nordpool-integrationen visar inte dessa attribut direkt, så den här filen skapar en ny sensor som tillhandahåller dem.

---

## ✅ Förutsättningar

Du måste ha **Nordpool-integrationen** installerad och fungerande i Home Assistant.

**Verifiera:**

1. Gå till **Inställningar → Enheter och tjänster**
2. Sök efter ”Nordpool”
3. Bekräfta att priser uppdateras

---

## 📥 Installation (3 steg)

### Steg 1: Hitta ditt `config_entry`-ID

**Enklaste metoden:**

1. Gå till **Utvecklarverktyg → Tillstånd**
2. Sök efter din Nordpool-sensor (t.ex. `sensor.nordpool`)
3. Klicka på sensorn
4. Kopiera **config_entry** från attributen

**Alternativ via URL:**

1. Gå till **Inställningar → Enheter och tjänster → Nordpool → Klicka på integrationen**
2. URL:en i webbläsaren innehåller ditt `config_entry`:
`.../config/integrations/integration/01KGFMFDG6SDFKHQFKK5QKCJ5T`
(Kopiera den alfanumeriska strängen i slutet)

---

### Steg 2: Anpassa filen

Öppna `nordpool_svotc_adapter.yaml` och ändra på **TVÅ STÄLLEN**:

⚠️ **VIKTIGT: Du måste ändra `config_entry` på BÅDA ställena i filen!**

```yaml
# FÖRSTA STÄLLET (runt rad ~20):
action:
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← ÄNDRA TILL DITT ID
      date: "{{ now().date() }}"
      areas: SE3  # ← ÄNDRA TILL DITT ELOMRÅDE
      currency: SEK
    # ...

# ANDRA STÄLLET (runt rad ~27):
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← ÄNDRA TILL DITT ID (igen!)
      date: "{{ now().date() + timedelta(days=1) }}"
      areas: SE3  # ← ÄNDRA TILL DITT ELOMRÅDE (igen!)
      currency: SEK
    # ...

```

**Sammanfattning av ändringar:**

| Vad | Var | Exempel |
| --- | --- | --- |
| `config_entry` | **Båda ställen** | `01KGFMFDG6SDFKHQFKK5QKCJ5T` → DITT |
| `areas` | **Båda ställen** | `SE3` → Ditt område |

**Elområden i Sverige:**

* **SE1** – Norra Sverige (Luleå)
* **SE2** – Norra Mellansverige (Sundsvall)
* **SE3** – Södra Mellansverige (Stockholm)
* **SE4** – Södra Sverige (Malmö)

**💡 Tips:** Använd "Sök och ersätt" (Ctrl+F) i din textredigerare:

* **Sök:** `01KGFMFDG6SDFKHQFKK5QKCJ5T`
* **Ersätt med:** `DITT_CONFIG_ENTRY_HÄR`
* **Ersätt alla:** 2 träffar bör ersättas.

---

### Steg 3: Installera filen

1. Placera filen här: `/config/packages/nordpool_svotc_adapter.yaml`
2. **Starta om Home Assistant.**

---

## ⚙️ Konfiguration

Efter omstart skapas två nya hjälpare (helpers):

| Hjälpare | Beskrivning | Exempel |
| --- | --- | --- |
| `Tibber markup (öre/kWh)` | Påslag från leverantör | 4.0 öre/kWh |
| `VAT (%)` | Moms (standard 25%) | 25% |

**Ställ in dessa i gränssnittet:**

1. Gå till **Inställningar → Enheter och tjänster → Hjälpare**
2. Sök efter ”Tibber markup” och ange ditt påslag (ofta 3–5 öre/kWh).
3. Sök efter ”VAT” och ange 25.

---

## 🔗 Koppla till SVOTC

Den nya sensorn heter: `sensor.nordpool_offical`

**I SVOTC entity mapping:**

1. Öppna **Hjälpare**
2. Sök: `svotc_entity_price`
3. Sätt värdet till: `sensor.nordpool_offical`

**Eller via YAML:**

```yaml
input_text:
  svotc_entity_price:
    initial: "sensor.nordpool_offical"

```

---

## 📊 Vad sensorn innehåller

`sensor.nordpool_offical` exponerar dessa attribut (som krävs av SVOTC):

| Attribut | Beskrivning |
| --- | --- |
| `current_price` | Aktuellt pris inkl. påslag + moms |
| `raw_today` | Lista över dagens priser: `[{start, end, value}, ...]` |
| `raw_tomorrow` | Lista över morgondagens priser (tom före ~13:00) |
| `min` | Lägsta pris idag |
| `max` | Högsta pris idag |
| `today` | Array med 24 priser |
| `tomorrow` | Array med 24 priser (tom före ~13:00) |

---

## 🧮 Prisberäkning

**Exempel:**

* Nordpool spotpris = 0,50 SEK/kWh
* Tibber påslag = 4,0 öre/kWh (= 0,04 SEK/kWh)
* Moms = 25%

**Beräkning:**

1. Pris med påslag =  SEK/kWh
2. Slutpris =  SEK/kWh

---

## ⏱️ Uppdateringar

Sensorn uppdateras automatiskt:

* ✅ Var 10:e minut (backup)
* ✅ När du ändrar påslag eller moms (omedelbart)
* ✅ Vid start av Home Assistant

---

## ❓ Felsökning

### Sensorn blir `unavailable` (ej tillgänglig)

Kontrollera i denna ordning:

1. **Nordpool-integrationen fungerar:** Gå till Inställningar → Enheter och tjänster → Nordpool. Bekräfta att den är laddad och uppdateras.
2. **`config_entry` är korrekt på BÅDA ställena:** Sök i filen efter "config_entry"; du ska hitta 2 identiska rader.
3. **`areas` är korrekt:** Se till att SE1/SE2/SE3/SE4 är rätt på båda ställena.
4. **Testa manuellt:** Gå till **Utvecklarverktyg → Tjänster**, anropa `nordpool.get_prices_for_date` med ditt entry-ID och område. Om det misslyckas där ligger felet i integrationen eller ID:t.

### Priserna är felaktiga

* Kontrollera att `Tibber markup` är i **öre/kWh**, inte SEK/kWh.
* Kontrollera att `VAT` är **25** (inte 0,25).

### Morgondagens priser saknas

**Detta är normalt före kl. 13:00–14:00.** Nordpool publicerar morgondagens priser runt kl. 13:00 varje dag.

---

## 📋 Snabb checklista

**Innan installation:**

* [ ] Nordpool-integrationen är installerad och fungerar.
* [ ] Jag har hittat mitt `config_entry`-ID.
* [ ] Jag vet mitt elområde (SE1–SE4).

**Under installation:**

* [ ] Ändrat `config_entry` på **FÖRSTA** och **ANDRA** stället.
* [ ] Ändrat `areas` på **FÖRSTA** och **ANDRA** stället.
* [ ] Placerat filen i `/config/packages/`.
* [ ] Startat om Home Assistant.

**Efter installation:**

* [ ] `sensor.nordpool_offical` finns under Tillstånd.
* [ ] Sensorn visar ett pris (inte `unavailable`).
* [ ] Attributen `current_price` och `raw_today` (24 poster) finns.
* [ ] Ställt in påslag och moms.
* [ ] Kopplat till SVOTC via `svotc_entity_price`.

---

Behöver du hjälp med att justera något i själva YAML-koden också?
