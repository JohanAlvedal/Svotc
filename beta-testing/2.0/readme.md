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

### 0. Ta en backup först
Innan du gör några ändringar — ta en fullständig backup av din Home Assistant-konfiguration.

**Inställningar → System → Backup → Skapa backup**

> 🛑 Hoppa inte över detta steg. Om något går fel kan du återställa till ett fungerande tillstånd.

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
