"""MCP tools for geocoding operations."""

from typing import Any, Dict

from mcp.server import Server
from mcp.types import Tool, TextContent

from construction_maps_mcp.clients.yandex_client import YandexMapsClient
from construction_maps_mcp.core.error_handler import handle_tool_error
from construction_maps_mcp.utils.formatters import format_geocoding_result, format_error


async def geocode_address_to_coords(
    yandex_client: YandexMapsClient,
    address: str,
    kind: str = None,
) -> str:
    """
    Geocode address to coordinates.

    Args:
        yandex_client: Yandex Maps API client
        address: Address string
        kind: Object type filter (house, street, district, locality)

    Returns:
        Markdown-formatted geocoding result
    """
    try:
        data = await yandex_client.geocode_address(address=address, kind=kind)
        return format_geocoding_result(data)

    except Exception as e:
        error_dict = await handle_tool_error("geocode_address_to_coords", e)
        return format_error(error_dict)


async def geocode_coords_to_address(
    yandex_client: YandexMapsClient,
    lon: float,
    lat: float,
    kind: str = None,
) -> str:
    """
    Reverse geocode coordinates to address.

    Args:
        yandex_client: Yandex Maps API client
        lon: Longitude
        lat: Latitude
        kind: Object type filter

    Returns:
        Markdown-formatted reverse geocoding result
    """
    try:
        data = await yandex_client.reverse_geocode(lon=lon, lat=lat, kind=kind)
        return format_geocoding_result(data)

    except Exception as e:
        error_dict = await handle_tool_error("geocode_coords_to_address", e)
        return format_error(error_dict)


async def geocode_validate_address(
    yandex_client: YandexMapsClient,
    address: str,
) -> str:
    """
    Validate and normalize address.

    Args:
        yandex_client: Yandex Maps API client
        address: Address to validate

    Returns:
        Markdown-formatted validation result
    """
    try:
        data = await yandex_client.geocode_address(address=address)

        # Check if address was found and normalized
        exists = data.get("coords") is not None
        normalized = data.get("address", address)

        md = f"""# Проверка адреса

**Исходный адрес**: {address}
**Нормализованный адрес**: {normalized}
**Существует**: {'✅ Да' if exists else '❌ Нет'}
"""

        if exists:
            lon, lat = data["coords"]
            md += f"""
**Координаты**: {lat:.6f}°N, {lon:.6f}°E
**Точность**: {data.get('precision', 'неизвестно')}
**Тип объекта**: {data.get('kind', 'неизвестно')}
"""

            if data.get("components"):
                md += "\n## Компоненты адреса\n"
                for key, value in data["components"].items():
                    md += f"- **{key}**: {value}\n"

        return md

    except Exception as e:
        error_dict = await handle_tool_error("geocode_validate_address", e)
        return format_error(error_dict)


def register_tools(
    server: Server,
    yandex_client: YandexMapsClient,
) -> None:
    """
    Register geocoding tools with MCP server.

    Args:
        server: MCP server instance
        yandex_client: Yandex Maps API client
    """

    # Tool 1: Address to coordinates
    @server.call_tool()
    async def geocode_address_to_coords_tool(
        address: str,
        kind: str = None,
    ) -> list[TextContent]:
        """Преобразовать адрес в координаты."""
        result = await geocode_address_to_coords(yandex_client, address, kind)
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="geocode_address_to_coords",
            description=(
                "Геокодирование: преобразование адреса в координаты (lon, lat). "
                "Использует Yandex Maps Geocoder API. "
                "Возвращает координаты, точность геокодирования и компоненты адреса."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Адрес для геокодирования",
                    },
                    "kind": {
                        "type": "string",
                        "description": "Тип объекта для фильтрации (house, street, district, locality)",
                        "enum": ["house", "street", "district", "locality"],
                    },
                },
                "required": ["address"],
            },
        )
    )

    # Tool 2: Coordinates to address
    @server.call_tool()
    async def geocode_coords_to_address_tool(
        lon: float,
        lat: float,
        kind: str = None,
    ) -> list[TextContent]:
        """Преобразовать координаты в адрес (обратное геокодирование)."""
        result = await geocode_coords_to_address(yandex_client, lon, lat, kind)
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="geocode_coords_to_address",
            description=(
                "Обратное геокодирование: преобразование координат в адрес. "
                "Использует Yandex Maps Geocoder API. "
                "Возвращает адрес и его компоненты по заданным координатам."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "lon": {
                        "type": "number",
                        "description": "Долгота (longitude)",
                        "minimum": -180,
                        "maximum": 180,
                    },
                    "lat": {
                        "type": "number",
                        "description": "Широта (latitude)",
                        "minimum": -90,
                        "maximum": 90,
                    },
                    "kind": {
                        "type": "string",
                        "description": "Тип объекта для фильтрации",
                        "enum": ["house", "street", "district", "locality"],
                    },
                },
                "required": ["lon", "lat"],
            },
        )
    )

    # Tool 3: Validate address
    @server.call_tool()
    async def geocode_validate_address_tool(address: str) -> list[TextContent]:
        """Проверить существование адреса и нормализовать его."""
        result = await geocode_validate_address(yandex_client, address)
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="geocode_validate_address",
            description=(
                "Проверка существования адреса и его нормализация. "
                "Возвращает нормализованный адрес, координаты и компоненты адреса. "
                "Полезно для валидации адресов участков перед дальнейшей обработкой."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Адрес для проверки и нормализации",
                    },
                },
                "required": ["address"],
            },
        )
    )
