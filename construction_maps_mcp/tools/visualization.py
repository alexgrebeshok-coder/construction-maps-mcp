"""MCP tools for visualization and export."""

import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from shapely.geometry import shape, mapping

from construction_maps_mcp.core.error_handler import handle_tool_error
from construction_maps_mcp.utils.formatters import format_error


async def visualization_generate_static_map(
    yandex_client,
    center_coords: List[float],
    markers: Optional[List[Dict[str, Any]]] = None,
    polygons: Optional[List[Dict[str, Any]]] = None,
    zoom: int = 14,
    width: int = 600,
    height: int = 400,
    layer: str = "map",
) -> str:
    """
    Generate static map with markers and polygons.

    Args:
        yandex_client: Yandex API client
        center_coords: Map center [lon, lat]
        markers: List of markers [{"coords": [lon, lat], "label": "A"}]
        polygons: List of polygons [{"geojson": {...}, "color": "red"}]
        zoom: Zoom level (1-17)
        width: Image width
        height: Image height
        layer: Map layer (map, sat, hybrid)

    Returns:
        Markdown-formatted result with map URL
    """
    try:
        center_lon, center_lat = center_coords

        # Build map URL with markers and polygons
        map_url = await yandex_client.get_static_map_url(
            lon=center_lon,
            lat=center_lat,
            zoom=zoom,
            width=width,
            height=height,
            layer=layer,
            markers=markers,
            polygons=polygons,
        )

        md = f"""# Статическая карта

**Центр**: {center_lat:.6f}°N, {center_lon:.6f}°E
**Масштаб**: {zoom}
**Слой**: {layer}
**Размер**: {width}x{height}px

"""

        if markers:
            md += f"**Маркеры**: {len(markers)} шт.\n"

        if polygons:
            md += f"**Полигоны**: {len(polygons)} шт.\n"

        md += f"""
**URL карты**:
```
{map_url}
```

![Карта]({map_url})

**Использование**:
Эта статическая карта подходит для:
- Включения в отчеты и презентации
- Документации проектов
- Визуализации расположения участков
- Печатных материалов

**Источник**: Yandex Static API
"""

        return md

    except Exception as e:
        error_dict = await handle_tool_error("visualization_generate_static_map", e)
        return format_error(error_dict)


async def visualization_export_geojson(
    geometries: List[Dict[str, Any]],
    properties: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Export geometries to GeoJSON FeatureCollection.

    Args:
        geometries: List of GeoJSON geometries
        properties: Optional list of properties for each geometry

    Returns:
        Markdown-formatted GeoJSON
    """
    try:
        # Validate geometries
        features = []

        for i, geom in enumerate(geometries):
            # Validate geometry using shapely
            try:
                geom_obj = shape(geom)
                if not geom_obj.is_valid:
                    geom_obj = geom_obj.buffer(0)  # Fix invalid geometry

                # Get properties
                props = properties[i] if properties and i < len(properties) else {}

                feature = {
                    "type": "Feature",
                    "geometry": mapping(geom_obj),
                    "properties": props,
                }
                features.append(feature)

            except Exception as e:
                # Skip invalid geometry
                continue

        # Create FeatureCollection
        feature_collection = {
            "type": "FeatureCollection",
            "features": features,
        }

        # Format as JSON
        geojson_str = json.dumps(feature_collection, ensure_ascii=False, indent=2)

        md = f"""# Экспорт GeoJSON

**Формат**: GeoJSON FeatureCollection
**Объектов**: {len(features)}

```json
{geojson_str}
```

**Использование**:
Этот GeoJSON можно использовать в:
- QGIS, ArcGIS и других ГИС
- Веб-картах (Leaflet, Mapbox, Yandex Maps API)
- PostGIS базах данных
- Геопространственном анализе

**Стандарт**: RFC 7946 (GeoJSON)
"""

        return md

    except Exception as e:
        error_dict = await handle_tool_error("visualization_export_geojson", e)
        return format_error(error_dict)


async def visualization_export_to_json(
    data: Dict[str, Any],
    title: str = "Экспорт данных",
) -> str:
    """
    Export any data to formatted JSON.

    Args:
        data: Data to export
        title: Title for the export

    Returns:
        Markdown-formatted JSON
    """
    try:
        # Format as JSON
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        md = f"""# {title}

```json
{json_str}
```

**Размер данных**: {len(json_str)} символов

**Использование**:
Этот JSON можно использовать для:
- Интеграции с другими системами
- Хранения данных
- Обработки в скриптах
- API запросов
"""

        return md

    except Exception as e:
        error_dict = await handle_tool_error("visualization_export_to_json", e)
        return format_error(error_dict)


def register_tools(
    server: Server,
    yandex_client,
) -> None:
    """
    Register visualization tools with MCP server.

    Args:
        server: MCP server instance
        yandex_client: Yandex API client
    """

    # Tool 1: Generate static map
    @server.call_tool()
    async def visualization_generate_static_map_tool(
        center_coords: List[float],
        markers: Optional[List[Dict[str, Any]]] = None,
        polygons: Optional[List[Dict[str, Any]]] = None,
        zoom: int = 14,
        width: int = 600,
        height: int = 400,
        layer: str = "map",
    ) -> list[TextContent]:
        """Генерация статической карты с маркерами и полигонами."""
        result = await visualization_generate_static_map(
            yandex_client,
            center_coords,
            markers,
            polygons,
            zoom,
            width,
            height,
            layer,
        )
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="visualization_generate_static_map",
            description=(
                "Генерация статической карты с маркерами и полигонами через Yandex Static API. "
                "Можно добавить маркеры (точки с подписями) и полигоны (границы участков). "
                "Доступны слои: map (схема), sat (спутник), hybrid (гибрид). "
                "Результат - URL изображения для включения в отчеты, презентации, документацию."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "center_coords": {
                        "type": "array",
                        "description": "Координаты центра карты [lon, lat]",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "markers": {
                        "type": "array",
                        "description": 'Маркеры на карте [{"coords": [lon, lat], "label": "A"}]',
                        "items": {
                            "type": "object",
                            "properties": {
                                "coords": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                },
                                "label": {"type": "string"},
                            },
                        },
                    },
                    "polygons": {
                        "type": "array",
                        "description": 'Полигоны на карте [{"geojson": {...}, "color": "red"}]',
                        "items": {
                            "type": "object",
                            "properties": {
                                "geojson": {"type": "object"},
                                "color": {"type": "string"},
                            },
                        },
                    },
                    "zoom": {
                        "type": "integer",
                        "description": "Масштаб (1-17)",
                        "default": 14,
                        "minimum": 1,
                        "maximum": 17,
                    },
                    "width": {
                        "type": "integer",
                        "description": "Ширина (пиксели)",
                        "default": 600,
                        "minimum": 100,
                        "maximum": 1024,
                    },
                    "height": {
                        "type": "integer",
                        "description": "Высота (пиксели)",
                        "default": 400,
                        "minimum": 100,
                        "maximum": 1024,
                    },
                    "layer": {
                        "type": "string",
                        "description": "Слой карты",
                        "enum": ["map", "sat", "hybrid"],
                        "default": "map",
                    },
                },
                "required": ["center_coords"],
            },
        )
    )

    # Tool 2: Export to GeoJSON
    @server.call_tool()
    async def visualization_export_geojson_tool(
        geometries: List[Dict[str, Any]],
        properties: Optional[List[Dict[str, Any]]] = None,
    ) -> list[TextContent]:
        """Экспорт геометрий в GeoJSON FeatureCollection."""
        result = await visualization_export_geojson(
            geometries,
            properties,
        )
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="visualization_export_geojson",
            description=(
                "Экспорт геометрий в формат GeoJSON FeatureCollection. "
                "Валидирует и исправляет некорректные геометрии. "
                "Результат совместим с QGIS, ArcGIS, Leaflet, Mapbox, PostGIS. "
                "Можно добавить произвольные свойства (properties) к каждому объекту."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "geometries": {
                        "type": "array",
                        "description": "Список GeoJSON геометрий",
                        "items": {"type": "object"},
                        "minItems": 1,
                    },
                    "properties": {
                        "type": "array",
                        "description": "Свойства для каждой геометрии (опционально)",
                        "items": {"type": "object"},
                    },
                },
                "required": ["geometries"],
            },
        )
    )

    # Tool 3: Export to JSON
    @server.call_tool()
    async def visualization_export_to_json_tool(
        data: Dict[str, Any],
        title: str = "Экспорт данных",
    ) -> list[TextContent]:
        """Экспорт данных в форматированный JSON."""
        result = await visualization_export_to_json(
            data,
            title,
        )
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="visualization_export_to_json",
            description=(
                "Экспорт любых данных в форматированный JSON. "
                "Полезно для сохранения результатов анализа, "
                "интеграции с другими системами, создания отчетов. "
                "Поддерживает кириллицу (ensure_ascii=False)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "Данные для экспорта",
                    },
                    "title": {
                        "type": "string",
                        "description": "Заголовок экспорта",
                        "default": "Экспорт данных",
                    },
                },
                "required": ["data"],
            },
        )
    )
