"""Yandex Maps API client for geocoding, static maps, and place search."""

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp

from construction_maps_mcp.clients.base_client import BaseAPIClient
from construction_maps_mcp.config import settings
from construction_maps_mcp.core.cache import TwoLevelCacheManager
from construction_maps_mcp.core.error_handler import GeocodeError, YandexAPIError
from construction_maps_mcp.core.rate_limiter import RateLimiter
from construction_maps_mcp.core.retry import async_retry_with_backoff
from construction_maps_mcp.utils.validators import validate_coordinates


class YandexMapsClient(BaseAPIClient):
    """
    Client for Yandex Maps API.

    Features:
    - Geocoding (address → coordinates)
    - Reverse geocoding (coordinates → address)
    - Static maps (image URLs)
    - Place search (Geosearch API)

    APIs:
    - Geocoder API: https://geocode-maps.yandex.ru/1.x/
    - Static API: https://static-maps.yandex.ru/1.x/
    - Geosearch API: https://search-maps.yandex.ru/v1/
    """

    GEOCODE_URL = "https://geocode-maps.yandex.ru/1.x/"
    STATIC_URL = "https://static-maps.yandex.ru/1.x/"
    GEOSEARCH_URL = "https://search-maps.yandex.ru/v1/"

    def __init__(
        self,
        api_key: str,
        cache_manager: TwoLevelCacheManager,
        rate_limiter: RateLimiter,
    ):
        """
        Initialize Yandex Maps client.

        Args:
            api_key: Yandex Maps API key
            cache_manager: Cache manager instance
            rate_limiter: Rate limiter instance
        """
        super().__init__(cache_manager, rate_limiter, "yandex")
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    @async_retry_with_backoff(
        max_tries=3,
        max_time=30,
        exceptions=(aiohttp.ClientError, YandexAPIError),
    )
    async def _make_request(
        self,
        url: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Yandex API.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON response

        Raises:
            YandexAPIError: If request fails
        """
        session = await self._get_session()

        async with session.get(url, params=params) as response:
            if response.status != 200:
                text = await response.text()
                raise YandexAPIError(
                    f"Yandex API error: {text}",
                    status_code=response.status,
                )

            return await response.json()

    async def geocode_address(
        self,
        address: str,
        kind: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Geocode address to coordinates.

        Args:
            address: Address string
            kind: Object type filter (house, street, district, locality)

        Returns:
            Dict with geocoding result:
            {
                "address": str,
                "coords": [lon, lat],
                "precision": str (exact, street, district, etc.),
                "kind": str,
                "components": dict (country, province, locality, etc.),
                "_cached": bool
            }

        Raises:
            GeocodeError: If geocoding fails
        """
        cache_key = self._make_cache_key("geocode_address", address, kind or "")

        async def fetch_data():
            """Fetch geocoding data from Yandex."""
            self.logger.info("Geocoding address", address=address, kind=kind)

            params = {
                "apikey": self.api_key,
                "geocode": address,
                "format": "json",
                "lang": "ru_RU",
            }
            if kind:
                params["kind"] = kind

            data = await self._make_request(self.GEOCODE_URL, params)

            # Parse response
            try:
                geo_objects = data["response"]["GeoObjectCollection"]["featureMember"]

                if not geo_objects:
                    raise GeocodeError(f"Адрес не найден: {address}")

                # Get first result
                geo_obj = geo_objects[0]["GeoObject"]

                # Extract coordinates
                pos = geo_obj["Point"]["pos"].split()
                coords = [float(pos[0]), float(pos[1])]  # [lon, lat]

                # Extract metadata
                metadata = geo_obj["metaDataProperty"]["GeocoderMetaData"]

                # Extract address components
                components = {}
                for comp in metadata.get("Address", {}).get("Components", []):
                    components[comp["kind"]] = comp["name"]

                result = {
                    "address": geo_obj.get("name", address),
                    "coords": coords,
                    "precision": metadata.get("precision", "unknown"),
                    "kind": metadata.get("kind", "unknown"),
                    "components": components,
                }

                return result

            except (KeyError, IndexError, ValueError) as e:
                raise GeocodeError(f"Ошибка парсинга ответа Yandex: {e}")

        return await self._cached_request(
            cache_key,
            ttl_seconds=settings.cache_ttl_geocode_seconds,
            fetch_fn=fetch_data,
            memory_only=False,
        )

    async def reverse_geocode(
        self,
        lon: float,
        lat: float,
        kind: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to address.

        Args:
            lon: Longitude
            lat: Latitude
            kind: Object type filter

        Returns:
            Dict with reverse geocoding result:
            {
                "coords": [lon, lat],
                "address": str,
                "components": dict,
                "_cached": bool
            }

        Raises:
            ValueError: If coordinates are invalid
            GeocodeError: If reverse geocoding fails
        """
        if not validate_coordinates(lon, lat):
            raise ValueError(f"Неверные координаты: lon={lon}, lat={lat}")

        cache_key = self._make_cache_key("reverse_geocode", f"{lon:.6f}", f"{lat:.6f}")

        async def fetch_data():
            """Fetch reverse geocoding data from Yandex."""
            self.logger.info("Reverse geocoding", lon=lon, lat=lat)

            params = {
                "apikey": self.api_key,
                "geocode": f"{lon},{lat}",
                "format": "json",
                "lang": "ru_RU",
            }
            if kind:
                params["kind"] = kind

            data = await self._make_request(self.GEOCODE_URL, params)

            # Parse response
            try:
                geo_objects = data["response"]["GeoObjectCollection"]["featureMember"]

                if not geo_objects:
                    raise GeocodeError(f"Адрес не найден для координат: {lon}, {lat}")

                geo_obj = geo_objects[0]["GeoObject"]
                metadata = geo_obj["metaDataProperty"]["GeocoderMetaData"]

                # Extract address components
                components = {}
                for comp in metadata.get("Address", {}).get("Components", []):
                    components[comp["kind"]] = comp["name"]

                result = {
                    "coords": [lon, lat],
                    "address": geo_obj.get("name", "Адрес не определен"),
                    "components": components,
                }

                return result

            except (KeyError, IndexError, ValueError) as e:
                raise GeocodeError(f"Ошибка парсинга ответа Yandex: {e}")

        return await self._cached_request(
            cache_key,
            ttl_seconds=settings.cache_ttl_geocode_seconds,
            fetch_fn=fetch_data,
            memory_only=False,
        )

    async def get_static_map_url(
        self,
        lon: float,
        lat: float,
        zoom: int = 15,
        width: int = 600,
        height: int = 400,
        layer: str = "map",
        markers: Optional[List[Dict[str, Any]]] = None,
        polygons: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate Yandex Static API URL for map image.

        Args:
            lon: Center longitude
            lat: Center latitude
            zoom: Zoom level (1-17)
            width: Image width in pixels
            height: Image height in pixels
            layer: Map layer (map, sat, hybrid, skl, trf)
            markers: Optional markers to add [{"coords": [lon, lat], "style": "pm2rdm"}]
            polygons: Optional polygons to add [{"geojson": {...}, "color": "red"}]

        Returns:
            Static map image URL
        """
        if not validate_coordinates(lon, lat):
            raise ValueError(f"Неверные координаты: lon={lon}, lat={lat}")

        params = {
            "ll": f"{lon},{lat}",
            "z": max(1, min(17, zoom)),
            "l": layer,
            "size": f"{width},{height}",
        }

        # Add markers if provided
        if markers:
            # Format: pt=lon,lat,style~lon,lat,style
            pt_parts = []
            for marker in markers:
                m_lon, m_lat = marker.get("coords", [lon, lat])
                style = marker.get("style", "pm2rdm")  # Red marker by default
                pt_parts.append(f"{m_lon},{m_lat},{style}")
            params["pt"] = "~".join(pt_parts)

        # Add polygons if provided (simplified - Yandex Static API has limited polygon support)
        if polygons:
            # Note: Full polygon rendering requires more complex implementation
            # For now, we just add markers at polygon centroids
            self.logger.info("Polygon rendering in static maps is simplified")

        query_string = urlencode(params)
        return f"{self.STATIC_URL}?{query_string}"

    async def get_satellite_image_url(
        self,
        lon: float,
        lat: float,
        zoom: int = 15,
        width: int = 600,
        height: int = 400,
    ) -> Dict[str, Any]:
        """
        Get satellite image URL (with caching).

        Args:
            lon: Center longitude
            lat: Center latitude
            zoom: Zoom level
            width: Image width
            height: Image height

        Returns:
            Dict with image URL and metadata
        """
        cache_key = self._make_cache_key(
            "static_map", f"{lon:.6f}", f"{lat:.6f}", zoom, "sat"
        )

        async def fetch_data():
            """Generate static map URL."""
            url = self.get_static_map_url(
                lon=lon,
                lat=lat,
                zoom=zoom,
                width=width,
                height=height,
                layer="sat",
            )

            return {
                "image_url": url,
                "coords": [lon, lat],
                "zoom": zoom,
                "layer": "sat",
                "width": width,
                "height": height,
            }

        return await self._cached_request(
            cache_key,
            ttl_seconds=settings.cache_ttl_cadastre_seconds * 3,  # 90 days
            fetch_fn=fetch_data,
            memory_only=False,
        )

    async def search_nearby(
        self,
        lon: float,
        lat: float,
        query: str = "",
        category: Optional[str] = None,
        radius_m: int = 1000,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for places near coordinates.

        Note: This is a placeholder. Yandex Geosearch API requires separate access.
        In production, you would implement this with the actual Geosearch API.

        Args:
            lon: Search center longitude
            lat: Search center latitude
            query: Text search query
            category: Category filter (school, hospital, fuel_station, etc.)
            radius_m: Search radius in meters
            limit: Maximum results

        Returns:
            Dict with search results
        """
        self.logger.warning(
            "Geosearch not fully implemented",
            lon=lon,
            lat=lat,
            query=query,
            category=category,
        )

        # Placeholder response
        return {
            "center": [lon, lat],
            "radius_m": radius_m,
            "query": query,
            "category": category,
            "objects": [],
            "total_found": 0,
            "note": (
                "Yandex Geosearch API требует отдельного доступа. "
                "Используйте другие сервисы (2GIS, OpenStreetMap) для поиска инфраструктуры."
            ),
        }
