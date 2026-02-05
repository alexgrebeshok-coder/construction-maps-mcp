# 🚀 Быстрый старт - Construction Maps MCP

## Один шаг до запуска!

API ключ Yandex Maps уже настроен ✅
Все 16 инструментов реализованы ✅
Осталось только установить Python 3.10+ и зависимости.

---

## 📋 Автоматическая установка

```bash
cd "/Users/aleksandrgrebeshok/Проекты VScode/construction-maps-mcp"
bash install.sh
```

Скрипт сам:
- Проверит версию Python (нужен 3.10+)
- Установит все зависимости
- Подскажет следующие шаги

---

## 🔧 Ручная установка (если нет Python 3.10+)

### Шаг 1: Установите Python 3.10+

**Через Homebrew (проще всего):**
```bash
# Установить Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установить Python 3.10
brew install python@3.10

# Проверка
python3.10 --version
```

**Или скачайте с сайта:**
https://www.python.org/downloads/ → Python 3.10+

### Шаг 2: Установите MCP сервер

```bash
cd "/Users/aleksandrgrebeshok/Проекты VScode/construction-maps-mcp"
python3.10 -m pip install --user -e .
```

---

## 🔌 Подключение к Claude Code

### Шаг 1: Добавьте конфигурацию

Откройте или создайте файл:
```bash
nano ~/.claude/mcp-servers.json
```

Добавьте туда содержимое из `claude-mcp-config.json`:
```json
{
  "construction-maps": {
    "command": "python3.10",
    "args": ["-m", "construction_maps_mcp"],
    "cwd": "/Users/aleksandrgrebeshok/Проекты VScode/construction-maps-mcp",
    "env": {}
  }
}
```

**Важно**: Замените `python3.10` на вашу версию если используете другую (python3.11, python3.12).

### Шаг 2: Перезапустите Claude Code

```bash
# Закройте Claude Code и откройте снова
# Или используйте команду перезапуска
```

---

## ✅ Проверка работы

### Тест 1: Запуск сервера вручную

```bash
cd "/Users/aleksandrgrebeshok/Проекты VScode/construction-maps-mcp"
python3.10 -m construction_maps_mcp
```

Должны увидеть:
```
INFO Starting Construction Maps MCP Server
INFO Cache initialized
INFO Rosreestr client initialized
INFO Yandex Maps client initialized
INFO Cadastre tools registered count=3
INFO Geocoding tools registered count=3
INFO Geometry tools registered count=4
INFO Infrastructure tools registered count=3
INFO Visualization tools registered count=3
INFO MCP server ready tools_registered=16
INFO Server started, listening on stdio
```

Нажмите `Ctrl+C` для выхода.

### Тест 2: В Claude Code

Откройте Claude Code и попробуйте:

```
Привет! Какие у тебя есть инструменты для работы с земельными участками?
```

Claude должен ответить списком 16 инструментов:
- cadastre_get_boundaries
- cadastre_get_info
- ... и т.д.

### Тест 3: Реальный запрос

```
Найди информацию о земельном участке с кадастровым номером 77:01:0005001:1234
```

Claude автоматически вызовет `cadastre_get_info` и вернёт данные.

---

## 📚 Что дальше?

### Изучите примеры

```bash
cat EXAMPLES.md
```

Там 5 детальных сценариев:
1. 🏗️ Предпроектный анализ участка
2. 🚚 Логистический анализ
3. 📊 Отчет с картами
4. ⚠️ Анализ пересечений
5. 🛡️ Санитарно-защитная зона (СЗЗ)

### Попробуйте команды

**Геокодирование:**
```
Найди координаты адреса "Москва, Красная площадь, 1"
```

**Кадастр:**
```
Покажи границы участка 50:21:0010401:14 в GeoJSON
```

**Инфраструктура:**
```
Найди все школы в радиусе 2км от координат 55.7558, 37.6173
```

**Геометрия:**
```
Рассчитай площадь полигона с координатами [...]
```

**Визуализация:**
```
Создай статическую карту участка с маркерами
```

---

## 🎯 16 доступных инструментов

### Кадастр (3)
- `cadastre_get_boundaries` - границы GeoJSON
- `cadastre_get_info` - информация об участке
- `cadastre_search_by_address` - поиск по адресу

### Геокодирование (3)
- `geocode_address_to_coords` - адрес → координаты
- `geocode_coords_to_address` - координаты → адрес
- `geocode_validate_address` - проверка адреса

### Инфраструктура (3)
- `infrastructure_find_nearby` - поиск объектов
- `infrastructure_calculate_distances` - матрица расстояний
- `infrastructure_get_satellite_image` - спутниковые снимки

### Геометрия (4)
- `geometry_calculate_area` - площадь полигона
- `geometry_check_intersection` - пересечение
- `geometry_measure_distance` - расстояние
- `geometry_buffer` - буферные зоны

### Визуализация (3)
- `visualization_generate_static_map` - карты с маркерами
- `visualization_export_geojson` - экспорт GeoJSON
- `visualization_export_to_json` - экспорт JSON

---

## ⚠️ Возможные проблемы

### "Command not found: python3.10"
→ Установите Python 3.10+ (см. выше)

### "No module named 'mcp'"
→ Запустите: `python3.10 -m pip install --user -e .`

### "YANDEX_MAPS_API_KEY not set"
→ Проверьте файл `.env` (ключ уже добавлен!)

### Сервер не появляется в Claude
→ Проверьте `~/.claude/mcp-servers.json`
→ Перезапустите Claude Code

### Медленная работа
→ Первый запрос к API медленный
→ Повторные запросы из кеша быстрые

---

## 📞 Помощь

- **README.md** - полная документация
- **INSTALL.md** - детальная установка
- **EXAMPLES.md** - примеры использования
- **GitHub Issues** - сообщить о проблеме

---

## 🎉 Готово!

После установки у Claude появятся 16 инструментов для профессионального анализа земельных участков в строительстве.

**API интеграции:**
- ✅ Росреестр (НСПД) - кадастровые границы
- ✅ Yandex Maps - геокодирование и карты
- ✅ Shapely + pyproj - точные геометрические расчёты

**Кеширование:**
- ✅ SQLite (персистентность)
- ✅ In-memory (скорость)
- ✅ TTL для разных типов данных

**Production-ready:**
- ✅ Rate limiting
- ✅ Retry логика
- ✅ Structured logging
- ✅ Обработка ошибок

Удачи в строительстве! 🏗️
