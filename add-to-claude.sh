#!/bin/bash
# Скрипт для автоматического добавления Construction Maps MCP в Claude Code

set -e

CLAUDE_CONFIG="$HOME/.claude/mcp-servers.json"
CLAUDE_DIR="$HOME/.claude"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔧 Добавление Construction Maps MCP в Claude Code"
echo "================================================"
echo ""

# Создать директорию если не существует
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "📁 Создание директории ~/.claude"
    mkdir -p "$CLAUDE_DIR"
fi

# Проверить существование файла
if [ ! -f "$CLAUDE_CONFIG" ]; then
    echo "📝 Создание нового файла конфигурации"
    cat > "$CLAUDE_CONFIG" << JSONEOF
{
  "construction-maps": {
    "command": "/usr/local/bin/python3.14",
    "args": [
      "-m",
      "construction_maps_mcp"
    ],
    "cwd": "$SCRIPT_DIR",
    "env": {},
    "description": "MCP server for construction land parcel analysis - Rosreestr + Yandex Maps"
  }
}
JSONEOF
    echo "✅ Конфигурация создана: $CLAUDE_CONFIG"
else
    echo "⚠️  Файл $CLAUDE_CONFIG уже существует"
    echo ""
    echo "Добавьте эту секцию в существующий файл вручную:"
    echo ""
    cat << JSONEOF
  "construction-maps": {
    "command": "/usr/local/bin/python3.14",
    "args": [
      "-m",
      "construction_maps_mcp"
    ],
    "cwd": "$SCRIPT_DIR",
    "env": {},
    "description": "MCP server for construction land parcel analysis"
  }
JSONEOF
    echo ""
    echo "Или откройте файл:"
    echo "  nano $CLAUDE_CONFIG"
fi

echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1️⃣  Перезапустите Claude Code (полностью закройте и откройте)"
echo ""
echo "2️⃣  Проверьте работу командой:"
echo '   "Какие у тебя есть инструменты для работы с участками?"'
echo ""
echo "3️⃣  Попробуйте тестовый запрос:"
echo '   "Найди координаты адреса Москва, Красная площадь, 1"'
echo ""
echo "✅ Готово! У Claude теперь 16 инструментов для анализа участков."
echo ""
echo "📚 Документация:"
echo "   - SUCCESS.md - инструкции по использованию"
echo "   - EXAMPLES.md - 5 сценариев для строительства"
echo ""
