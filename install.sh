#!/bin/bash
# Скрипт установки Construction Maps MCP Server

set -e  # Остановка при ошибке

echo "🚀 Установка Construction Maps MCP Server"
echo "=========================================="
echo ""

# Проверка версии Python
echo "📋 Проверка Python..."
if command -v python3.10 &> /dev/null; then
    PYTHON_VERSION=$(python3.10 --version)
    echo "✅ Python 3.10+ найден: $PYTHON_VERSION"
    PYTHON_CMD="python3.10"
elif command -v python3.11 &> /dev/null; then
    PYTHON_VERSION=$(python3.11 --version)
    echo "✅ Python 3.11+ найден: $PYTHON_VERSION"
    PYTHON_CMD="python3.11"
elif command -v python3.12 &> /dev/null; then
    PYTHON_VERSION=$(python3.12 --version)
    echo "✅ Python 3.12+ найден: $PYTHON_VERSION"
    PYTHON_CMD="python3.12"
else
    echo "❌ Python 3.10+ не найден"
    echo ""
    echo "Установите Python 3.10+ одним из способов:"
    echo ""
    echo "1️⃣  Через Homebrew (рекомендуется):"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "   brew install python@3.10"
    echo ""
    echo "2️⃣  Официальный установщик:"
    echo "   https://www.python.org/downloads/"
    echo ""
    echo "После установки запустите этот скрипт снова:"
    echo "   bash install.sh"
    exit 1
fi

echo ""
echo "📦 Установка зависимостей..."
$PYTHON_CMD -m pip install --user -e .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Установка завершена успешно!"
    echo ""
    echo "📝 Следующие шаги:"
    echo ""
    echo "1️⃣  Проверьте API ключ Yandex Maps в .env:"
    echo "   cat .env | grep YANDEX_MAPS_API_KEY"
    echo ""
    echo "2️⃣  Протестируйте сервер:"
    echo "   $PYTHON_CMD -m construction_maps_mcp"
    echo "   (нажмите Ctrl+C для выхода)"
    echo ""
    echo "3️⃣  Добавьте в Claude Code:"
    echo "   Скопируйте содержимое файла claude-mcp-config.json"
    echo "   в ~/.claude/mcp-servers.json"
    echo ""
    echo "4️⃣  Перезапустите Claude Code"
    echo ""
    echo "📚 Документация:"
    echo "   - README.md - общая информация"
    echo "   - INSTALL.md - подробная установка"
    echo "   - EXAMPLES.md - примеры использования"
    echo ""
    echo "🎯 Готово! У Claude теперь 16 инструментов для анализа участков."
else
    echo ""
    echo "❌ Ошибка при установке зависимостей"
    echo ""
    echo "Попробуйте установить вручную:"
    echo "   $PYTHON_CMD -m pip install --user -e ."
    exit 1
fi
