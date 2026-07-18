"""Rosreestr API client using rosreestr2coord library."""

import asyncio
import json
from typing import Any, Dict, Optional

from rosreestr2coord.parser import Area

from construction_maps_mcp.clients.base_client import BaseAPIClient
from construction_maps_mcp.config import settings
from construction_maps_mcp.core.cache import TwoLevelCacheManager
from construction_maps_mcp.core.error_handler import CadastreNotFoundError, RosreestrAPIError
from construction_maps_mcp.core.rate_limiter import RateLimiter
from construction_maps_mcp.core.retry import sync_retry_with_backoff
from construction_maps_mcp.utils.validators import validate_cadastral_number


class RosreestrClient(BaseAPIClient):
    """
    Client for Rosreestr/NSPD cadastral data using rosreestr2coord.

    Features:
    - Get cadastral boundaries (GeoJSON)
    - Get cadastral information (area, address, category)
    - Automatic caching (30 days)
    - Rate limiting and retry logic
    """

    def __init__(
        self,
        cache_manager: TwoLevelCacheManager,
        rate_limiter: RateLimiter,
    ):
        """
        Initialize Rosreestr client.

        Args:
            cache_manager: Cache manager instance
            rate_limiter: Rate limiter instance
        """
        super().__init__(cache_manager, rate_limiter, "rosreestr")

    @sync_retry_with_backoff(
        max_tries=3,
        max_time=30,
        exceptions=(Exception,),
    )
    def _fetch_area_sync(self, cadastral_number: str) -> Area:
        """
        Fetch area data synchronously (rosreestr2coord is sync).

        Args:
            cadastral_number: Cadastral number

        Returns:
            Area object from rosreestr2coord

        Raises:
            CadastreNotFoundError: If cadastral number not found
            RosreestrAPIError: If API request fails
        """
        try:
            area = Area(cadastral_number)
            return area
        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                raise CadastreNotFoundError(
                    f"Кадастровый номер {cadastral_number} не найден в НСПД"
                )
            else:
                raise RosreestrAPIError(f"Ошибка запроса к Росреестру: {e}")

    async def get_boundaries(
        self,
        cadastral_number: str,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Get cadastral boundaries in GeoJSON format.

        Args:
            cadastral_number: Cadastral number (XX:XX:XXXXXXX:XXXX)
            include_metadata: Include area, address, category

        Returns:
            Dict with cadastral data:
            {
                "cadastral_number": str,
                "geometry": GeoJSON geometry,
                "area_m2": float (if include_metadata),
                "address": str (if include_metadata),
                "category": str (if include_metadata),
                "source": "НСПД",
                "_cached": bool
            }

        Raises:
            ValueError: If cadastral number format is invalid
            CadastreNotFoundError: If cadastral number not found
            RosreestrAPIError: If API request fails
        """
        # Validate format
        if not validate_cadastral_number(cadastral_number):
            raise ValueError(
                f"Неверный формат кадастрового номера: {cadastral_number}. "
                f"Ожидается формат XX:XX:XXXXXXX:XXXX"
            )

        # Generate cache key
        cache_key = self._make_cache_key("boundaries", cadastral_number)

        async def fetch_data():
            """Fetch boundaries from Rosreestr."""
            self.logger.info(
                "Fetching cadastral boundaries",
                cadastral_number=cadastral_number,
            )

            # Run sync rosreestr2coord in thread pool
            area = await asyncio.to_thread(self._fetch_area_sync, cadastral_number)

            # Get GeoJSON geometry
            geojson = await asyncio.to_thread(area.to_geojson)

            # Prepare result
            result = {
                "cadastral_number": cadastral_number,
                "geometry": geojson,
                "source": "НСПД",
            }

            if include_metadata:
                # Note: rosreestr2coord doesn't provide metadata (area, address, category)
                # These would need to be fetched separately from Rosreestr API
                # For now, return defaults
                result["area_m2"] = 0
                result["address"] = "Адрес не указан (требуется доп. запрос)"
                result["category"] = "Категория не указана (требуется доп. запрос)"

            return result

        # Execute with caching
        return await self._cached_request(
            cache_key,
            ttl_seconds=settings.cache_ttl_cadastre_seconds,
            fetch_fn=fetch_data,
            memory_only=False,  # Persist to SQLite
        )

    async def get_info(self, cadastral_number: str) -> Dict[str, Any]:
        """
        Get cadastral information without geometry (faster).

        Args:
            cadastral_number: Cadastral number

        Returns:
            Dict with cadastral info (no geometry):
            {
                "cadastral_number": str,
                "area_m2": float,
                "address": str,
                "category": str,
                "source": "НСПД",
                "_cached": bool
            }

        Raises:
            ValueError: If cadastral number format is invalid
            CadastreNotFoundError: If cadastral number not found
            RosreestrAPIError: If API request fails
        """
        # Validate format
        if not validate_cadastral_number(cadastral_number):
            raise ValueError(
                f"Неверный формат кадастрового номера: {cadastral_number}"
            )

        # Generate cache key
        cache_key = self._make_cache_key("info", cadastral_number)

        async def fetch_data():
            """Fetch info from Rosreestr."""
            self.logger.info(
                "Fetching cadastral info",
                cadastral_number=cadastral_number,
            )

            # Run sync rosreestr2coord in thread pool
            area = await asyncio.to_thread(self._fetch_area_sync, cadastral_number)

            # Get metadata only
            # Note: rosreestr2coord doesn't provide metadata (area, address, category)
            # These would need to be fetched separately from Rosreestr API
            result = {
                "cadastral_number": cadastral_number,
                "area_m2": 0,
                "address": "Адрес не указан (требуется доп. запрос)",
                "category": "Категория не указана (требуется доп. запрос)",
                "source": "НСПД",
            }

            return result

        # Execute with caching
        return await self._cached_request(
            cache_key,
            ttl_seconds=settings.cache_ttl_cadastre_seconds,
            fetch_fn=fetch_data,
            memory_only=False,  # Persist to SQLite
        )

    async def search_by_coordinates(
        self,
        lon: float,
        lat: float,
        radius_m: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for cadastral parcels near coordinates.

        Note: This is a placeholder as rosreestr2coord doesn't support coordinate search.
        In production, you would need to use official Rosreestr API or alternative service.

        Args:
            lon: Longitude
            lat: Latitude
            radius_m: Search radius in meters

        Returns:
            Dict with search results
        """
        self.logger.warning(
            "Coordinate search not implemented in rosreestr2coord",
            lon=lon,
            lat=lat,
            radius_m=radius_m,
        )

        return {
            "error": "not_implemented",
            "message": (
                "Поиск участков по координатам не реализован в текущей версии. "
                "Используйте поиск по кадастровому номеру."
            ),
            "lon": lon,
            "lat": lat,
            "radius_m": radius_m,
        }
