#!/usr/bin/env python3
"""Ручной тест MCP сервера construction-maps."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from construction_maps_mcp.clients.rosreestr_client import RosreestrClient
from construction_maps_mcp.clients.yandex_client import YandexMapsClient
from construction_maps_mcp.tools.cadastre import cadastre_get_info, cadastre_get_boundaries
from construction_maps_mcp.tools.geocoding import geocode_address_to_coords
from construction_maps_mcp.tools.infrastructure import infrastructure_find_nearby
from construction_maps_mcp.config import Settings


async def test_cadastre():
    """Тест кадастровых инструментов."""
    print("=" * 60)
    print("ТЕСТ 1: Кадастровая информация")
    print("=" * 60)

    settings = Settings()
    rosreestr = RosreestrClient(settings=settings)

    # Тестовый кадастровый номер (Москва, Красная площадь)
    cadastral_number = "77:01:0001000:1051"

    print(f"\n📋 Запрос информации об участке {cadastral_number}...")

    try:
        result = await cadastre_get_info(rosreestr, cadastral_number)
        print(result)
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def test_boundaries():
    """Тест получения границ."""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Границы участка (GeoJSON)")
    print("=" * 60)

    settings = Settings()
    rosreestr = RosreestrClient(settings=settings)

    cadastral_number = "77:01:0001000:1051"

    print(f"\n🗺️  Запрос границ участка {cadastral_number}...")

    try:
        result = await cadastre_get_boundaries(
            rosreestr,
            cadastral_number,
            include_metadata=True
        )
        print(result[:1000] + "..." if len(result) > 1000 else result)
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def test_geocoding():
    """Тест геокодирования."""
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Геокодирование адреса")
    print("=" * 60)

    settings = Settings()
    yandex = YandexMapsClient(settings=settings)

    address = "Москва, Красная площадь, 1"

    print(f"\n📍 Геокодирую адрес: {address}...")

    try:
        result = await geocode_address_to_coords(yandex, address)
        print(result)
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def test_infrastructure():
    """Тест поиска инфраструктуры."""
    print("\n" + "=" * 60)
    print("ТЕСТ 4: Поиск инфраструктуры")
    print("=" * 60)

    settings = Settings()
    yandex = YandexMapsClient(settings=settings)

    # Координаты Красной площади
    lon, lat = 37.621029, 55.753676

    print(f"\n🏢 Ищу школы в радиусе 1 км от координат ({lat}, {lon})...")

    try:
        result = await infrastructure_find_nearby(
            yandex,
            lon=lon,
            lat=lat,
            radius_m=1000,
            categories=["school"]
        )
        print(result[:1000] + "..." if len(result) > 1000 else result)
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def main():
    """Запуск всех тестов."""
    print("\n🚀 Запуск тестов construction-maps MCP сервера\n")

    await test_cadastre()
    await test_boundaries()
    await test_geocoding()
    await test_infrastructure()

    print("\n" + "=" * 60)
    print("✅ Все тесты завершены!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
