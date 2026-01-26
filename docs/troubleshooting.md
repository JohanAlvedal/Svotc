# Troubleshooting

## Tomorrow prices are empty before ~13:30
Many Nord Pool-backed sensors do not publish tomorrow's prices until around 13:30 local time. Until then, the tomorrow list can be empty, which is expected. SVOTC continues to operate with today's prices only.

If you use templates like `min()` on the tomorrow list, guard against empty data to avoid warnings. Example:

```jinja
{% set tomorrow_prices = state_attr('sensor.price_tomorrow', 'prices') or [] %}
{% if tomorrow_prices %}
  {{ (tomorrow_prices | map(attribute='price') | list | min) }}
{% else %}
  unknown
{% endif %}
```

## Unique ID collisions in template sensors
Home Assistant requires template sensors to have unique IDs. If you reuse an ID (for example, a `ps_status_summary` sensor copied between configurations), Home Assistant will show a collision and only one entity will be created.

Fix:
- Update the template sensor configuration to use a unique `unique_id`.
- Remove the old entity from **Settings → Devices & Services → Entities** (or delete the entry in the entity registry) so Home Assistant can recreate it with the new ID.

## SVOTC sensor updates
SVOTC sensor entities are updated by the coordinator. They do not poll on their own, so they must inherit from `CoordinatorEntity`. If you see sensors stuck with old timestamps, verify the integration is using coordinator-driven entities and that the coordinator is refreshing successfully.
