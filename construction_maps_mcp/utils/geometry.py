"""Geometry utilities compatibility module.

This module provides backward compatibility by re-exporting geometry functions
from construction_maps_mcp.tools.geometry. Some parts of the codebase expect
geometry functions to be available from construction_maps_mcp.utils.geometry.

All geometry operations are actually implemented in construction_maps_mcp.tools.geometry.
This module serves as a bridge/compatibility layer.
"""

from construction_maps_mcp.tools.geometry import (
    geometry_calculate_area,
    geometry_check_intersection,
    geometry_measure_distance,
    geometry_buffer,
)

__all__ = [
    "geometry_calculate_area",
    "geometry_check_intersection",
    "geometry_measure_distance",
    "geometry_buffer",
]
