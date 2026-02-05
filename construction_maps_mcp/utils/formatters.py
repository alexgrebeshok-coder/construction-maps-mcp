"""Markdown formatters for MCP tool responses."""

from typing import Any, Dict, List, Optional


def format_cadastre_info(data: Dict[str, Any]) -> str:
    """
    Format cadastral information as Markdown.

    Args:
        data: Cadastral data dict

    Returns:
        Markdown-formatted string
    """
    md = f"""# Кадастровый участок {data['cadastral_number']}

## Основные характеристики
- **Площадь**: {data.get('area_m2', 'Н/Д')} м² ({data.get('area_m2', 0) / 10000:.4f} га)
- **Адрес**: {data.get('address', 'Не указан')}
- **Категория**: {data.get('category', 'Н/Д')}
"""

    if data.get('cost_per_m2'):
        md += f"- **Кадастровая стоимость**: {data['cost_per_m2']:,.0f} ₽/м²\n"

    if data.get('permitted_use'):
        md += f"- **Разрешенное использование**: {data['permitted_use']}\n"

    if data.get('geometry'):
        md += "\n## Геометрия\n"
        geom_type = data['geometry'].get('type', 'Unknown')
        coords_count = len(data['geometry'].get('coordinates', [[]])[0])
        md += f"- **Тип**: {geom_type}\n"
        md += f"- **Вершин**: {coords_count}\n"

    md += f"\n**Источник**: {data.get('source', 'НСПД')}"

    if data.get('cached'):
        md += " (из кеша)"

    return md


def format_geocoding_result(data: Dict[str, Any]) -> str:
    """
    Format geocoding result as Markdown.

    Args:
        data: Geocoding result dict

    Returns:
        Markdown-formatted string
    """
    md = "# Результат геокодирования\n\n"

    if data.get('address'):
        md += f"**Адрес**: {data['address']}\n\n"

    if data.get('coords'):
        lon, lat = data['coords']
        md += f"**Координаты**: {lat:.6f}°N, {lon:.6f}°E\n"
        md += f"- Широта: {lat:.6f}\n"
        md += f"- Долгота: {lon:.6f}\n\n"

    if data.get('precision'):
        md += f"**Точность**: {data['precision']}\n"

    if data.get('kind'):
        md += f"**Тип объекта**: {data['kind']}\n"

    if data.get('components'):
        md += "\n## Компоненты адреса\n"
        for key, value in data['components'].items():
            md += f"- **{key}**: {value}\n"

    return md


def format_infrastructure_list(objects: List[Dict[str, Any]], center: List[float]) -> str:
    """
    Format infrastructure objects list as Markdown.

    Args:
        objects: List of infrastructure objects
        center: Center coordinates [lon, lat]

    Returns:
        Markdown-formatted string
    """
    md = f"# Инфраструктура вокруг участка\n\n"
    md += f"**Центр поиска**: {center[1]:.6f}°N, {center[0]:.6f}°E\n"
    md += f"**Найдено объектов**: {len(objects)}\n\n"

    if not objects:
        return md + "_Объекты не найдены_"

    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for obj in objects:
        category = obj.get('category', 'other')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(obj)

    # Format each category
    category_names = {
        'school': '🏫 Школы',
        'hospital': '🏥 Больницы',
        'fuel_station': '⛽ АЗС',
        'pharmacy': '💊 Аптеки',
        'shop': '🛒 Магазины',
        'cafe': '☕ Кафе',
        'bank': '🏦 Банки',
        'other': '📍 Другое',
    }

    for category, category_objects in sorted(by_category.items()):
        md += f"## {category_names.get(category, category)}\n\n"

        for obj in sorted(category_objects, key=lambda x: x.get('distance_m', 0)):
            name = obj.get('name', 'Без названия')
            address = obj.get('address', '')
            distance = obj.get('distance_m', 0)

            md += f"### {name}\n"
            if address:
                md += f"- **Адрес**: {address}\n"
            md += f"- **Расстояние**: {distance:.0f} м ({distance/1000:.2f} км)\n"

            if obj.get('coords'):
                lon, lat = obj['coords']
                md += f"- **Координаты**: {lat:.6f}°N, {lon:.6f}°E\n"

            md += "\n"

    return md


def format_distance_matrix(distances: List[Dict[str, Any]], from_coords: List[float]) -> str:
    """
    Format distance matrix as Markdown table.

    Args:
        distances: List of distance calculations
        from_coords: Origin coordinates [lon, lat]

    Returns:
        Markdown-formatted table
    """
    md = "# Матрица расстояний\n\n"
    md += f"**От точки**: {from_coords[1]:.6f}°N, {from_coords[0]:.6f}°E\n\n"

    md += "| № | Адрес | Расстояние (м) | Расстояние (км) |\n"
    md += "|---|-------|----------------|------------------|\n"

    for idx, dist in enumerate(distances, 1):
        address = dist.get('to_address', 'Н/Д')
        dist_m = dist.get('distance_m', 0)
        dist_km = dist.get('distance_km', 0)
        md += f"| {idx} | {address} | {dist_m:.0f} | {dist_km:.2f} |\n"

    return md


def format_geometry_result(operation: str, data: Dict[str, Any]) -> str:
    """
    Format geometry operation result as Markdown.

    Args:
        operation: Operation name (area, intersection, buffer, etc.)
        data: Result data

    Returns:
        Markdown-formatted string
    """
    md = f"# Геометрическая операция: {operation}\n\n"

    if operation == "area":
        area_m2 = data.get('area_m2', 0)
        area_ha = data.get('area_ha', 0)
        md += f"**Площадь**:\n"
        md += f"- {area_m2:,.2f} м²\n"
        md += f"- {area_ha:.4f} га\n"
        md += f"- {area_ha / 100:.6f} км²\n"

    elif operation == "intersection":
        md += f"**Пересечение**: {'Да' if data.get('intersects') else 'Нет'}\n\n"
        if data.get('intersects') and data.get('intersection_area_m2'):
            area = data['intersection_area_m2']
            md += f"**Площадь пересечения**: {area:,.2f} м² ({area/10000:.4f} га)\n"

    elif operation == "distance":
        dist_m = data.get('distance_m', 0)
        dist_km = data.get('distance_km', 0)
        md += f"**Расстояние**:\n"
        md += f"- {dist_m:,.2f} м\n"
        md += f"- {dist_km:.3f} км\n"

    elif operation == "buffer":
        orig_area = data.get('original_area_m2', 0)
        buff_area = data.get('buffer_area_m2', 0)
        md += f"**Исходная площадь**: {orig_area:,.2f} м²\n"
        md += f"**Площадь с буфером**: {buff_area:,.2f} м²\n"
        md += f"**Увеличение**: {buff_area - orig_area:,.2f} м²\n"

    return md


def format_error(error_dict: Dict[str, Any]) -> str:
    """
    Format error as Markdown (wrapper for error_handler).

    Args:
        error_dict: Error dictionary

    Returns:
        Markdown-formatted error message
    """
    from construction_maps_mcp.core.error_handler import format_error_markdown

    return format_error_markdown(error_dict)
