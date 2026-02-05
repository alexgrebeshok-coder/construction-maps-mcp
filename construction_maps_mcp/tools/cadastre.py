"""MCP tools for cadastral data operations."""

from typing import Any, Dict

from mcp.server import Server
from mcp.types import Tool, TextContent

from construction_maps_mcp.clients.rosreestr_client import RosreestrClient
from construction_maps_mcp.clients.yandex_client import YandexMapsClient
from construction_maps_mcp.core.error_handler import handle_tool_error
from construction_maps_mcp.utils.formatters import format_cadastre_info, format_error


async def cadastre_get_boundaries(
    rosreestr_client: RosreestrClient,
    cadastral_number: str,
    include_metadata: bool = True,
) -> str:
    """
    Get cadastral boundaries by cadastral number.

    Args:
        rosreestr_client: Rosreestr API client
        cadastral_number: Cadastral number (XX:XX:XXXXXXX:XXXX)
        include_metadata: Include area, address, category

    Returns:
        Markdown-formatted cadastral information with GeoJSON
    """
    try:
        data = await rosreestr_client.get_boundaries(
            cadastral_number=cadastral_number,
            include_metadata=include_metadata,
        )

        return format_cadastre_info(data)

    except Exception as e:
        error_dict = await handle_tool_error("cadastre_get_boundaries", e)
        return format_error(error_dict)


async def cadastre_get_info(
    rosreestr_client: RosreestrClient,
    cadastral_number: str,
) -> str:
    """
    Get cadastral information without geometry (faster).

    Args:
        rosreestr_client: Rosreestr API client
        cadastral_number: Cadastral number

    Returns:
        Markdown-formatted cadastral information
    """
    try:
        data = await rosreestr_client.get_info(cadastral_number=cadastral_number)

        return format_cadastre_info(data)

    except Exception as e:
        error_dict = await handle_tool_error("cadastre_get_info", e)
        return format_error(error_dict)


async def cadastre_search_by_address(
    rosreestr_client: RosreestrClient,
    yandex_client: YandexMapsClient,
    address: str,
    limit: int = 5,
) -> str:
    """
    Search cadastral numbers by address.

    Workflow:
    1. Geocode address using Yandex Maps
    2. Search parcels near coordinates (placeholder)

    Args:
        rosreestr_client: Rosreestr API client
        yandex_client: Yandex Maps API client
        address: Address to search
        limit: Maximum results

    Returns:
        Markdown-formatted search results
    """
    try:
        # Step 1: Geocode address
        geocode_result = await yandex_client.geocode_address(address)

        coords = geocode_result["coords"]
        lon, lat = coords

        # Step 2: Search parcels (placeholder - not implemented in rosreestr2coord)
        search_result = await rosreestr_client.search_by_coordinates(
            lon=lon,
            lat=lat,
            radius_m=50,
        )

        # Format response
        md = f"""# Поиск участков по адресу

**Запрос**: {address}
**Найденный адрес**: {geocode_result['address']}
**Координаты**: {lat:.6f}°N, {lon:.6f}°E

"""

        if search_result.get("error"):
            md += f"""## ⚠️ Ограничение

{search_result['message']}

**Рекомендация**: Используйте инструмент `cadastre_get_boundaries` с известным кадастровым номером.
"""
        else:
            md += f"**Найдено участков**: {len(search_result.get('results', []))}\n\n"

            for idx, parcel in enumerate(search_result.get("results", []), 1):
                md += f"### {idx}. {parcel['cadastral_number']}\n"
                md += f"- **Адрес**: {parcel.get('address', 'Н/Д')}\n"
                md += f"- **Площадь**: {parcel.get('area_m2', 0)} м²\n"
                md += f"- **Расстояние**: {parcel.get('distance_m', 0)} м\n\n"

        return md

    except Exception as e:
        error_dict = await handle_tool_error("cadastre_search_by_address", e)
        return format_error(error_dict)


def register_tools(
    server: Server,
    rosreestr_client: RosreestrClient,
    yandex_client: YandexMapsClient,
) -> None:
    """
    Register cadastral tools with MCP server.

    Args:
        server: MCP server instance
        rosreestr_client: Rosreestr API client
        yandex_client: Yandex Maps API client
    """

    # Tool 1: Get boundaries
    @server.call_tool()
    async def cadastre_get_boundaries_tool(
        cadastral_number: str,
        include_metadata: bool = True,
    ) -> list[TextContent]:
        """Получить границы земельного участка по кадастровому номеру (GeoJSON)."""
        result = await cadastre_get_boundaries(
            rosreestr_client,
            cadastral_number,
            include_metadata,
        )
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="cadastre_get_boundaries",
            description=(
                "Получение границ земельного участка по кадастровому номеру. "
                "Возвращает GeoJSON геометрию, площадь, адрес и категорию участка из НСПД (Росреестр). "
                "Кадастровый номер должен быть в формате XX:XX:XXXXXXX:XXXX."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cadastral_number": {
                        "type": "string",
                        "description": "Кадастровый номер в формате XX:XX:XXXXXXX:XXXX",
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Включить метаданные (площадь, адрес, категория)",
                        "default": True,
                    },
                },
                "required": ["cadastral_number"],
            },
        )
    )

    # Tool 2: Get info
    @server.call_tool()
    async def cadastre_get_info_tool(cadastral_number: str) -> list[TextContent]:
        """Получить информацию об участке без геометрии (быстрый запрос)."""
        result = await cadastre_get_info(rosreestr_client, cadastral_number)
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="cadastre_get_info",
            description=(
                "Получение информации о земельном участке без геометрии (площадь, адрес, категория). "
                "Быстрее чем cadastre_get_boundaries, если геометрия не нужна."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cadastral_number": {
                        "type": "string",
                        "description": "Кадастровый номер в формате XX:XX:XXXXXXX:XXXX",
                    },
                },
                "required": ["cadastral_number"],
            },
        )
    )

    # Tool 3: Search by address
    @server.call_tool()
    async def cadastre_search_by_address_tool(
        address: str,
        limit: int = 5,
    ) -> list[TextContent]:
        """Поиск кадастровых номеров по адресу."""
        result = await cadastre_search_by_address(
            rosreestr_client,
            yandex_client,
            address,
            limit,
        )
        return [TextContent(type="text", text=result)]

    server.add_tool(
        Tool(
            name="cadastre_search_by_address",
            description=(
                "Поиск земельных участков по адресу. "
                "Сначала геокодирует адрес через Yandex Maps, затем ищет участки рядом. "
                "Примечание: поиск по координатам имеет ограничения в текущей версии."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Адрес для поиска участков",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимальное количество результатов",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20,
                    },
                },
                "required": ["address"],
            },
        )
    )
