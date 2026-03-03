# 💥 Breaking Changes – Svotc 2.0

## Filstruktur är nu uppdelad i separata filer

Tidigare bestod Svotc av **en enda stor konfigurationsfil**. Från och med version 2.0 är konfigurationen **splittad i flera mindre filer**, organiserade i en dedikerad mapp.

---

## Vad har ändrats?

### Tidigare struktur (1.x)
```
packages/
└── svotc.yaml   ← en enda fil med all konfiguration
```

### Ny struktur (2.0)
```
packages/svotc/
├── 00_helpers.yaml       ← Hjälpfunktioner och mallar
├── 10_sensors.yaml       ← Sensorkonfiguration
├── 20_price_fsm.yaml     ← Prislogik / tillståndsmaskin
├── 22_engine.yaml        ← Motor och styrlogik
├── 30_learning.yaml      ← Inlärning och adaptiv logik
└── 40_notify             ← Notifikationskonfiguration
```

---

## Vad behöver du göra?

1. **Ta bort** din gamla `svotc.yaml` (eller motsvarande fil).
2. **Skapa en ny mapp** för Svotc-konfigurationen i ditt `/packages/`-katalog.
3. **Kopiera in** de nya filerna från [`beta-testing/2.0`](https://github.com/JohanAlvedal/Svotc/tree/main/beta-testing/2.0) till din nya mapp.
4. **Inkludera alla filer** i din Home Assistant-konfiguration via `packages:`-direktivet:

```yaml
# configuration.yaml
homeassistant:
  packages: !include_dir_named packages/
```

> ✅ Se till att alla sex filer finns på plats – de är beroende av varandra och fungerar inte var för sig.

---

## Varför denna förändring?

Den uppdelade strukturen gör det enklare att:
- **Felsöka** specifika delar av systemet
- **Uppdatera** enskilda moduler utan att röra resten
- **Förstå** hur de olika delarna hänger ihop

---

## Behöver du hjälp?

Öppna ett [issue på GitHub](https://github.com/JohanAlvedal/Svotc/issues) om du stöter på problem under migrationen.
