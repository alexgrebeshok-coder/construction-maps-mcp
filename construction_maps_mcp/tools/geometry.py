"""MCP tools for geometric operations using Shapely."""

import json
from typing import Any, Dict

from mcp.server import Server
from mcp.types import Tool, TextContent
from shapely.geometry import shape, Point
from shapely.ops import transform
import pyproj

from construction_maps_mcp.core.error_handler import handle_tool_error
from construction_maps_mcp.utils.formatters import format_geometry_result, format_error


def geometry_calculate_area(geometry_geojson: dict, unit: str = "m2") -> str:
    """
    Calculate area of a polygon.

    Args:
        geometry_geojson: GeoJSON geometry (Polygon or MultiPolygon)
        unit: Unit of measurement (m2, ha, km2)

    Returns:
        Markdown-formatted area result
    """
    try:
        # Parse GeoJSON to Shapely geometry
        geom = shape(geometry_geojson)

        # Project to metric coordinate system for accurate area calculation
        # Use WGS84 to UTM projection
        wgs84 = pyproj.CRS("EPSG:4326")
        # Auto-detect UTM zone based on geometry centroid
        centroid = geom.centroid
        utm_zone = int((centroid.x + 180) / 6) + 1
        hemisphere = "north" if centroid.y >= 0 else "south"
        utm_crs = pyproj.CRS(f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84")

        project = pyproj.Transformer.from_crs(
            wgs84, utm_crs, always_xy=True
        ).transform
        geom_projected = transform(project, geom)

        # Calculate area in square meters
        area_m2 = geom_projected.area

        # Convert to requested unit
        conversions = {
            "m2": 1,
            "ha": 1 / 10000,
            "km2": 1 / 1000000,
        }

        area_value = area_m2 * conversions.get(unit, 1)

        data = {
            "area_m2": area_m2,
            "area_ha": area_m2 / 10000,
            "area_km2": area_m2 / 1000000,
            "unit": unit,
            "area_value": area_value,
        }

        return format_geometry_result("area", data)

    except Exception as e:
        error_dict = {
            "error": "geometry_error",
            "message": str(e),
            "retry": False,
            "user_message": f"Ошибка вычисления площади: {str(e)}",
        }
        return format_error(error_dict)


def geometry_check_intersection(
    geometry1_geojson: dict,
    geometry2_geojson: dict,
) -> str:
    """
    Check if two geometries intersect.

    Args:
        geometry1_geojson: First GeoJSON geometry
        geometry2_geojson: Second GeoJSON geometry

    Returns:
        Markdown-formatted intersection result
    """
    try:
        geom1 = shape(geometry1_geojson)
        geom2 = shape(geometry2_geojson)

        intersects = geom1.intersects(geom2)

        data = {"intersects": intersects}

        if intersects:
            intersection = geom1.intersection(geom2)

            # Calculate intersection area if applicable
            if intersection.geom_type in ["Polygon", "MultiPolygon"]:
                # Project for accurate area
                wgs84 = pyproj.CRS("EPSG:4326")
                centroid = intersection.centroid
                utm_zone = int((centroid.x + 180) / 6) + 1
                hemisphere = "north" if centroid.y >= 0 else "south"
                utm_crs = pyproj.CRS(
                    f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84"
                )

                project = pyproj.Transformer.from_crs(
                    wgs84, utm_crs, always_xy=True
                ).transform
                intersection_projected = transform(project, intersection)

                data["intersection_area_m2"] = intersection_projected.area
                data["intersection_geometry"] = intersection.__geo_interface__

        return format_geometry_result("intersection", data)

    except Exception as e:
        error_dict = {
            "error": "geometry_error",
            "message": str(e),
            "retry": False,
            "user_message": f"Ошибка проверки пересечения: {str(e)}",
        }
        return format_error(error_dict)


def geometry_measure_distance(
    from_coords: list,
    to_coords: list,
    unit: str = "m",
) -> str:
    """
    Measure geodesic distance between two points.

    Args:
        from_coords: Origin coordinates [lon, lat]
        to_coords: Destination coordinates [lon, lat]
        unit: Unit (m, km)

    Returns:
        Markdown-formatted distance result
    """
    try:
        from_lon, from_lat = from_coords
        to_lon, to_lat = to_coords

        # Use geodesic distance calculation
        geod = pyproj.Geod(ellps="WGS84")
        _, _, distance_m = geod.inv(from_lon, from_lat, to_lon, to_lat)

        data = {
            "from": from_coords,
            "to": to_coords,
            "distance_m": distance_m,
            "distance_km": distance_m / 1000,
        }

        return format_geometry_result("distance", data)

    except Exception as e:
        error_dict = {
            "error": "geometry_error",
            "message": str(e),
            "retry": False,
            "user_message": f"Ошибка измерения расстояния: {str(e)}",
        }
        return format_error(error_dict)


def geometry_buffer(geometry_geojson: dict, distance_m: float) -> str:
    """
    Create buffer around geometry.

    Args:
        geometry_geojson: GeoJSON geometry
        distance_m: Buffer distance in meters

    Returns:
        Markdown-formatted buffer result
    """
    try:
        geom = shape(geometry_geojson)

        # Project to metric system for accurate buffer
        wgs84 = pyproj.CRS("EPSG:4326")
        centroid = geom.centroid
        utm_zone = int((centroid.x + 180) / 6) + 1
        hemisphere = "north" if centroid.y >= 0 else "south"
        utm_crs = pyproj.CRS(f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84")

        project = pyproj.Transformer.from_crs(wgs84, utm_crs, always_xy=True).transform
        project_back = pyproj.Transformer.from_crs(
            utm_crs, wgs84, always_xy=True
        ).transform

        geom_projected = transform(project, geom)
        buffered_projected = geom_projected.buffer(distance_m)
        buffered = transform(project_back, buffered_projected)

        data = {
            "original_area_m2": geom_projected.area,
            "buffer_area_m2": buffered_projected.area,
            "buffered_geometry": buffered.__geo_interface__,
            "buffer_distance_m": distance_m,
        }

        return format_geometry_result("buffer", data)

    except Exception as e:
        error_dict = {
            "error": "geometry_error",
            "message": str(e),
            "retry": False,
            "user_message": f"Ошибка создания буфера: {str(e)}",
        }
        return format_error(error_dict)


def register_tools(server: Server) -> None:
    """
    Register geometry tools with MCP server.

    Args:
        server: MCP server instance
    """

    # Tool 1: Calculate area
    @server.call_tool()
    async def geometry_calculate_area_tool(
        geometry: dict,
        unit: str = "m2",
    ) -> list[TextContent]:
        """Рассчитать площадь полигона."""
        result = geometry_calculate_area(geometry, unit)
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="geometry_calculate_area",
            description=(
                "Расчет площади полигона (участка) в квадратных метрах, гектарах или квадратных километрах. "
                "Принимает GeoJSON геометрию и возвращает точную площадь с учетом проекции."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "geometry": {
                        "type": "object",
                        "description": "GeoJSON геометрия (Polygon или MultiPolygon)",
                    },
                    "unit": {
                        "type": "string",
                        "description": "Единица измерения",
                        "enum": ["m2", "ha", "km2"],
                        "default": "m2",
                    },
                },
                "required": ["geometry"],
            },
        )
    )

    # Tool 2: Check intersection
    @server.call_tool()
    async def geometry_check_intersection_tool(
        geometry1: dict,
        geometry2: dict,
    ) -> list[TextContent]:
        """Проверить пересечение двух участков."""
        result = geometry_check_intersection(geometry1, geometry2)
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="geometry_check_intersection",
            description=(
                "Проверка пересечения границ двух земельных участков. "
                "Возвращает информацию о наличии пересечения и площадь наложения (если есть). "
                "Полезно для выявления конфликтов границ."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "geometry1": {
                        "type": "object",
                        "description": "GeoJSON геометрия первого участка",
                    },
                    "geometry2": {
                        "type": "object",
                        "description": "GeoJSON геометрия второго участка",
                    },
                },
                "required": ["geometry1", "geometry2"],
            },
        )
    )

    # Tool 3: Measure distance
    @server.call_tool()
    async def geometry_measure_distance_tool(
        from_coords: list,
        to_coords: list,
        unit: str = "m",
    ) -> list[TextContent]:
        """Измерить расстояние между двумя точками."""
        result = geometry_measure_distance(from_coords, to_coords, unit)
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="geometry_measure_distance",
            description=(
                "Измерение геодезического расстояния между двумя точками. "
                "Использует эллипсоид WGS84 для точного расчета расстояний. "
                "Возвращает расстояние в метрах и километрах."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from_coords": {
                        "type": "array",
                        "description": "Координаты начальной точки [lon, lat]",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "to_coords": {
                        "type": "array",
                        "description": "Координаты конечной точки [lon, lat]",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "unit": {
                        "type": "string",
                        "description": "Единица измерения",
                        "enum": ["m", "km"],
                        "default": "m",
                    },
                },
                "required": ["from_coords", "to_coords"],
            },
        )
    )

    # Tool 4: Create buffer
    @server.call_tool()
    async def geometry_buffer_tool(
        geometry: dict,
        distance_m: float,
    ) -> list[TextContent]:
        """Создать буфер вокруг геометрии."""
        result = geometry_buffer(geometry, distance_m)
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="geometry_buffer",
            description=(
                "Создание буферной зоны вокруг геометрии участка. "
                "Полезно для анализа санитарных зон, зон отступа от границ, "
                "зон охраны и других пространственных ограничений. "
                "Возвращает новую геометрию с буфером и площади."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "geometry": {
                        "type": "object",
                        "description": "GeoJSON геометрия участка",
                    },
                    "distance_m": {
                        "type": "number",
                        "description": "Радиус буфера в метрах",
                        "minimum": 0,
                    },
                },
                "required": ["geometry", "distance_m"],
            },
        )
    )
