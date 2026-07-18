"""MCP tools for infrastructure analysis using Yandex Maps."""

import asyncio
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from pyproj import Geod

from construction_maps_mcp.core.error_handler import handle_tool_error
from construction_maps_mcp.utils.formatters import (
    format_infrastructure_list,
    format_distance_matrix,
    format_error,
)


async def infrastructure_find_nearby(
    yandex_client,
    lon: float,
    lat: float,
    radius_m: int = 1000,
    categories: Optional[List[str]] = None,
    limit: int = 20,
) -> str:
    """
    Find infrastructure objects near coordinates.

    Args:
        yandex_client: Yandex API client
        lon: Longitude
        lat: Latitude
        radius_m: Search radius in meters (max 50000)
        categories: Object categories (school, hospital, fuel_station, pharmacy, shop, cafe, bank)
        limit: Maximum number of results

    Returns:
        Markdown-formatted list of infrastructure objects
    """
    try:
        # Validate radius
        if radius_m > 50000:
            radius_m = 50000

        # Default categories if not specified
        if not categories:
            categories = ["school", "hospital", "fuel_station", "pharmacy"]

        # Search for each category
        all_objects = []

        for category in categories:
            try:
                results = await yandex_client.search_nearby(
                    lon=lon,
                    lat=lat,
                    radius_m=radius_m,
                    category=category,
                    limit=limit,
                )

                # Add category to each object
                for obj in results.get("objects", []):
                    obj["category"] = category
                    all_objects.append(obj)

            except Exception as e:
                # Log error but continue with other categories
                yandex_client.logger.warning(
                    f"Failed to search category {category}: {e}"
                )
                continue

        # Sort by distance
        all_objects.sort(key=lambda x: x.get("distance_m", float("inf")))

        # Limit total results
        all_objects = all_objects[:limit]

        return format_infrastructure_list(all_objects, [lon, lat])

    except Exception as e:
        error_dict = await handle_tool_error("infrastructure_find_nearby", e)
        return format_error(error_dict)


async def infrastructure_calculate_distances(
    yandex_client,
    from_coords: List[float],
    to_addresses: List[str],
) -> str:
    """
    Calculate distances from parcel to multiple addresses (logistics).

    Args:
        yandex_client: Yandex API client
        from_coords: Origin coordinates [lon, lat]
        to_addresses: List of destination addresses

    Returns:
        Markdown-formatted distance matrix
    """
    try:
        from_lon, from_lat = from_coords
        distances = []

        # Geocode each address and calculate distance
        for address in to_addresses:
            try:
                # Geocode address
                geocode_result = await yandex_client.geocode_address(address)
                to_coords = geocode_result.get("coords")

                if not to_coords:
                    distances.append({
                        "to_address": address,
                        "error": "Адрес не найден",
                        "distance_m": None,
                        "distance_km": None,
                    })
                    continue

                to_lon, to_lat = to_coords

                # Calculate geodesic distance
                geod = Geod(ellps="WGS84")
                _, _, distance_m = geod.inv(from_lon, from_lat, to_lon, to_lat)

                distances.append({
                    "to_address": address,
                    "to_coords": to_coords,
                    "distance_m": distance_m,
                    "distance_km": distance_m / 1000,
                })

            except Exception as e:
                distances.append({
                    "to_address": address,
                    "error": str(e),
                    "distance_m": None,
                    "distance_km": None,
                })

        return format_distance_matrix(distances, from_coords)

    except Exception as e:
        error_dict = await handle_tool_error("infrastructure_calculate_distances", e)
        return format_error(error_dict)


async def infrastructure_get_satellite_image(
    yandex_client,
    lon: float,
    lat: float,
    zoom: int = 15,
    width: int = 600,
    height: int = 400,
    layer: str = "sat",
) -> str:
    """
    Get satellite image URL for parcel visualization.

    Args:
        yandex_client: Yandex API client
        lon: Longitude
        lat: Latitude
        zoom: Zoom level (1-17, default 15)
        width: Image width in pixels
        height: Image height in pixels
        layer: Map layer (sat, map, hybrid)

    Returns:
        Markdown-formatted result with image URL
    """
    try:
        # Get static map URL
        map_url = await yandex_client.get_static_map_url(
            lon=lon,
            lat=lat,
            zoom=zoom,
            width=width,
            height=height,
            layer=layer,
        )

        md = f"""# Спутниковый снимок участка

**Координаты**: {lat:.6f}°N, {lon:.6f}°E
**Масштаб**: {zoom}
**Слой**: {layer}

**URL изображения**:
```
{map_url}
```

![Карта]({map_url})

**Параметры**:
- Ширина: {width}px
- Высота: {height}px
- Источник: Yandex Static API
"""

        return md

    except Exception as e:
        error_dict = await handle_tool_error("infrastructure_get_satellite_image", e)
        return format_error(error_dict)


def register_tools(
    server: Server,
    yandex_client,
) -> None:
    """
    Register infrastructure tools with MCP server.

    Args:
        server: MCP server instance
        yandex_client: Yandex API client
    """

    # Tool 1: Find nearby infrastructure
    @server.call_tool()
    async def infrastructure_find_nearby_tool(
        lon: float,
        lat: float,
        radius_m: int = 1000,
        categories: Optional[List[str]] = None,
        limit: int = 20,
    ) -> list[TextContent]:
        """Поиск инфраструктуры вокруг участка."""
        result = await infrastructure_find_nearby(
            yandex_client,
            lon,
            lat,
            radius_m,
            categories,
            limit,
        )
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="infrastructure_find_nearby",
            description=(
                "Поиск объектов инфраструктуры вокруг земельного участка: "
                "школы, больницы, АЗС, аптеки, магазины, кафе, банки. "
                "Возвращает список объектов с адресами и расстояниями. "
                "Полезно для оценки развитости района и доступности сервисов."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "lon": {
                        "type": "number",
                        "description": "Долгота центра поиска",
                    },
                    "lat": {
                        "type": "number",
                        "description": "Широта центра поиска",
                    },
                    "radius_m": {
                        "type": "integer",
                        "description": "Радиус поиска в метрах (максимум 50000)",
                        "default": 1000,
                        "minimum": 1,
                        "maximum": 50000,
                    },
                    "categories": {
                        "type": "array",
                        "description": "Категории объектов для поиска",
                        "items": {
                            "type": "string",
                            "enum": [
                                "school",
                                "hospital",
                                "fuel_station",
                                "pharmacy",
                                "shop",
                                "cafe",
                                "bank",
                            ],
                        },
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимальное количество результатов",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["lon", "lat"],
            },
        )
    )

    # Tool 2: Calculate distances
    @server.call_tool()
    async def infrastructure_calculate_distances_tool(
        from_coords: List[float],
        to_addresses: List[str],
    ) -> list[TextContent]:
        """Расчет расстояний до списка адресов."""
        result = await infrastructure_calculate_distances(
            yandex_client,
            from_coords,
            to_addresses,
        )
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="infrastructure_calculate_distances",
            description=(
                "Расчет расстояний от земельного участка до списка адресов. "
                "Полезно для логистического анализа: расстояния до складов, "
                "производственных баз, поставщиков, клиентов. "
                "Использует геокодирование Yandex + точные геодезические расчеты."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from_coords": {
                        "type": "array",
                        "description": "Координаты участка [lon, lat]",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "to_addresses": {
                        "type": "array",
                        "description": "Список адресов назначения",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                },
                "required": ["from_coords", "to_addresses"],
            },
        )
    )

    # Tool 3: Get satellite image
    @server.call_tool()
    async def infrastructure_get_satellite_image_tool(
        lon: float,
        lat: float,
        zoom: int = 15,
        width: int = 600,
        height: int = 400,
        layer: str = "sat",
    ) -> list[TextContent]:
        """Получить спутниковый снимок участка."""
        result = await infrastructure_get_satellite_image(
            yandex_client,
            lon,
            lat,
            zoom,
            width,
            height,
            layer,
        )
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="infrastructure_get_satellite_image",
            description=(
                "Получение URL спутникового снимка земельного участка через Yandex Static API. "
                "Доступны слои: sat (спутник), map (схема), hybrid (гибрид). "
                "Масштаб от 1 до 17 (15 - оптимально для участка). "
                "Полезно для визуального анализа местности, окружения, подъездов."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "lon": {
                        "type": "number",
                        "description": "Долгота центра карты",
                    },
                    "lat": {
                        "type": "number",
                        "description": "Широта центра карты",
                    },
                    "zoom": {
                        "type": "integer",
                        "description": "Масштаб карты (1-17)",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 17,
                    },
                    "width": {
                        "type": "integer",
                        "description": "Ширина изображения (пиксели)",
                        "default": 600,
                        "minimum": 100,
                        "maximum": 1024,
                    },
                    "height": {
                        "type": "integer",
                        "description": "Высота изображения (пиксели)",
                        "default": 400,
                        "minimum": 100,
                        "maximum": 1024,
                    },
                    "layer": {
                        "type": "string",
                        "description": "Слой карты",
                        "enum": ["sat", "map", "hybrid"],
                        "default": "sat",
                    },
                },
                "required": ["lon", "lat"],
            },
        )
    )
