"""MCP server with tool registration."""

import asyncio
import sys
from pathlib import Path

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server

from construction_maps_mcp import __version__
from construction_maps_mcp.config import settings
from construction_maps_mcp.core.cache import InMemoryCache, SQLiteCache, TwoLevelCacheManager
from construction_maps_mcp.core.rate_limiter import RateLimiter

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        (
            structlog.processors.JSONRenderer()
            if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer()
        ),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def setup_cache() -> TwoLevelCacheManager:
    """Initialize two-level cache system."""
    logger.info(
        "Initializing cache",
        cache_dir=str(settings.cache_dir),
        cache_db=str(settings.cache_db_path),
    )

    # Initialize SQLite cache
    sqlite_cache = SQLiteCache(settings.cache_db_path)

    # Initialize in-memory cache
    memory_cache = InMemoryCache(maxsize=1000, default_ttl=3600)

    # Create two-level manager
    cache_manager = TwoLevelCacheManager(sqlite_cache, memory_cache)

    # Cleanup expired entries
    deleted = await cache_manager.cleanup()
    if deleted > 0:
        logger.info("Cache cleanup completed", deleted_entries=deleted)

    # Log cache stats
    stats = await cache_manager.get_stats()
    logger.info("Cache initialized", **stats)

    return cache_manager


async def setup_rate_limiters() -> dict:
    """Initialize rate limiters for APIs."""
    return {
        "yandex": RateLimiter(settings.yandex_rate_limit_rpm),
        "rosreestr": RateLimiter(settings.rosreestr_rate_limit_rpm),
    }


async def main():
    """Run MCP server."""
    logger.info(
        "Starting Construction Maps MCP Server",
        version=__version__,
        server_name=settings.mcp_server_name,
    )

    # Validate configuration
    try:
        logger.info(
            "Configuration loaded",
            cache_dir=str(settings.cache_dir),
            yandex_rpm=settings.yandex_rate_limit_rpm,
            rosreestr_rpm=settings.rosreestr_rate_limit_rpm,
            log_level=settings.log_level,
        )
    except Exception as e:
        logger.error("Configuration error", error=str(e))
        sys.exit(1)

    # Initialize cache
    try:
        cache_manager = await setup_cache()
    except Exception as e:
        logger.error("Failed to initialize cache", error=str(e))
        sys.exit(1)

    # Initialize rate limiters
    rate_limiters = await setup_rate_limiters()
    logger.info("Rate limiters initialized", limiters=list(rate_limiters.keys()))

    # Create MCP server
    server = Server(settings.mcp_server_name)

    # Initialize API clients
    from construction_maps_mcp.clients.rosreestr_client import RosreestrClient
    from construction_maps_mcp.clients.yandex_client import YandexMapsClient

    rosreestr_client = RosreestrClient(
        cache_manager=cache_manager,
        rate_limiter=rate_limiters["rosreestr"],
    )
    logger.info("Rosreestr client initialized")

    yandex_client = YandexMapsClient(
        api_key=settings.yandex_maps_api_key,
        cache_manager=cache_manager,
        rate_limiter=rate_limiters["yandex"],
    )
    logger.info("Yandex Maps client initialized")

    # Register all tools
    from construction_maps_mcp.tools import cadastre, geocoding, geometry, infrastructure, visualization

    cadastre.register_tools(server, rosreestr_client)
    logger.info("Cadastre tools registered", count=3)

    geocoding.register_tools(server, yandex_client)
    logger.info("Geocoding tools registered", count=3)

    geometry.register_tools(server)
    logger.info("Geometry tools registered", count=4)

    infrastructure.register_tools(server, yandex_client)
    logger.info("Infrastructure tools registered", count=3)

    visualization.register_tools(server, yandex_client)
    logger.info("Visualization tools registered", count=3)

    total_tools = 16
    logger.info(
        "MCP server ready",
        tools_registered=total_tools,
    )

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server started, listening on stdio")
        try:
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
        except Exception as e:
            logger.error("Server error", error=str(e))
            raise
        finally:
            # Cleanup
            await yandex_client.close()
            await cache_manager.close()
            logger.info("Server shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
