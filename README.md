**Language:** **English** · [Русский](README.ru.md)

# wash-module-usage-stats

WASH PRO CRM module: workload statistics collection via `GET /api/crm/usage-stats`.

## Install

Dashboard → Automation → Modules → Install.

## Settings

- `poll_interval` — API poll interval (seconds)
- `lookback_hours` — aggregation depth (hours)

## Data

Aggregates are saved to `data/last_snapshot.json`.
