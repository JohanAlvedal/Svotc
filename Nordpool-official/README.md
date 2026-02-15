# SVOTC Bonus - Nordpool Price Sensors

> 🇸🇪 **Svenska:** För instruktioner på svenska, se [README.sv.md](./README.sv.md).

---

## 🎯 What is this?

A comprehensive Nordpool price package that provides:

1. **SVOTC-compatible price sensor** with all fees included
2. **Price coefficient** (dynamic relative price level)
3. **Price bands** (5 zones: very_cheap → very_expensive)
4. **Helper sensors** (price OK, peak detection)

Perfect for advanced automations and SVOTC integration.

---

## ✅ Prerequisites

You must have the **Nordpool integration** installed and working in Home Assistant.

**Verify:**
1. Go to **Settings → Devices & services**
2. Search for "Nordpool"
3. Confirm that prices are updating

---

## 📥 Installation (3 steps)

### Step 1: Find your `config_entry` ID

**Easiest method:**
1. Go to **Developer Tools → States**
2. Search for your Nordpool sensor (e.g. `sensor.nordpool`)
3. Click the sensor
4. Copy **config_entry** from the attributes

**Alternative via URL:**
```
Settings → Devices & services → Nordpool → Click the integration
The URL contains the config_entry:
.../config/integrations/integration/01KGFMFDG6SDFKHQFKK5QKCJ5T
                                    ^^^^^^^^^^^^^^^^^^^^^^^^
                                    Copy this part
```

---

### Step 2: Customize the file

Open `svotc_bonus_nordpool_sensors.yaml` and change **TWO PLACES**:

⚠️ **IMPORTANT: You must change `config_entry` in BOTH places in the file!**

```yaml
# FIRST PLACE (around line 94):
action:
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← CHANGE TO YOURS
      date: "{{ now().date() }}"
      areas: SE3  # ← CHANGE TO YOUR PRICE AREA
      currency: SEK
    response_variable: today_price

# SECOND PLACE (around line 102):
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← CHANGE TO YOURS (again!)
      date: "{{ (now() + timedelta(days=1)).date() }}"
      areas: SE3  # ← CHANGE TO YOUR PRICE AREA (again!)
      currency: SEK
    response_variable: tomorrow_price
```

**Summary of changes:**

| What           | Where           | Example                              |
| -------------- | --------------- | ------------------------------------ |
| `config_entry` | **Both places** | `01KGFMFDG6SDFKHQFKK5QKCJ5T` → YOURS |
| `areas`        | **Both places** | `SE3` → Your area                    |

**Price areas (Sweden):**
* **SE1** – Northern Sweden (Luleå)
* **SE2** – Northern Central Sweden (Sundsvall)
* **SE3** – Southern Central Sweden (Stockholm)
* **SE4** – Southern Sweden (Malmö)

**💡 Tip:** Use Find & Replace (Ctrl+F) in your editor:
```
Find:       01KGFMFDG6SDFKHQFKK5QKCJ5T
Replace:    YOUR_CONFIG_ENTRY_HERE
Replace all: 2 matches should be replaced
```

---

### Step 3: Install the file

```bash
# Place the file here:
/config/packages/svotc_bonus_nordpool_sensors.yaml

# Restart Home Assistant
```

---

## ⚙️ Configuration - Set your contract details

After restarting, configure your electricity contract in the helpers:

### Electricity Trading (Elhandel)
| Helper                                       | Description              | Typical value |
| -------------------------------------------- | ------------------------ | ------------- |
| `Elhandel påslag (SEK/kWh)`                  | Supplier markup          | 0.035-0.050   |
| `Elhandel elcertifikat (SEK/kWh)`            | Green certificates       | 0.005-0.015   |
| `Elhandel moms (%)`                          | VAT on trading           | 25            |
| `Elhandel månadsavgift (SEK/månad)` (unused) | Monthly fee (info only)  | 0-50          |

### Grid (Nät)
| Helper                             | Description             | Typical value |
| ---------------------------------- | ----------------------- | ------------- |
| `Nät elöverföring (SEK/kWh)`       | Grid transfer fee       | 0.30-0.50     |
| `Nät energiskatt (SEK/kWh)`        | Energy tax              | 0.42          |
| `Nät moms (%)`                     | VAT on grid             | 25            |

**Set these values in the UI:**
1. Go to **Settings → Devices & services → Helpers**
2. Search for each helper name
3. Enter your values from your contract

**Example Swedish contract (2026):**
```
Elhandel påslag:         0.040 SEK/kWh  (4.0 öre/kWh)
Elhandel elcertifikat:   0.010 SEK/kWh  (1.0 öre/kWh)
Elhandel moms:           25%
Nät elöverföring:        0.45 SEK/kWh
Nät energiskatt:         0.42 SEK/kWh
Nät moms:                25%
```

---

## 🔗 Connect to SVOTC

The main price sensor is: `sensor.elpris_total_inkl_avgifter_moms`

**In SVOTC entity mapping:**
1. Open **Helpers**
2. Search: `svotc_entity_price`
3. Set value to: `sensor.elpris_total_inkl_avgifter_moms`

**Or via YAML:**
```yaml
input_text:
  svotc_entity_price:
    initial: "sensor.elpris_total_inkl_avgifter_moms"
```

---

## 📊 What sensors are created

### 1. Price Sensors

#### `sensor.elpris_spot_exkl_moms`
Pure spot price (no fees, no VAT)
- Useful for comparisons and graphs

#### `sensor.elpris_total_inkl_avgifter_moms` ⭐
**Total price including ALL fees** (use this for SVOTC!)
- Spot price + trading markup + certificates + grid fees + energy tax + VAT
- **SVOTC-compatible attributes:**
  - `current_price` - Current total price
  - `raw_today` - Array of 24 hourly prices with start/end/value
  - `raw_tomorrow` - Array of tomorrow's prices (empty before ~13:00)
  - `min` / `max` - Lowest/highest price today
  - All your contract details in attributes

### 2. Analysis Sensors

#### `sensor.elpriskoefficient`
Dynamic price level relative to today's range
- **< 1.0** = Cheap (below threshold)
- **> 1.0** = Expensive (above threshold)
- Uses smart formula that adapts to both min/max levels
- Perfect for automations: "only run when coefficient < 0.8"

#### `sensor.nordpool_price_band`
5 price zones with hysteresis (prevents flapping)
- `very_cheap` (0-15% of daily range)
- `cheap` (15-35%)
- `normal` (35-65%)
- `expensive` (65-85%)
- `very_expensive` (85-100%)
- Includes 2% hysteresis for stable transitions

### 3. Helper Sensors (Binary)

#### `binary_sensor.elpris_ok`
True when price is cheap AND temperature is mild
- Coefficient < 1.0 AND outdoor temp < 3°C
- Useful for conditional heating/charging

#### `binary_sensor.kort_peak_nu`
True during short price peaks
- Coefficient >= 1.0
- Useful for pausing non-critical loads

---

## 🧮 Price calculation example

```python
# Example spot price from Nordpool
Spot price              = 0.50 SEK/kWh

# Your trading contract
+ Elhandel påslag       = 0.04 SEK/kWh
+ Elcertifikat          = 0.01 SEK/kWh
= Subtotal trading      = 0.55 SEK/kWh
× Elhandel moms (25%)   = 0.6875 SEK/kWh

# Your grid contract
Grid transfer           = 0.45 SEK/kWh
+ Energy tax            = 0.42 SEK/kWh
= Subtotal grid         = 0.87 SEK/kWh
× Grid moms (25%)       = 1.0875 SEK/kWh

# Final total price
Trading (with VAT)      = 0.6875 SEK/kWh
+ Grid (with VAT)       = 1.0875 SEK/kWh
= TOTAL                 = 1.775 SEK/kWh  ← This is what SVOTC sees
```

---

## ⏱️ Updates

All sensors update automatically:
* ✅ Every 10 minutes (backup)
* ✅ When you change any contract parameter (immediately)
* ✅ At Home Assistant startup
* ✅ Tomorrow's prices appear around 13:00 each day

---

## ❓ Troubleshooting

### Sensor becomes `unavailable`

Check in this order:

1. ✅ **Nordpool integration works**
   ```
   Settings → Devices & services → Nordpool
   Confirm it is loaded and updating
   ```

2. ✅ **`config_entry` is correct in BOTH places**
   ```yaml
   # Search the file for "config_entry"
   # Should find 2 identical IDs
   ```

3. ✅ **`areas` is correct (SE1/SE2/SE3/SE4) in BOTH places**

4. ✅ **Test manually:**
   ```yaml
   # Developer Tools → Services
   service: nordpool.get_prices_for_date
   data:
     config_entry: YOUR_CONFIG_ENTRY_HERE
     date: "{{ now().date() }}"
     areas: SE3
     currency: SEK
   ```

### Prices seem wrong

Check:
1. ✅ All contract values are in **SEK/kWh** (not öre/kWh)
2. ✅ VAT percentages are whole numbers (25, not 0.25)
3. ✅ Compare with your actual electricity bill

**Price verification:**
```
Open sensor.elpris_total_inkl_avgifter_moms attributes
Check: elhandel_paslag, nat_overforing, etc.
Verify these match your contract
```

### Tomorrow's prices missing

**This is normal before ~13:00.**

Nordpool publishes tomorrow's prices around 13:00 CET daily.

Check:
```yaml
# Developer Tools → States → sensor.elpris_total_inkl_avgifter_moms
attributes:
  tomorrow_valid: false  # ← normal before ~13:00
  raw_tomorrow: []       # ← empty before prices published
```

### Price coefficient always 0

Check:
```yaml
# Developer Tools → States
sensor.elpris_total_inkl_avgifter_moms
  attributes:
    min: [should have value]
    max: [should have value]

# If min/max are missing → check contract settings
```

### Price band stuck in one state

The sensor has 2% hysteresis by design to prevent flapping.

Wait 10 minutes for next update, or check:
```yaml
# Developer Tools → States → sensor.nordpool_price_band
attributes:
  normalized_0_1: [should be between 0.0 and 1.0]
  current_price: [should be updating]
```

---

## 🔍 Verify it works

### Test 1: All sensors exist
```yaml
# Developer Tools → States
# Search and verify these exist:
sensor.elpris_spot_exkl_moms
sensor.elpris_total_inkl_avgifter_moms  ← Main sensor
sensor.elpriskoefficient
sensor.nordpool_price_band
binary_sensor.elpris_ok
binary_sensor.kort_peak_nu
```

### Test 2: Main sensor has correct attributes
```yaml
# Developer Tools → States → sensor.elpris_total_inkl_avgifter_moms
# Verify:
state: [number in SEK/kWh]
attributes:
  current_price: [same as state]
  raw_today: [{start: ..., end: ..., value: ...}, ...]  # 24 entries
  raw_tomorrow: [...]  # 24 entries after ~13:00
  min: [number]
  max: [number]
  elhandel_paslag: [your value]
  nat_overforing: [your value]
```

### Test 3: SVOTC integration works
```yaml
# Developer Tools → States
# Search: sensor.svotc_src_current_price
# Should match sensor.elpris_total_inkl_avgifter_moms
```

### Test 4: Analysis sensors work
```yaml
# Check coefficient
sensor.elpriskoefficient: [number, typically 0.5-2.0]

# Check price band
sensor.nordpool_price_band: [one of: very_cheap, cheap, normal, expensive, very_expensive]
```

---

## 📋 Quick checklist

Before install:
* [ ] Nordpool integration installed and working
* [ ] Found my `config_entry` ID
* [ ] Know my price area (SE1/SE2/SE3/SE4)
* [ ] Have my electricity contract details ready

During install:
* [ ] Changed `config_entry` in **BOTH** places
* [ ] Changed `areas` in **BOTH** places
* [ ] Placed file in `/config/packages/`
* [ ] Restarted Home Assistant

After install:
* [ ] All sensors exist and show values
* [ ] Configured all contract helpers (elhandel + nät)
* [ ] Verified total price matches expectations
* [ ] Connected to SVOTC via `svotc_entity_price`
* [ ] Price coefficient and bands are working

---

## ✅ Done!

Now you have:
* ✅ Complete price calculation with all fees
* ✅ SVOTC-compatible price sensor
* ✅ Smart price coefficient for automations
* ✅ 5-zone price band system
* ✅ Helper sensors for advanced control
* ✅ Automatic updates

**Next step:** Configure SVOTC and create price-based automations!

---

## 📝 FAQ

### What's the difference between this and the simple adapter?

**Simple adapter:**
- Just makes Nordpool work with SVOTC
- Basic markup + VAT

**This bonus package:**
- Complete fee calculation (trading + grid + taxes)
- Price coefficient (smart relative pricing)
- Price bands (5 zones)
- Helper sensors
- Ready for advanced automations

### Can I use this without SVOTC?

Yes! The sensors work standalone and are perfect for any price-based automations.

### What if I have a different contract type?

Adjust the input_number values:
- Fixed price? Set markup to your fixed price minus spot
- Different grid fees? Update nat_eloverforing and nat_energiskatt
- Different VAT zones? Adjust moms percentages

### Why are trading and grid separated?

Swedish contracts typically have:
- **Trading (elhandel):** Spot + markup, with 25% VAT
- **Grid (nät):** Transfer + tax, with 25% VAT

This separation allows accurate calculation per Swedish market structure.

### Can I add more fees?

Yes, edit the template calculations. Search for:
```yaml
{% set elhandel = (spot + el_paslag + el_cert) * el_moms %}
{% set nat = (nat_overf + nat_skatt) * nat_moms %}
```

Add your fees to the appropriate section.

---

## 🆚 Comparison with Tibber integration

| Feature                | SVOTC Bonus (Nordpool) | Tibber HACS       |
| ---------------------- | ---------------------- | ----------------- |
| SVOTC compatible       | ✅ Yes                 | ✅ Yes            |
| Custom fees            | ✅ Full control        | ⚠️ Limited        |
| Price coefficient      | ✅ Included            | ❌ No             |
| Price bands (5 zones)  | ✅ Included            | ❌ No             |
| Requires subscription  | ❌ No (free Nordpool)  | ⚠️ Tibber account |
| Real-time prices       | ⚠️ Hourly only         | ✅ Yes            |

**Use Nordpool + this package if:**
- You want full control over fee calculation
- You need price coefficient/bands
- You don't have/want Tibber subscription

**Use Tibber HACS if:**
- You have Tibber as supplier
- You want real-time pricing
- You prefer simpler setup

---
