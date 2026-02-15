# Nordpool Package for SVOTC

> 🇸🇪 **Svenska:** För instruktioner på svenska, se [README.sv.md](./README.sv.md).

---

## 🎯 What is this?
A simple package that makes the **official Nordpool integration** compatible with SVOTC...

## 🎯 What is this?

A simple package that makes the **official Nordpool integration** compatible with SVOTC.

SVOTC expects specific attributes like `current_price`, `raw_today`, and `raw_tomorrow`. The official Nordpool integration does not expose these attributes directly, so this file creates a new sensor that provides them.

---

## ✅ Prerequisites

You must have the **Nordpool integration** installed and working in Home Assistant.

**Verify:**
1. Go to **Settings → Devices & services**
2. Search for “Nordpool”
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

````

---

### Step 2: Customize the file

Open `nordpool_svotc_adapter.yaml` and change **TWO PLACES**:

⚠️ **IMPORTANT: You must change `config_entry` in BOTH places in the file!**
```yaml
# FIRST PLACE (around line ~20):
action:
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← CHANGE TO YOURS
      date: "{{ now().date() }}"
      areas: SE3  # ← CHANGE TO YOUR PRICE AREA
      currency: SEK
    response_variable: today_price

# SECOND PLACE (around line ~27):
  - action: nordpool.get_prices_for_date
    data:
      config_entry: 01KGFMFDG6SDFKHQFKK5QKCJ5T  # ← CHANGE TO YOURS (again!)
      date: "{{ now().date() + timedelta(days=1) }}"
      areas: SE3  # ← CHANGE TO YOUR PRICE AREA (again!)
      currency: SEK
    response_variable: tomorrow_price
````

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
/config/packages/nordpool_svotc_adapter.yaml

# Restart Home Assistant
```

---

## ⚙️ Configuration

After restarting, two new helpers are created:

| Helper                    | Description       | Example     |
| ------------------------- | ----------------- | ----------- |
| `Tibber markup (öre/kWh)` | Supplier markup   | 4.0 öre/kWh |
| `VAT (%)`                 | VAT (default 25%) | 25%         |

**Set these in the UI:**

1. Go to **Settings → Devices & services → Helpers**
2. Search “Tibber markup”
3. Enter your markup (commonly 3–5 öre/kWh)
4. Search “VAT”
5. Enter 25%

---

## 🔗 Connect to SVOTC

The new sensor is named: `sensor.nordpool_offical`

**In SVOTC entity mapping:**

1. Open **Helpers**
2. Search: `svotc_entity_price`
3. Set value to: `sensor.nordpool_offical`

**Or via YAML:**

```yaml
input_text:
  svotc_entity_price:
    initial: "sensor.nordpool_offical"
```

---

## 📊 What the sensor contains

`sensor.nordpool_offical` exposes these attributes (required by SVOTC):

| Attribute       | Description                                          |
| --------------- | ---------------------------------------------------- |
| `current_price` | Current price incl. markup + VAT                     |
| `raw_today`     | List of today’s prices: `[{start, end, value}, ...]` |
| `raw_tomorrow`  | List of tomorrow’s prices (empty before ~13:00)      |
| `min`           | Lowest price today                                   |
| `max`           | Highest price today                                  |
| `today`         | Array of 24 prices                                   |
| `tomorrow`      | Array of 24 prices (empty before ~13:00)             |

---

## 🧮 Price calculation

```python
# Example:
Nordpool spot price = 0.50 SEK/kWh
Tibber markup       = 4.0 öre/kWh (= 0.04 SEK/kWh)
VAT                 = 25%

# Calculation:
Price w/ markup = 0.50 + 0.04 = 0.54 SEK/kWh
Final price     = 0.54 × 1.25 = 0.675 SEK/kWh
```

---

## ⏱️ Updates

The sensor updates automatically:

* ✅ Every 10 minutes (backup)
* ✅ When you change markup or VAT (immediately)
* ✅ At Home Assistant startup

---

## ❓ Troubleshooting

### The sensor becomes `unavailable`

Check in this order:

1. ✅ **The Nordpool integration works**

```
Settings → Devices & services → Nordpool
Confirm it is loaded/enabled and updating
```

2. ✅ **`config_entry` is correct in BOTH places**

```yaml
# Open the file and search for "config_entry"
# You should find 2 lines with the same ID
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

# If this fails → Nordpool integration issue or wrong config_entry
# If this works → issue in the adapter file
```

---

### Prices are incorrect

Check:

1. ✅ `Tibber markup` is correct (öre/kWh, not SEK/kWh!)
2. ✅ `VAT` is 25% (not 0.25)

Compare:

```
Nordpool spot price × 1000 = öre/kWh
sensor.nordpool_offical = spot + markup, then × 1.25
```

---

### Tomorrow’s prices are missing

**This is normal before ~13:00–14:00.**

Nordpool publishes tomorrow’s prices around 13:00 each day.

Check attributes:

```yaml
# Developer Tools → States → sensor.nordpool_offical
attributes:
  tomorrow_valid: false  # ← false before ~13:00
  raw_tomorrow: []       # ← empty list before ~13:00
```

---

### The sensor is not created at all

Checklist:

1. ✅ File is in `/config/packages/`
2. ✅ Packages are enabled in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

3. ✅ Home Assistant has been restarted
4. ✅ Check logs for errors:

```
Settings → System → Logs
Search for: "nordpool_offical" or "template"
```

---

## 🔍 Verify it works

### Test 1: Sensor exists and updates

```yaml
# Developer Tools → States
# Search: sensor.nordpool_offical
# Should show current price in SEK/kWh
```

### Test 2: Attributes exist

```yaml
# Developer Tools → States → sensor.nordpool_offical
# Click the sensor and verify:
attributes:
  current_price: 0.675
  raw_today: [{start: ..., end: ..., value: ...}, ...]  # ← 24 entries
  raw_tomorrow: [...]  # ← 24 entries (or [] before ~13:00)
  min: 0.450
  max: 0.890
```

### Test 3: SVOTC uses the sensor

```yaml
# Developer Tools → States
# Search: sensor.svotc_src_current_price
# Should match sensor.nordpool_offical
```

---

## 📋 Quick checklist

Before install:

* [ ] Nordpool integration installed and working
* [ ] Found my `config_entry` ID
* [ ] Know my price area (SE1/SE2/SE3/SE4)

During install:

* [ ] Changed `config_entry` in the **FIRST** place (today)
* [ ] Changed `config_entry` in the **SECOND** place (tomorrow)
* [ ] Changed `areas` in the **FIRST** place (today)
* [ ] Changed `areas` in the **SECOND** place (tomorrow)
* [ ] Placed the file in `/config/packages/`
* [ ] Restarted Home Assistant

After install:

* [ ] `sensor.nordpool_offical` exists in States
* [ ] Sensor shows a price (not `unavailable`)
* [ ] Attribute `current_price` exists and has a value
* [ ] Attribute `raw_today` has 24 entries
* [ ] Set Tibber markup (e.g. 4.0 öre/kWh)
* [ ] Set VAT (25%)
* [ ] Connected it in SVOTC via `svotc_entity_price`

---

## ✅ Done!

Now you have:

* ✅ `sensor.nordpool_offical` with SVOTC-compatible attributes
* ✅ Markup and VAT included in the price
* ✅ Automatic updates every 10 minutes

**Next step:** Configure SVOTC (see the SVOTC README)

---

## 📝 Frequently asked questions

### Can I use this with Tibber too?

No—this adapter is **only for the official Nordpool integration**.

If you use Tibber, use the Tibber HACS integration directly:

```yaml
input_text:
  svotc_entity_price:
    initial: "sensor.electricity_price_skarholmen"  # Your Tibber sensor
```

### What if the Nordpool integration stops working?

The sensor becomes `unavailable`. SVOTC will then go into `MISSING_INPUTS` or continue in `ComfortOnly` mode (depending on configuration).

### Do I need to change anything when prices update?

No—everything is automatic. Tomorrow’s prices are pulled in automatically when published (around 13:00).

### Can I have multiple price areas?

Yes, but you must create one sensor per area. Copy the entire `sensor` block and change `unique_id`, `name`, and `areas`.

### Why is `config_entry` repeated twice?

Because the file fetches prices for **two dates**:

* **First call** (`today_price`) fetches today
* **Second call** (`tomorrow_price`) fetches tomorrow

Both must use the same `config_entry` and `areas`.

---
