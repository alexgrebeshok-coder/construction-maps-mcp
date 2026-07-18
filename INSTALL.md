# Инструкция по установке Construction Maps MCP

## 🔴 Критично: Python 3.10+

MCP SDK требует **Python 3.10 или выше**. Текущая версия системы - Python 3.9.6 - не подходит.

## Установка Python 3.10+

### Вариант 1: Homebrew (рекомендуется для macOS)

```bash
# Установить Homebrew (если еще не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установить Python 3.10
brew install python@3.10

# Проверка версии
python3.10 --version  # Должно быть >= 3.10.0
```

### Вариант 2: Официальный установщик

1. Скачать Python 3.10+ с https://www.python.org/downloads/
2. Установить .pkg файл
3. Проверить: `python3.10 --version`

### Вариант 3: pyenv (для разработчиков)

```bash
# Установить pyenv
curl https://pyenv.run | bash

# Установить Python 3.10
pyenv install 3.10.13
pyenv global 3.10.13

# Проверка
python3 --version
```

## Установка MCP Server

После установки Python 3.10+:

```bash
cd /Users/aleksandrgrebeshok/Проекты\ VScode/construction-maps-mcp

# Установить зависимости (используйте python3.10!)
python3.10 -m pip install -e .

# Проверка установки
python3.10 -m construction_maps_mcp --help
```

## Конфигурация

API ключ Yandex Maps уже добавлен в `.env`:
```
YANDEX_MAPS_API_KEY=YOUR_YANDEX_KEY
```

Остальные настройки можно оставить по умолчанию.

## Подключение к Claude Code

После успешной установки добавьте сервер в `~/.claude/mcp-servers.json`:

```json
{
  "construction-maps": {
    "command": "python3.10",
    "args": [
      "-m",
      "construction_maps_mcp"
    ],
    "cwd": "/Users/aleksandrgrebeshok/Проекты VScode/construction-maps-mcp",
    "env": {}
  }
}
```

**Или** если файл уже существует, добавьте секцию `"construction-maps"` в список серверов.

## Перезапуск Claude Code

```bash
# Перезапустите Claude Code чтобы MCP сервер подключился
# В Claude Code появятся 16 новых tools для анализа участков
```

## Проверка работы

После подключения к Claude Code попробуйте:

```
Найди информацию о земельном участке с кадастровым номером 50:21:0010401:123
```

Claude автоматически использует инструмент `cadastre_get_info` для получения данных.

## Возможные проблемы

### Ошибка "No module named 'mcp'"
- Убедитесь что используете Python 3.10+
- Переустановите: `python3.10 -m pip install -e .`

### Ошибка "YANDEX_MAPS_API_KEY not set"
- Проверьте что файл `.env` существует в директории проекта
- Убедитесь что ключ указан правильно

### Сервер не запускается
- Проверьте логи: добавьте `LOG_LEVEL=DEBUG` в `.env`
- Запустите вручную: `python3.10 -m construction_maps_mcp`

## Что дальше?

После установки у Claude появятся 16 инструментов:
- 🏘️ Кадастр (границы, информация, поиск)
- 🗺️ Геокодирование (адрес ↔ координаты)
- 📐 Геометрия (площади, пересечения, расстояния)
- 🏗️ Инфраструктура (поиск объектов, логистика)
- 📊 Визуализация (карты, экспорт GeoJSON)

Попробуйте задачи:
- "Покажи границы участка 77:01:0005001:1234"
- "Найди все школы в радиусе 1км от координат 55.7558, 37.6173"
- "Рассчитай площадь пересечения двух участков"
- "Создай статическую карту с маркерами для отчёта"
