# SVOTC Lovelace Cards - Installationsguide

## Förutsättningar

Dessa kort använder custom cards från HACS. Du behöver installera följande:

### 1. Installera HACS (om du inte har det)
1. Följ guiden på https://hacs.xyz/docs/setup/download
2. Starta om Home Assistant
3. Gå till HACS i sidomenyn

### 2. Installera Custom Cards via HACS

Gå till **HACS → Frontend** och sök efter och installera följande:

#### Obligatoriska (för alla kort):
- ✅ **Mushroom Cards** - Moderna, snygga kort
- ✅ **Card Mod** - För anpassade styling

#### Rekommenderade (för avancerade kort):
- 📊 **ApexCharts Card** - För priskurvor och grafer
- 📦 **Stack In Card** - För att stacka kort
- 🎛️ **Mini Graph Card** - Kompakta grafer
- 🎨 **Fold Entity Row** - Inkläppbara rader

#### Installation steg-för-steg:
```
1. HACS → Frontend → "+" i nedre högra hörnet
2. Sök efter "Mushroom"
3. Välj "Mushroom Cards"
4. Klicka "Download"
5. Upprepa för varje card ovan
6. Starta om Home Assistant
```

### 3. Aktivera Advanced Mode (för YAML-editing)

1. Gå till din profil (klicka på ditt namn nere till vänster)
2. Scrolla ner och aktivera **"Advanced Mode"**

---

## Installation av Kort

Det finns 4 olika uppsättningar av kort att välja mellan:

### 📱 Variant 1: Komplett Dashboard (LOVELACE_CARDS.yaml)
**För:** Desktop/Tablet, komplett kontroll
**Innehåller:** Allt - grafer, kontroller, status, historik
**Installation:**
```yaml
1. Gå till Overview → Redigera Dashboard → "+" (ny tab)
2. Döp till "SVOTC Kontrollpanel"
3. Klicka på de tre prickarna → "Raw configuration editor"
4. Klistra in innehållet från LOVELACE_CARDS.yaml
5. Klicka "Spara"
```

### 📱 Variant 2: Mobil Kompakt (LOVELACE_MOBILE.yaml)
**För:** Smartphone, snabb åtkomst
**Innehåller:** Essentiella kontroller och status
**Installation:** Samma som ovan, använd LOVELACE_MOBILE.yaml

### 👁️ Variant 3: Glance Cards (LOVELACE_GLANCE.yaml)
**För:** Lägg till på befintlig dashboard
**Innehåller:** Enstaka kort du kan lägga till var som helst
**Installation:**
```yaml
1. Gå till din befintliga dashboard
2. Klicka "Redigera Dashboard"
3. Klicka "+ Lägg till kort"
4. Scrolla ner och välj "Manual" 
5. Klistra in ETT av korten från LOVELACE_GLANCE.yaml
6. Klicka "Spara"
```

### 🎨 Variant 4: Custom (blanda själv)
**För:** Skapa din egen layout
**Gör:** Kombinera kort från alla filer efter eget tycke

---

## Troubleshooting

### Problem: "Custom element doesn't exist: mushroom-template-card"
**Lösning:**
1. Kontrollera att Mushroom Cards är installerat via HACS
2. Tvinga en cache-refresh: Ctrl+F5 (Windows) eller Cmd+Shift+R (Mac)
3. Starta om Home Assistant
4. Rensa webbläsarens cache

### Problem: "Entity not available"
**Lösning:**
1. Kontrollera att SVOTC.yaml är korrekt laddad
2. Gå till Developer Tools → States
3. Sök efter "svotc" för att se att alla entiteter finns
4. Om de saknas: Kontrollera configuration.yaml och starta om

### Problem: Grafer visas inte (ApexCharts)
**Lösning:**
1. Installera "ApexCharts Card" via HACS
2. Tvinga en cache-refresh
3. Om du inte vill ha grafer: Ta bort de kort som börjar med `type: custom:apexcharts-card`

### Problem: Kort ser "basic" ut
**Lösning:**
1. Installera "Card Mod" via HACS
2. Om styling fortfarande saknas: Ta bort `card_mod:` sektionerna från korten

---

## Anpassningar

### Ändra färger
Hitta dessa rader i korten och ändra färgerna:
```yaml
icon_color: green   # Ändra till: blue, red, orange, purple, pink, yellow, grey
```

### Ta bort grafer (för bättre prestanda)
Ta bort eller kommentera ut dessa kort-typer:
```yaml
# - type: custom:apexcharts-card
# - type: custom:mini-graph-card
```

### Ändra rubriker
```yaml
title: SVOTC Kontrollpanel  # Ändra till vad du vill
```

### Ändra ordning på kort
Flytta helt enkelt kortens YAML-block upp eller ner i filen.

---

## Exempel Layouts

### Layout 1: Minimalistisk
```
[Status Banner]
[Mode Selector]
[Temperature + Price]
[Quick Adjustments]
```
**Använd:** Glance cards + Mobile chips

### Layout 2: Full Kontroll
```
[Animated Status Card]
[Temperature Grid]
[Price Chart]
[Controls Grid]
[Advanced Settings]
[History Graph]
```
**Använd:** Komplett dashboard

### Layout 3: Hybrid
```
[Main Dashboard: Glance Card]
[Dedikerad Tab: Komplett Dashboard]
```
**Använd:** Båda - lägg glance på översikt, dedikerad tab för detaljer

---

## Tips & Tricks

### 1. Lägg till på huvuddashboard
För att lägga SVOTC Glance-kortet högst upp på din huvuddashboard:
```yaml
1. Gå till din huvuddashboard
2. Klicka "Redigera Dashboard"
3. Dra ditt första kort åt sidan
4. Lägg till SVOTC Glance-kortet i position 1
5. Kortet syns nu först
```

### 2. Skapa snabbåtkomst
Lägg till i sidomenyn:
```yaml
# configuration.yaml
lovelace:
  mode: yaml
  dashboards:
    lovelace-svotc:
      mode: yaml
      title: SVOTC
      icon: mdi:heat-pump
      show_in_sidebar: true
      filename: dashboards/svotc.yaml
```

### 3. Notifikationer vid statusändring
Lägg till automation:
```yaml
automation:
  - alias: "SVOTC Status Notification"
    trigger:
      - platform: state
        entity_id: input_text.svotc_reason_code
    action:
      - service: notify.mobile_app
        data:
          title: "SVOTC Status"
          message: "Nytt läge: {{ states('sensor.svotc_status') }}"
```

### 4. Widget på Apple Watch
Om du har Home Assistant Companion app:
```
1. Öppna Watch-appen på iPhone
2. Scrolla till Home Assistant
3. Lägg till "Entity" widget
4. Välj sensor.svotc_status
```

### 5. Snabb Toggle-knapp
Lägg till en snabbknapp för att växla mellan Smart och ComfortOnly:
```yaml
type: button
name: Toggle SVOTC Mode
icon: mdi:swap-horizontal
tap_action:
  action: call-service
  service: input_select.select_next
  target:
    entity_id: input_select.svotc_mode
```

---

## Support

Om du stöter på problem:
1. Kontrollera att alla custom cards är installerade
2. Kolla browser console för felmeddelanden (F12)
3. Verifiera att alla SVOTC-entiteter finns i Developer Tools → States
4. Testa med ett enklare kort först (t.ex. mushroom-entity-card)

**Vanliga frågor:**
- **Kort laddar inte:** Rensa cache och starta om HA
- **Grafer saknas:** Installera ApexCharts Card
- **Styling saknas:** Installera Card Mod
- **"Entity unavailable":** Kontrollera SVOTC.yaml är laddat
