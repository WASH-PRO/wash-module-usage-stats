**Язык:** [English](README.md) · **Русский**

# wash-module-usage-stats

Модуль WASH PRO CRM: сбор статистики загруженности через `GET /api/crm/usage-stats`.

## Установка

Dashboard → Автоматизация → Модули → Установить.

## Настройки

- `poll_interval` — интервал опроса API (секунды)
- `lookback_hours` — глубина агрегации (часы)

## Данные

Агрегаты сохраняются в `data/last_snapshot.json`.
