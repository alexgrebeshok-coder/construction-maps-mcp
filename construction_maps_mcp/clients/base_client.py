"""Base client with common functionality for all API clients."""

from typing import Optional

import structlog

from construction_maps_mcp.core.cache import TwoLevelCacheManager
from construction_maps_mcp.core.rate_limiter import RateLimiter

logger = structlog.get_logger()


class BaseAPIClient:
    """
    Base class for API clients with caching and rate limiting.

    Provides:
    - Cache manager integration
    - Rate limiter integration
    - Structured logging
    """

    def __init__(
        self,
        cache_manager: TwoLevelCacheManager,
        rate_limiter: RateLimiter,
        service_name: str,
    ):
        """
        Initialize base API client.

        Args:
            cache_manager: Two-level cache manager
            rate_limiter: Rate limiter for API requests
            service_name: Name of the service (for logging)
        """
        self.cache = cache_manager
        self.rate_limiter = rate_limiter
        self.service_name = service_name
        self.logger = logger.bind(service=service_name)

    async def _cached_request(
        self,
        cache_key: str,
        ttl_seconds: int,
        fetch_fn,
        memory_only: bool = False,
    ):
        """
        Execute request with caching.

        Args:
            cache_key: Key for caching
            ttl_seconds: Cache TTL in seconds
            fetch_fn: Async function to fetch data if not cached
            memory_only: If True, cache only in memory

        Returns:
            Cached or freshly fetched data
        """
        # Check cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            self.logger.debug("Cache hit", key=cache_key)
            cached_data["_cached"] = True
            return cached_data

        # Cache miss - fetch from API
        self.logger.debug("Cache miss, fetching from API", key=cache_key)

        # Apply rate limiting
        await self.rate_limiter.acquire()

        # Fetch data
        data = await fetch_fn()
        data["_cached"] = False

        # Store in cache
        await self.cache.set(cache_key, data, ttl_seconds, memory_only=memory_only)

        return data

    def _make_cache_key(self, prefix: str, *args) -> str:
        """
        Generate cache key for this service.

        Args:
            prefix: Key prefix
            args: Additional key components

        Returns:
            Cache key string
        """
        return self.cache.make_key(f"{self.service_name}:{prefix}", *args)
