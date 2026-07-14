# Construction Maps MCP Server

<!-- mcp-name: io.github.alexgrebeshok-coder/construction-maps-mcp -->

**MCP-сервер для анализа земельных участков в строительстве**

Интеграция данных Росреестра (НСПД) и Yandex Maps для предпроектного анализа участков.

---

## 🎯 Возможности

### 16 MCP Tools для Claude

**Кадастр** (3 tools):
- `cadastre_get_boundaries` — границы участка по кадастровому номеру (GeoJSON)
- `cadastre_get_info` — информация об участке (площадь, адрес, категория)
- `cadastre_search_by_address` — поиск участков по адресу

**Геокодирование** (3 tools):
- `geocode_address_to_coords` — адрес → координаты
- `geocode_coords_to_address` — координаты → адрес
- `geocode_validate_address` — проверка адреса

**Инфраструктура** (3 tools):
- `infrastructure_find_nearby` — поиск объектов в радиусе (школы, больницы, АЗС)
- `infrastructure_calculate_distances` — расстояния до поставщиков
- `infrastructure_get_satellite_image` — спутниковый снимок участка

**Геометрия** (4 tools):
- `geometry_calculate_area` — площадь полигона
- `geometry_check_intersection` — пересечение участков
- `geometry_measure_distance` — расстояние между точками
- `geometry_buffer` — буфер вокруг геометрии

**Визуализация** (3 tools):
- `visualization_generate_static_map` — статическая карта с маркерами
- `visualization_export_geojson` — экспорт в GeoJSON
- `export_to_json` — экспорт данных в JSON

---

## 🚀 Быстрый старт

**One-liner (after PyPI publish):**

```bash
pipx run construction-maps-mcp
# or: uvx construction-maps-mcp
```

Set `YANDEX_MAPS_API_KEY` in your MCP client env (see below).

### Требования

- **Python 3.10+** (критично! MCP SDK не работает на Python 3.9)
- Yandex Maps API ключ (бесплатный)

#### Установка Python 3.10+ на macOS

```bash
# Через Homebrew
brew install python@3.10

# Проверка версии
python3.10 --version
```

Альтернативно: скачать с [python.org](https://www.python.org/downloads/)

### 1. Установка

```bash
# Клонировать репозиторий (если еще не клонировали)
# git clone <repo_url>
cd construction-maps-mcp

# ВАЖНО: Используйте Python 3.10+
python3.10 -m pip install -e .
pip install -r requirements.txt
```

### 2. Конфигурация

Создайте файл `.env`:

```env
# Обязательно: ключ Yandex Maps API
YANDEX_MAPS_API_KEY=your_api_key_here

# Опционально: настройки кеша
CACHE_DIR=~/.construction_maps_mcp
CACHE_MAX_SIZE_MB=500

# Опционально: rate limiting
YANDEX_RATE_LIMIT_RPM=15
ROSREESTR_RATE_LIMIT_RPM=30
```

**Получить API ключ Yandex Maps**: https://developer.tech.yandex.ru/

### 3. Интеграция с Claude Code

Добавьте в `~/.claude/mcp-servers.json`:

```json
{
  "mcpServers": {
    "construction-maps": {
      "command": "python",
      "args": ["-m", "construction_maps_mcp"],
      "env": {
        "YANDEX_MAPS_API_KEY": "${YANDEX_MAPS_API_KEY}"
      }
    }
  }
}
```

### 4. Запуск

```bash
# Через Claude Code (автоматически)
# Или вручную для тестирования:
python -m construction_maps_mcp
```

---

## 📖 Примеры использования

### Предпроектный анализ участка

```
Проанализируй участок 77:07:0001002:1002:
1. Покажи границы и площадь
2. Найди школы и больницы в радиусе 2 км
3. Создай спутниковую карту
4. Экспортируй в GeoJSON
```

**Claude автоматически вызовет**:
- `cadastre_get_boundaries("77:07:0001002:1002")`
- `infrastructure_find_nearby(lon, lat, 2000, ["school", "hospital"])`
- `infrastructure_get_satellite_image(lon, lat, zoom=15)`
- `visualization_export_geojson("77:07:0001002:1002")`

### Оценка логистики

```
Рассчитай расстояния от участка 50:22:0060703:11331 до:
- Склад стройматериалов, ул. Поставщиков, 10
- Бетонный завод, Промзона 5
- База ООО "Стройснаб"
```

### Анализ пересечений

```
Проверь, пересекаются ли участки 77:07:0001002:1002 и 77:07:0001002:1003
```

---

## 🏗️ Архитектура

### Двухуровневый кеш

**Level 1**: In-memory (cachetools)
- Быстрый доступ для частых запросов
- Автоматическое истечение по TTL

**Level 2**: SQLite (`~/.construction_maps_mcp/cache.db`)
- Персистентный кеш между перезапусками
- Автоочистка устаревших записей

### TTL стратегия

| Данные | TTL | Обоснование |
|--------|-----|-------------|
| Кадастровые границы | 30 дней | Статические данные |
| Геокодирование | 7 дней | Адреса постоянны |
| Инфраструктура | 1 день | Объекты могут обновляться |
| Спутниковые снимки | 90 дней | Редко меняются |

### Rate Limiting

- **Yandex Maps**: 15 req/min (бесплатный тариф: ~25,000/день)
- **Росреестр/НСПД**: 30 req/min (консервативно)
- Автоматический exponential backoff при ошибках

---

## 🔧 Разработка

### Структура проекта

```
construction-maps-mcp/
├── construction_maps_mcp/
│   ├── core/            # Инфраструктура (cache, rate limiter, retry)
│   ├── clients/         # API клиенты (Rosreestr, Yandex)
│   ├── tools/           # MCP tools (cadastre, geocoding, etc.)
│   ├── models/          # Pydantic модели
│   ├── utils/           # Утилиты (formatters, validators)
│   ├── config.py        # Конфигурация
│   └── server.py        # MCP сервер
├── tests/               # Unit тесты
├── pyproject.toml       # Метаданные проекта
└── requirements.txt     # Зависимости
```

### Запуск тестов

```bash
pytest tests/
```

### Линтинг

```bash
ruff check .
mypy construction_maps_mcp/
```

---

## 📊 Use Cases

### 1. Предпроектный анализ
- Границы и площадь участка
- Окружающая инфраструктура
- Спутниковые снимки
- Экспорт в GeoJSON для визуализации

### 2. Логистика
- Расстояния до поставщиков
- Расстояния до производственных баз
- Матрица расстояний

### 3. Отчеты
- Статические карты для документов
- GeoJSON для веб-визуализации
- JSON для интеграции с другими системами

### 4. Анализ конфликтов
- Пересечение границ участков
- Проверка наложений
- Расчет площади конфликтных зон

---

## 🛠️ Технологии

- **Python 3.10+**
- **MCP SDK** (Anthropic)
- **rosreestr2coord** — данные Росреестра/НСПД
- **Yandex Maps API** — геокодирование, карты
- **Shapely** — геометрические операции
- **SQLite + aiosqlite** — персистентный кеш
- **Pydantic** — валидация конфигурации

---

## 📝 Лицензия

MIT

---

## 🤝 Поддержка

Для вопросов и предложений создавайте Issue в репозитории.

---

## ⚠️ Важно

- **API ключ Yandex Maps обязателен** для работы геокодирования и карт
- **Бесплатный тариф Yandex**: ~25,000 запросов/день
- **Росреестр/НСПД**: неофициальное API через rosreestr2coord
- **Кеш**: по умолчанию `~/.construction_maps_mcp/cache.db` (настраивается)

---

**Версия**: 1.0.0
**Статус**: Production Ready (MVP)
